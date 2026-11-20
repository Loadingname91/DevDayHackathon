"""Clair's tool registry (clair-agent.md §10): report_understanding, list_apps, get_app, query_records,
ask_user, propose_changes, and propose_app when api/clair/build.py provides it.

Each tool is bound to a `RunContext` (workspace, user, read level, run, emitter, seen ids); the model
never passes a workspace or user. Inputs are validated with Pydantic first; a failure goes back as an
`is_error` tool result listing the problems so Clair can fix and retry (§10 "Validation and failure").

`propose_changes` is the only write: it stores ONE basted change set through the command service
(`commands.create_change_set`, or `update_ops` when the run already has a draft) and streams the card.
"""
from __future__ import annotations

import copy
import dataclasses
import importlib
import json
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable, Literal
from uuid import UUID

from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .. import db
from .. import workspace as wsp
from ..commands import CommandError, create_change_set, update_ops
from ..commands.ops import parse_ops
from ..commands.service import affected_apps, expand_stitches, is_flagged, load_model, resolve
from ..logic import fmt
from ..logic.clock import parse_value, to_local, window_bounds
from ..models import ChangeSet
from . import brief as brief_mod
from .brief import Brief
from .events import Emitter


# ---------------------------------------------------------------- run context

@dataclass
class RunContext:
    workspace_id: UUID
    user_id: UUID
    tz: str
    run_id: UUID
    thread_id: UUID
    read_level: str
    emitter: Emitter
    source_kind: str = 'text'                  # ChangeSource.kind of the turn ('text' | 'voice')
    source_label: str = 'You typed'
    mode: Literal['live', 'fixture'] = 'live'
    planning: bool = False
    seen: set[str] = field(default_factory=set)
    sources: list[str] = field(default_factory=list)   # app keys, in the order first used
    change_set_id: UUID | None = None
    change_set: dict | None = None             # the last card sent
    understood: bool = False
    ld: wsp.Loaded | None = None
    persist_calls: bool = True                 # tool_calls rows
    asks: int = 0                              # ask_user pauses this run (a card counts as one; at most 2)
    plan_required: bool = False                # the last question had plan_after: propose_app must carry a plan
    built: bool = False                        # propose_app stored a draft: the run costs 10 (§14)
    brief: Brief | None = None                 # the planning brief of a planning run (§12.9, brief.py)

    def loaded(self, fresh: bool = False) -> wsp.Loaded:
        if self.ld is None or fresh:
            with db.connect() as conn:
                self.ld = wsp.load(conn, self.workspace_id)
        return self.ld

    def source(self, app_key: str) -> None:
        if app_key and app_key not in self.sources:
            self.sources.append(app_key)


class ToolError(Exception):
    """Returned to the model as an `is_error` tool result."""


class StoreError(Exception):
    """The draft couldn't be saved (DB down): the run ends with `done {status: error}` (§10)."""


class NeedsUserInput(Exception):
    """ask_user's run() body (§11): never reached, the loop pauses before running tools. A backstop."""


# ---------------------------------------------------------------- input models (§10 signatures)

class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid')


Kind = Literal['receipt', 'fridge', 'pantry', 'schedule', 'calendar', 'syllabus', 'note', 'document', 'request', 'other']
Window = Literal['today', 'week', 'month', 'all']


class SeenItem(Closed):
    name: str
    qty: str | None = None
    state: Literal['plenty', 'low', 'empty', 'not_seen'] | None = None
    confidence: float = Field(1.0, ge=0, le=1)


class ReportUnderstanding(Closed):
    kind: Kind
    summary: str = Field(min_length=1, max_length=300)
    confidence: float = Field(1.0, ge=0, le=1)
    items: list[SeenItem] | None = Field(None, max_length=100)


class NoInput(Closed):
    pass


class GetApp(Closed):
    app: str


class Filter(Closed):
    field: str
    op: Literal['eq', 'ne', 'lt', 'gt', 'within', 'contains']
    value: str | float | bool


class Sort(Closed):
    field: str
    dir: Literal['asc', 'desc']


class QueryRecords(Closed):
    app: str
    collection: str
    where: list[Filter] = Field(default_factory=list)
    window: Window | None = None
    sort: Sort | None = None
    limit: int = Field(20, ge=1, le=50)


class FieldValue(Closed):
    key: str
    value: str


class ClairOp(Closed):
    op: Literal['insert', 'update', 'delete', 'move_occurrence', 'keep']
    app: str
    collection: str
    record_id: str | None = None
    fields: list[FieldValue] = Field(default_factory=list)
    occurrence: str | None = None
    reason: str | None = None
    reason_source: str | None = None
    keep: bool = False
    also: str | None = None
    also_source: str | None = None


