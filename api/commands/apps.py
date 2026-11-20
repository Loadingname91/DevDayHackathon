"""App ops for the command service (backend.md §5, §10 `/apps`, §11 #21 to #23; clair-agent.md §10 `propose_app`).

Three ops, stored in `change_sets.ops` like record ops, written through the same events so `/sync` sees them and
Undo reverses them (an insert event's undo is a tombstone, a tombstone's undo a restore, a field event's undo writes
the old value back):

- `{op: "create_app", spec, rows: [{collection, record_id?, fields}], examples: [...], stitches_into: [{app, stitch}],
  plan?, strict?, app_id?}`: inserts the page block (the spec minus collections), one collection block per collection,
  the `rows` as records (Sam's data, e.g. Running's 10K race) and appends each `stitches_into` stitch to the receiving
  app's page (`stitches` field event). `examples` are preview-only sample rows, never written. `app_id` is filled in
  at apply time (the page block id). `strict: false` (templates) lets refs to apps that aren't there yet pass.
- `{op: "update_app", app_id, spec, base_version?}`: page properties, one field event per changed top-level key;
  collections matched by key (changed: field events; new: inserted; gone: tombstoned; records stay).
- `{op: "delete_app", app_id}`: tombstones the app's records, collections and page in one change set.

`validate_app` is the two-stage check of clair-agent.md §10 (Pydantic AppSpec, then semantic: one face, at least 3
fields, closed formula grammar with every ref and field resolving, stitch targets exist, no stitch loop, style tokens
in the vocabulary, unique key per workspace). Every block kind of the contract (base and instruments) is allowed.
"""
from __future__ import annotations

import copy
import json
import re
import uuid
from typing import Any, Iterable
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from . import position as pos
from .ops import CoerceError, CommandError, TEMP_PREFIX, coerce_value, invalid, parse_relation
from .service import (
    FacesHook, Model, _Applied, _block_out, _event, _get_cs, _insert_cs, _lock, _max_seq, _q, _status_event,
    load_model, no_faces,
)

APP_OPS = ('create_app', 'update_app', 'delete_app')
# App icons the client draws (web/src/components/Icon.tsx, from design/tools/gen_soft.py ICON).
APP_ICONS = {'wallet', 'basket', 'calendar', 'check', 'dumbbell', 'book', 'repeat', 'note', 'flame', 'moon', 'shoe',
             'drop', 'spool', 'receipt', 'app', 'build', 'lock', 'user', 'search', 'play'}
KEY_RE = re.compile(r'^[a-z][a-z0-9_]{0,31}$')
FIELD_RE = re.compile(r'^[a-z][a-zA-Z0-9_]{0,47}$')
MIN_FIELDS = 3
MAX_ROWS = 100
PAGE_ONLY = ('collections', 'id', 'version')
REF_KEYS = ('source', 'collection', 'from', 'log')
NAME_KEYS = ('group', 'switch', 'due', 'x', 'by', 'minutesField', 'kindField', 'dateField', 'mark')
LIST_KEYS = ('fields', 'after', 'moodFields')
AGG_NEEDS_FIELD = {'sum', 'avg', 'min', 'max'}


def is_app_ops(raw: Any) -> bool:
    return (isinstance(raw, list) and bool(raw)
            and all(isinstance(o, dict) and o.get('op') in APP_OPS for o in raw))


# ---------------------------------------------------------------- validation

class _Issues(list):
    def add(self, problem: str, field: str | None = None, code: str = 'invalid', **kw) -> None:
        d: dict[str, Any] = {}
        if field:
            d['field'] = field
        d.update(problem=problem, code=code, **kw)
        self.append(d)


def _pairs(v: Any) -> dict:
    if isinstance(v, list):
        return {x['key']: x.get('value') for x in v if isinstance(x, dict) and 'key' in x}
    return dict(v or {})


