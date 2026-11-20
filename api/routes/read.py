"""The read routes (backend.md §10, §7): `GET /apps`, `GET /apps/{id}`, `POST /apps/{id}/opened`,
`GET /home`, `GET /sync`.

Each request loads the workspace once (`api.workspace.load`) and computes faces, values, `*dated`
rows and Next up in memory (backend.md §6 "Where it runs"). `{id}` is the page block UUID or the
app key (the client routes by key, `/a/budget`).

`Patch.changed` ("Just changed", ui-tech-plan.md §2: change log entries since the app was last
opened) is measured in `server_seq`, not in time: the demo clock is pinned (DEMO_NOW) while event
rows carry real time, so a time comparison would be wrong in the demo. `POST /apps/{id}/opened`
stores the open time in `app_opens[page id]` (the contract) and the seq it was opened at in
`app_opens._seq[page id]`; an app is changed when a non-seed event touched it after that seq.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg.types.json import Jsonb

from .. import db
from .. import workspace as W
from ..auth import Member, current_member
from ..logic import fmt
from ..logic.clock import parse_value, to_local, week_start
from ..logic.dated import dated_rows, next_up
from ..models import (
    AppDetail, AppSpec, Block, BlockValue, ChangeSet, ChangeSetCard, Dated, Face, Home, Patch, Record, SyncResponse,
)

router = APIRouter(tags=['apps'])

SEQ_KEY = '_seq'        # app_opens._seq: {page id: server_seq at the last open}
NOT_CHANGES = ('seed',)  # change set origins that never mark an app changed


# ---------------------------------------------------------------- helpers

def _not_found(what: str = 'app') -> HTTPException:
    return HTTPException(404, {'error': 'not_found', 'what': what})


def _member_row(conn, m: Member) -> dict:
    r = conn.execute('select display_name, app_opens from workspace_members where workspace_id = %s and user_id = %s',
                     (m.workspace_id, m.user.id)).fetchone()
    return r or {'display_name': None, 'app_opens': {}}


def _app_or_404(ld: W.Loaded, id_or_key: str) -> dict:
    a = ld.app(id_or_key)
    if a is None:
        raise _not_found()
    return a


def _app_key_of_coll(ld: W.Loaded) -> dict[str, str]:
    """collection block id -> app key."""
    return {cid: ref.split('/', 1)[0] for ref, cid in ld.collection_ids.items()}


def _calendar_colls(ld: W.Loaded) -> set[str]:
    return {c['id'] for a in ld.apps for c in a.get('collections', []) if c.get('calendar')}


def _changed_since(conn, ld: W.Loaded, opens: dict) -> set[str]:
    """App keys touched by a non-seed event after the app was last opened (seq-based)."""
    rows = conn.execute(
        'select b.block_type, b.parent_id, b.collection_id, b.properties ->> \'key\' as key, max(e.server_seq) as s '
        'from events e join blocks b on b.id = e.block_id join change_sets cs on cs.id = e.change_set_id '
        'where e.workspace_id = %s and cs.origin <> all(%s) group by 1, 2, 3, 4',
        (ld.workspace_id, list(NOT_CHANGES))).fetchall()
    if not rows:
        return set()
    key_of_coll = _app_key_of_coll(ld)
    key_of_page = {v: k for k, v in ld.page_ids.items()}
    cal = _calendar_colls(ld)
    last: dict[str, int] = {}

    def bump(key: str | None, s: int):
        if key:
            last[key] = max(last.get(key, 0), s)

    for r in rows:
        s = r['s']
        if r['block_type'] == 'page':
            bump(r['key'], s)
        elif r['block_type'] == 'collection':
            bump(key_of_page.get(str(r['parent_id'])), s)
        else:
            cid = str(r['collection_id'])
            bump(key_of_coll.get(cid), s)
            if cid in cal:
                bump('calendar', s)
    seqs = opens.get(SEQ_KEY) or {}
    out = set()
    for key, s in last.items():
        pid = ld.page_ids.get(key)
        if pid and s > int(seqs.get(pid, 0) or 0):
            out.add(key)
    return out


def _patches(conn, ld: W.Loaded, opens: dict) -> list[Patch]:
    faces = W.faces(ld)
    pins = set(str(p) for p in (ld.settings.get('pins') or []))
    changed = _changed_since(conn, ld, opens)
    out = []
    for i, a in enumerate(ld.apps):
        opened = opens.get(a['id'])
        out.append((opened, i, Patch(
            id=a['id'], key=a['key'], name=a['name'], icon=a['icon'], dye=a['dye'], print=a.get('print'),
            face=Face(**faces.get(a['key'], {'text': '', 'label': ''})), changed=a['key'] in changed,
            lastOpened=opened, pinned=a['id'] in pins, isNew=True if opened is None else None)))
    # Most recently opened first; never-opened (just built) apps lead; ties keep page order.
    out.sort(key=lambda t: (t[0] is not None, -datetime.fromisoformat(t[0]).timestamp() if t[0] else 0, t[1]))
    return [p for _, _, p in out]


def _walk_blocks(tabs: Iterable[dict]) -> Iterable[dict]:
    for t in tabs or []:
        for b in t.get('children') or []:
            yield b


def _dated_for(ld: W.Loaded, app: dict) -> list[dict] | None:
    """`*dated` rows for the app's blocks that read it, or None when none does.

    A `days` block with a month view gets the six-week grid of the current month (backend.md §10
    "Rows, not values": Mon 26 Oct to Sun 6 Dec at DEMO_NOW); a week-only `days` block gets this week
    and next (the fixtures' Mon 16 to Sun 29 Nov); a `calendar` block its `window` (default week).
    """
    today = to_local(ld.now, ld.tz).date()
    lo = hi = None
    keys: set[str] | None = set()
    for b in _walk_blocks(app.get('tabs')):
        if b.get('source') != '*dated':
            continue
        if b.get('kind') == 'days':
            views = set(b.get('views') or []) | {b.get('view')}
            if 'month' in views:
                first = today.replace(day=1)
                blo = week_start(first)
                bhi = blo + timedelta(days=41)
            else:
                blo = week_start(today)
                bhi = blo + timedelta(days=13)
        elif b.get('window') == 'today':
            blo = bhi = today
        else:
            blo = week_start(today)
            bhi = blo + timedelta(days=6)
        lo = blo if lo is None else min(lo, blo)
        hi = bhi if hi is None else max(hi, bhi)
        if keys is not None:
            if b.get('apps'):
                keys |= set(b['apps'])
            else:
                keys = None
    if lo is None:
        return None
    return dated_rows(ld.apps, ld.records, lo, hi, ld.tz, app_keys=keys)


def _spec(app: dict) -> AppSpec:
    spec = dict(app)
    return AppSpec.model_validate(spec)


def app_detail(ld: W.Loaded, app: dict) -> AppDetail:
    data: dict[str, list] = {}
    by_ref: dict[str, list] = {f"{app['key']}/{c['key']}": [] for c in app.get('collections', [])}
    for r in ld.records:
        lst = by_ref.get(r['collection'])
        if lst is not None:
            lst.append(Record(id=r['id'], position=r['position'], version=r['version'], properties=r['properties']))
    data.update(by_ref)
    dated = _dated_for(ld, app)
    if dated is not None:
        data['*dated'] = [Dated(**row) for row in dated]
    face = W.faces(ld, [app['key']])
    return AppDetail(
        spec=_spec(app), data=data, faces={k: Face(**v) for k, v in face.items()},
        values={k: BlockValue(**v) for k, v in (W.values(ld, app) or {}).items()},
        status=W.status(ld, app), seq=ld.seq, server_now=ld.now)


def _change_set(conn, ld: W.Loaded, row: dict) -> ChangeSet:
    """Expand a stored change set into the card shape. api.cards does the full job when it exists."""
    try:
        from .. import cards  # type: ignore[attr-defined]
        expand = getattr(cards, 'expand_change_set', None)
    except ImportError:
        expand = None
    if expand is not None:
        cs = expand(conn, ld, row)
        return cs if isinstance(cs, ChangeSet) else ChangeSet.model_validate(cs)
    src = row.get('source') or {}
    kind = src.get('kind') or row.get('origin') or 'seed'
    if kind == 'clair':
        kind = 'text'
    if kind not in ChangeSet.model_fields['source'].annotation.model_fields['kind'].annotation.__args__:
        kind = 'seed'
    at = src.get('at') or row['created_at'].isoformat()
    ops = _row_ops(ld, row.get('ops') or [])
    return ChangeSet.model_validate({
        'id': str(row['id']), 'status': row['status'],
        'source': {'kind': kind, 'label': src.get('label') or row.get('title') or '', 'at': at},
        'mode': src.get('mode', 'live'), 'title': row.get('title') or '', 'summary': row.get('summary'),
        'ops': ops, 'lines': [], 'expanded': ops, 'targets': [], 'deltas': [],
        'actions': {'primary': 'Add', 'secondary': 'Review items'}, 'flagged': False,
        'version': row.get('version') or 1,
    })


_REASONS = ('reason', 'reason_source', 'also', 'also_source')


def _row_ops(ld: W.Loaded, stored: list[dict]) -> list[dict]:
    """Stored command-service ops (api/commands/ops.py `Op`) -> the wire `RowOp` shapes, best effort.
    An op that doesn't map (complete, skip, move, restore) is left out of the fallback card."""
    ref_of_cid = {cid: ref for ref, cid in ld.collection_ids.items()}
    out = []
    for o in stored:
        kind = o.get('op', 'update')
        extra = {k: o[k] for k in _REASONS if o.get(k)}
        fields = o.get('fields') or {}
        if isinstance(fields, list):
            fields = {f['key']: f.get('value') for f in fields}
        if kind == 'keep' or o.get('keep'):
            if o.get('record_id') and o.get('occurrence'):
                out.append({'op': 'keep', 'record_id': o['record_id'], 'occurrence': o['occurrence'], **extra})
        elif kind == 'insert':
            ref = (f"{o['app']}/{o['collection']}" if o.get('app') and o.get('collection')
                   else ref_of_cid.get(str(o.get('collection_id'))))
            if ref:
                out.append({'op': 'insert', 'ref': ref, 'values': fields, **extra,
                            **({'record_id': o['record_id']} if o.get('record_id') else {})})
        elif kind in ('update', 'delete') and o.get('record_id'):
            out.append({'op': kind, 'rowId': o['record_id'], **({'values': fields} if kind == 'update' else {}),
                        **extra})
        elif kind == 'move_occurrence' and o.get('record_id') and o.get('occurrence'):
            out.append({'op': kind, 'app': o.get('app'), 'collection': o.get('collection'), 'record_id': o['record_id'],
                        'occurrence': o['occurrence'],
                        'fields': [{'key': k, 'value': str(v)} for k, v in fields.items()], **extra})
    return out


def _status_line(ld: W.Loaded, nxt: list[dict]) -> str:
    """FR-H2: money left this month and the next dated thing (backend.md §10 `GET /home`)."""
    parts = []
    for a in ld.apps:
        f = a.get('face') or {}
        if f.get('status') and f.get('format') == 'money':
            face = W.faces(ld, [a['key']]).get(a['key'])
            if face and 'value' in face:
                parts.append(f"**{face['text']}** {face['label']} this month.")
            break
    if nxt:
        row = nxt[0]
        at = parse_value(row['at'], ld.tz)
        today = to_local(ld.now, ld.tz).date()
        title = row['title']
        if isinstance(at, datetime):
            lt = to_local(at, ld.tz)
            when = f"at **{fmt.time_label(lt, short=True)}**"
            d = lt.date()
        else:
            when, d = '', at
        if d == today:
            day = '' if when else 'today'
        elif d == today + timedelta(days=1):
            day = 'tomorrow'
        else:
            day = f"on {d.strftime('%a')}"
        parts.append(' '.join(x for x in (title, day, when) if x) + '.')
    return ' '.join(parts) or 'Nothing logged yet. Add a receipt or tell Clair something.'


def _greeting(ld: W.Loaded, name: str | None) -> str:
    h = to_local(ld.now, ld.tz).hour
    band = 'Morning' if h < 12 else 'Afternoon' if h < 17 else 'Evening'
    return f'{band}, {name}.' if name else f'{band}.'


# ---------------------------------------------------------------- routes

@router.get('/apps', response_model=list[Patch], operation_id='apps_list')
def apps_list(m: Member = Depends(current_member)) -> list[Patch]:
    with db.connect() as conn:
        ld = W.load(conn, m.workspace_id)
        return _patches(conn, ld, _member_row(conn, m)['app_opens'] or {})


@router.get('/apps/{id}', response_model=AppDetail, response_model_exclude_none=True, operation_id='app_get')
def app_get(id: str, m: Member = Depends(current_member)) -> AppDetail:
    with db.connect() as conn:
        ld = W.load(conn, m.workspace_id)
    return app_detail(ld, _app_or_404(ld, id))


@router.post('/apps/{id}/opened', status_code=204, response_class=Response, response_model=None,
             operation_id='app_opened')
def app_opened(id: str, m: Member = Depends(current_member)) -> Response:
    """Not a change set: no undo, no event (backend.md §10). Time is the server clock (DEMO_NOW when pinned)."""
    from .me import server_now
    with db.connect() as conn:
        row = conn.execute(
            "select p.id, (select coalesce(max(server_seq), 0) from events where workspace_id = %(ws)s) as seq "
            "from blocks p where p.workspace_id = %(ws)s and p.block_type = 'page' and p.deleted_at is null "
            "and (p.id::text = %(id)s or p.properties ->> 'key' = %(id)s) limit 1",
            {'ws': m.workspace_id, 'id': id}).fetchone()
        if row is None:
            raise _not_found()
        pid = str(row['id'])
        conn.execute(
            "update workspace_members set app_opens = app_opens || jsonb_build_object(%(pid)s::text, %(at)s::text, "
            "%(sk)s::text, coalesce(app_opens -> %(sk)s::text, '{}'::jsonb) || jsonb_build_object(%(pid)s::text, %(seq)s::bigint)) "
            "where workspace_id = %(ws)s and user_id = %(uid)s",
            {'pid': pid, 'at': server_now(m.tz).isoformat(), 'sk': SEQ_KEY, 'seq': row['seq'],
             'ws': m.workspace_id, 'uid': m.user.id})
    return Response(status_code=204)


@router.get('/home', response_model=Home, operation_id='home_get', tags=['home'])
def home_get(m: Member = Depends(current_member)) -> Home:
    with db.connect() as conn:
        ld = W.load(conn, m.workspace_id)
        mem = _member_row(conn, m)
        patches = _patches(conn, ld, mem['app_opens'] or {})
        basted = conn.execute("select * from change_sets where workspace_id = %s and status = 'basted' "
                              'order by created_at desc', (m.workspace_id,)).fetchall()
        cards = [ChangeSetCard(kind='change_set', change_set=_change_set(conn, ld, r)) for r in basted]
    nxt = next_up(ld.apps, ld.records, ld.now, ld.tz)
    return Home(greeting=_greeting(ld, mem['display_name']), status=_status_line(ld, nxt), needsOk=cards,
                nextUp=[Dated(**r) for r in nxt], apps=patches, seq=ld.seq, server_now=ld.now)


def _block(r: dict) -> Block:
    return Block(id=str(r['id']), block_type=r['block_type'],
                 parent_id=str(r['parent_id']) if r['parent_id'] else None,
                 collection_id=str(r['collection_id']) if r['collection_id'] else None,
                 position=r['position'], version=r['version'], properties=r['properties'],
                 deleted_at=r['deleted_at'])


@router.get('/sync', response_model=SyncResponse, operation_id='sync', tags=['sync'])
def sync(since: int = Query(0, ge=0), m: Member = Depends(current_member)) -> SyncResponse:
    """backend.md §7. `since=0` is a full load: every live block and every change set with a status event."""
    from .me import server_now
    ws = m.workspace_id
    with db.connect() as conn:
        head = conn.execute('select w.epoch, (select coalesce(max(server_seq), 0) from events where workspace_id = w.id) '
                            'as seq from workspaces w where w.id = %s', (ws,)).fetchone()
        if since >= head['seq']:   # nothing new: answer without loading the workspace (the poll path)
            return SyncResponse(seq=head['seq'], epoch=head['epoch'], server_now=server_now(m.tz), blocks=[],
                                change_sets=[], faces={}, touched_apps=[])
        cols = 'b.id, b.block_type, b.parent_id, b.collection_id, b.position, b.version, b.properties, b.deleted_at'
        if since == 0:
            rows = conn.execute(f'select {cols} from blocks b where b.workspace_id = %s and b.deleted_at is null '
                                'order by b.position', (ws,)).fetchall()
        else:
            rows = conn.execute(
                f'select {cols} from blocks b where b.workspace_id = %s and b.id in '
                '(select distinct block_id from events where workspace_id = %s and server_seq > %s '
                'and block_id is not null) order by b.position', (ws, ws, since)).fetchall()
        cs_rows = conn.execute(
            'select * from change_sets where workspace_id = %s and id in (select distinct change_set_id from events '
            'where workspace_id = %s and server_seq > %s and block_id is null) order by created_at',
            (ws, ws, since)).fetchall()
        # app keys of every touched block, deleted pages and collections included
        ids = [r['id'] for r in rows]
        keymap = {r['id']: r for r in conn.execute(
            "select b.id, case when b.block_type = 'page' then b.properties ->> 'key' "
            "when b.block_type = 'collection' then p.properties ->> 'key' else cp.properties ->> 'key' end as app, "
            "coalesce((c.properties ->> 'calendar')::boolean, false) as cal "
            'from blocks b left join blocks p on p.id = b.parent_id left join blocks c on c.id = b.collection_id '
            'left join blocks cp on cp.id = c.parent_id where b.workspace_id = %s and b.id = any(%s)',
            (ws, ids)).fetchall()} if ids else {}
        ld = W.load(conn, ws)
        change_sets = [_change_set(conn, ld, r) for r in cs_rows]
    touched: list[str] = []
    for r in rows:
        k = keymap.get(r['id'], {})
        for key in (k.get('app'), 'calendar' if k.get('cal') else None):
            if key and key not in touched:
                touched.append(key)
    if since == 0:
        touched = [a['key'] for a in ld.apps]
    faces = W.faces(ld, [k for k in touched if ld.app(k) is not None])
    return SyncResponse(seq=ld.seq, epoch=ld.epoch, server_now=ld.now, blocks=[_block(r) for r in rows],
                        change_sets=change_sets, faces={k: Face(**v) for k, v in faces.items()}, touched_apps=touched)
