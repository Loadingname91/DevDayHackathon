"""The command service: the one write path for records (backend.md §5).

Every write to record blocks comes through here: a user gesture (`run_gesture`), a Clair proposal
(`create_change_set` → basted, then `confirm`), an undo, a rebalance. Each public function takes a psycopg
connection, takes the workspace's advisory lock (re-entrant inside one transaction, so it's safe when the
caller already holds it through `api.db.transaction(ws)`), and does its work inside `conn.transaction()`,
so a refused command leaves nothing behind.

Pipeline (§5): parse (Pydantic, 422) → resolve against the workspace (semantic validation and coercion,
422 / 404 / 409 at confirm) → expand stitches (one hop per stitch, chains up to 3) → apply under the lock,
one event per changed field (or per inserted, deleted or restored block) → result
`{change_set_id, server_seq, blocks[], faces{}, warnings[]}`.

Event encoding (what `/sync` and undo read from `events`):
- insert or restore: `field_path` null, `old` null, `new` = properties. Undo: delete.
- delete: `field_path` null, `old` = properties, `new` null. Undo: restore.
- a field: `field_path` = field key, `old` / `new` = values (SQL null when absent). Undo: write `old` back.
- the `position` column: `field_path` = '@position' (never a field key, which can't start with '@').
- a change set's status: `block_id` null, `field_path` 'status', `old` / `new` the statuses.
"""
from __future__ import annotations

import copy
import unicodedata
import uuid
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import Any, Callable, Iterable
from uuid import UUID
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import position as pos
from .ops import (
    CoerceError, CommandError, Op, TEMP_PREFIX, coerce_value, dump_ops, invalid, is_from_google, localize,
    parse_ops, parse_select,
)

POSITION_PATH = '@position'
STITCH_HOPS = 3
BULK_LIMIT = 5
NO_STITCH_ORIGINS = {'undo', 'sweep', 'seed', 'connector'}
WRITES_GOOGLE = {'connector', 'seed'}       # origins allowed to touch `source: "google"` records

FacesHook = Callable[[psycopg.Connection, UUID, list[str]], dict]
ExpandHook = Callable[[psycopg.Connection, UUID, list['Cmd'], 'Model'], list['Cmd']]


def no_faces(conn: psycopg.Connection, ws: UUID, app_ids: list[str]) -> dict:
    return {}


# ---------------------------------------------------------------- small helpers

def _q(conn: psycopg.Connection, sql: str, params: Iterable[Any] | dict | None = None):
    cur = conn.cursor(row_factory=dict_row)
    cur.execute(sql, params)
    return cur


def _j(v: Any) -> Jsonb | None:
    return None if v is None else Jsonb(v)


def _lock(conn: psycopg.Connection, ws: UUID) -> None:
    conn.execute('select pg_advisory_xact_lock(hashtextextended(%s::text, 0))', (str(ws),))


def _now(tz: str) -> datetime:
    """Server time in the workspace zone; pinned by DEMO_NOW when set (§3)."""
    demo = None
    try:
        from ..settings import settings
        demo = settings().demo_now
    except Exception:  # settings missing in a bare unit test
        demo = None
    if demo:
        dt = datetime.fromisoformat(demo)
        return localize(dt, tz) if dt.tzinfo is None else dt.astimezone(ZoneInfo(tz))
    return datetime.now(ZoneInfo(tz))


def _norm(s: Any) -> str:
    return ' '.join(unicodedata.normalize('NFKC', str(s or '')).casefold().split())


def _block_out(r: dict[str, Any]) -> dict[str, Any]:
    def iso(v):
        return v.isoformat() if isinstance(v, datetime) else v
    return {
        'id': str(r['id']), 'block_type': r['block_type'],
        'parent_id': str(r['parent_id']) if r.get('parent_id') else None,
        'collection_id': str(r['collection_id']) if r.get('collection_id') else None,
        'position': r['position'], 'properties': r['properties'], 'version': r['version'],
        'deleted_at': iso(r.get('deleted_at')), 'created_at': iso(r.get('created_at')),
        'updated_at': iso(r.get('updated_at')),
    }


def _to_local_date(v: Any, tz: str) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return (v.astimezone(ZoneInfo(tz)) if v.tzinfo else v).date()
    if isinstance(v, date):
        return v
    s = str(v)
    if 'T' in s:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return (dt.astimezone(ZoneInfo(tz)) if dt.tzinfo else dt).date()
    return date.fromisoformat(s[:10])


# ---------------------------------------------------------------- workspace model

@dataclass
class Model:
    """Pages and collections of one workspace (records are read per command)."""
    ws: UUID
    tz: str
    pages: dict[UUID, dict] = dc_field(default_factory=dict)
    pages_by_key: dict[str, dict] = dc_field(default_factory=dict)
    colls: dict[UUID, dict] = dc_field(default_factory=dict)
    colls_by_ref: dict[str, dict] = dc_field(default_factory=dict)

    def ref(self, coll_id: UUID) -> str:
        c = self.colls[coll_id]
        return f"{self.pages[c['parent_id']]['properties'].get('key')}/{c['properties'].get('key')}"

    def app_key(self, coll_id: UUID) -> str:
        return self.pages[self.colls[coll_id]['parent_id']]['properties'].get('key')

    def fields(self, coll_id: UUID) -> dict[str, dict]:
        return {f['key']: f for f in self.colls[coll_id]['properties'].get('fields') or [] if 'key' in f}

    def cprops(self, coll_id: UUID) -> dict:
        return self.colls[coll_id]['properties']


def load_model(conn: psycopg.Connection, ws: UUID) -> Model:
    w = _q(conn, 'select tz from workspaces where id = %s', (ws,)).fetchone()
    if not w:
        raise CommandError(404, {'error': 'not_found', 'what': 'workspace'})
    m = Model(ws=ws, tz=w['tz'])
    rows = _q(conn, "select id, parent_id, block_type, properties from blocks where workspace_id = %s "
                    "and block_type in ('page', 'collection') and deleted_at is null", (ws,)).fetchall()
    for r in rows:
        if r['block_type'] == 'page':
            m.pages[r['id']] = r
            m.pages_by_key[r['properties'].get('key')] = r
    for r in rows:
        if r['block_type'] == 'collection' and r['parent_id'] in m.pages:
            m.colls[r['id']] = r
            m.colls_by_ref[m.ref(r['id'])] = r
    return m


# ---------------------------------------------------------------- commands (resolved ops)

