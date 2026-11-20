"""Change-set cards, fully expanded for the client (ui-tech-plan.md §4 `Proposal`, backend.md §5, §10).

`expand_change_set(conn, ld, row)` turns one `change_sets` row into a `ChangeSet` (api/models.py): the stored ops
in contract shape, `expanded` (ops + stitch fan-out, tagged `via`), `targets`, `deltas`, `lines`, `actions`,
`review`, `flagged`. Used by `GET /change-sets`, `PATCH /change-sets/{id}`, `/home` needsOk and Clair's
`proposal` event.

Faces "after" come from a dry run in memory: the set's resolved commands are applied to a copy of the loaded
workspace's records and the formula engine runs on the copy. Nothing touches `blocks` or `events`, so a basted
set never counts before confirm (check.py item 2). Deltas are recomputed on every read (§11 #12).

App references in `targets`, `deltas[].app`, `lines[].apps` and `review[].app` are app keys (as `faces{}`).
"""
from __future__ import annotations

import copy
import json
import uuid
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from .commands.ops import CommandError, Op, localize, parse_ops
from .commands.apps import is_app_ops, normalize_ops
from .commands.service import Cmd, Model, _expand, affected_apps, expand_stitches, is_flagged, load_model, resolve
from .logic import fmt as F
from .logic import formula
from .logic.clock import parse_value, to_local
from .workspace import Loaded, faces as ws_faces

SOURCE_KINDS = {'text', 'voice', 'photo', 'file', 'insight', 'checkin', 'workflow', 'gesture', 'template', 'sweep',
                'undo', 'seed'}
ORIGIN_KIND = {'clair': 'text', 'gesture': 'gesture', 'template': 'template', 'undo': 'undo', 'sweep': 'sweep',
               'seed': 'seed', 'connector': 'sweep'}
KIND_LABEL = {'text': 'You typed', 'voice': 'You said', 'photo': 'Photo', 'file': 'File', 'gesture': 'You',
              'template': 'Template', 'undo': 'Undo', 'sweep': 'Quilt', 'seed': 'Quilt', 'workflow': 'Rule',
              'insight': 'Clair noticed', 'checkin': 'Check-in'}
CHANGE = {'insert': 'new', 'update': 'changed', 'delete': 'removed', 'restore': 'new', 'move_occurrence': 'moved',
          'keep': 'kept', 'complete': 'changed', 'skip': 'changed', 'move': 'changed'}
QUIET_SELECTS = {'status', 'list', 'usual', 'flow', 'meal'}


# ---------------------------------------------------------------- small helpers

def _str(v: Any) -> str:
    if isinstance(v, str):
        return v
    return json.dumps(v) if isinstance(v, (dict, list, bool)) or v is None else str(v)


def _public(fields: dict) -> dict:
    return {k: v for k, v in (fields or {}).items() if not str(k).startswith('_')}


def _opt_label(field: dict, v: Any) -> str | None:
    for o in field.get('options') or []:
        oid = o.get('id') if isinstance(o, dict) else o
        if oid == v:
            return str(o.get('label', oid)) if isinstance(o, dict) else str(o)
    return None


def _when(v: Any, tz: str, today: date) -> str | None:
    """'Today, 5:45 pm' · 'Mon 23 Nov 6:00 pm' · 'Sun 22 Nov'."""
    if v in (None, ''):
        return None
    try:
        pv = parse_value(v, tz)
    except Exception:
        return None
    if isinstance(pv, datetime):
        lv = to_local(pv, tz)
        d, t = lv.date(), F.time_label(lv)
        if d == today:
            return f'Today, {t}'
        if d == today + timedelta(days=1):
            return f'Tomorrow, {t}'
        return f'{F.day_label(d, today)} {t}'
    if isinstance(pv, date):
        if pv == today:
            return 'Today'
        return F.day_label(pv, today)
    return None


def _local_dt(v: Any, tz: str) -> datetime | date | None:
    if v in (None, ''):
        return None
    try:
        pv = parse_value(v, tz)
    except Exception:
        return None
    return to_local(pv, tz) if isinstance(pv, datetime) else pv