class ProposeChanges(Closed):
    title: str = Field(min_length=1, max_length=80)
    summary: str = Field('', max_length=400)
    ops: list[ClairOp] = Field(min_length=1, max_length=100)


# ---- Ask (§10 "Ask")
MAX_ASKS = 2


class AskOptionInput(Closed):
    placeholder: str = Field(min_length=1, max_length=40)
    numeric: bool = False


class AskOption(Closed):
    label: str = Field(min_length=1, max_length=40)
    description: str | None = Field(None, max_length=80)
    input: AskOptionInput | None = None


class AskQuestion(Closed):
    id: str = Field(min_length=1, max_length=40)              # slug, unique in the card ("target")
    header: str = Field(min_length=1, max_length=12)
    question: str = Field(min_length=1, max_length=140)
    options: list[AskOption] = Field(min_length=2, max_length=4)
    multi_select: bool = False
    allow_other: bool = True


class AskUser(Closed):
    question: str | None = Field(None, min_length=1, max_length=140)
    options: list[AskOption] | None = Field(None, min_length=2, max_length=8)
    multi_select: bool = False
    allow_other: bool = True
    questions: list[AskQuestion] | None = Field(None, min_length=1, max_length=3)
    plan_after: bool = False


def _schema(model: type[BaseModel]) -> dict:
    """A strict-ready JSON schema: refs inlined, titles dropped, closed objects (§10 signatures)."""
    raw = model.model_json_schema()
    defs = raw.pop('$defs', {})

    def walk(n):
        if isinstance(n, dict):
            if '$ref' in n:
                return walk(copy.deepcopy(defs[n['$ref'].split('/')[-1]]))
            # Length and range constraints stay in Pydantic (checked inside the tool, §10), not the strict schema.
            out = {k: walk(v) for k, v in n.items() if k != 'properties' and k not in (
                'title', 'default', 'minLength', 'maxLength', 'minItems', 'maxItems', 'minimum', 'maximum',
                'exclusiveMinimum', 'exclusiveMaximum')}
            if isinstance(n.get('properties'), dict):
                out['properties'] = {k: walk(v) for k, v in n['properties'].items()}
            if out.get('type') == 'object':
                out.setdefault('properties', {})
                out['additionalProperties'] = False
            return out
        if isinstance(n, list):
            return [walk(x) for x in n]
        return n
    return walk(raw)


# ---------------------------------------------------------------- helpers

def _norm(s: Any) -> str:
    return ' '.join(unicodedata.normalize('NFKC', str(s)).casefold().split())


def _app(ld: wsp.Loaded, name: str) -> dict:
    a = ld.app(name)
    if a is None:
        n = _norm(name)
        a = next((x for x in ld.apps if _norm(x.get('name', '')) == n or _norm(x['key']) == n), None)
    if a is None:
        raise ToolError(f"No app called {name!r}. Apps: {', '.join(x.get('name', x['key']) for x in ld.apps)}")
    return a


def _private(a: dict) -> bool:
    return not brief_mod.clair_can_read(a)


def _coll(a: dict, key: str) -> dict:
    for c in a.get('collections') or []:
        if c['key'] == key or _norm(c.get('name', '')) == _norm(key):
            return c
    raise ToolError(f"{a['key']} has no collection {key!r}; collections: "
                    f"{', '.join(c['key'] for c in a.get('collections') or [])}")


def _title_of(c: dict | None, props: dict) -> str:
    keys = [(c or {}).get('titleField'), 'name', 'title', 'note', 'store']
    for k in keys:
        if k and props.get(k) not in (None, ''):
            v = props[k]
            return str(v[0]) if isinstance(v, list) and v else str(v)
    return 'Row'


def _when(v: Any, tz: str) -> str:
    try:
        x = parse_value(v, tz)
    except Exception:
        return str(v)
    if hasattr(x, 'hour'):
        lx = to_local(x, tz)
        return f"{lx.strftime('%a')} {fmt.time_label(lx)}"
    return f"{x.strftime('%a')} {x.day} {x.strftime('%b')}"


# ---------------------------------------------------------------- tools

def report_understanding(ctx: RunContext, inp: ReportUnderstanding) -> dict:
    ctx.understood = True
    items = [i.name for i in inp.items] if inp.items else None
    summary = inp.summary
    if ctx.planning and ctx.brief is not None and ctx.brief.apps:
        summary = ctx.brief.understanding()   # the server's facts, word for word (§12.9 step 1), not the model's
    ctx.emitter.emit('understood', {'kind': inp.kind, 'summary': summary, **({'items': items} if items else {})})
    return {'ok': True}


