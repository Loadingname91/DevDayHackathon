"""Record gestures and change-set routes (backend.md §5, §10), over the command service (api/commands).

Gestures (`/records…`) apply at once as one stitched `actor user` / `origin gesture` change set; the toast's
Undo is `POST /change-sets/{id}/undo`. Change sets are Clair's basted cards: listed and edited fully expanded
(api/cards.py), confirmed, undone, dismissed. Every write returns the command result
`{change_set_id, server_seq, blocks[], faces{}, warnings[]}`.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from .. import db
from ..auth import Member, current_member
from ..cards import expand_change_set, row_op_to_internal
from ..commands import CommandError, confirm, dismiss, load_model, run_gesture, undo, update_ops
from ..commands.service import _now
from ..contract import AUTH, E401, E404, E409, E409S, E422, R
from .. import models as m
from ..workspace import compute_faces, load, wire_blocks

router = APIRouter()

BLOCK_KEYS = ('id', 'block_type', 'parent_id', 'collection_id', 'position', 'properties', 'version', 'deleted_at')


@contextmanager
def _errors() -> Iterator[None]:
    try:
        yield
    except CommandError as e:
        raise HTTPException(e.status, detail=e.body) from e


def _uuid(s: str, what: str = 'record') -> UUID:
    try:
        return UUID(str(s))
    except ValueError:
        raise HTTPException(404, detail={'error': 'not_found', 'what': what})


def _num(v: Any) -> Any:
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


def _warning(w: dict) -> dict | None:
    if 'changed_since' in w:
        c = w['changed_since']
        return {'changed_since': {'block_id': str(c.get('block_id')), 'field': c.get('field') or '*',
                                  'now': c.get('now'), 'was': c.get('was')}}
    if 'superseded' in w:
        return {'superseded': w['superseded']}
    return None


def command_result(r: dict, change_set_id: str | None = None, ws: UUID | None = None) -> dict:
    """The service's result trimmed to the contract's CommandResult. With `ws`, a record block that carries links has its
    `_links` as `LinkRef`s, as `GET /apps/{id}` sends them (one query, only when there is a link to word)."""
    faces = {k: {kk: _num(vv) for kk, vv in f.items() if kk in ('text', 'label', 'value')}
             for k, f in (r.get('faces') or {}).items()}
    blocks = [{k: b.get(k) for k in BLOCK_KEYS} for b in r.get('blocks') or []]
    if ws is not None and any(b['block_type'] == 'record' and (b['properties'] or {}).get('_links') for b in blocks):
        with db.connect() as conn:
            blocks = wire_blocks(conn, ws, blocks)
    return {
        'change_set_id': change_set_id or r['change_set_id'],
        'server_seq': r['server_seq'],
        'blocks': blocks,
        'faces': faces,
        'warnings': [x for x in (_warning(w) for w in r.get('warnings') or []) if x],
    }


def _gesture(mem: Member, ops: list[dict]) -> dict:
    with _errors(), db.transaction(mem.workspace_id) as conn:
        r = run_gesture(conn, mem.workspace_id, mem.user.id, ops, compute_faces=compute_faces)
    return command_result(r, ws=mem.workspace_id)


# ---------------------------------------------------------------- records (gestures)

def _stamp_date(coll: dict, fields: dict, tz: str) -> dict:
    """Picks, the timer and guided sets send no time: stamp the collection's dateField with now (§10 "Writes
    the instruments make"). Not for calendar collections (To-dos' add field expects Someday), unless the row
    arrives done (Running's timer)."""
    props = coll.get('properties') or {}
    df = props.get('dateField')
    if not df or df in fields:
        return fields
    f = next((x for x in props.get('fields') or [] if x.get('key') == df), None)
    if f is None or f.get('type') not in ('datetime', 'date'):
        return fields
    if props.get('calendar') and fields.get('done') is not True:
        return fields
    now = _now(tz)
    return {**fields, df: now.date().isoformat() if f['type'] == 'date' else now.isoformat()}


@router.post('/records', status_code=201, response_model=m.CommandResult, operation_id='record_create',
             tags=['records'], responses=AUTH)
def record_create(body: m.RecordCreate, mem: Member = Depends(current_member)) -> Any:
    with _errors(), db.transaction(mem.workspace_id) as conn:
        model = load_model(conn, mem.workspace_id)
        coll = None
        try:
            coll = model.colls.get(UUID(body.collection_id))
        except ValueError:
            coll = model.colls_by_ref.get(body.collection_id)
        if coll is None:
            raise HTTPException(404, detail={'error': 'not_found', 'what': 'collection'})
        op = {'op': 'insert', 'collection_id': str(coll['id']), 'fields': _stamp_date(coll, body.fields, model.tz)}
        for k in ('before_id', 'after_id'):
            v = getattr(body, k)
            if v:
                op[k] = str(_uuid(v))
        r = run_gesture(conn, mem.workspace_id, mem.user.id, [op], compute_faces=compute_faces)
    return command_result(r, ws=mem.workspace_id)


@router.patch('/records/{id}', response_model=m.CommandResult, operation_id='record_update', tags=['records'],
              responses=AUTH)
def record_update(id: str, body: m.RecordUpdate, mem: Member = Depends(current_member)) -> Any:
    return _gesture(mem, [{'op': 'update', 'record_id': str(_uuid(id)), 'fields': body.fields,
                           'base_version': body.base_version}])


@router.post('/records/{id}/move', response_model=m.CommandResult, operation_id='record_move', tags=['records'],
             responses=AUTH)
def record_move(id: str, body: m.RecordMove, mem: Member = Depends(current_member)) -> Any:
    op: dict[str, Any] = {'op': 'move', 'record_id': str(_uuid(id))}
    for k in ('before_id', 'after_id'):
        v = getattr(body, k)
        if v:
            op[k] = str(_uuid(v))
    if body.list is not None:
        op['list'] = body.list
    return _gesture(mem, [op])


@router.post('/records/{id}/complete', response_model=m.CommandResult, operation_id='record_complete',
             tags=['records'], responses=AUTH)
def record_complete(id: str, body: m.RecordComplete | None = None, mem: Member = Depends(current_member)) -> Any:
    op: dict[str, Any] = {'op': 'complete', 'record_id': str(_uuid(id))}
    if body is not None and body.occurrence:
        op['occurrence'] = body.occurrence.isoformat()
    if body is not None and body.minutes is not None:
        op['minutes'] = body.minutes
    return _gesture(mem, [op])


@router.post('/records/{id}/skip', response_model=m.CommandResult, operation_id='record_skip', tags=['records'],
             responses=AUTH)
def record_skip(id: str, body: m.RecordSkip, mem: Member = Depends(current_member)) -> Any:
    return _gesture(mem, [{'op': 'skip', 'record_id': str(_uuid(id)), 'occurrence': body.occurrence.isoformat()}])


@router.delete('/records/{id}', response_model=m.CommandResult, operation_id='record_delete', tags=['records'],
               responses=R(E401, E404))
def record_delete(id: str, mem: Member = Depends(current_member)) -> Any:
    return _gesture(mem, [{'op': 'delete', 'record_id': str(_uuid(id))}])


# ---------------------------------------------------------------- change sets

def _row(conn, ws, cs_id: UUID) -> dict:
    r = conn.execute('select * from change_sets where id = %s and workspace_id = %s', (cs_id, ws)).fetchone()
    if r is None:
        raise HTTPException(404, detail={'error': 'not_found', 'what': 'change_set'})
    return r


@router.get('/change-sets', response_model=list[m.ChangeSet], operation_id='change_sets_list',
            tags=['change-sets'], responses=R(E401, E422))
def change_sets_list(status: m.ChangeSetStatus | None = Query(None), mem: Member = Depends(current_member)) -> Any:
    ws = mem.workspace_id
    with _errors(), db.connect() as conn:
        if status:
            rows = conn.execute('select * from change_sets where workspace_id = %s and status = %s '
                                'order by created_at desc, id limit 50', (ws, status)).fetchall()
        else:
            rows = conn.execute('select * from change_sets where workspace_id = %s '
                                'order by created_at desc, id limit 50', (ws,)).fetchall()
        if not rows:
            return []
        ld = load(conn, ws)
        model = load_model(conn, ws)
        return [expand_change_set(conn, ld, r, model) for r in rows]


@router.patch('/change-sets/{id}', response_model=m.ChangeSet, operation_id='change_set_update',
              tags=['change-sets'], responses=R(AUTH, E409))
def change_set_update(id: str, body: m.ChangeSetPatch, mem: Member = Depends(current_member)) -> Any:
    ws, cs_id = mem.workspace_id, _uuid(id, 'change_set')
    ops = [x for x in (row_op_to_internal(o.model_dump(mode='json', exclude_none=True)) for o in body.ops) if x]
    with _errors(), db.transaction(ws) as conn:
        _row(conn, ws, cs_id)
        update_ops(conn, ws, cs_id, ops, body.version)
        row = _row(conn, ws, cs_id)
        return expand_change_set(conn, load(conn, ws), row)


@router.post('/change-sets/{id}/confirm', response_model=m.CommandResult, operation_id='change_set_confirm',
             tags=['change-sets'], responses=R(AUTH, E409S))
def change_set_confirm(id: str, mem: Member = Depends(current_member)) -> Any:
    ws, cs_id = mem.workspace_id, _uuid(id, 'change_set')
    with _errors(), db.transaction(ws) as conn:
        r = confirm(conn, ws, cs_id, compute_faces=compute_faces)
    return command_result(r, ws=ws)


@router.post('/change-sets/{id}/undo', response_model=m.CommandResult, operation_id='change_set_undo',
             tags=['change-sets'], responses=R(AUTH, E409S))
def change_set_undo(id: str, mem: Member = Depends(current_member)) -> Any:
    ws, cs_id = mem.workspace_id, _uuid(id, 'change_set')
    with _errors(), db.transaction(ws) as conn:
        r = undo(conn, ws, cs_id, user_id=mem.user.id, compute_faces=compute_faces)
    # The id the client acts on next: the undone set (a Clair card is basted again under it).
    return command_result(r, change_set_id=str(cs_id), ws=ws)


@router.post('/change-sets/{id}/dismiss', status_code=204, response_class=Response, response_model=None,
             operation_id='change_set_dismiss', tags=['change-sets'], responses=R(E401, E404, E409S))
def change_set_dismiss(id: str, mem: Member = Depends(current_member)) -> Response:
    ws, cs_id = mem.workspace_id, _uuid(id, 'change_set')
    with _errors(), db.transaction(ws) as conn:
        dismiss(conn, ws, cs_id)
    return Response(status_code=204)