class _Ws:
    """Lookups over the loaded workspace and the command model."""

    def __init__(self, ld: Loaded, model: Model):
        self.ld, self.model = ld, model
        self.by_id = {r['id']: r for r in ld.records}
        self.today = ld.now.date()

    def coll(self, ref: str) -> dict | None:
        app_key, _, ckey = ref.partition('/')
        a = self.ld.app(app_key)
        for c in (a or {}).get('collections') or []:
            if c.get('key') == ckey:
                return c
        return None

    def fields(self, ref: str) -> dict[str, dict]:
        return {f['key']: f for f in (self.coll(ref) or {}).get('fields') or [] if 'key' in f}

    def app_name(self, key: str) -> str:
        a = self.ld.app(key)
        return (a or {}).get('name') or key

    def title(self, ref: str, props: dict) -> str:
        c = self.coll(ref) or {}
        tf = c.get('titleField')
        for k in [tf, 'name', 'title', 'note', 'store']:
            if k and props.get(k) not in (None, ''):
                v = props[k]
                if isinstance(v, list):   # a relation as title (workout/sets: exercise)
                    return ', '.join(self.rel_titles(ref, k, v)) or c.get('label') or c.get('name') or ''
                return str(v)
        return c.get('label') or c.get('name') or ''

    def rel_titles(self, ref: str, key: str, ids: list) -> list[str]:
        f = self.fields(ref).get(key) or {}
        out = []
        for x in ids or []:
            r = self.by_id.get(str(x))
            if r is not None:
                out.append(self.title(r['collection'], r['properties']))
        return out if f.get('target') or out else []

    def source_name(self, src: str | None) -> str | None:
        """`reason_source` (a record id, a seed key or an app key) → the app it came from."""
        if not src:
            return None
        r = self.by_id.get(src)
        if r is None:
            for ref in self.model.colls_by_ref:
                r = self.by_id.get(str(uuid.uuid5(UUID(str(self.ld.workspace_id)), f'{ref}/{src}')))
                if r is not None:
                    break
        if r is not None:
            if (r['properties'] or {}).get('source') == 'google':
                return 'Google Calendar'
            return self.app_name(r['collection'].split('/')[0])
        if self.ld.app(src) is not None:
            return self.app_name(src)
        return None


# ---------------------------------------------------------------- contract ops

def _ref_of(model: Model, o: Op) -> str | None:
    if o.app and o.collection:
        return f'{o.app}/{o.collection}'
    if o.collection_id and o.collection_id in model.colls:
        return model.ref(o.collection_id)
    return None


def _reasons(o: Op) -> dict:
    return {k: getattr(o, k) for k in ('reason', 'reason_source', 'also', 'also_source') if getattr(o, k)}


def _to_row_op(o: Op, cmds: list[Cmd] | None, model: Model, names: dict[str, str]) -> dict:
    """One stored op in the contract's RowOp shape. Values are the coerced ones when the set resolved."""
    def unname(fields: dict) -> dict:
        out = {}
        for k, v in _public(fields).items():
            if isinstance(v, list):
                v = [names.get(str(x), x) for x in v]
            out[k] = v
        return out

    mine = cmds or []
    if o.op == 'insert':
        c = next((c for c in mine if c.kind == 'insert' and c.hop == 0), None)
        d = {'op': 'insert', 'ref': _ref_of(model, o) or '', 'values': unname(c.fields) if c else _public(o.fields)}
        if o.record_id:
            d['record_id'] = o.record_id
    elif o.op == 'delete':
        d = {'op': 'delete', 'rowId': o.record_id}
    elif o.op == 'move_occurrence':
        d = {'op': 'move_occurrence', 'record_id': o.record_id, 'occurrence': o.occurrence.isoformat(),
             'fields': [{'key': k, 'value': _str(v)} for k, v in o.fields.items()]}
        if o.app:
            d['app'] = o.app
        if o.collection:
            d['collection'] = o.collection
    elif o.op == 'keep':
        d = {'op': 'keep', 'record_id': o.record_id, 'occurrence': o.occurrence.isoformat() if o.occurrence else None}
    else:   # update, and gesture ops (complete, skip, move, restore) shown as the update they make
        c = next((c for c in mine if c.kind in ('update', 'move') and c.hop == 0), None)
        d = {'op': 'update', 'rowId': o.record_id, 'values': unname(c.fields) if c else _public(o.fields)}
    d.update(_reasons(o))
    return d