def list_apps(ctx: RunContext, inp: NoInput) -> list[dict]:
    ld = ctx.loaded()
    fc = wsp.faces(ld) if ctx.read_level == 'full' else {}
    out = []
    for a in ld.apps:
        f = fc.get(a['key'])
        out.append({'app': a['key'], 'name': a.get('name', a['key']),
                    'face': f"{f['text']} {f.get('label', '')}".strip() if f and not _private(a) else None,
                    'collections': [c['key'] for c in a.get('collections') or []],
                    **({'private': True} if _private(a) else {})})
    return out


def get_app(ctx: RunContext, inp: GetApp) -> dict:
    ld = ctx.loaded()
    a = _app(ld, inp.app)
    ctx.source(a['key'])
    face = wsp.faces(ld, [a['key']]).get(a['key']) if ctx.read_level == 'full' and not _private(a) else None
    return {'app': a['key'], 'name': a.get('name'), 'face': face,
            'collections': [{'name': c['key'], 'calendar': bool(c.get('calendar')),
                             'fields': [{k: f[k] for k in ('key', 'type', 'options', 'target') if k in f}
                                        for f in c.get('fields') or []]}
                            for c in a.get('collections') or []],
            'stitches': a.get('stitches') or []}


def _match(props: dict, f: Filter, ctx: RunContext) -> bool:
    v = props.get(f.field)
    if f.op == 'within':
        if v is None or not isinstance(f.value, str):
            return False
        try:
            b = window_bounds(f.value, ctx.loaded().now, ctx.tz)
            if b is None:
                return True
            x = parse_value(v, ctx.tz)
            if not hasattr(x, 'hour'):
                from ..logic.clock import midnight
                x = midnight(x, ctx.tz)
            return b[0] <= x < b[1]
        except Exception:
            return False
    if f.op == 'contains':
        return _norm(f.value) in _norm(v if not isinstance(v, list) else ' '.join(map(str, v)))
    if f.op in ('eq', 'ne'):
        eq = (_norm(v) == _norm(f.value)) if not isinstance(f.value, bool) else (bool(v) == f.value)
        return eq if f.op == 'eq' else not eq
    try:
        a, b = float(v), float(f.value)
    except (TypeError, ValueError):
        a, b = str(v), str(f.value)
    return a < b if f.op == 'lt' else a > b


def query_records(ctx: RunContext, inp: QueryRecords) -> dict:
    ld = ctx.loaded()
    a = _app(ld, inp.app)
    if _private(a):
        raise ToolError(f"{a.get('name')} is private: Clair can't read it unless Sam turns that on.")
    c = _coll(a, inp.collection)
    keys = {f.get('key') for f in c.get('fields') or []} | {'id'}
    bad = [f.field for f in inp.where if f.field not in keys] + ([inp.sort.field] if inp.sort and inp.sort.field not in keys else [])
    if bad:
        raise ToolError(f"No field {', '.join(map(repr, bad))} in {a['key']}/{c['key']}; fields: {', '.join(sorted(k for k in keys if k))}")
    ctx.emitter.emit('status', {'text': f"Reading {a.get('name', a['key'])}…"})
    ctx.source(a['key'])
    ref = f"{a['key']}/{c['key']}"
    rows = [r for r in ld.records if r['collection'] == ref]
    rows = [r for r in rows if all(_match(r['properties'], f, ctx) for f in inp.where)]
    if inp.window and inp.window != 'all' and c.get('dateField'):
        dk = c['dateField']
        rows = [r for r in rows if _match(r['properties'], Filter(field=dk, op='within', value=inp.window), ctx)]
    if inp.sort:
        rows.sort(key=lambda r: (r['properties'].get(inp.sort.field) is None, str(r['properties'].get(inp.sort.field))),
                  reverse=inp.sort.dir == 'desc')
    more = len(rows) > inp.limit
    rows = rows[:inp.limit]
    for r in rows:
        ctx.seen.add(r['id'])
    if ctx.read_level != 'full':
        return {'rows': [{'id': r['id']} for r in rows], 'more': more}
    return {'rows': [{'id': r['id'], 'fields': {k: v for k, v in r['properties'].items() if not k.startswith('_')}}
                     for r in rows], 'more': more}