@dataclass
class Cmd:
    kind: str                          # insert | update | delete | restore | move
    record_id: UUID
    collection_id: UUID
    fields: dict[str, Any] = dc_field(default_factory=dict)   # insert: all properties; update/move: changed fields
    before_id: UUID | None = None
    after_id: UUID | None = None
    add_at: str | None = None
    op_index: int | None = None
    hop: int = 0                       # 0 = from an op; n = n stitch hops away
    base_version: int | None = None

    def out(self, model: Model) -> dict[str, Any]:
        d = {'op': self.kind, 'app': model.app_key(self.collection_id),
             'collection': model.colls[self.collection_id]['properties'].get('key'),
             'record_id': str(self.record_id), 'fields': self.fields}
        if self.hop:
            d['via'] = self.fields.get('_via')
        return d


# ---------------------------------------------------------------- repeats (§3)

def _rrule(rep: dict[str, Any]):
    from dateutil.rrule import rrulestr
    start = datetime.fromisoformat(str(rep['start']))
    if start.tzinfo is not None:
        start = start.replace(tzinfo=None)
    rule = ';'.join(p.rstrip('Z') if p.upper().startswith('UNTIL=') else p for p in str(rep['rule']).split(';'))
    return rrulestr(rule, dtstart=start)


def _is_occurrence(rep: dict, occ: date) -> datetime | None:
    for dt in _rrule(rep):
        if dt.date() == occ:
            return dt
        if dt.date() > occ:
            return None
    return None


def _next_open(rep: dict, after: date) -> datetime | None:
    closed = set(rep.get('skip') or []) | set(rep.get('log') or [])
    for dt in _rrule(rep):
        d = dt.date()
        if d > after and d.isoformat() not in closed:
            return dt
    return None


def _date_value(ftype: str, naive: datetime, tz: str) -> str:
    return naive.date().isoformat() if ftype == 'date' else localize(naive, tz).isoformat()


def _repeat_field(fields: dict[str, dict], props: dict) -> str | None:
    for k, f in fields.items():
        if f.get('type') == 'repeat' and isinstance(props.get(k), dict):
            return k
    return None


# ---------------------------------------------------------------- resolve: semantic validation (§5 step 4)

class _Issues(list):
    def add(self, i: int | None, problem: str, code: str = 'invalid', field: str | None = None, **kw):
        d: dict[str, Any] = {}
        if i is not None:
            d['op'] = i
        if field:
            d['field'] = field
        d['problem'] = problem
        d['code'] = code
        d.update(kw)
        self.append(d)


def _raise(issues: _Issues, context: str) -> None:
    if not issues:
        return
    if any(x['code'] == 'from_google' for x in issues):
        raise invalid([x for x in issues if x['code'] == 'from_google'], error='from_google')
    if context == 'gesture' and any(x['code'] == 'not_found' for x in issues):
        raise CommandError(404, {'error': 'not_found', 'issues': issues})
    if context == 'confirm':
        raise CommandError(409, {'error': 'changed', 'status': 'basted', 'issues': issues})
    raise invalid(issues)


def _view_add_at(model: Model, coll_id: UUID) -> str:
    """`addAt` of a view that shows this collection ('start' wins if any view asks for it)."""
    ref = model.ref(coll_id)
    page = model.pages[model.colls[coll_id]['parent_id']]['properties']
    stack = list(page.get('tabs') or [])
    while stack:
        b = stack.pop()
        if isinstance(b, dict):
            if b.get('source') == ref and b.get('addAt') == 'start':
                return 'start'
            stack.extend(b.get('children') or [])
    return 'end'


def _coerce_fields(model: Model, coll_id: UUID, values: dict[str, Any], issues: _Issues, i: int | None,
                   existing: dict | None = None) -> dict[str, Any]:
    fields = model.fields(coll_id)
    date_key = model.cprops(coll_id).get('dateField')
    out: dict[str, Any] = {}
    repeat_keys = []
    for k, v in values.items():
        f = fields.get(k)
        if f is None:
            issues.add(i, f'no field {k!r} in {model.ref(coll_id)}; fields: {", ".join(fields)}', field=k)
            continue
        if f.get('type') == 'repeat':
            repeat_keys.append(k)
            continue
        try:
            out[k] = coerce_value(f, v, model.tz)
        except CoerceError as e:
            issues.add(i, str(e), field=k)
    for k in repeat_keys:
        dv = out.get(date_key) if date_key in out else (existing or {}).get(date_key)
        try:
            out[k] = coerce_value(fields[k], values[k], model.tz, date_value=dv)
        except CoerceError as e:
            issues.add(i, str(e), field=k)
    return out