def row_op_to_internal(op: dict) -> dict | None:
    """A contract RowOp (PATCH /change-sets/{id}) → the stored op shape. Derived ops (`via`) are dropped."""
    if op.get('via'):
        return None
    reasons = {k: op[k] for k in ('reason', 'reason_source', 'also', 'also_source') if op.get(k)}
    kind = op['op']
    if kind == 'insert':
        app, _, coll = str(op['ref']).partition('/')
        d = {'op': 'insert', 'app': app, 'collection': coll, 'fields': dict(op.get('values') or {})}
        if op.get('record_id'):
            d['record_id'] = op['record_id']
    elif kind == 'update':
        d = {'op': 'update', 'record_id': op['rowId'], 'fields': dict(op.get('values') or {})}
    elif kind == 'delete':
        d = {'op': 'delete', 'record_id': op['rowId']}
    elif kind == 'move_occurrence':
        d = {'op': 'move_occurrence', 'record_id': op['record_id'], 'occurrence': str(op['occurrence']),
             'fields': [{'key': f['key'], 'value': f['value']} for f in op.get('fields') or []]}
        for k in ('app', 'collection'):
            if op.get(k):
                d[k] = op[k]
    elif kind == 'keep':
        d = {'op': 'keep', 'record_id': op['record_id'], 'occurrence': str(op['occurrence'])}
    else:
        raise CommandError(422, {'error': 'invalid', 'issues': [{'problem': f'unknown op {kind!r}'}]})
    d.update(reasons)
    return d


# ---------------------------------------------------------------- dry run

def _dry_run(conn, ld: Loaded, model: Model, cmds: list[Cmd]) -> formula.Ctx:
    """The workspace's records with the commands applied, in memory."""
    recs = {r['id']: r for r in ld.records}
    order = [r['id'] for r in ld.records]
    restore_ids = [c.record_id for c in cmds if c.kind == 'restore']
    restored = {}
    if restore_ids:
        restored = {str(r['id']): r for r in conn.execute(
            'select id, collection_id, properties, position, version from blocks where id = any(%s)',
            (restore_ids,)).fetchall()}
    for c in cmds:
        rid = str(c.record_id)
        if c.collection_id not in model.colls:
            continue
        ref = model.ref(c.collection_id)
        if c.kind == 'insert':
            recs[rid] = {'id': rid, 'collection': ref, 'properties': dict(c.fields), 'position': '~', 'version': 1}
            order.append(rid)
        elif c.kind in ('update', 'move'):
            r = recs.get(rid)
            if r is None:
                continue
            props = dict(r['properties'])
            for k, v in c.fields.items():
                if v is None:
                    props.pop(k, None)
                else:
                    props[k] = v
            recs[rid] = dict(r, properties=props)
        elif c.kind == 'delete':
            recs.pop(rid, None)
        elif c.kind == 'restore' and rid in restored:
            b = restored[rid]
            recs[rid] = {'id': rid, 'collection': ref, 'properties': b['properties'], 'position': b['position'],
                         'version': b['version']}
            order.append(rid)
    records = [recs[i] for i in dict.fromkeys(order) if i in recs]
    return formula.Ctx(ld.apps, records, now=ld.now, tz=ld.tz)


# ---------------------------------------------------------------- entries (one per op, plus stitch fan-out)

def _occ_dt(w: _Ws, ref: str, props: dict, occ: date):
    """An occurrence's wall time: the series' time of day on that date."""
    c = w.coll(ref) or {}
    base = _local_dt(props.get(c.get('dateField')), w.ld.tz)
    if not isinstance(base, datetime):
        rep = next((v for v in props.values() if isinstance(v, dict) and 'rule' in v), None)
        base = _local_dt((rep or {}).get('start'), w.ld.tz)
    if isinstance(base, datetime):
        return localize(datetime.combine(occ, base.replace(tzinfo=None).time()), w.ld.tz)
    return occ