class _Checker:
    """Semantic checks of one AppSpec against the workspace (model) it would join."""

    def __init__(self, spec: dict, model: Model, *, app_id: UUID | None, strict: bool, issues: _Issues):
        self.s, self.model, self.strict, self.issues = spec, model, strict, issues
        self.key = spec['key']
        self.own = {c['key']: c for c in spec.get('collections') or []}
        self.other_pages: dict[str, dict] = {}
        self.others: dict[str, dict] = {}
        for pid, p in model.pages.items():
            if app_id is not None and pid == app_id:
                continue
            self.other_pages[p['properties'].get('key')] = p['properties']
        for cid, c in model.colls.items():
            if app_id is not None and c['parent_id'] == app_id:
                continue
            self.others[model.ref(cid)] = c['properties']

    # -- lookups
    def coll(self, ref: str) -> dict | None:
        app, _, ck = str(ref).partition('/')
        if app == self.key:
            return self.own.get(ck)
        return self.others.get(ref)

    def app_known(self, app: str) -> bool:
        return app == self.key or app in self.other_pages

    def missing_ok(self, ref: str) -> bool:
        """Templates (strict off) may point at an app that isn't in the workspace yet ("waiting for Groceries")."""
        app = str(ref).partition('/')[0]
        return not self.strict and not self.app_known(app)

    @staticmethod
    def fields(c: dict | None) -> dict[str, dict]:
        return {f['key']: f for f in (c or {}).get('fields') or [] if 'key' in f}

    def need_coll(self, ref: Any, where: str) -> dict | None:
        if not isinstance(ref, str):
            return None
        c = self.coll(ref)
        if c is None and not self.missing_ok(ref):
            known = sorted(set(f'{self.key}/{k}' for k in self.own) | set(self.others))
            self.issues.add(f'{where}: no collection {ref!r}; collections: {", ".join(known)}', field=where,
                            code='not_found')
        return c

    def need_field(self, c: dict | None, name: Any, where: str, ref: str = '') -> None:
        if c is None or name is None:
            return
        if name not in self.fields(c) and name != 'id':
            self.issues.add(f'{where}: no field {name!r} in {ref or c.get("key")}; fields: '
                            f'{", ".join(self.fields(c))}', field=where)

    # -- formula grammar (backend.md §6)
    def value(self, v: Any, where: str) -> None:
        if v is None or isinstance(v, bool):
            if isinstance(v, bool):
                self.issues.add(f'{where}: a value is a number or a query, not {v!r}', field=where)
            return
        if isinstance(v, (int, float)):
            return
        if not isinstance(v, dict):
            self.issues.add(f'{where}: not a value', field=where)
            return
        if 'minus' in v:
            for i, t in enumerate(v['minus']):
                self.value(t, f'{where}.minus[{i}]')
        elif 'setting' in v:
            return
        elif 'limit' in v:
            lim = v['limit']
            ok = any(f.get('type') == 'select' and f['key'] == lim.get('field')
                     and any(o.get('id') == lim.get('option') for o in f.get('options') or [])
                     for c in self.own.values() for f in c.get('fields') or [])
            if not ok:
                self.issues.add(f'{where}: no select option {lim.get("field")}/{lim.get("option")} in this app',
                                field=where)
        elif 'agg' in v:
            self.query(v, where)
        else:
            self.issues.add(f'{where}: not a value (number, query, setting, limit or minus)', field=where)

    def query(self, q: dict, where: str) -> None:
        ref = q.get('from')
        if ref == '*dated':
            return
        c = self.need_coll(ref, f'{where}.from')
        if q.get('agg') in AGG_NEEDS_FIELD and not q.get('field'):
            self.issues.add(f'{where}: {q.get("agg")} needs a field', field=where)
        self.need_field(c, q.get('field'), f'{where}.field', ref)
        for i, w in enumerate(q.get('where') or []):
            self.need_field(c, w.get('field'), f'{where}.where[{i}]', ref)

    # -- the whole spec
    def run(self) -> None:
        s = self.s
        if not KEY_RE.match(self.key):
            self.issues.add(f'key {self.key!r}: lowercase letters, digits and _ (start with a letter)', field='key')
        if s.get('icon') not in APP_ICONS:
            self.issues.add(f'icon {s.get("icon")!r} is not in the vocabulary: {", ".join(sorted(APP_ICONS))}',
                            field='icon')
        self.collections()
        self.face()
        self.tabs()
        self.stitches(s.get('stitches') or [], receiving=self.key, where='stitches')
        for i, w in enumerate(s.get('workflows') or []):
            t = w.get('trigger') or {}
            if t.get('collection'):
                c = self.need_coll(t['collection'], f'workflows[{i}].trigger.collection')
                for j, f in enumerate(t.get('where') or []):
                    self.need_field(c, f.get('field'), f'workflows[{i}].trigger.where[{j}]')
                if t.get('field'):
                    self.need_field(c, t['field'], f'workflows[{i}].trigger.field')
            a = w.get('action') or {}
            if a.get('collection'):
                c = self.need_coll(a['collection'], f'workflows[{i}].action.collection')
                for k in a.get('map') or {}:
                    self.need_field(c, k, f'workflows[{i}].action.map')

    def collections(self) -> None:
        cols = self.s.get('collections') or []
        if not cols:
            self.issues.add('an app needs at least one collection', field='collections')
        seen: set[str] = set()
        total = 0
        for i, c in enumerate(cols):
            w = f'collections[{i}]'
            if c['key'] in seen:
                self.issues.add(f'{w}: collection key {c["key"]!r} used twice', field=w)
            seen.add(c['key'])
            if not KEY_RE.match(c['key']):
                self.issues.add(f'{w}: key {c["key"]!r}: lowercase letters, digits and _', field=w)
            fseen: set[str] = set()
            fields = c.get('fields') or []
            total += len(fields)
            for j, f in enumerate(fields):
                fw = f'{w}.fields[{j}]'
                if f['key'] in fseen:
                    self.issues.add(f'{fw}: field key {f["key"]!r} used twice', field=fw)
                fseen.add(f['key'])
                if not FIELD_RE.match(f['key']) or f['key'] == 'id':
                    self.issues.add(f'{fw}: field key {f["key"]!r} must start with a letter (and not be "id")',
                                    field=fw)
                t = f.get('type')
                if t == 'select':
                    ids = [o['id'] for o in f.get('options') or []]
                    if not ids:
                        self.issues.add(f'{fw}: a select needs options', field=fw)
                    if len(ids) != len(set(ids)):
                        self.issues.add(f'{fw}: option ids must be unique', field=fw)
                elif t == 'relation':
                    if not f.get('target'):
                        self.issues.add(f'{fw}: a relation needs a target collection', field=fw)
                    else:
                        self.need_coll(f['target'], f'{fw}.target')
                elif t == 'formula':
                    if not f.get('op') or f.get('a') is None or f.get('b') is None:
                        self.issues.add(f'{fw}: a formula needs op, a and b', field=fw)
                    for side in ('a', 'b'):
                        v = f.get(side)
                        if isinstance(v, str) and v not in {x['key'] for x in fields}:
                            self.issues.add(f'{fw}.{side}: no field {v!r} in {c["key"]}', field=fw)
            fd = self.fields(c)
            for k in ('titleField', 'dateField', 'amountField'):
                if c.get(k) is not None and c[k] not in fd:
                    self.issues.add(f'{w}.{k}: no field {c[k]!r}', field=f'{w}.{k}')
            if c.get('dateField') in fd and fd[c['dateField']].get('type') not in ('date', 'datetime'):
                self.issues.add(f'{w}.dateField: {c["dateField"]!r} is not a date', field=f'{w}.dateField')
            if c.get('calendar') and not c.get('dateField'):
                self.issues.add(f'{w}: a calendar collection needs a dateField', field=w)
        if total < MIN_FIELDS:
            self.issues.add(f'an app needs at least {MIN_FIELDS} fields (has {total})', field='collections')

    def face(self) -> None:
        f = self.s.get('face')
        if not f:
            self.issues.add('an app needs one face', field='face')
            return
        self.value(f.get('value'), 'face.value')

    def tabs(self) -> None:
        tabs = self.s.get('tabs') or []
        if not tabs:
            self.issues.add('an app needs at least one tab', field='tabs')
        ids: set[str] = set()
        for ti, t in enumerate(tabs):
            for bid in [t.get('id')] + [b.get('id') for b in t.get('children') or []]:
                if bid in ids:
                    self.issues.add(f'block id {bid!r} used twice', field=f'tabs[{ti}]')
                ids.add(bid)
            for bi, b in enumerate(t.get('children') or []):
                self.block(b, f'tabs[{ti}].children[{bi}]')

    def block(self, b: dict, w: str) -> None:
        colls, dated = [], False
        for k in REF_KEYS:
            ref = b.get(k)
            if not isinstance(ref, str):
                continue
            if ref == '*dated':
                dated = True
                continue
            c = self.need_coll(ref, f'{w}.{k}')
            if c is not None:
                colls.append(c)
        names: list[tuple[str, Any]] = []
        for k in NAME_KEYS:
            if isinstance(b.get(k), str):
                names.append((k, b[k]))
        for k in LIST_KEYS:
            for x in b.get(k) or []:
                names.append((k, x))
        if isinstance(b.get('sort'), dict):
            names.append(('sort', b['sort'].get('field')))
        for i, f in enumerate(b.get('where') or []):
            names.append((f'where[{i}]', f.get('field')))
        for gi, g in enumerate(b.get('groups') or []):
            for i, f in enumerate(g.get('where') or []):
                names.append((f'groups[{gi}].where[{i}]', f.get('field')))
        for k in (b.get('set') or {}):
            names.append(('set', k))
        for k in ((b.get('add') or {}).get('set') or {}):
            names.append(('add.set', k))
        if colls and not dated:
            known = set().union(*(self.fields(c) for c in colls)) | {'id'}
            for where, name in names:
                if name is not None and name not in known:
                    self.issues.add(f'{w}.{where}: no field {name!r}; fields: {", ".join(sorted(known - {"id"}))}',
                                    field=f'{w}.{where}')
        for k in ('value', 'target', 'compare'):
            if k in b:
                self.value(b[k], f'{w}.{k}')
        if isinstance(b.get('y'), dict):
            self.query(b['y'], f'{w}.y')
        link = b.get('link')
        if isinstance(link, dict) and link.get('app') and not self.app_known(link['app']) and self.strict:
            self.issues.add(f'{w}.link: no app {link["app"]!r}', field=f'{w}.link', code='not_found')
        for a in b.get('apps') or []:
            if not self.app_known(a) and self.strict:
                self.issues.add(f'{w}.apps: no app {a!r}', field=f'{w}.apps', code='not_found')

    def stitches(self, stitches: Iterable[dict], *, receiving: str, where: str) -> None:
        for i, st in enumerate(stitches):
            w = f'{where}[{i}]'
            to, frm = st.get('to'), st.get('from')
            if str(to).partition('/')[0] != receiving:
                self.issues.add(f'{w}: a stitch lives on the receiving app; to must be a collection of {receiving}',
                                field=w)
            tc = self.need_coll(to, f'{w}.to')
            fc = self.need_coll(frm, f'{w}.from')
            if to == frm:
                self.issues.add(f'{w}: a stitch can\'t point at its own collection', field=w)
            for j, m in enumerate(st.get('map') or []):
                self.need_field(tc, m.get('to'), f'{w}.map[{j}].to', to)
                if m.get('from') is not None:
                    self.need_field(fc, m['from'], f'{w}.map[{j}].from', frm)
                elif m.get('const') is None:
                    self.issues.add(f'{w}.map[{j}]: give from or const', field=f'{w}.map[{j}]')
            for j, f in enumerate(st.get('where') or []):
                self.need_field(fc, f.get('field'), f'{w}.where[{j}]', frm)