def resolve(conn: psycopg.Connection, ws: UUID, model: Model, ops: list[Op], origin: str,
            context: str = 'propose', lock: bool = False) -> list[Cmd]:
    """Turn ops into commands against current data. Raises CommandError with every problem found."""
    issues = _Issues()
    tz = model.tz
    today = _now(tz).date()
    ids = set()
    for o in ops:
        if o.op != 'insert' and o.record_id:
            ids.add(UUID(o.record_id))
        for n in (o.before_id, o.after_id):
            if n:
                ids.add(n)
    rows: dict[UUID, dict] = {}
    if ids:
        sql = ('select * from blocks where workspace_id = %s and id = any(%s)' + (' for update' if lock else ''))
        rows = {r['id']: r for r in _q(conn, sql, (ws, list(ids))).fetchall()}

    temp: dict[str, UUID] = {}
    for i, o in enumerate(ops):
        if o.op == 'insert' and o.record_id:
            if o.record_id.startswith(TEMP_PREFIX):
                if o.record_id in temp:
                    issues.add(i, f'temp name {o.record_id!r} used twice', field='record_id')
                temp[o.record_id] = uuid.uuid4()
            else:
                temp[o.record_id] = UUID(o.record_id)
    if temp:
        clash = _q(conn, 'select id from blocks where id = any(%s)',
                   ([t for k, t in temp.items() if not k.startswith(TEMP_PREFIX)],)).fetchall()
        for r in clash:
            issues.add(None, f'record {r["id"]} already exists', field='record_id')

    cmds: list[Cmd] = []
    seen_update: set[UUID] = set()
    google_ok = origin in WRITES_GOOGLE

    def record(i: int, o: Op) -> dict | None:
        r = rows.get(UUID(o.record_id))
        if r is None or r['block_type'] != 'record':
            issues.add(i, f'no record {o.record_id}', code='not_found', field='record_id')
            return None
        cid = r['collection_id']
        if cid not in model.colls:
            issues.add(i, 'the record\'s app was deleted', code='not_found', field='record_id')
            return None
        if o.app and o.collection and model.colls_by_ref.get(f'{o.app}/{o.collection}', {}).get('id') != cid:
            issues.add(i, f'record {o.record_id} is not in {o.app}/{o.collection}', field='record_id')
            return None
        if o.collection_id and o.collection_id != cid:
            issues.add(i, f'record {o.record_id} is not in collection {o.collection_id}', field='record_id')
            return None
        if not google_ok and is_from_google(r['properties']):
            issues.add(i, 'from Google Calendar: read-only in Quilt', code='from_google', field='record_id')
            return None
        if o.op == 'restore':
            if r['deleted_at'] is None:
                issues.add(i, 'record is not deleted', field='record_id')
                return None
        elif r['deleted_at'] is not None:
            issues.add(i, f'record {o.record_id} was deleted', code='deleted', field='record_id')
            return None
        return r

    for i, o in enumerate(ops):
        if o.op == 'keep':
            continue
        if o.op == 'insert':
            if o.collection_id:
                coll = model.colls.get(o.collection_id)
            else:
                coll = model.colls_by_ref.get(f'{o.app}/{o.collection}')
            if coll is None:
                what = o.collection_id or f'{o.app}/{o.collection}'
                issues.add(i, f'no collection {what}; collections: {", ".join(sorted(model.colls_by_ref))}',
                           code='not_found', field='collection')
                continue
            cid = coll['id']
            props = _coerce_fields(model, cid, o.fields, issues, i)
            props = {k: v for k, v in props.items() if v is not None}
            for k, f in model.fields(cid).items():
                if f.get('required') and props.get(k) in (None, '', []):
                    issues.add(i, f'{k!r} is required', field=k)
            if not google_ok and props.get('source') == 'google':
                issues.add(i, 'only the Google connector writes Google events', code='from_google', field='source')
            _copy_usual(conn, ws, model, cid, props)
            rid = temp.get(o.record_id) if o.record_id else uuid.uuid4()
            cmds.append(Cmd('insert', rid, cid, props, o.before_id, o.after_id,
                            o.add_at or _view_add_at(model, cid), i))
            continue

        r = record(i, o)
        if r is None:
            continue
        rid, cid, props = r['id'], r['collection_id'], r['properties']
        if o.op in ('update', 'complete', 'skip', 'move_occurrence'):
            if rid in seen_update and o.op == 'update':
                issues.add(i, f'record {rid} is updated twice in one change set', field='record_id')
            seen_update.add(rid)

        if o.op == 'update':
            changes = _coerce_fields(model, cid, o.fields, issues, i, existing=props)
            cmds.append(Cmd('update', rid, cid, changes, op_index=i, base_version=o.base_version))
        elif o.op in ('delete', 'restore'):
            cmds.append(Cmd(o.op, rid, cid, op_index=i))
        elif o.op == 'move':
            changes = {}
            if o.list is not None:
                lf = model.fields(cid).get('list')
                if not lf:
                    issues.add(i, 'this collection has no lists', field='list')
                else:
                    try:
                        changes['list'] = parse_select(o.list, lf)
                    except CoerceError as e:
                        issues.add(i, str(e), field='list')
            cmds.append(Cmd('move', rid, cid, changes, o.before_id, o.after_id, op_index=i))
        elif o.op in ('complete', 'skip'):
            changes = _complete_or_skip(model, cid, props, o, today, issues, i)
            if changes is not None:
                cmds.append(Cmd('update', rid, cid, changes, op_index=i))
        elif o.op == 'move_occurrence':
            cmds.extend(_move_occurrence(model, cid, r, o, today, issues, i))

    _resolve_relations(conn, ws, model, cmds, temp, issues)
    _raise(issues, context)
    return cmds


def _copy_usual(conn, ws, model: Model, cid: UUID, props: dict) -> None:
    """§11 #61: a new record named like an earlier one takes the earlier one's `usual` mark."""
    if 'usual' not in model.fields(cid) or 'usual' in props:
        return
    title_key = model.cprops(cid).get('titleField') or 'name'
    name = _norm(props.get(title_key))
    if not name:
        return
    rows = _q(conn, "select properties from blocks where workspace_id = %s and collection_id = %s "
                    "and deleted_at is null and properties ? 'usual' order by created_at desc, id",
              (ws, cid)).fetchall()
    for r in rows:
        if _norm(r['properties'].get(title_key)) == name:
            props['usual'] = r['properties']['usual']
            return


def _complete_or_skip(model: Model, cid: UUID, props: dict, o: Op, today: date, issues: _Issues,
                      i: int) -> dict | None:
    fields = model.fields(cid)
    date_key = model.cprops(cid).get('dateField')
    rkey = _repeat_field(fields, props)
    if rkey:
        rep = copy.deepcopy(props[rkey])
        occ = o.occurrence or _to_local_date(props.get(date_key), model.tz)
        if occ is None:
            issues.add(i, 'which occurrence?', field='occurrence')
            return None
        if _is_occurrence(rep, occ) is None:
            issues.add(i, f'{occ} is not a date of this series', field='occurrence')
            return None
        key = 'log' if o.op == 'complete' else 'skip'
        if occ.isoformat() in (rep.get('log') or []) + (rep.get('skip') or []):
            issues.add(i, f'{occ} is already {"done" if occ.isoformat() in (rep.get("log") or []) else "skipped"}',
                       field='occurrence')
            return None
        rep[key] = sorted(set(rep.get(key) or []) | {occ.isoformat()})
        if o.op == 'complete' and o.minutes is not None:
            # minutes for one occurrence live on the series, by date (log holds dates only)
            rep['minutes'] = {**(rep.get('minutes') or {}), occ.isoformat(): o.minutes}
        changes: dict[str, Any] = {rkey: rep}
        nxt = _next_open(rep, max(occ, today))
        if nxt is not None and date_key in fields:
            changes[date_key] = _date_value(fields[date_key].get('type', 'datetime'), nxt, model.tz)
        elif nxt is None and fields.get('done', {}).get('type') == 'bool':
            changes['done'] = True
        return changes
    if o.op == 'skip':
        issues.add(i, 'only a repeating record can skip a date', field='record_id')
        return None
    changes = {}
    if fields.get('done', {}).get('type') == 'bool':
        changes['done'] = True
    elif fields.get('status', {}).get('type') == 'select':
        opts = [x.get('id') if isinstance(x, dict) else x for x in fields['status'].get('options') or []]
        target = next((x for x in ('bought', 'done', 'complete') if x in opts), None)
        if target is None:
            issues.add(i, 'nothing to complete on this record', field='status')
            return None
        changes['status'] = target
        if target == 'bought' and fields.get('bought_on', {}).get('type') == 'date':
            changes['bought_on'] = today.isoformat()
    else:
        issues.add(i, 'nothing to complete on this record', field='record_id')
        return None
    if o.minutes is not None and 'minutes' in fields:
        changes['minutes'] = o.minutes
    return changes