def _fmt_dt(v, w: _Ws) -> str:
    if isinstance(v, datetime):
        return f'{F.day_label(v.date(), w.today)} {F.time_label(v)}'
    if isinstance(v, date):
        return F.day_label(v, w.today)
    return ''


def _extras(w: _Ws, ref: str, props: dict) -> list[str]:
    out = []
    for k, f in w.fields(ref).items():
        v = props.get(k)
        if v is None or isinstance(v, bool):
            continue
        if f.get('type') == 'money' and isinstance(v, (int, float)):
            out.append(F.money_row(v))
        elif f.get('type') == 'number' and f.get('unit') and isinstance(v, (int, float)) and f.get('unit') != '→':
            out.append(f'{F.number(v)} {f["unit"]}')
    return out


def _entries(w: _Ws, ops: list[Op], cmds: list[Cmd] | None) -> list[dict]:
    model, tz = w.model, w.ld.tz
    out = []
    by_op: dict[int, list[Cmd]] = {}
    for c in cmds or []:
        if c.op_index is not None and c.hop == 0:
            by_op.setdefault(c.op_index, []).append(c)
    for i, o in enumerate(ops):
        rec = w.by_id.get(o.record_id) if o.record_id and o.op != 'insert' else None
        if o.op == 'insert':
            ref = _ref_of(model, o)
            c = next(iter(by_op.get(i, [])), None)
            props = c.fields if c else o.fields
        else:
            ref = rec['collection'] if rec else None
            props = rec['properties'] if rec else {}
        if not ref:
            continue
        app = ref.split('/')[0]
        coll = w.coll(ref) or {}
        df = coll.get('dateField')
        e = {'i': i, 'op': o, 'app': app, 'ref': ref, 'change': CHANGE.get(o.op, 'changed'),
             'title': w.title(ref, props), 'props': props, 'hop': 0, 'dated': bool(coll.get('calendar'))}
        if o.op == 'insert':
            e['when'] = _local_dt(props.get(df), tz) if df else None
        elif o.op in ('move_occurrence', 'keep'):
            e['old'] = _occ_dt(w, ref, props, o.occurrence) if o.occurrence else None
            e['when'] = _local_dt(o.fields.get(df), tz) if o.op == 'move_occurrence' and df else e['old']
        elif o.op == 'update':
            new = (next(iter(by_op.get(i, [])), None) or Cmd('update', uuid.uuid4(), uuid.uuid4(), o.fields)).fields
            e['when'] = _local_dt(new.get(df, props.get(df)), tz) if df else None
            e['changed_fields'] = [k for k in new if not str(k).startswith('_')]
        else:
            e['when'] = _local_dt(props.get(df), tz) if df else None
        out.append(e)
    for c in cmds or []:
        if c.hop > 0 and c.collection_id in model.colls:
            ref = model.ref(c.collection_id)
            coll = w.coll(ref) or {}
            df = coll.get('dateField')
            out.append({'i': c.op_index, 'op': None, 'app': ref.split('/')[0], 'ref': ref, 'change': 'new',
                        'title': w.title(ref, c.fields), 'props': c.fields, 'hop': c.hop,
                        'dated': bool(coll.get('calendar')),
                        'when': _local_dt(c.fields.get(df), tz) if df else None})
    return out


def _near_now(v, w: _Ws) -> bool:
    return isinstance(v, datetime) and v.tzinfo is not None and abs((v - to_local(w.ld.now, w.ld.tz)).total_seconds()) < 120


def _detail(w: _Ws, e: dict) -> str:
    """One destination with one item: 'Lunch · Eating out' · 'Haircut · Barber · Sat 21 Nov 2:00 pm'."""
    parts = [e['title']] if e['title'] else []
    fields = w.fields(e['ref'])
    tf = (w.coll(e['ref']) or {}).get('titleField')
    for k, f in fields.items():
        v = e['props'].get(k)
        if v in (None, '', []) or k == tf:
            continue
        if f.get('type') == 'select' and k not in QUIET_SELECTS:
            lab = _opt_label(f, v)
            if lab:
                parts.append(lab)
        elif f.get('type') == 'relation' and isinstance(v, list):
            parts.extend(w.rel_titles(e['ref'], k, v))
    if e['change'] == 'moved' and e.get('when'):
        parts.append(_moved_when(w, e))
    elif e.get('when') is not None and not _near_now(e['when'], w):
        parts.append(_fmt_dt(e['when'], w))
    return ' · '.join(p for p in parts if p)