def _loop(edges: list[tuple[str, str]]) -> list[str] | None:
    graph: dict[str, list[str]] = {}
    for a, b in edges:
        graph.setdefault(a, []).append(b)
    state: dict[str, int] = {}
    path: list[str] = []

    def dfs(n: str) -> list[str] | None:
        state[n] = 1
        path.append(n)
        for m in graph.get(n, []):
            if state.get(m) == 1:
                return path[path.index(m):] + [m]
            if state.get(m) is None:
                r = dfs(m)
                if r:
                    return r
        state[n] = 2
        path.pop()
        return None

    for n in list(graph):
        if state.get(n) is None:
            r = dfs(n)
            if r:
                return r
    return None


def _edges(stitches: Iterable[dict]) -> list[tuple[str, str]]:
    return [(s['from'], s['to']) for s in stitches
            if isinstance(s, dict) and s.get('on') != 'occurrence' and s.get('from') and s.get('to')]


def _rows(chk: _Checker, raw: list[Any], label: str, tz: str, issues: _Issues) -> list[dict]:
    """Rows of the new app: coerced to their field types (money to cents, dates in the workspace zone)."""
    out: list[dict] = []
    if len(raw) > MAX_ROWS:
        issues.add(f'at most {MAX_ROWS} {label}', field=label)
        return out
    temps = {r.get('record_id') for r in raw if isinstance(r, dict) and r.get('record_id')}
    for i, r in enumerate(raw):
        w = f'{label}[{i}]'
        if not isinstance(r, dict):
            issues.add(f'{w}: not a row', field=w)
            continue
        ck = str(r.get('collection') or '')
        if ck.startswith(chk.key + '/'):
            ck = ck.split('/', 1)[1]
        c = chk.own.get(ck)
        if c is None:
            issues.add(f'{w}: no collection {ck!r} in the new app; collections: {", ".join(chk.own)}',
                       field=f'{w}.collection')
            continue
        rid = r.get('record_id')
        if rid is not None and not str(rid).startswith(TEMP_PREFIX):
            issues.add(f'{w}.record_id: a temp name "new:<name>"', field=f'{w}.record_id')
        fields = chk.fields(c)
        values = _pairs(r.get('fields'))
        props: dict[str, Any] = {}
        repeat = []
        for k, v in values.items():
            f = fields.get(k)
            if f is None or k.startswith('_'):
                issues.add(f'{w}: no field {k!r} in {ck}; fields: {", ".join(fields)}', field=f'{w}.{k}')
                continue
            if f.get('type') == 'repeat':
                repeat.append(k)
                continue
            try:
                if f.get('type') == 'relation':
                    val = parse_relation(v)
                    bad = [x for x in val if x.startswith(TEMP_PREFIX) and x not in temps]
                    if bad:
                        raise CoerceError(f'no row named {", ".join(bad)}')
                else:
                    val = coerce_value(f, v, tz)
            except CoerceError as e:
                issues.add(f'{w}.{k}: {e}', field=f'{w}.{k}')
                continue
            if val is not None:
                props[k] = val
        for k in repeat:
            try:
                val = coerce_value(fields[k], values[k], tz, date_value=props.get(c.get('dateField')))
            except CoerceError as e:
                issues.add(f'{w}.{k}: {e}', field=f'{w}.{k}')
                continue
            if val is not None:
                props[k] = val
        for k, f in fields.items():
            if f.get('required') and props.get(k) in (None, '', []):
                issues.add(f'{w}: {k!r} is required', field=f'{w}.{k}')
        row = {'collection': ck, 'fields': props}
        if rid:
            row['record_id'] = rid
        out.append(row)
    return out