def _move_occurrence(model: Model, cid: UUID, r: dict, o: Op, today: date, issues: _Issues, i: int) -> list[Cmd]:
    """§3: skip the occurrence on the series, insert a one-off at the new date with `_moved_from`."""
    fields = model.fields(cid)
    props = r['properties']
    date_key = model.cprops(cid).get('dateField')
    rkey = _repeat_field(fields, props)
    occ = o.occurrence
    if not rkey:
        issues.add(i, 'move_occurrence needs a repeating record', field='record_id')
        return []
    rep = copy.deepcopy(props[rkey])
    if _is_occurrence(rep, occ) is None:
        issues.add(i, f'{occ} is not a date of this series', field='occurrence')
        return []
    if occ < today:
        issues.add(i, f'{occ} is in the past', field='occurrence')
        return []
    if occ.isoformat() in (rep.get('log') or []) + (rep.get('skip') or []):
        issues.add(i, f'{occ} is already done or skipped', field='occurrence')
        return []
    new_vals = _coerce_fields(model, cid, o.fields, issues, i, existing=props)
    if rkey in new_vals:
        issues.add(i, 'a moved occurrence has no repeat', field=rkey)
        return []
    if not date_key or new_vals.get(date_key) is None:
        issues.add(i, f'move_occurrence needs the new {date_key or "date"}', field=date_key)
        return []
    rep['skip'] = sorted(set(rep.get('skip') or []) | {occ.isoformat()})
    series_changes: dict[str, Any] = {rkey: rep}
    if _to_local_date(props.get(date_key), model.tz) == occ:
        nxt = _next_open(rep, max(occ, today))
        if nxt is not None:
            series_changes[date_key] = _date_value(fields[date_key].get('type', 'datetime'), nxt, model.tz)
    one_off = {k: v for k, v in props.items()
               if not k.startswith('_') and k != rkey and fields.get(k, {}).get('type') != 'repeat'}
    one_off.update({k: v for k, v in new_vals.items() if v is not None})
    one_off['_moved_from'] = {'record_id': str(r['id']), 'occurrence': occ.isoformat()}
    return [Cmd('update', r['id'], cid, series_changes, op_index=i),
            Cmd('insert', uuid.uuid4(), cid, one_off, add_at=_view_add_at(model, cid), op_index=i)]


def _resolve_relations(conn, ws, model: Model, cmds: list[Cmd], temp: dict[str, UUID], issues: _Issues) -> None:
    """Relation values: temp names become UUIDs; every target is a live record of the target collection."""
    made = {c.record_id: c.collection_id for c in cmds if c.kind == 'insert'}
    checks: list[tuple[Cmd, str, UUID, list[UUID]]] = []
    for c in cmds:
        if c.kind not in ('insert', 'update'):
            continue
        fields = model.fields(c.collection_id)
        for k, v in list(c.fields.items()):
            f = fields.get(k)
            if not f or f.get('type') != 'relation' or v is None:
                continue
            target = model.colls_by_ref.get(f.get('target', ''))
            ids = []
            for x in v:
                if x.startswith(TEMP_PREFIX):
                    if x not in temp:
                        issues.add(c.op_index, f'no insert named {x!r} in this change set', field=k)
                        continue
                    ids.append(temp[x])
                else:
                    ids.append(UUID(x))
            c.fields[k] = [str(x) for x in ids]
            if target is None:
                issues.add(c.op_index, f'relation target {f.get("target")!r} is missing', field=k)
                continue
            checks.append((c, k, target['id'], ids))
    lookup = {x for _, _, _, ids in checks for x in ids if x not in made}
    live = {}
    if lookup:
        live = {r['id']: r['collection_id'] for r in _q(
            conn, 'select id, collection_id from blocks where workspace_id = %s and id = any(%s) '
                  'and deleted_at is null', (ws, list(lookup))).fetchall()}
    for c, k, target_id, ids in checks:
        for x in ids:
            if (made.get(x) or live.get(x)) != target_id:
                issues.add(c.op_index, f'{x} is not a live record of {model.ref(target_id)}', field=k)


# ---------------------------------------------------------------- stitches (§5)

def _where_ok(where: list[dict] | None, props: dict) -> bool:
    for w in where or []:
        v = props.get(w.get('field'))
        if w.get('op') == 'eq' and v != w.get('value'):
            return False
        if w.get('op') == 'ne' and v == w.get('value'):
            return False
        if w.get('op') == 'empty' and v not in (None, '', []):
            return False
    return True


def expand_stitches(conn: psycopg.Connection, ws: UUID, cmds: list[Cmd], model: Model) -> list[Cmd]:
    """One hop per stitch, chains up to 3 hops; each derived insert carries `_via: {app, record_id}`.

    A stitch lives on the receiving app's page (`{from, to, map: [{to, from? | const?}], where?}`) and fires
    on insert. `"on": "occurrence"` stitches (Subscriptions → Budget) belong to the sweep and are skipped
    here, as is a stitch whose `from` or `to` collection is missing ("waiting for Groceries").
    """
    stitches = []
    for page in model.pages.values():
        for s in page['properties'].get('stitches') or []:
            if isinstance(s, dict) and s.get('on') != 'occurrence' and s.get('enabled', True) is not False:
                stitches.append(s)
    if not stitches:
        return []
    extra: list[Cmd] = []
    frontier = [c for c in cmds if c.kind == 'insert']
    for hop in range(1, STITCH_HOPS + 1):
        nxt = []
        for c in frontier:
            ref = model.ref(c.collection_id)
            for s in stitches:
                to = model.colls_by_ref.get(s.get('to', ''))
                if s.get('from') != ref or to is None or not _where_ok(s.get('where'), c.fields):
                    continue
                tfields = model.fields(to['id'])
                props: dict[str, Any] = {}
                for m in s.get('map') or []:
                    tkey = m.get('to')
                    if tkey not in tfields:
                        continue
                    raw = c.fields.get(m['from']) if 'from' in m else m.get('const')
                    try:
                        val = coerce_value(tfields[tkey], raw, model.tz)
                    except CoerceError:
                        continue
                    if val is not None:
                        props[tkey] = val
                props['_via'] = {'app': model.app_key(c.collection_id), 'record_id': str(c.record_id)}
                nxt.append(Cmd('insert', uuid.uuid4(), to['id'], props, add_at=_view_add_at(model, to['id']),
                               op_index=c.op_index, hop=hop))
        extra.extend(nxt)
        frontier = nxt
        if not frontier:
            break
    return extra


def affected_apps(model: Model, cmds: list[Cmd]) -> list[str]:
    """Target apps: apps with changed records, plus Calendar when a `calendar: true` collection changed (§5)."""
    out: list[str] = []
    cal = False
    for c in cmds:
        if c.collection_id not in model.colls:
            continue
        pid = str(model.colls[c.collection_id]['parent_id'])
        if pid not in out:
            out.append(pid)
        if model.cprops(c.collection_id).get('calendar'):
            cal = True
    calendar = model.pages_by_key.get('calendar')
    if cal and calendar and str(calendar['id']) not in out:
        out.append(str(calendar['id']))
    return out