def propose_changes(ctx: RunContext, inp: ProposeChanges) -> dict:
    problems = []
    for i, o in enumerate(inp.ops):
        kind = 'keep' if o.keep else o.op
        if kind != 'insert':
            if not o.record_id:
                problems.append({'op': i, 'field': 'record_id', 'problem': f'{kind} needs record_id'})
            elif o.record_id not in ctx.seen:
                problems.append({'op': i, 'field': 'record_id',
                                 'problem': f'record {o.record_id} was not in the snapshot or a read result this run'})
        if kind in ('keep', 'move_occurrence') and not o.occurrence:
            problems.append({'op': i, 'field': 'occurrence', 'problem': f'{kind} needs occurrence (YYYY-MM-DD)'})
        for k in ('reason_source', 'also_source'):
            v = getattr(o, k)
            if v and v not in ctx.seen:
                problems.append({'op': i, 'field': k, 'problem': f'{v} is not a record read this run'})
        if o.reason and len(o.reason.split()) > 12:
            problems.append({'op': i, 'field': 'reason', 'problem': 'reason is over 12 words'})
    if ctx.planning and ctx.brief is not None:
        problems += [{'problem': p} for p in brief_mod.check_plan(inp.ops, ctx.brief, ctx.loaded())]
    if problems:
        raise ToolError(json.dumps(problems))

    ops = []
    for o in inp.ops:
        d: dict[str, Any] = {'op': 'keep' if o.keep else o.op, 'app': o.app, 'collection': o.collection,
                             'fields': [f.model_dump() for f in o.fields]}
        for k in ('record_id', 'occurrence', 'reason', 'reason_source', 'also', 'also_source'):
            if getattr(o, k) is not None:
                d[k] = getattr(o, k)
        ops.append(d)

    ld = ctx.loaded()
    src = {'kind': ctx.source_kind, 'label': ctx.source_label, 'at': ld.now.isoformat(), 'mode': ctx.mode}
    try:
        with db.transaction(ctx.workspace_id) as conn:
            if ctx.change_set_id is not None:
                cur = conn.execute('select status, version from change_sets where id = %s', (ctx.change_set_id,)).fetchone()
            else:
                cur = None
            if cur is not None and cur['status'] == 'basted':
                update_ops(conn, ctx.workspace_id, ctx.change_set_id, ops, cur['version'])
                conn.execute('update change_sets set title = %s, summary = %s, source = %s where id = %s',
                             (inp.title, inp.summary, Jsonb(src), ctx.change_set_id))
                cs_id = ctx.change_set_id
            else:
                cs_id = create_change_set(conn, ctx.workspace_id, 'clair', 'clair', ops, user_id=ctx.user_id,
                                          title=inp.title, summary=inp.summary, source=src, run_id=ctx.run_id)
            conn.execute('update agent_runs set change_set_id = %s where id = %s', (cs_id, ctx.run_id))
            row = conn.execute('select * from change_sets where id = %s', (cs_id,)).fetchone()
            card = build_card(conn, ctx.workspace_id, ld, row)
    except CommandError as e:
        raise ToolError(json.dumps(e.body.get('issues') or e.body)) from e
    except ToolError:
        raise
    except Exception as e:
        raise StoreError(f"Couldn't save the draft: {e}") from e

    ctx.change_set_id = cs_id
    ctx.change_set = card
    for t in card['targets']:
        ctx.source(t)
    ctx.emitter.emit('proposal', {'change_set': card})
    return {'change_set_id': str(cs_id), 'lines': card['lines'], 'targets': card['targets'],
            'deltas': card['deltas'], 'warnings': []}


def ask_user(ctx: RunContext, inp: AskUser) -> dict:
    raise NeedsUserInput('ask_user pauses the run in the loop body (clair-agent.md §11)')


def check_ask(ctx: RunContext, tool_input: Any) -> AskUser:
    """Validate an ask_user call before pausing (§10 table). Raises ToolError (goes back as is_error)."""
    if ctx.asks >= MAX_ASKS:
        raise ToolError('Question limit reached. Decide or propose with what you have.')
    try:
        inp = AskUser.model_validate(tool_input or {})
    except ValidationError as e:
        raise ToolError(json.dumps([{'field': '.'.join(map(str, err['loc'])), 'problem': err['msg']}
                                    for err in e.errors()]))
    problems = []
    single = inp.question is not None or inp.options is not None
    if single and inp.questions is not None:
        problems.append('Use one form: question + options, or questions.')
    elif single and (inp.question is None or inp.options is None):
        problems.append('A single question needs both question and options (2 to 8).')
    elif not single and inp.questions is None:
        problems.append('Give question + options, or questions (1 to 3).')
    if single and inp.options:
        if any(o.input for o in inp.options):
            problems.append('input is only for a card of questions (questions[]).')
        if len({_norm(o.label) for o in inp.options}) != len(inp.options):
            problems.append('Option labels must be unique.')
    for q in inp.questions or []:
        if len({_norm(o.label) for o in q.options}) != len(q.options):
            problems.append(f'{q.id}: option labels must be unique.')
        if q.multi_select and any(o.input for o in q.options):
            problems.append(f'{q.id}: input is only allowed on a single-select question.')
    if inp.questions and len({q.id for q in inp.questions}) != len(inp.questions):
        problems.append('Question ids must be unique in the card.')
    if inp.plan_after and inp.questions is None:
        problems.append('plan_after goes with a card of questions (questions[]).')
    if problems:
        raise ToolError(json.dumps(problems))
    return inp