def _pydantic(spec: Any, new: bool, issues: _Issues) -> dict | None:
    from ..models import AppSpec, NewAppSpec
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError as e:
            issues.add(f'spec is not JSON: {e}', field='spec')
            return None
    if not isinstance(spec, dict):
        issues.add('spec must be an object', field='spec')
        return None
    spec = dict(spec)
    spec.setdefault('v', 1)
    if new:
        spec.pop('id', None)
    spec.pop('version', None)
    try:
        m = (NewAppSpec if new else AppSpec).model_validate(spec)
    except ValidationError as e:
        for err in e.errors():
            loc = '.'.join(str(p) for p in err['loc'])
            issues.add(f'{loc}: {err["msg"]}' if loc else err['msg'], field=f'spec.{loc}' if loc else 'spec')
        return None
    out = m.model_dump(mode='json', by_alias=True, exclude_none=True)
    out.pop('id', None)
    out.pop('version', None)
    for c in out.get('collections') or []:
        c.pop('id', None)
    return out


def validate_app(model: Model, spec: Any, *, new: bool = True, app_id: UUID | None = None, strict: bool = True,
                 rows: list | None = None, examples: list | None = None, stitches_into: list | None = None,
                 batch_keys: Iterable[str] = ()) -> dict:
    """Two-stage validation (clair-agent.md §10). Returns the normalized `{spec, rows, examples, stitches_into}`;
    raises 422 `{error: invalid, issues}` listing every problem."""
    issues = _Issues()
    s = _pydantic(spec, new, issues)
    if s is None:
        raise invalid(issues)
    # privacy: a private app starts with Clair's read switch off; a Cycle app always does (FR-A8, §12.11)
    settings = s.setdefault('settings', {})
    if new and (s.get('private') or s['key'] == 'cycle') and 'clair_read' not in settings:
        settings['clair_read'] = False
    chk = _Checker(s, model, app_id=app_id, strict=strict, issues=issues)
    if new and (s['key'] in chk.other_pages or s['key'] in set(batch_keys)):
        issues.add(f'an app with key {s["key"]!r} already exists', field='key', code='exists')
    if app_id is not None:
        page = model.pages.get(app_id)
        if page is not None and page['properties'].get('key') != s['key']:
            issues.add('an app\'s key can\'t change', field='key')
    chk.run()

    norm_into = []
    for i, x in enumerate(stitches_into or []):
        w = f'stitches_into[{i}]'
        app = (x or {}).get('app')
        st = (x or {}).get('stitch')
        if app not in chk.other_pages:
            issues.add(f'{w}: no app {app!r}', field=w, code='not_found')
            continue
        from ..models import Stitch
        try:
            st = Stitch.model_validate(st).model_dump(mode='json', by_alias=True, exclude_none=True)
        except ValidationError as e:
            for err in e.errors():
                issues.add(f'{w}.stitch.{".".join(map(str, err["loc"]))}: {err["msg"]}', field=w)
            continue
        chk.stitches([st], receiving=app, where=f'{w}.stitch')
        norm_into.append({'app': app, 'stitch': st})

    # the receiving apps' other stitches must still find the fields they read (§11 #23)
    if app_id is not None:
        own_refs = {f'{s["key"]}/{k}' for k in chk.own}
        for key, props in chk.other_pages.items():
            for st in props.get('stitches') or []:
                if not isinstance(st, dict):
                    continue
                if st.get('from') in own_refs:
                    for m in st.get('map') or []:
                        if m.get('from') is not None and m['from'] not in chk.fields(chk.coll(st['from'])):
                            issues.add(f'{key}\'s stitch reads {st["from"]}.{m["from"]}, which this change removes',
                                       field='collections', code='in_use')

    # stitch loop (§11 #22): every stitch edge in the workspace plus the new ones
    edges = []
    for key, props in chk.other_pages.items():
        edges += _edges(props.get('stitches') or [])
    edges += _edges(s.get('stitches') or [])
    edges += _edges(x['stitch'] for x in norm_into)
    cyc = _loop(edges)
    if cyc:
        issues.add(f'stitch loop: {" → ".join(cyc)}', field='stitches', code='loop')

    tz = model.tz
    out_rows = _rows(chk, list(rows or []), 'rows', tz, issues)
    out_examples = _rows(chk, list(examples or []), 'examples', tz, issues)
    if issues:
        raise invalid(issues)
    return {'spec': s, 'rows': out_rows, 'examples': out_examples, 'stitches_into': norm_into}