def is_flagged(cmds: list[Cmd]) -> bool:
    """Bulk flag (§5): more than 5 deletes, or more than 5 updates that aren't closing an open item."""
    deletes = sum(1 for c in cmds if c.kind == 'delete')
    updates = sum(1 for c in cmds if c.kind == 'update'
                  and not (set(c.fields) <= {'status', 'done', 'price', 'bought_on', 'trip', 'qty'}
                           and (c.fields.get('status') == 'bought' or c.fields.get('done') is True)))
    return deletes > BULK_LIMIT or updates > BULK_LIMIT


# ---------------------------------------------------------------- apply (§5 step 5)

def _event(conn, ws: UUID, cs: UUID, block_id: UUID | None, path: str | None, old: Any, new: Any,
           version: int | None) -> int:
    return _q(conn,
              'insert into events (workspace_id, change_set_id, block_id, field_path, old, new, version) '
              'values (%s, %s, %s, %s, %s, %s, %s) returning server_seq',
              (ws, cs, block_id, path, _j(old), _j(new), version)).fetchone()['server_seq']


def _status_event(conn, ws: UUID, cs: UUID, old: str | None, new: str) -> int:
    return _event(conn, ws, cs, None, 'status', old, new, None)


def _insert_cs(conn, ws: UUID, *, actor: str, origin: str, status: str, user_id: UUID | None = None,
               ops: list[dict] | None = None, title: str | None = None, summary: str | None = None,
               source: dict | None = None, run_id: UUID | None = None, input_hash: str | None = None,
               undo_of: UUID | None = None) -> UUID:
    return _q(conn,
              'insert into change_sets (workspace_id, actor, user_id, origin, status, source, title, summary, ops, '
              'input_hash, run_id, undo_of) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id',
              (ws, actor, user_id, origin, status, Jsonb(source or {}), title, summary, Jsonb(ops or []),
               input_hash, run_id, undo_of)).fetchone()['id']


def _sibling(conn, ws, parent: UUID, exclude: UUID | None, *, above: str | None = None,
             below: str | None = None, first: bool = False) -> str | None:
    """The key next to a position among live siblings: the largest key < below, the smallest key > above,
    or the first / last key."""
    excl = exclude or uuid.UUID(int=0)
    base = 'select position from blocks where workspace_id = %s and parent_id = %s and deleted_at is null and id <> %s'
    if above is not None:
        r = _q(conn, base + ' and position > %s order by position, id limit 1', (ws, parent, excl, above)).fetchone()
    elif below is not None:
        r = _q(conn, base + ' and position < %s order by position desc, id desc limit 1',
               (ws, parent, excl, below)).fetchone()
    elif first:
        r = _q(conn, base + ' order by position, id limit 1', (ws, parent, excl)).fetchone()
    else:
        r = _q(conn, base + ' order by position desc, id desc limit 1', (ws, parent, excl)).fetchone()
    return r['position'] if r else None


def _neighbour(conn, ws, parent: UUID, nid: UUID | None, exclude: UUID | None, list_value: Any) -> dict | None:
    if nid is None or nid == exclude:
        return None
    r = _q(conn, 'select id, position, properties from blocks where workspace_id = %s and id = %s '
                 'and parent_id = %s and deleted_at is null', (ws, nid, parent)).fetchone()
    if r is None or (list_value is not None and r['properties'].get('list') != list_value):
        return None
    return r


def position_for(conn, ws: UUID, parent: UUID, before_id: UUID | None = None, after_id: UUID | None = None,
                 add_at: str | None = 'end', exclude: UUID | None = None, list_value: Any = None) -> str:
    """A key for a block placed between `before_id` (above) and `after_id` (below) under `parent`, read
    under the workspace lock (§4). A neighbour that moved away, was deleted or sits on another list is
    dropped; with neither, the block goes at the end (or the start, for `addAt: 'start'`) (§11 #26)."""
    b = _neighbour(conn, ws, parent, before_id, exclude, list_value)
    a = _neighbour(conn, ws, parent, after_id, exclude, list_value)
    if b and a and b['position'] >= a['position']:
        a = None
    if b and a:
        lo, hi = b['position'], a['position']
    elif b:
        lo, hi = b['position'], _sibling(conn, ws, parent, exclude, above=b['position'])
    elif a:
        lo, hi = _sibling(conn, ws, parent, exclude, below=a['position']), a['position']
    elif add_at == 'start':
        lo, hi = None, _sibling(conn, ws, parent, exclude, first=True)
    else:
        lo, hi = _sibling(conn, ws, parent, exclude), None
    return pos.key_between(lo, hi)


def _safe_position(conn, ws, parent, **kw) -> str:
    try:
        return position_for(conn, ws, parent, **kw)
    except ValueError:  # a malformed or duplicate key among siblings: rewrite the parent, then retry
        rebalance(conn, ws, parent)
        return position_for(conn, ws, parent, **kw)


@dataclass
class _Applied:
    blocks: dict[UUID, dict] = dc_field(default_factory=dict)
    seq: int = 0
    long_parents: set[UUID] = dc_field(default_factory=set)
    warnings: list[dict] = dc_field(default_factory=list)
    events: int = 0