def _short(w: _Ws, e: dict) -> str:
    when = e.get('when')
    if when is None or _near_now(when, w):
        return e['title']
    if isinstance(when, datetime):
        return f'{e["title"]} {when.strftime("%a")} {F.time_label(when)}'
    return f'{e["title"]} {when.strftime("%a")}'


def _moved_when(w: _Ws, e: dict) -> str:
    old, new = e.get('old'), e.get('when')
    if isinstance(old, datetime) and isinstance(new, datetime):
        if old.date() == new.date():
            return f'{_fmt_dt(old, w)} → {F.time_label(new)}'
        if old.month == new.month:
            return f'{old.strftime("%a")} {old.day} → {_fmt_dt(new, w)}'
        return f'{F.day_label(old.date(), w.today)} → {_fmt_dt(new, w)}'
    return _fmt_dt(new, w) if new else ''


def _review_when(w: _Ws, e: dict) -> str:
    when = e.get('when')
    if e['change'] == 'moved':
        base = _moved_when(w, e)
    elif when is not None:
        base = _when(when.isoformat() if isinstance(when, (date, datetime)) else when, w.ld.tz, w.today) or ''
    else:
        lf = w.fields(e['ref']).get('list')
        base = _opt_label(lf, e['props'].get('list')) or '' if lf else ''
    extra = _extras(w, e['ref'], e['props']) if e['change'] in ('new', 'removed') else []
    return ' · '.join(p for p in [base, *extra] if p)


def _count_phrase(entries: list[dict]) -> str:
    n = {}
    for e in entries:
        n[e['change']] = n.get(e['change'], 0) + 1
    words = {'new': 'added', 'moved': 'moved', 'changed': 'changed', 'removed': 'removed'}
    parts = [f'{n[k]} {v}' for k, v in words.items() if n.get(k)]
    return ', '.join(parts)


# ---------------------------------------------------------------- the card

def _source(row: dict) -> dict:
    src = row.get('source') or {}
    kind = src.get('kind')
    if kind not in SOURCE_KINDS:
        kind = 'seed' if kind == 'seed_history' else ORIGIN_KIND.get(row.get('origin'), 'text')
    at = src.get('at') or row['created_at']
    if isinstance(at, str):
        try:
            at = datetime.fromisoformat(at.replace('Z', '+00:00'))
        except ValueError:
            at = row['created_at']
    if isinstance(at, datetime) and at.tzinfo is None:
        at = row['created_at']
    return {'kind': kind, 'label': src.get('label') or KIND_LABEL.get(kind, 'Clair'), 'at': at}