def normalize_op(model: Model, op: dict, *, batch_keys: Iterable[str] = ()) -> dict:
    """Validate one stored app op and return it in canonical form (what `change_sets.ops` holds)."""
    kind = op.get('op')
    if kind == 'create_app':
        norm = validate_app(model, op.get('spec'), new=True, strict=op.get('strict', True) is not False,
                            rows=op.get('rows'), examples=op.get('examples'), stitches_into=op.get('stitches_into'),
                            batch_keys=batch_keys)
        out = {'op': 'create_app', **norm}
        for k in ('plan', 'purpose'):
            if op.get(k) is not None:
                out[k] = op[k]
        if op.get('strict') is False:
            out['strict'] = False
        return out
    app_id = _page_id(model, op.get('app_id'))
    if kind == 'update_app':
        norm = validate_app(model, op.get('spec'), new=False, app_id=app_id)
        out = {'op': 'update_app', 'app_id': str(app_id), 'spec': norm['spec']}
        if op.get('base_version') is not None:
            out['base_version'] = int(op['base_version'])
        return out
    if kind == 'delete_app':
        return {'op': 'delete_app', 'app_id': str(app_id)}
    raise invalid([{'problem': f'unknown app op {kind!r}', 'code': 'invalid'}])


def normalize_ops(model: Model, ops: list[dict]) -> list[dict]:
    out, keys = [], []
    for o in ops:
        n = normalize_op(model, o, batch_keys=keys)
        if n['op'] == 'create_app':
            keys.append(n['spec']['key'])
        out.append(n)
    return out