def ask_options(inp: AskUser) -> Any:
    """What `clair_questions.options` holds: the option list of a single question, or the card."""
    if inp.questions is None:
        return [{'id': f'o{i + 1}', 'label': o.label, **({'description': o.description} if o.description else {})}
                for i, o in enumerate(inp.options or [])]
    return {'questions': [q.model_dump(exclude_none=True) for q in inp.questions], 'plan_after': inp.plan_after}


def question_event(qid: str, question: str, options: Any, multi: bool, expires_at: str) -> dict:
    """The `question` event data (§2) from a stored clair_questions row."""
    if isinstance(options, list):
        return {'id': qid, 'text': question, 'multi': multi, 'expires_at': expires_at,
                'options': [{'id': o['id'], 'label': o['label'], **({'hint': o['description']} if o.get('description') else {})}
                            for o in options]}
    qs = []
    for q in options['questions']:
        qs.append({'id': q['id'], 'header': q['header'], 'text': q['question'], 'multi': bool(q.get('multi_select')),
                   **({} if q.get('allow_other', True) else {'other': False}),
                   'options': [{'label': o['label'], **({'description': o['description']} if o.get('description') else {}),
                                **({'input': {'placeholder': o['input']['placeholder'],
                                              **({'numeric': True} if o['input'].get('numeric') else {})}}
                                   if o.get('input') else {})} for o in q['options']]})
    return {'id': qid, 'questions': qs, 'plan_after': bool(options.get('plan_after')), 'expires_at': expires_at}


class AnswerError(Exception):
    """The answer doesn't fit the question (422)."""


def answer_result(options: Any, multi: bool, ans: dict) -> dict:
    """The ask_user tool_result body from an `Answer` (§10 "Ask"); raises AnswerError when it doesn't fit."""
    if ans.get('skip'):
        return {'skipped': True}

    def pick(opts: list[dict], choices: list[str] | None, other: str | None, multi: bool, allow_other: bool,
             where: str) -> dict:
        labels = []
        for c in choices or []:
            o = next((o for o in opts if c == o.get('id') or _norm(c) == _norm(o['label'])), None)
            if o is None:
                raise AnswerError(f"{where}: no option {c!r}")
            if o['label'] not in labels:
                labels.append(o['label'])
        if not multi and len(labels) > 1:
            raise AnswerError(f'{where}: pick one option')
        other = (other or '').strip() or None
        takes_value = any(o.get('input') for o in opts if o['label'] in labels)
        if other and not allow_other and not takes_value:
            raise AnswerError(f'{where}: this question has no Other')
        if not labels and not other:
            raise AnswerError(f'{where}: no answer')
        for o in opts:
            if o['label'] in labels and (o.get('input') or {}).get('numeric') and other is not None:
                try:
                    float(other.replace(',', ''))
                except ValueError:
                    raise AnswerError(f'{where}: {o["label"]} takes a number')
        return {'choices': labels, **({'other': other} if other else {})}

    if isinstance(options, list):
        if ans.get('answers'):
            raise AnswerError('this is one question: send choices and other')
        return pick(options, ans.get('choices'), ans.get('other'), multi, True, 'answer')
    answers = ans.get('answers') or {}
    ids = [q['id'] for q in options['questions']]
    extra = [k for k in answers if k not in ids]
    if extra:
        raise AnswerError(f"no question {', '.join(map(repr, extra))}")
    missing = [i for i in ids if i not in answers]
    if missing:
        raise AnswerError(f"answer every question: {', '.join(missing)}")
    out = {}
    for q in options['questions']:
        a = answers[q['id']] or {}
        out[q['id']] = pick(q['options'], a.get('choices'), a.get('other'), bool(q.get('multi_select')),
                            q.get('allow_other', True), q['id'])
    return {'answers': out}


# ---------------------------------------------------------------- propose_app (api/clair/build.py)

def build_module():
    """api/clair/build.py (TOOL and handle(ctx, tool_input)). Imported lazily: build.py imports this module.
    None only if it fails to import, so a broken build module can't take the rest of Clair down."""
    try:
        mod = importlib.import_module(f'{__package__}.build')
    except ImportError:
        return None
    except Exception as e:   # a broken build module must not take Clair down
        print(f'clair: api/clair/build.py failed to import: {e!r}')
        return None
    if isinstance(getattr(mod, 'TOOL', None), dict) and callable(getattr(mod, 'handle', None)):
        return mod
    return None


def _propose_app(ctx: RunContext, mod, tool_input: Any) -> Any:
    """Harness around build.handle (§11). build.handle validates, stores ONE basted `create_app` change set
    (a second call replaces it in place, same id: "Change answers") and emits `plan` then `proposal`.
    The harness adds the one rule that depends on the run: after a plan_after question the call needs a plan."""
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    if ctx.plan_required and not tool_input.get('plan'):
        raise ToolError(json.dumps([{'field': 'plan', 'problem': "This build follows questions: send plan, 2 to 5 "
                                                                 "lines in Sam's words built from the answers."}]))
    res = mod.handle(ctx, tool_input)
    ctx.built = True
    return res


