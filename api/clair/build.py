"""Clair's `propose_app` tool (clair-agent.md §10 signature and validation row, §11, §12.11, §7 rule 7).

Exports `TOOL` (the Anthropic tool definition, strict schema) and `handle(ctx, tool_input) -> dict`. The runner
registers it next to the base tools in api/clair/tools.py.

`spec` is a JSON string holding the AppSpec (ui-tech-plan §3). The full AppSpec can't be a strict schema: it has
open maps (`settings`, a timer's `set`, a rule's `map`) and a 2-tuple (`minus`), which strict tool use doesn't
allow, so the fallback §10 names is used: the string is parsed and validated server-side (Pydantic, then the
semantic checks of api/commands/apps.py). Every block kind of the contract may be used, base and instruments.

The tool stores ONE basted change set of kind `app` (a `create_app` op). A second call in the same run (or after
"Change answers") replaces that basted set in place, same id. It emits `plan` (when a plan is given) and then
`proposal`, whose card carries the Build preview (`preview: AppDetail`). Nothing is written to blocks before
**Make it** (`POST /change-sets/{id}/confirm`).
"""
from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .. import db
from ..commands import CommandError
from ..commands.apps import is_app_ops, store
from .tools import FieldValue, StoreError, ToolError, _schema, build_card


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class RowInsert(Closed):
    collection: str = Field(description='A collection key of the new app ("races")')
    record_id: str | None = Field(None, description='Temp name "new:<name>" if another row links to it')
    fields: list[FieldValue] = Field(default_factory=list)


class StitchMapIn(Closed):
    to: str
    from_: str | None = Field(None, alias='from')
    const: str | None = None


class StitchFilterIn(Closed):
    field: str
    op: Literal['eq', 'ne', 'empty']
    value: str


class StitchInto(Closed):
    """A stitch the new app needs on an existing app; it lives on that (receiving) app (backend.md §5)."""

    app: str = Field(description='The existing receiving app key ("budget")')
    from_: str = Field(alias='from', description='"<new app>/<collection>"')
    to: str = Field(description='"<receiving app>/<collection>"')
    map: list[StitchMapIn]
    where: list[StitchFilterIn] = Field(default_factory=list)


class PlanLine(Closed):
    app: str | None = Field(None, description="The new app's key or an existing app's key (its dye dot)")
    text: str = Field(max_length=80)


class ProposeApp(Closed):
    name: str = Field(min_length=1, max_length=40)
    purpose: str = Field('', max_length=200)
    spec: str = Field(description='The AppSpec as a JSON string (v 1, key, name, icon, dye, collections, tabs, face, ...)')
    title: str | None = Field(None, max_length=80, description='Card title, default "Make a <name> app?"')
    summary: str = Field('', max_length=400, description='One or two plain sentences: what it holds, what flows where')
    rows: list[RowInsert] = Field(default_factory=list, description="Sam's real rows from the input, saved with the app")
    examples: list[RowInsert] = Field(default_factory=list, description='Sample rows for the preview only, never saved')
    stitches_into: list[StitchInto] = Field(default_factory=list)
    plan: list[PlanLine] = Field(default_factory=list, description='2 to 5 lines; required after a plan_after question')


DESCRIPTION = (
    "Make a new app. Stores ONE draft (the Build preview) that Sam confirms with Make it; nothing is saved before "
    "then, and a second call replaces the draft. spec is the AppSpec as a JSON string: {v: 1, key, name, icon, dye, "
    "print?, private?, settings?, collections: [{key, name, fields: [{key, label, type, options?, target?, unit?}], "
    "titleField, dateField?, calendar?, label?}], tabs: [{kind: 'page', id, title, children: [blocks]}], face: "
    "{value, format, label}, stitches?}. Any block kind may be used (text, metric, progress, list, table, calendar, "
    "form, chart, gauge, bars, ring, countdown, strip, picks, checklist, days, next, timer, month). One face, at "
    "least 3 fields, refs as '<app>/<collection>'. Dated collections set calendar: true so their rows show on "
    "Calendar. rows are Sam's own data from the input (values as strings); examples are samples for the preview. "
    "After a plan_after question give a plan of 2 to 5 plain lines. A private app keeps settings.clair_read false. "
    "Never set a health, diet or training number Sam didn't give."
)

TOOL: dict[str, Any] = {
    'name': 'propose_app',
    'description': DESCRIPTION,
    'input_schema': _schema(ProposeApp),
    'strict': True,
}


def _issues_text(issues: list[dict]) -> str:
    return json.dumps([{k: v for k, v in i.items() if k in ('field', 'problem')} for i in issues])