def expand_change_set(conn, ld: Loaded, row: dict, model: Model | None = None) -> dict:
    """A `ChangeSet` (api/models.py) for one change_sets row, computed from current data.

    `ld` is `api.workspace.load(conn, ws)`; pass `model` (`load_model`) when expanding many rows."""
    ws = ld.workspace_id
    model = model or load_model(conn, ws)
    if is_app_ops(row.get('ops')):
        return app_card(conn, ld, row, model)
    w = _Ws(ld, model)
    try:
        ops = parse_ops(row.get('ops') or [])
    except CommandError:
        ops = []
    cmds: list[Cmd] | None = None
    if row['status'] == 'basted' and ops:
        try:
            cmds = resolve(conn, ws, model, ops, row['origin'], context='confirm')
            cmds = _expand(conn, ws, cmds, model, row['origin'], expand_stitches)
        except CommandError:
            cmds = None      # no longer validates on current data: show the ops, no deltas (confirm will 409)

    # temp names back for display, so values don't show a fresh random UUID on every read
    names: dict[str, str] = {}
    for c in cmds or []:
        if c.kind == 'insert' and c.hop == 0 and c.op_index is not None:
            o = ops[c.op_index]
            if o.op == 'insert' and o.record_id:
                names[str(c.record_id)] = o.record_id
    by_op: dict[int, list[Cmd]] = {}
    for c in cmds or []:
        if c.op_index is not None and c.hop == 0:
            by_op.setdefault(c.op_index, []).append(c)
    row_ops = [_to_row_op(o, by_op.get(i), model, names) for i, o in enumerate(ops)]
    expanded = list(row_ops)
    for c in cmds or []:
        if c.hop > 0 and c.kind == 'insert' and c.collection_id in model.colls:
            via = c.fields.get('_via') or {}
            vrid = via.get('record_id')
            expanded.append({'op': 'insert', 'ref': model.ref(c.collection_id), 'values': _public(c.fields),
                             'via': {'app': via.get('app'), 'record_id': names.get(str(vrid), vrid)}})

    entries = _entries(w, ops, cmds)

    # targets: app keys, in thread order
    if cmds is not None:
        targets = []
        for pid in affected_apps(model, cmds):
            a = ld.app(pid)
            if a and a['key'] not in targets:
                targets.append(a['key'])
    else:
        targets = list(dict.fromkeys(e['app'] for e in entries if e['change'] != 'kept'))
        if any(e['dated'] for e in entries) and ld.app('calendar') and 'calendar' not in targets:
            targets.append('calendar')

    # deltas: faces before → after on the in-memory copy
    deltas: list[dict] = []
    after_faces: dict[str, dict] = {}
    before_faces = ws_faces(ld, targets)
    if cmds:
        ctx = _dry_run(conn, ld, model, cmds)
        for k in targets:
            a = ld.app(k)
            if a is None or not a.get('face'):
                continue
            after_faces[k] = formula.face(a, ctx)
            b = before_faces.get(k)
            if b and after_faces[k]['text'] != b['text']:
                deltas.append({'app': k, 'before': b['text'], 'after': after_faces[k]['text']})
    delta_of = {d['app']: d for d in deltas}

    # lines: one per destination
    lines = []
    for k in targets:
        mine = [e for e in entries if e['app'] == k]
        line: dict[str, Any] = {'apps': [k], 'what': '', 'val': ''}
        if mine:
            line['what'] = _detail(w, mine[0]) if len(mine) == 1 else ' · '.join(_short(w, e) for e in mine)
            money = 0
            seen = False
            for e in mine:
                if e['change'] != 'new':
                    continue
                for fk, f in w.fields(e['ref']).items():
                    v = e['props'].get(fk)
                    if f.get('type') == 'money' and isinstance(v, (int, float)) and not isinstance(v, bool):
                        money += v
                        seen = True
            if seen:
                line['val'] = F.money_row(money)
        else:   # reached through *dated (Calendar)
            dated = [e for e in entries if e['dated'] and e['change'] != 'kept']
            line['what'] = dated[0]['title'] if len(dated) == 1 else _count_phrase(dated)
        d = delta_of.get(k)
        if d:
            label = (after_faces.get(k) or before_faces.get(k) or {}).get('label') or ''
            line['sub'] = f'{d["before"]} → {d["after"]} {label}'.rstrip()
        lines.append(line)

    # review rows, worded by the server
    review = []
    for e in entries:
        if e['hop']:
            continue
        o = e['op']
        r = {'title': e['title'], 'when': _review_when(w, e), 'change': e['change'], 'app': e['app']}
        if o.reason:
            r['reason'] = o.reason
        src = w.source_name(o.reason_source)
        if src:
            r['source'] = src
        if o.also:
            r['also'] = o.also
        asrc = w.source_name(o.also_source)
        if asrc:
            r['also_source'] = asrc
        review.append(r)

    if len(targets) == 1:
        primary = f'Add to {w.app_name(targets[0])}'
    elif targets:
        primary = f'Add to {len(targets)} apps'
    else:
        primary = 'Add'
    src = row.get('source') or {}
    title = row.get('title') or (entries[0]['title'] if entries else '') or 'Changes'
    return {
        'id': str(row['id']),
        'status': row['status'],
        'source': _source(row),
        'mode': 'fixture' if src.get('mode') == 'fixture' or src.get('fixture') else 'live',
        'title': title,
        'summary': row.get('summary'),
        'ops': row_ops,
        'lines': lines,
        'expanded': expanded,
        'targets': targets,
        'deltas': deltas,
        'actions': {'primary': primary, 'secondary': 'Review items'},
        'flagged': is_flagged(cmds) if cmds else False,
        'version': row['version'],
        'kind': 'records',
        'review': review or None,
    }