def _page_id(model: Model, id_or_key: Any) -> UUID:
    if id_or_key is not None:
        try:
            pid = UUID(str(id_or_key))
            if pid in model.pages:
                return pid
        except ValueError:
            p = model.pages_by_key.get(str(id_or_key))
            if p is not None:
                return p['id']
    raise CommandError(404, {'error': 'not_found', 'what': 'app'})


# ---------------------------------------------------------------- dependents (§11 #21, FR-S8)

def dependents(model: Model, app_id: UUID) -> list[dict]:
    """What else in the workspace reads this app: stitches, relations, blocks or faces of other apps."""
    page = model.pages.get(app_id)
    if page is None:
        raise CommandError(404, {'error': 'not_found', 'what': 'app'})
    key = page['properties'].get('key')
    prefix = f'{key}/'
    out: list[dict] = []

    def add(app: str, what: str) -> None:
        d = {'app': app, 'what': what}
        if d not in out:
            out.append(d)

    def strings(v: Any) -> Iterable[str]:
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for x in v.values():
                yield from strings(x)
        elif isinstance(v, list):
            for x in v:
                yield from strings(x)

    for pid, p in model.pages.items():
        if pid == app_id:
            continue
        props = p['properties']
        other = props.get('key')
        for st in props.get('stitches') or []:
            if isinstance(st, dict) and str(st.get('from', '')).startswith(prefix):
                add(other, f'stitch from {st["from"]}')
            if isinstance(st, dict) and str(st.get('to', '')).startswith(prefix):
                add(other, f'stitch to {st["to"]}')
        for v in strings({'tabs': props.get('tabs'), 'face': props.get('face')}):
            if v.startswith(prefix):
                add(other, f'reads {v}')
        for t in props.get('tabs') or []:
            for b in t.get('children') or []:
                if key in (b.get('apps') or []):
                    add(other, f'shows {page["properties"].get("name") or key}')
    for cid, c in model.colls.items():
        if model.pages[c['parent_id']]['id'] == app_id:
            continue
        for f in c['properties'].get('fields') or []:
            if f.get('type') == 'relation' and str(f.get('target', '')).startswith(prefix):
                add(model.app_key(cid), f'{model.ref(cid)}.{f["key"]} links to {f["target"]}')
    return out


# ---------------------------------------------------------------- write