# ---------------------------------------------------------------- the card

def build_card(conn, ws: UUID, ld: wsp.Loaded, row: dict) -> dict:
    """The ChangeSet for the `proposal` event. Uses api/cards.py when it exists; otherwise a minimal
    server-built card (lines, targets, deltas from a dry run, button label)."""
    try:
        from ..cards import expand_change_set   # another agent's module
    except ImportError:
        expand_change_set = None
    if expand_change_set is not None:
        try:
            out = expand_change_set(conn, ld, row)
            return ChangeSet.model_validate(out).model_dump(mode='json', by_alias=True, exclude_none=True)
        except Exception as e:   # keep the demo standing; the fallback is still server-computed
            print(f'clair: cards.expand_change_set failed, using fallback card: {e!r}')
    return ChangeSet.model_validate(fallback_card(conn, ws, ld, row)).model_dump(mode='json', by_alias=True,
                                                                                  exclude_none=True)


def _simulate(ld: wsp.Loaded, model, cmds) -> wsp.Loaded:
    recs = {r['id']: dict(r, properties=copy.deepcopy(r['properties'])) for r in ld.records}
    order = list(recs)
    for c in cmds:
        rid = str(c.record_id)
        if c.kind == 'insert':
            recs[rid] = {'id': rid, 'collection': model.ref(c.collection_id), 'properties': dict(c.fields),
                         'position': 'zz', 'version': 1}
            order.append(rid)
        elif c.kind in ('update', 'move') and rid in recs:
            recs[rid]['properties'].update(c.fields)
        elif c.kind == 'delete':
            recs.pop(rid, None)
    return dataclasses.replace(ld, records=[recs[i] for i in order if i in recs], _ctx=None)