# ---------------------------------------------------------------- app cards (kind "app": propose_app, /apps)

def _and(items: list[str]) -> str:
    items = [x for x in items if x]
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1] if items else ''


def _preview_records(spec: dict, op: dict) -> tuple[list[dict], set[str]]:
    """The rows (Sam's data) and examples (samples, `example: true`) as preview records with display ids."""
    key = spec['key']
    recs, examples = [], set()
    temps = {r['record_id']: f'row_{i + 1}' for i, r in enumerate(op.get('rows') or []) if r.get('record_id')}
    last: dict[str, str | None] = {}
    from .commands.position import key_between
    for label, rows in (('row', op.get('rows') or []), ('example', op.get('examples') or [])):
        for i, r in enumerate(rows):
            rid = temps.get(r.get('record_id')) if label == 'row' else None
            rid = rid or f'{label}_{i + 1}'
            props = {k: ([temps.get(x, x) for x in v] if isinstance(v, list) else v) for k, v in r['fields'].items()}
            ref = f'{key}/{r["collection"]}'
            last[ref] = key_between(last.get(ref), None)
            recs.append({'id': rid, 'collection': ref, 'properties': props, 'position': last[ref], 'version': 1})
            if label == 'example':
                examples.add(rid)
    return recs, examples


def app_preview(ld: Loaded, op: dict, app_id: str | None = None) -> tuple[dict, Loaded]:
    """A build card's `preview`: the new app as `GET /apps/{id}` would send it, on the workspace plus this app,
    its rows and its example rows (marked `example: true`), seq 0 (split.md §7 item 12)."""
    import dataclasses
    from .routes.read import app_detail
    spec = copy.deepcopy(op['spec'])
    app = dict(spec, id=app_id or spec['key'])
    recs, examples = _preview_records(spec, op)
    others = []
    for a in ld.apps:
        if a['key'] == spec['key']:
            continue
        a = dict(a)
        extra = [x['stitch'] for x in op.get('stitches_into') or [] if x['app'] == a['key']]
        if extra:
            a['stitches'] = list(a.get('stitches') or []) + extra
        others.append(a)
    ld2 = dataclasses.replace(ld, apps=others + [app], records=list(ld.records) + recs, _ctx=None, seq=0)
    detail = app_detail(ld2, app).model_dump(mode='json', by_alias=True, exclude_none=True)
    detail['seq'] = 0
    # Faces as the app will read after Make it: Sam's rows count, sample rows don't (the instruments above
    # do show them, so the preview isn't empty).
    ld_saved = dataclasses.replace(ld2, records=[r for r in ld2.records if r['id'] not in examples], _ctx=None)
    detail['faces'] = ws_faces(ld_saved, [spec['key']])
    for rows in detail['data'].values():
        for r in rows:
            if r.get('id') in examples:
                r['example'] = True
    return detail, ld_saved