class _Writer:
    def __init__(self, conn: psycopg.Connection, ws: UUID, cs: UUID, out: _Applied):
        self.conn, self.ws, self.cs, self.out = conn, ws, cs, out
        self.apps: list[str] = []          # page ids whose faces the result carries

    def ev(self, block_id, path, old, new, version) -> None:
        self.out.seq = max(self.out.seq, _event(self.conn, self.ws, self.cs, block_id, path, old, new, version))
        self.out.events += 1

    def insert(self, bid: UUID, parent: UUID | None, block_type: str, position: str, props: dict,
               collection_id: UUID | None = None) -> dict:
        try:
            with self.conn.transaction():
                r = _q(self.conn, 'insert into blocks (id, workspace_id, parent_id, collection_id, block_type, '
                                  'position, properties) values (%s, %s, %s, %s, %s, %s, %s) returning *',
                       (bid, self.ws, parent, collection_id, block_type, position, Jsonb(props))).fetchone()
        except psycopg.errors.UniqueViolation as e:
            raise CommandError(409, {'error': 'exists', 'issues': [
                {'field': 'key', 'problem': f'an app with key {props.get("key")!r} already exists',
                 'code': 'exists'}]}) from e
        self.ev(r['id'], None, None, r['properties'], r['version'])
        self.out.blocks[r['id']] = r
        return r

    def tombstone(self, r: dict) -> None:
        r = _q(self.conn, 'update blocks set deleted_at = now(), version = version + 1, updated_at = now() '
                          'where id = %s returning *', (r['id'],)).fetchone()
        self.ev(r['id'], None, r['properties'], None, r['version'])
        self.out.blocks[r['id']] = r

    def set_props(self, r: dict, new: dict) -> dict:
        old = r['properties'] or {}
        changed = [(k, old.get(k), new.get(k)) for k in dict.fromkeys([*old, *new]) if old.get(k) != new.get(k)]
        if not changed:
            return r
        r = _q(self.conn, 'update blocks set properties = %s, version = version + 1, updated_at = now() '
                          'where id = %s returning *', (Jsonb(new), r['id'])).fetchone()
        for k, o, n in changed:
            self.ev(r['id'], k, o, n, r['version'])
        self.out.blocks[r['id']] = r
        return r

    def last_page_position(self) -> str | None:
        r = _q(self.conn, "select position from blocks where workspace_id = %s and block_type = 'page' "
                          "and deleted_at is null order by position desc limit 1", (self.ws,)).fetchone()
        return r['position'] if r else None

    # -- the three ops
    def create(self, op: dict) -> UUID:
        spec = copy.deepcopy(op['spec'])
        page_id = uuid.uuid4()
        page_props = {k: v for k, v in spec.items() if k not in PAGE_ONLY}
        self.insert(page_id, None, 'page', pos.key_between(self.last_page_position(), None), page_props)
        coll_ids: dict[str, UUID] = {}
        ckey = None
        for c in spec.get('collections') or []:
            cid = uuid.uuid4()
            ckey = pos.key_between(ckey, None)
            self.insert(cid, page_id, 'collection', ckey, {k: v for k, v in c.items() if k != 'id'})
            coll_ids[c['key']] = cid
        temps = {r['record_id']: uuid.uuid4() for r in op.get('rows') or [] if r.get('record_id')}
        last: dict[str, str | None] = {}
        fields_of = {c['key']: {f['key']: f for f in c.get('fields') or []} for c in spec.get('collections') or []}
        for r in op.get('rows') or []:
            props = dict(r['fields'])
            for k, v in list(props.items()):
                if fields_of[r['collection']].get(k, {}).get('type') == 'relation' and isinstance(v, list):
                    props[k] = [str(temps.get(x, x)) for x in v]
            cid = coll_ids[r['collection']]
            last[r['collection']] = pos.key_between(last.get(r['collection']), None)
            rid = temps.get(r.get('record_id')) or uuid.uuid4()
            self.insert(rid, cid, 'record', last[r['collection']], props, collection_id=cid)
        for x in op.get('stitches_into') or []:
            p = _q(self.conn, "select * from blocks where workspace_id = %s and block_type = 'page' "
                              "and deleted_at is null and properties->>'key' = %s for update",
                   (self.ws, x['app'])).fetchone()
            if p is None:
                raise CommandError(409, {'error': 'changed', 'status': 'basted', 'issues': [
                    {'field': 'stitches_into', 'problem': f'no app {x["app"]!r}', 'code': 'not_found'}]})
            new = dict(p['properties'])
            new['stitches'] = list(new.get('stitches') or []) + [x['stitch']]
            self.set_props(p, new)
            self.apps.append(str(p['id']))
        self.apps.insert(0, str(page_id))
        return page_id

    def update(self, op: dict) -> None:
        app_id = UUID(op['app_id'])
        page = _q(self.conn, "select * from blocks where workspace_id = %s and id = %s and block_type = 'page' "
                             "and deleted_at is null for update", (self.ws, app_id)).fetchone()
        if page is None:
            raise CommandError(404, {'error': 'not_found', 'what': 'app'})
        if op.get('base_version') is not None and page['version'] != op['base_version']:
            raise CommandError(409, {'error': 'version', 'version': page['version']})
        spec = op['spec']
        self.set_props(page, {k: v for k, v in spec.items() if k not in PAGE_ONLY})
        existing = {r['properties'].get('key'): r for r in _q(
            self.conn, "select * from blocks where workspace_id = %s and parent_id = %s and block_type = 'collection' "
                       "and deleted_at is null order by position for update", (self.ws, app_id)).fetchall()}
        last = max((r['position'] for r in existing.values()), default=None)
        for c in spec.get('collections') or []:
            props = {k: v for k, v in c.items() if k != 'id'}
            r = existing.pop(c['key'], None)
            if r is not None:
                self.set_props(r, props)
            else:
                last = pos.key_between(last, None)
                self.insert(uuid.uuid4(), app_id, 'collection', last, props)
        for r in existing.values():          # a collection left out: tombstoned, its records stay (hidden)
            self.tombstone(r)
        self.apps.append(str(app_id))

    def delete(self, op: dict) -> None:
        app_id = UUID(op['app_id'])
        page = _q(self.conn, "select * from blocks where workspace_id = %s and id = %s and block_type = 'page' "
                             "and deleted_at is null for update", (self.ws, app_id)).fetchone()
        if page is None:
            raise CommandError(404, {'error': 'not_found', 'what': 'app'})
        colls = _q(self.conn, "select * from blocks where workspace_id = %s and parent_id = %s "
                              "and block_type = 'collection' and deleted_at is null for update",
                   (self.ws, app_id)).fetchall()
        if colls:
            recs = _q(self.conn, 'select * from blocks where workspace_id = %s and collection_id = any(%s) '
                                 'and deleted_at is null order by position for update',
                      (self.ws, [c['id'] for c in colls])).fetchall()
            for r in recs:
                self.tombstone(r)
        for c in colls:
            self.tombstone(c)
        self.tombstone(page)


def _write(conn, ws: UUID, cs_id: UUID, ops: list[dict], out: _Applied) -> tuple[list[dict], list[str]]:
    w = _Writer(conn, ws, cs_id, out)
    stored = []
    for o in ops:
        o = dict(o)
        if o['op'] == 'create_app':
            o['app_id'] = str(w.create(o))
        elif o['op'] == 'update_app':
            w.update(o)
        else:
            w.delete(o)
        stored.append(o)
    return stored, w.apps