def _parse(tool_input: Any) -> ProposeApp:
    raw = dict(tool_input or {})
    if isinstance(raw.get('spec'), dict):          # tests and replays may pass the object itself
        raw['spec'] = json.dumps(raw['spec'])
    try:
        return ProposeApp.model_validate(raw)
    except ValidationError as e:
        raise ToolError(json.dumps([{'field': '.'.join(map(str, err['loc'])), 'problem': err['msg']}
                                    for err in e.errors()])) from e


def _check_plan(inp: ProposeApp, key: str, ld) -> None:
    if not inp.plan:
        return
    problems = []
    if not 2 <= len(inp.plan) <= 5:
        problems.append({'field': 'plan', 'problem': f'a plan has 2 to 5 lines, got {len(inp.plan)}'})
    for i, line in enumerate(inp.plan):
        if line.app and line.app != key and ld.app(line.app) is None:
            problems.append({'field': f'plan[{i}].app', 'problem': f'{line.app!r} is neither the new app nor an app of Sam\'s'})
    if problems:
        raise ToolError(json.dumps(problems))


def handle(ctx, tool_input: Any) -> dict:
    """Validate, store or replace the basted `create_app` change set, emit `plan` then `proposal`."""
    inp = _parse(tool_input)
    try:
        spec = json.loads(inp.spec)
    except json.JSONDecodeError as e:
        raise ToolError(json.dumps([{'field': 'spec', 'problem': f'not JSON: {e}'}])) from e
    if not isinstance(spec, dict):
        raise ToolError(json.dumps([{'field': 'spec', 'problem': 'spec must be a JSON object'}]))
    spec.setdefault('name', inp.name)
    key = str(spec.get('key') or '')
    ld = ctx.loaded()
    _check_plan(inp, key, ld)

    op = {
        'op': 'create_app', 'spec': spec, 'purpose': inp.purpose or None,
        'rows': [{'collection': r.collection, 'fields': [f.model_dump() for f in r.fields],
                  **({'record_id': r.record_id} if r.record_id else {})} for r in inp.rows],
        'examples': [{'collection': r.collection, 'fields': [f.model_dump() for f in r.fields]} for r in inp.examples],
        'stitches_into': [{'app': s.app, 'stitch': {
            'from': s.from_, 'to': s.to,
            'map': [m.model_dump(by_alias=True, exclude_none=True) for m in s.map],
            **({'where': [w.model_dump() for w in s.where]} if s.where else {})}} for s in inp.stitches_into],
    }
    if inp.plan:
        op['plan'] = [p.model_dump(exclude_none=True) for p in inp.plan]
    title = inp.title or f'Make a {spec.get("name") or inp.name} app?'
    src = {'kind': ctx.source_kind, 'label': ctx.source_label, 'at': ld.now.isoformat(), 'mode': ctx.mode}

    try:
        with db.transaction(ctx.workspace_id) as conn:
            replace = None
            if ctx.change_set_id is not None:
                cur = conn.execute('select status from change_sets where id = %s', (ctx.change_set_id,)).fetchone()
                if cur is not None and cur['status'] == 'basted':
                    replace = ctx.change_set_id
            cs_id = store(conn, ctx.workspace_id, 'clair', 'clair', [op], user_id=ctx.user_id, title=title,
                          summary=inp.summary or None, source=src, run_id=ctx.run_id, replace=replace)
            conn.execute('update agent_runs set change_set_id = %s where id = %s', (cs_id, ctx.run_id))
            row = conn.execute('select * from change_sets where id = %s', (cs_id,)).fetchone()
            card = build_card(conn, ctx.workspace_id, ld, row)
    except CommandError as e:
        raise ToolError(_issues_text(e.body.get('issues') or [{'problem': str(e.body)}])) from e
    except ToolError:
        raise
    except Exception as e:
        raise StoreError(f"Couldn't save the draft: {e}") from e

    stored = (row.get('ops') or [{}])[0] if is_app_ops(row.get('ops')) else {}
    sspec = stored.get('spec') or spec
    ctx.change_set_id = cs_id
    ctx.change_set = card
    if inp.plan:
        ctx.emitter.emit('plan', {
            'title': sspec.get('name') or inp.name,
            'new_app': {k: sspec[k] for k in ('key', 'name', 'icon', 'dye')},
            'lines': op['plan'],
            **({'private': True} if sspec.get('private') else {}),
        })
    ctx.emitter.emit('proposal', {'change_set': card})
    return {'change_set_id': str(cs_id), 'preview': 'build', 'targets': card.get('targets', [])}