def app_card(conn, ld: Loaded, row: dict, model: Model) -> dict:
    """A `ChangeSet` of kind `app`. A create carries `preview` (AppDetail) and **Make it**; `ops` and `expanded`
    list the rows the app is made with as inserts (the app itself has no RowOp shape; split.md §7 item 12)."""
    stored = row.get('ops') or []
    ops = stored
    if row['status'] == 'basted':
        try:
            ops = normalize_ops(model, [{k: v for k, v in o.items() if k != 'app_id'} if o['op'] == 'create_app'
                                        else o for o in stored])
        except CommandError:
            ops = stored          # no longer valid on current data: confirm will 409; show what was proposed
    today = ld.now.date()
    lines, targets, row_ops, deltas = [], [], [], []
    preview = None
    primary = 'Make it'
    title = row.get('title')
    for o in ops:
        if o['op'] == 'create_app':
            spec = o['spec']
            key, name = spec['key'], spec.get('name') or spec['key']
            targets.append(key)
            what = 'new app · ' + _and([t.get('title') for t in spec.get('tabs') or []])
            if spec.get('private'):
                what += ' · private'
            lines.append({'apps': [key], 'what': what, 'val': ''})
            colls = {c['key']: c for c in spec.get('collections') or []}
            dated = []
            for r in o.get('rows') or []:
                c = colls.get(r['collection']) or {}
                row_ops.append({'op': 'insert', 'ref': f'{key}/{r["collection"]}', 'values': r['fields'],
                                **({'record_id': r['record_id']} if r.get('record_id') else {})})
                if c.get('calendar') and r['fields'].get(c.get('dateField')):
                    dated.append((c, r['fields']))
            if dated and ld.app('calendar') is not None:
                targets.append('calendar')
                if len(dated) == 1:
                    c, props = dated[0]
                    tf = c.get('titleField') or 'name'
                    when = _local_dt(props.get(c.get('dateField')), ld.tz)
                    day = F.day_label(when if isinstance(when, date) and not isinstance(when, datetime)
                                      else when.date(), today) if when is not None else ''
                    label = ' · '.join(x for x in (c.get('label'), str(props.get(tf) or '')) if x)
                    lines.append({'apps': ['calendar'], 'what': f'{label}, {day}' if day else label, 'val': ''})
                else:
                    lines.append({'apps': ['calendar'], 'what': f'{len(dated)} added', 'val': ''})
            for x in o.get('stitches_into') or []:
                t = ld.app(x['app']) or {}
                src = colls.get(str(x['stitch']['from']).partition('/')[2]) or {}
                targets.append(x['app'])
                lines.append({'apps': [x['app']], 'what': f'{name} {(src.get("name") or "rows").lower()} go to '
                                                          f'{t.get("name") or x["app"]}', 'val': ''})
            try:
                preview, ld2 = app_preview(ld, o, o.get('app_id') if row['status'] == 'stitched' else None)
                existing = [k for k in dict.fromkeys(targets) if k != key and ld.app(k) is not None]
                before = ws_faces(ld, existing)
                after = ws_faces(ld2, existing)
                for k in existing:
                    if k in before and k in after and before[k]['text'] != after[k]['text']:
                        deltas.append({'app': k, 'before': before[k]['text'], 'after': after[k]['text']})
                        lab = after[k].get('label') or ''
                        for ln in lines:
                            if ln['apps'] == [k]:
                                ln['sub'] = f'{before[k]["text"]} → {after[k]["text"]} {lab}'.rstrip()
            except Exception as e:      # keep the card standing; the preview is display only
                print(f'cards: app preview failed: {e!r}')
            title = title or f'Make a {name} app?'
        else:
            a = ld.app(str(o.get('app_id'))) or {}
            key = a.get('key') or str(o.get('app_id'))
            name = a.get('name') or (o.get('spec') or {}).get('name') or key
            targets.append(key)
            if o['op'] == 'update_app':
                lines.append({'apps': [key], 'what': 'app changed', 'val': ''})
                title, primary = title or f'Change {name}', 'Save'
            else:
                lines.append({'apps': [key], 'what': 'app deleted', 'val': ''})
                title, primary = title or f'Delete {name}', 'Delete'
    src = row.get('source') or {}
    return {
        'id': str(row['id']),
        'status': row['status'],
        'source': _source(row),
        'mode': 'fixture' if src.get('mode') == 'fixture' or src.get('fixture') else 'live',
        'title': title or 'New app',
        'summary': row.get('summary'),
        'ops': row_ops,
        'lines': lines,
        'expanded': list(row_ops),
        'targets': list(dict.fromkeys(targets)),
        'deltas': deltas,
        'actions': {'primary': primary},
        'flagged': False,
        'version': row['version'],
        'kind': 'app',
        'preview': preview,
    }