def _write(conn, ws: UUID, cs: UUID, cmds: list[Cmd], out: _Applied) -> None:
    ids = [c.record_id for c in cmds if c.kind != 'insert']
    cache: dict[UUID, dict] = {}
    if ids:
        cache = {r['id']: r for r in _q(conn, 'select * from blocks where workspace_id = %s and id = any(%s) '
                                              'for update', (ws, ids)).fetchall()}

    def ev(block_id, path, old, new, version):
        out.seq = max(out.seq, _event(conn, ws, cs, block_id, path, old, new, version))
        out.events += 1

    for c in cmds:
        if c.kind == 'insert':
            key = _safe_position(conn, ws, c.collection_id, before_id=c.before_id, after_id=c.after_id,
                                 add_at=c.add_at, list_value=c.fields.get('list') if (c.before_id or c.after_id) else None)
            r = _q(conn, "insert into blocks (id, workspace_id, parent_id, collection_id, block_type, position, "
                         "properties) values (%s, %s, %s, %s, 'record', %s, %s) returning *",
                   (c.record_id, ws, c.collection_id, c.collection_id, key, Jsonb(c.fields))).fetchone()
            ev(r['id'], None, None, r['properties'], r['version'])
            if pos.needs_rebalance(key):
                out.long_parents.add(c.collection_id)
        else:
            r = cache[c.record_id]
            if c.kind == 'update':
                props = dict(r['properties'])
                changed = []
                for k, v in c.fields.items():
                    old = props.get(k)
                    if old == v:
                        continue
                    if v is None:
                        props.pop(k, None)
                    else:
                        props[k] = v
                    changed.append((k, old, v))
                if not changed:
                    continue
                if c.base_version is not None and r['version'] > c.base_version:
                    later = _q(conn, 'select distinct field_path from events where block_id = %s and version > %s '
                                     'and field_path = any(%s)', (r['id'], c.base_version, [k for k, _, _ in changed]))
                    for x in later.fetchall():
                        out.warnings.append({'superseded': x['field_path'], 'block_id': str(r['id'])})
                r = _q(conn, 'update blocks set properties = %s, version = version + 1, updated_at = now() '
                             'where id = %s returning *', (Jsonb(props), r['id'])).fetchone()
                for k, old, new in changed:
                    ev(r['id'], k, old, new, r['version'])
            elif c.kind == 'delete':
                r = _q(conn, 'update blocks set deleted_at = now(), version = version + 1, updated_at = now() '
                             'where id = %s returning *', (r['id'],)).fetchone()
                ev(r['id'], None, r['properties'], None, r['version'])
            elif c.kind == 'restore':
                r = _q(conn, 'update blocks set deleted_at = null, version = version + 1, updated_at = now() '
                             'where id = %s returning *', (r['id'],)).fetchone()
                ev(r['id'], None, None, r['properties'], r['version'])
            elif c.kind == 'move':
                new_list = c.fields.get('list', r['properties'].get('list'))
                key = _safe_position(conn, ws, r['parent_id'], before_id=c.before_id, after_id=c.after_id,
                                     add_at='end', exclude=r['id'],
                                     list_value=new_list if 'list' in c.fields or new_list is not None else None)
                props = dict(r['properties'])
                list_changed = 'list' in c.fields and props.get('list') != c.fields['list']
                old_list = props.get('list')
                if list_changed:
                    props['list'] = c.fields['list']
                if key == r['position'] and not list_changed:
                    continue
                old_key = r['position']
                r = _q(conn, 'update blocks set position = %s, properties = %s, version = version + 1, '
                             'updated_at = now() where id = %s returning *', (key, Jsonb(props), r['id'])).fetchone()
                ev(r['id'], POSITION_PATH, old_key, key, r['version'])
                if list_changed:
                    ev(r['id'], 'list', old_list, c.fields['list'], r['version'])
                if pos.needs_rebalance(key):
                    out.long_parents.add(r['parent_id'])
        cache[r['id']] = r
        out.blocks[r['id']] = r


def rebalance(conn: psycopg.Connection, ws: UUID, parent_id: UUID) -> UUID | None:
    """Rewrite a parent's keys evenly, as one `system` / `sweep` change set (§4). Returns its id, or None."""
    _lock(conn, ws)
    with conn.transaction():
        kids = _q(conn, 'select id, position from blocks where workspace_id = %s and parent_id = %s '
                        'and deleted_at is null order by position, id for update', (ws, parent_id)).fetchall()
        keys = pos.even_keys(len(kids))
        if all(k['position'] == key for k, key in zip(kids, keys)):
            return None
        cs = _insert_cs(conn, ws, actor='system', origin='sweep', status='stitched', title='Rebalance')
        seq = 0
        for k, key in zip(kids, keys):
            if k['position'] == key:
                continue
            v = _q(conn, 'update blocks set position = %s, version = version + 1, updated_at = now() '
                         'where id = %s returning version', (key, k['id'])).fetchone()['version']
            seq = _event(conn, ws, cs, k['id'], POSITION_PATH, k['position'], key, v)
        conn.execute('update change_sets set stitched_seq = %s where id = %s', (seq, cs))
        return cs


def _max_seq(conn, ws: UUID) -> int:
    return _q(conn, 'select coalesce(max(server_seq), 0) as s from events where workspace_id = %s',
              (ws,)).fetchone()['s']


def _result(conn, ws: UUID, cs: UUID, applied: _Applied, model: Model, cmds: list[Cmd],
            compute_faces: FacesHook | None, **extra) -> dict[str, Any]:
    apps = affected_apps(model, cmds)
    faces = (compute_faces or no_faces)(conn, ws, apps) if apps else {}
    return {'change_set_id': str(cs), 'server_seq': applied.seq or _max_seq(conn, ws),
            'blocks': [_block_out(b) for b in applied.blocks.values()], 'faces': faces,
            'warnings': applied.warnings, 'targets': apps, **extra}


def _expand(conn, ws, cmds: list[Cmd], model: Model, origin: str, expand: ExpandHook | None) -> list[Cmd]:
    if origin in NO_STITCH_ORIGINS or expand is None:
        return cmds
    return cmds + list(expand(conn, ws, cmds, model))


def _get_cs(conn, ws: UUID, cs_id: UUID, lock: bool = False) -> dict:
    r = _q(conn, 'select * from change_sets where id = %s and workspace_id = %s' + (' for update' if lock else ''),
           (cs_id, ws)).fetchone()
    if r is None:
        raise CommandError(404, {'error': 'not_found', 'what': 'change_set'})
    return r


def _transition(conn, ws: UUID, cs_id: UUID, frm: str, to: str, extra_sql: str = '', extra: tuple = ()) -> dict:
    """The guarded transition (§5): one conditional update; zero rows is 409 {status} (or 404)."""
    r = _q(conn, f'update change_sets set status = %s, updated_at = now(){extra_sql} '
                 'where id = %s and workspace_id = %s and status = %s returning *',
           (to, *extra, cs_id, ws, frm)).fetchone()
    if r is None:
        cur = _get_cs(conn, ws, cs_id)
        raise CommandError(409, {'error': 'status', 'status': cur['status']})
    return r


# ---------------------------------------------------------------- public API

def _app_ops(raw: Any) -> bool:
    """App ops (create_app, update_app, delete_app; api/commands/apps.py) take their own path."""
    return (isinstance(raw, list) and bool(raw)
            and all(isinstance(o, dict) and o.get('op') in ('create_app', 'update_app', 'delete_app') for o in raw))