def fallback_card(conn, ws: UUID, ld: wsp.Loaded, row: dict) -> dict:
    model = load_model(conn, ws)
    ops = parse_ops(row['ops'])
    cmds = resolve(conn, ws, model, ops, row['origin'], context='propose')
    allc = cmds + list(expand_stitches(conn, ws, cmds, model))
    by_i: dict[int, list] = {}
    for c in cmds:
        by_i.setdefault(c.op_index, []).append(c)
    page_key = {str(pid): p['properties'].get('key') for pid, p in model.pages.items()}
    targets = [page_key[p] for p in affected_apps(model, allc) if p in page_key]
    recs = {r['id']: r for r in ld.records}
    tz = ld.tz

    def coll_of(app, ck):
        a = ld.app(app) or {}
        return next((c for c in a.get('collections') or [] if c['key'] == ck), None)

    def ref_label(rid):
        r = recs.get(rid or '')
        if not r:
            return None
        a = ld.app(r['collection'].split('/')[0])
        if r['properties'].get('source') == 'google':
            return 'Google Calendar'
        return a.get('name') if a else None

    card_ops, review, app_lines = [], [], {}
    for i, o in enumerate(ops):
        reasons = {k: getattr(o, k) for k in ('reason', 'reason_source', 'also', 'also_source') if getattr(o, k)}
        c0 = (by_i.get(i) or [None])[0]
        coll = coll_of(o.app, o.collection) if o.app else None
        existing = recs.get(o.record_id or '', {}).get('properties', {})
        if o.op == 'insert' and c0 is not None:
            card_ops.append({'op': 'insert', 'ref': model.ref(c0.collection_id), 'values': c0.fields, **reasons,
                             **({'record_id': o.record_id} if o.record_id else {})})
            title, change = _title_of(coll, c0.fields), 'new'
            dk = (coll or {}).get('dateField')
            when = _when(c0.fields[dk], tz) if dk and c0.fields.get(dk) else ''
        elif o.op == 'update' and c0 is not None:
            card_ops.append({'op': 'update', 'rowId': o.record_id, 'values': c0.fields, **reasons})
            title, change, when = _title_of(coll, existing), 'changed', ''
        elif o.op == 'delete':
            card_ops.append({'op': 'delete', 'rowId': o.record_id, **reasons})
            title, change, when = _title_of(coll, existing), 'removed', ''
        elif o.op == 'move_occurrence':
            card_ops.append({'op': 'move_occurrence', 'app': o.app, 'collection': o.collection, 'record_id': o.record_id,
                             'occurrence': o.occurrence.isoformat(),
                             'fields': [{'key': k, 'value': str(v)} for k, v in o.fields.items()], **reasons})
            dk = (coll or {}).get('dateField') or 'at'
            title, change = _title_of(coll, existing), 'moved'
            when = f"{o.occurrence.strftime('%a')} {o.occurrence.day} {o.occurrence.strftime('%b')} → {_when(o.fields.get(dk), tz)}"
        elif o.op == 'keep':
            card_ops.append({'op': 'keep', 'record_id': o.record_id, 'occurrence': o.occurrence.isoformat(), **reasons})
            title, change = _title_of(coll, existing), 'kept'
            when = f"{o.occurrence.strftime('%a')} {o.occurrence.day} {o.occurrence.strftime('%b')}"
        else:
            continue
        app = o.app or (model.app_key(c0.collection_id) if c0 else '')
        review.append({'title': title, 'when': when, 'change': change, 'app': app,
                       **({'reason': o.reason} if o.reason else {}),
                       **({'source': ref_label(o.reason_source)} if ref_label(o.reason_source) else {}),
                       **({'also': o.also} if o.also else {}),
                       **({'also_source': ref_label(o.also_source)} if ref_label(o.also_source) else {})})
        short = f"{title} {when.split(' → ')[-1]}".strip() if change in ('moved', 'kept', 'new') and when else title
        app_lines.setdefault(app, []).append((short, c0, coll))

    expanded = []
    for c in allc:
        if c.kind == 'insert':
            e = {'op': 'insert', 'ref': model.ref(c.collection_id), 'values': c.fields}
        elif c.kind in ('update', 'move', 'restore'):
            e = {'op': 'update', 'rowId': str(c.record_id), 'values': c.fields}
        else:
            e = {'op': 'delete', 'rowId': str(c.record_id)}
        via = c.fields.get('_via') if c.hop else None
        if isinstance(via, dict):
            e['via'] = {k: str(v) for k, v in via.items() if k in ('app', 'record_id', 'workflow') and v is not None}
        expanded.append(e)

    before = wsp.faces(ld, targets)
    after = wsp.faces(_simulate(ld, model, allc), targets)
    deltas = [{'app': k, 'before': before[k]['text'], 'after': after[k]['text']}
              for k in targets if k in before and k in after and before[k]['text'] != after[k]['text']]
    dmap = {d['app']: d for d in deltas}

    lines = []
    for app in targets:
        items = app_lines.get(app)
        d = dmap.get(app)
        sub = f"{d['before']} → {d['after']} {before[app].get('label', '')}".strip() if d else None
        if items:
            what = ' · '.join(s for s, _, _ in items[:4]) + (f' · +{len(items) - 4} more' if len(items) > 4 else '')
            val = ''
            if len(items) == 1 and items[0][1] is not None:
                c0, coll = items[0][1], items[0][2]
                money = [f['key'] for f in (coll or {}).get('fields') or [] if f.get('type') == 'money']
                if money and isinstance(c0.fields.get(money[0]), int):
                    val = fmt.money_row(c0.fields[money[0]])
                sel = [f for f in (coll or {}).get('fields') or [] if f.get('type') == 'select' and f['key'] == 'category']
                if sel and c0.fields.get('category'):
                    lab = next((o.get('label') for o in sel[0].get('options') or [] if isinstance(o, dict)
                                and o.get('id') == c0.fields['category']), None)
                    if lab:
                        what = f'{what} · {lab}'
        else:
            n_move = sum(1 for r in review if r['change'] == 'moved')
            n_new = sum(1 for c in allc if c.kind == 'insert' and model.cprops(c.collection_id).get('calendar')) - n_move
            parts = ([f'{n_move} moved'] if n_move else []) + ([f'{n_new} added'] if n_new > 0 else [])
            what, val = ', '.join(parts) or 'Shows the changes', ''
        lines.append({'apps': [app], 'what': what, 'val': val, **({'sub': sub} if sub else {})})

    names = {a['key']: a.get('name', a['key']) for a in ld.apps}
    primary = f"Add to {names.get(targets[0], targets[0])}" if len(targets) == 1 else f'Add to {len(targets)} apps'
    src = row['source'] or {}
    return {
        'id': str(row['id']), 'status': row['status'], 'version': row['version'],
        'source': {'kind': src.get('kind', 'text'), 'label': src.get('label', 'You typed'), 'at': src.get('at') or ld.now.isoformat()},
        'mode': src.get('mode', 'live'), 'kind': 'records',
        'title': row['title'] or 'Changes', 'summary': row['summary'] or None,
        'ops': card_ops, 'expanded': expanded, 'lines': lines, 'targets': targets, 'deltas': deltas,
        'actions': {'primary': primary, 'secondary': 'Review items'}, 'flagged': is_flagged(allc),
        'review': review,
    }


# ---------------------------------------------------------------- registry

@dataclass
class Tool:
    name: str
    description: str
    model: type[BaseModel]
    fn: Callable[[RunContext, Any], Any]
    status: str | None = None

    def definition(self, strict: bool = True) -> dict:
        d = {'name': self.name, 'description': self.description, 'input_schema': _schema(self.model)}
        if strict:
            d['strict'] = True
        return d