def _result(conn, ws, cs_id: UUID, out: _Applied, apps: list[str], compute_faces: FacesHook | None) -> dict:
    faces = (compute_faces or no_faces)(conn, ws, apps) if apps else {}
    return {'change_set_id': str(cs_id), 'server_seq': out.seq or _max_seq(conn, ws),
            'blocks': [_block_out(b) for b in out.blocks.values()], 'faces': faces, 'warnings': out.warnings,
            'targets': apps}


# ---------------------------------------------------------------- public API (called by service.py)

def _fresh(ops: list[dict]) -> list[dict]:
    """Stored ops ready to re-validate: a create's `app_id` is from an earlier apply (undone since)."""
    return [{k: v for k, v in o.items() if k != 'app_id'} if o.get('op') == 'create_app' else o for o in ops]


def apply_ops(conn: psycopg.Connection, ws: UUID, cs: dict, *, compute_faces: FacesHook | None = None,
              context: str = 'confirm') -> dict[str, Any]:
    """Write a claimed change set's app ops (inside the caller's lock and transaction). Re-validates on current
    data first: at confirm a problem is 409 `{error: changed, status: basted, issues}`."""
    model = load_model(conn, ws)
    try:
        ops = normalize_ops(model, _fresh(cs['ops']))
    except CommandError as e:
        if context == 'confirm' and e.status == 422:
            raise CommandError(409, {'error': 'changed', 'status': 'basted', 'issues': e.body.get('issues', [])}) from e
        raise
    out = _Applied()
    stored, apps = _write(conn, ws, cs['id'], ops, out)
    conn.execute('update change_sets set ops = %s, stitched_seq = %s, updated_at = now() where id = %s',
                 (Jsonb(stored), out.seq or None, cs['id']))
    return _result(conn, ws, cs['id'], out, apps, compute_faces)


def store(conn: psycopg.Connection, ws: UUID, actor: str, origin: str, ops: list[dict], *,
          user_id: UUID | None = None, title: str | None = None, summary: str | None = None,
          source: dict | None = None, run_id: UUID | None = None, replace: UUID | None = None) -> UUID:
    """Validate app ops and store them as a `basted` change set (nothing touches blocks). With `replace`, the
    basted set of that id is rewritten in place (same id, version + 1: Clair's second propose_app, "Change
    answers", clair-agent.md §11); if it's no longer basted a new set is made."""
    _lock(conn, ws)
    with conn.transaction():
        norm = normalize_ops(load_model(conn, ws), ops)
        if replace is not None:
            r = _q(conn, "update change_sets set ops = %s, title = %s, summary = %s, source = %s, "
                         "version = version + 1, updated_at = now() where id = %s and workspace_id = %s "
                         "and status = 'basted' returning id",
                   (Jsonb(norm), title, summary, Jsonb(source or {}), replace, ws)).fetchone()
            if r is not None:
                return r['id']
        cs = _insert_cs(conn, ws, actor=actor, origin=origin, status='basted', user_id=user_id, ops=norm,
                        title=title, summary=summary, source=source, run_id=run_id)
        _status_event(conn, ws, cs, None, 'basted')
        return cs


def run_ops(conn: psycopg.Connection, ws: UUID, ops: list[dict], *, actor: str, origin: str,
            user_id: UUID | None = None, title: str | None = None, summary: str | None = None,
            source: dict | None = None, compute_faces: FacesHook | None = None) -> dict[str, Any]:
    """Validate and apply at once as one `stitched` change set (POST/PATCH/DELETE /apps, templates)."""
    _lock(conn, ws)
    with conn.transaction():
        model = load_model(conn, ws)
        norm = normalize_ops(model, ops)
        cs = _insert_cs(conn, ws, actor=actor, origin=origin, status='stitched', user_id=user_id, ops=norm,
                        title=title, summary=summary, source=source)
        out = _Applied()
        stored, apps = _write(conn, ws, cs, norm, out)
        conn.execute('update change_sets set ops = %s, stitched_seq = %s where id = %s',
                     (Jsonb(stored), out.seq or None, cs))
        return _result(conn, ws, cs, out, apps, compute_faces)


def preview(conn: psycopg.Connection, ws: UUID, cs: dict) -> dict[str, Any]:
    """`service.preview` for an app change set: targets are the touched apps' keys or the new key."""
    model = load_model(conn, ws)
    targets: list[str] = []
    issues: list = []
    try:
        ops = normalize_ops(model, _fresh(cs['ops'])) if cs['status'] == 'basted' else cs['ops']
    except CommandError as e:
        return {'status': cs['status'], 'expanded': [], 'targets': [], 'flagged': False,
                'issues': e.body.get('issues', [])}
    for o in ops:
        if o['op'] == 'create_app':
            targets.append(o['spec']['key'])
            targets += [x['app'] for x in o.get('stitches_into') or []]
        else:
            p = model.pages.get(UUID(o['app_id']))
            if p is not None:
                targets.append(p['properties'].get('key'))
    return {'status': cs['status'], 'expanded': [], 'targets': list(dict.fromkeys(targets)), 'flagged': False,
            'issues': issues}


def get_change_set(conn, ws: UUID, cs_id: UUID) -> dict:
    return _get_cs(conn, ws, cs_id)