def apply(conn: psycopg.Connection, ws: UUID, change_set_id: UUID, *, compute_faces: FacesHook | None = None,
          expand: ExpandHook | None = expand_stitches, context: str = 'confirm') -> dict[str, Any]:
    """Write a change set's stored ops to blocks (resolve again on current data, expand, apply, events).

    Building block for `confirm` and `run`: it doesn't check or change the status, so call it only on a
    change set you've just claimed. Sets `stitched_seq`.
    """
    _lock(conn, ws)
    with conn.transaction():
        cs = _get_cs(conn, ws, change_set_id)
        if _app_ops(cs['ops']):
            from . import apps
            return apps.apply_ops(conn, ws, cs, compute_faces=compute_faces, context=context)
        model = load_model(conn, ws)
        ops = parse_ops(cs['ops'])
        cmds = resolve(conn, ws, model, ops, cs['origin'], context=context, lock=True)
        cmds = _expand(conn, ws, cmds, model, cs['origin'], expand)
        applied = _Applied()
        _write(conn, ws, change_set_id, cmds, applied)
        conn.execute('update change_sets set stitched_seq = %s, updated_at = now() where id = %s',
                     (applied.seq or None, change_set_id))
        for parent in applied.long_parents:
            rebalance(conn, ws, parent)
        return _result(conn, ws, change_set_id, applied, model, cmds, compute_faces)


def create_change_set(conn: psycopg.Connection, ws: UUID, actor: str, origin: str, ops: list[Any], *,
                      user_id: UUID | None = None, title: str | None = None, summary: str | None = None,
                      source: dict | None = None, run_id: UUID | None = None, input_hash: str | None = None,
                      expand: ExpandHook | None = expand_stitches) -> UUID:
    """Validate ops (422 with every issue) and store them as a `basted` change set. Nothing touches blocks.
    Writes a status event so other devices pick up the new card. App ops (create_app, update_app, delete_app)
    go to api/commands/apps.py."""
    if _app_ops(ops):
        from . import apps
        return apps.store(conn, ws, actor, origin, ops, user_id=user_id, title=title, summary=summary,
                          source=source, run_id=run_id)
    parsed = parse_ops(ops)
    _lock(conn, ws)
    with conn.transaction():
        model = load_model(conn, ws)
        resolve(conn, ws, model, parsed, origin, context='propose')
        cs = _insert_cs(conn, ws, actor=actor, origin=origin, status='basted', user_id=user_id,
                        ops=dump_ops(parsed), title=title, summary=summary, source=source, run_id=run_id,
                        input_hash=input_hash)
        _status_event(conn, ws, cs, None, 'basted')
        return cs


def preview(conn: psycopg.Connection, ws: UUID, change_set_id: UUID, *,
            expand: ExpandHook | None = expand_stitches) -> dict[str, Any]:
    """What a basted card would write, on current data: `expanded` ops (with stitch fan-out), `targets`
    (app ids), `flagged`, and `issues` if it no longer validates. Writes nothing. Faces before / after are
    the formula engine's dry run (api/logic), fed from `expanded`."""
    cs = _get_cs(conn, ws, change_set_id)
    if _app_ops(cs['ops']):
        from . import apps
        return apps.preview(conn, ws, cs)
    model = load_model(conn, ws)
    try:
        cmds = resolve(conn, ws, model, parse_ops(cs['ops']), cs['origin'], context='confirm')
    except CommandError as e:
        return {'status': cs['status'], 'expanded': [], 'targets': [], 'flagged': False,
                'issues': e.body.get('issues', [])}
    cmds = _expand(conn, ws, cmds, model, cs['origin'], expand)
    return {'status': cs['status'], 'expanded': [c.out(model) for c in cmds],
            'targets': affected_apps(model, cmds), 'flagged': is_flagged(cmds), 'issues': []}


def confirm(conn: psycopg.Connection, ws: UUID, change_set_id: UUID, *, compute_faces: FacesHook | None = None,
            expand: ExpandHook | None = expand_stitches) -> dict[str, Any]:
    """basted → stitched: re-validate on current data, apply all expanded ops, return final faces.
    A second confirm is 409 {status: 'stitched'}; a record deleted since is 409 {issues} (§11 #1, #2, #13)."""
    _lock(conn, ws)
    with conn.transaction():
        _transition(conn, ws, change_set_id, 'basted', 'stitched')
        result = apply(conn, ws, change_set_id, compute_faces=compute_faces, expand=expand, context='confirm')
        seq = _status_event(conn, ws, change_set_id, 'basted', 'stitched')
        conn.execute('update change_sets set stitched_seq = %s where id = %s', (seq, change_set_id))
        result['server_seq'] = seq
        return result


def dismiss(conn: psycopg.Connection, ws: UUID, change_set_id: UUID) -> None:
    """basted → dismissed. Nothing written to blocks; a status event drops the card on other devices."""
    _lock(conn, ws)
    with conn.transaction():
        _transition(conn, ws, change_set_id, 'basted', 'dismissed')
        _status_event(conn, ws, change_set_id, 'basted', 'dismissed')


def update_ops(conn: psycopg.Connection, ws: UUID, change_set_id: UUID, ops: list[Any], version: int) -> dict:
    """Review items (`PATCH /change-sets/{id}`): replace the ops of a basted set at the version the client saw."""
    if _app_ops(ops):
        from . import apps
        _lock(conn, ws)
        with conn.transaction():
            norm = apps.normalize_ops(load_model(conn, ws), ops)
            r = _q(conn, "update change_sets set ops = %s, version = version + 1, updated_at = now() "
                         "where id = %s and workspace_id = %s and status = 'basted' and version = %s returning *",
                   (Jsonb(norm), change_set_id, ws, version)).fetchone()
            if r is None:
                cur = _get_cs(conn, ws, change_set_id)
                raise CommandError(409, {'error': 'version', 'status': cur['status'], 'version': cur['version']})
            return {'id': str(r['id']), 'version': r['version'], 'status': r['status']}
    parsed = parse_ops(ops)
    _lock(conn, ws)
    with conn.transaction():
        cs = _get_cs(conn, ws, change_set_id)
        resolve(conn, ws, load_model(conn, ws), parsed, cs['origin'], context='propose')
        r = _q(conn, "update change_sets set ops = %s, version = version + 1, updated_at = now() "
                     "where id = %s and workspace_id = %s and status = 'basted' and version = %s returning *",
               (Jsonb(dump_ops(parsed)), change_set_id, ws, version)).fetchone()
        if r is None:
            cur = _get_cs(conn, ws, change_set_id)
            raise CommandError(409, {'error': 'version', 'status': cur['status'], 'version': cur['version']})
        return {'id': str(r['id']), 'version': r['version'], 'status': r['status']}