TOOLS: list[Tool] = [
    Tool('report_understanding', 'Say what the input is and what you can read in it. Call once, first, for photos, '
         'files and requests that need reading Sam\'s apps. kind "request" for typed asks.', ReportUnderstanding,
         report_understanding),
    Tool('list_apps', "Sam's apps with their face and collections.", NoInput, list_apps),
    Tool('get_app', "One app's collections, fields, select options and stitches.", GetApp, get_app),
    Tool('query_records', 'Rows of one collection, with filters (eq, ne, lt, gt, within today|week|past|future|7d|-7d, '
         'contains), an optional window on its date field, sort and limit (max 50). Ids returned may be used in '
         'propose_changes.', QueryRecords, query_records),
    Tool('ask_user', 'Ask Sam and wait for the answer (the run pauses). Either question + options (2 to 8, a menu: '
         'which list, which items to check) or questions (1 to 3 in one card, each with an id slug, a header of 12 '
         'characters or fewer and 2 to 4 options with a one-line description; input on an option of a single-select '
         'question shows a field, for Sam\'s own number) with plan_after true before propose_app. At most 2 asks per '
         'run; never ask permission to propose. The answer comes back as this tool\'s result: {choices, other?}, '
         '{answers: {<id>: {choices, other?}}} or {skipped: true} (decide, and set no number for Sam).',
         AskUser, ask_user),
    Tool('propose_changes', 'The only way to change Sam\'s apps. Stores ONE draft card that Sam confirms; nothing is '
         'saved until then. Send the complete set of ops each call (a second call replaces the draft). Values are '
         'strings: money in dollars ("12.00"), datetimes ISO 8601 with offset, selects by label or id. '
         'move_occurrence moves one date of a repeating record (occurrence = that date, fields = the new date); '
         'keep shows a planned occurrence as kept. Give each planner row a reason of 12 words or fewer with '
         'reason_source set to a record id you were shown.', ProposeChanges, propose_changes),
]
REGISTRY = {t.name: t for t in TOOLS}


def definitions(strict: bool = True) -> list[dict]:
    out = [t.definition(strict) for t in TOOLS]
    mod = build_module()
    if mod is not None:
        out.append(dict(mod.TOOL))       # as build.py defines it (strict or not is its call, §10 propose_app)
    return out


def record_call(ctx: RunContext, name: str, tool_input: Any, tool_use_id: str, out: str, is_error: bool,
                cs_id: UUID | None = None, latency_ms: int = 0) -> None:
    """A tool_calls row (§14); never fails the run."""
    if not ctx.persist_calls:
        return
    try:
        with db.connect() as conn:
            conn.execute(
                'insert into tool_calls (run_id, workspace_id, tool_use_id, name, input, is_error, result, '
                'change_set_id, latency_ms) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (ctx.run_id, ctx.workspace_id, tool_use_id or '-', name, Jsonb(tool_input or {}), is_error,
                 Jsonb({'text': out[:4000]}), cs_id, latency_ms))
            conn.commit()
    except Exception:
        pass


def call(ctx: RunContext, name: str, tool_input: Any, tool_use_id: str = '') -> tuple[str, bool]:
    """Run one tool: (result JSON text, is_error). StoreError propagates (it ends the run)."""
    t0 = time.monotonic()
    tool = REGISTRY.get(name)
    is_error, cs_id = False, None
    mod = build_module() if name == 'propose_app' else None
    if mod is not None:
        try:
            out = json.dumps(_propose_app(ctx, mod, tool_input), default=str)
            cs_id = ctx.change_set_id
        except ValidationError as e:
            out = json.dumps([{'field': '.'.join(map(str, err['loc'])), 'problem': err['msg']} for err in e.errors()])
            is_error = True
        except (ToolError, CommandError) as e:
            out, is_error = (str(e) if isinstance(e, ToolError) else json.dumps(e.body.get('issues') or e.body)), True
    elif tool is None:
        out, is_error = f'No tool {name!r}. Tools: {", ".join(REGISTRY)}', True
    else:
        try:
            inp = tool.model.model_validate(tool_input or {})
            res = tool.fn(ctx, inp)
            out = json.dumps(res, default=str)
            cs_id = ctx.change_set_id if name == 'propose_changes' else None
        except ValidationError as e:
            out = json.dumps([{'field': '.'.join(map(str, err['loc'])), 'problem': err['msg']} for err in e.errors()])
            is_error = True
        except ToolError as e:
            out, is_error = str(e), True
    record_call(ctx, name, tool_input, tool_use_id, out, is_error, cs_id, int((time.monotonic() - t0) * 1000))
    return out, is_error