def run(conn: psycopg.Connection, ws: UUID, ops: list[Any], *, actor: str, origin: str,
        user_id: UUID | None = None, title: str | None = None, summary: str | None = None,
        source: dict | None = None, compute_faces: FacesHook | None = None,
        expand: ExpandHook | None = expand_stitches) -> dict[str, Any]:
    """Validate and apply at once as a `stitched` change set (gestures, templates, connector, seed)."""
    if _app_ops(ops):
        from . import apps
        return apps.run_ops(conn, ws, ops, actor=actor, origin=origin, user_id=user_id, title=title,
                            summary=summary, source=source, compute_faces=compute_faces)
    parsed = parse_ops(ops)
    context = 'gesture' if origin == 'gesture' else 'propose'
    _lock(conn, ws)
    with conn.transaction():
        model = load_model(conn, ws)
        cmds = resolve(conn, ws, model, parsed, origin, context=context, lock=True)
        cmds = _expand(conn, ws, cmds, model, origin, expand)
        cs = _insert_cs(conn, ws, actor=actor, origin=origin, status='stitched', user_id=user_id,
                        ops=dump_ops(parsed), title=title, summary=summary, source=source)
        applied = _Applied()
        _write(conn, ws, cs, cmds, applied)
        conn.execute('update change_sets set stitched_seq = %s where id = %s', (applied.seq or None, cs))
        for parent in applied.long_parents:
            rebalance(conn, ws, parent)
        return _result(conn, ws, cs, applied, model, cmds, compute_faces)


def run_gesture(conn: psycopg.Connection, ws: UUID, user_id: UUID | None, ops: list[Any], *,
                compute_faces: FacesHook | None = None, expand: ExpandHook | None = expand_stitches) -> dict:
    """A user gesture: one stitched change set, `actor user`, `origin gesture`, offered for Undo."""
    return run(conn, ws, ops, actor='user', origin='gesture', user_id=user_id,
               compute_faces=compute_faces, expand=expand)


def undo(conn: psycopg.Connection, ws: UUID, change_set_id: UUID, *, user_id: UUID | None = None,
         compute_faces: FacesHook | None = None) -> dict[str, Any]:
    """stitched → undone (a Clair set goes straight back to basted, so it can be confirmed again).

    Writes every event's `old` back as a new change set (`origin undo`, `undo_of`). Later edits to the same
    block and field don't block it (DevDay rule); they come back as `warnings[{changed_since}]` (§5, §11 #4).
    A second undo is 409 {status}. System sets (seed, sweep, connector) aren't offered for Undo: 409.
    """
    _lock(conn, ws)
    with conn.transaction():
        cs = _get_cs(conn, ws, change_set_id, lock=True)
        if cs['actor'] == 'system':
            raise CommandError(409, {'error': 'not_undoable', 'status': cs['status']})
        final = 'basted' if cs['actor'] == 'clair' else 'undone'
        _transition(conn, ws, change_set_id, 'stitched', final)
        events = _q(conn, 'select * from events where change_set_id = %s and block_id is not null '
                          'order by server_seq desc', (change_set_id,)).fetchall()
        since = cs['stitched_seq'] or 0
        warnings: list[dict] = []
        if events:
            later = _q(conn,
                       'select distinct on (block_id, field_path) block_id, field_path, new from events '
                       'where workspace_id = %s and block_id = any(%s) and server_seq > %s and change_set_id <> %s '
                       'order by block_id, field_path, server_seq desc',
                       (ws, list({e['block_id'] for e in events}), since, change_set_id)).fetchall()
            later_by = {(r['block_id'], r['field_path']): r['new'] for r in later}
            seen = set()
            for e in events:
                k = (e['block_id'], e['field_path'])
                if k in later_by and k not in seen:
                    seen.add(k)
                    warnings.append({'changed_since': {'block_id': str(e['block_id']), 'field': e['field_path'],
                                                       'now': later_by[k], 'was': e['new']}})
        ucs = _insert_cs(conn, ws, actor='user', origin='undo', status='stitched', user_id=user_id,
                         title=cs['title'], undo_of=change_set_id)
        applied = _Applied(warnings=warnings)
        rows = {r['id']: r for r in _q(conn, 'select * from blocks where id = any(%s) for update',
                                         (list({e['block_id'] for e in events}),)).fetchall()} if events else {}

        def ev(block_id, path, old, new, version):
            applied.seq = max(applied.seq, _event(conn, ws, ucs, block_id, path, old, new, version))

        for e in events:
            r = rows[e['block_id']]
            path = e['field_path']
            if path is None and e['old'] is None:          # was an insert or restore → delete
                if r['deleted_at'] is not None:
                    continue
                r = _q(conn, 'update blocks set deleted_at = now(), version = version + 1, updated_at = now() '
                             'where id = %s returning *', (r['id'],)).fetchone()
                ev(r['id'], None, r['properties'], None, r['version'])
            elif path is None:                              # was a delete → restore
                if r['deleted_at'] is None:
                    continue
                try:
                    r = _q(conn, 'update blocks set deleted_at = null, version = version + 1, updated_at = now() '
                                 'where id = %s returning *', (r['id'],)).fetchone()
                except psycopg.errors.UniqueViolation as exc:   # a deleted app whose key is taken again
                    raise CommandError(409, {'error': 'exists', 'status': cs['status'], 'issues': [
                        {'field': 'key', 'problem': f'an app with key {r["properties"].get("key")!r} exists',
                         'code': 'exists'}]}) from exc
                ev(r['id'], None, None, r['properties'], r['version'])
            elif path == POSITION_PATH:
                if r['position'] == e['old']:
                    continue
                old_key = r['position']
                r = _q(conn, 'update blocks set position = %s, version = version + 1, updated_at = now() '
                             'where id = %s returning *', (e['old'], r['id'])).fetchone()
                ev(r['id'], POSITION_PATH, old_key, e['old'], r['version'])
            else:
                props = dict(r['properties'])
                cur = props.get(path)
                if cur == e['old']:
                    continue
                if e['old'] is None:
                    props.pop(path, None)
                else:
                    props[path] = e['old']
                r = _q(conn, 'update blocks set properties = %s, version = version + 1, updated_at = now() '
                             'where id = %s returning *', (Jsonb(props), r['id'])).fetchone()
                ev(r['id'], path, cur, e['old'], r['version'])
            rows[r['id']] = r
            applied.blocks[r['id']] = r
        conn.execute('update change_sets set stitched_seq = %s where id = %s', (applied.seq or None, ucs))
        seq = _status_event(conn, ws, change_set_id, 'stitched', final)
        applied.seq = max(applied.seq, seq)
        model = load_model(conn, ws)
        touched = [Cmd('update', b['id'], b['collection_id']) for b in applied.blocks.values()
                   if b.get('collection_id') in model.colls]
        return _result(conn, ws, ucs, applied, model, touched, compute_faces, undo_of=str(change_set_id),
                       status=final)


def find_duplicate(conn: psycopg.Connection, ws: UUID, input_hash: str) -> dict | None:
    """§11 #6: a stitched change set with the same receipt hash ("Already added on Fri 20 Nov?")."""
    return _q(conn, "select id, created_at, title from change_sets where workspace_id = %s and input_hash = %s "
                    "and status = 'stitched' order by created_at desc limit 1", (ws, input_hash)).fetchone()
