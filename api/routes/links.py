"""Search and links (backend.md section 10: `GET /search`, `POST /records/{id}/links`, `DELETE /records/{id}/links/{target_id}`).

Search is scoped to the caller's workspace on every query, never reaches a private app, leaves out deleted rows and apps, and
passes `q` to Postgres only as a bound parameter, with the LIKE wildcards in it escaped. The two link routes go through the
command service: one gesture change set (`actor user`, `origin gesture`), applied at once, with an Undo like any other edit.
The pure parts (ranking, snippets, interleaving) are api/logic/links.py; the storage note is api/commands/links.py.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import db
from .. import models as m
from ..auth import Member, current_member
from ..commands import load_model, run
from ..contract import AUTH, E401, R
from ..logic import links as L
from ..logic.clock import now as clock_now
from ..logic.clock import to_local
from ..settings import settings
from ..workspace import compute_faces, lookup_records
from .write import _errors, _uuid, command_result

router = APIRouter()

CANDIDATE_CAP = 1000       # rows read before ranking (a workspace holds a few hundred)
MAX_EXCLUDE = 50


# ---------------------------------------------------------------- search

def _eligible(model, app: str | None) -> dict[UUID, dict]:
    """The collections a search may read: live, in an app that is not private (and is `app`, when given), whose records have a
    title of their own. `{collection id: {app, ref, key, coll, app_idx, coll_idx, select_title}}`."""
    out: dict[UUID, dict] = {}
    for ai, page in enumerate(sorted(model.pages.values(), key=lambda p: p['position'])):
        pk = page['properties'].get('key')
        if L.is_private(page['properties']) or (app and pk != app):
            continue
        colls = sorted((c for c in model.colls.values() if c['parent_id'] == page['id']), key=lambda c: c['position'])
        for ci, c in enumerate(colls):
            if not L.titled(c['properties']):
                continue
            tf = L.title_field(c['properties']) or {}
            out[c['id']] = {'app': pk, 'ref': f"{pk}/{c['properties'].get('key')}", 'key': c['properties'].get('key'),
                            'coll': c['properties'], 'app_idx': ai, 'coll_idx': ci, 'select_title': tf.get('type') == 'select'}
    return out


@router.get('/search', response_model=m.SearchResponse, operation_id='search', tags=['search'], responses=R(E401))
def search(q: str = Query(''), app: str | None = Query(None), exclude: list[str] | None = Query(None),
           limit: int = Query(L.SEARCH_DEFAULT, ge=1, le=L.SEARCH_MAX), mem: Member = Depends(current_member)) -> Any:
    """Records of every app by title (and by their text), case-insensitive: prefix matches first, then word starts, then the rest.
    An empty `q` is "Suggested": the most recent records, taken in turn from each app, so one app never fills the list."""
    q = L.clean_query(q)
    ws = mem.workspace_id
    skip: list[UUID] = []
    for x in [p for e in (exclude or []) for p in str(e).split(',')][:MAX_EXCLUDE]:
        try:
            skip.append(UUID(x.strip()))
        except ValueError:
            continue                      # an id that is no record's can't be one to leave out
    with db.connect() as conn:
        model = load_model(conn, ws)
        metas = _eligible(model, app)
        if not metas:
            return {'hits': []}
        params: dict[str, Any] = {'ws': ws, 'cids': list(metas), 'cap': CANDIDATE_CAP}
        sql = ("select b.id, b.collection_id, b.position, b.properties, b.updated_at from blocks b "
               "where b.workspace_id = %(ws)s and b.block_type = 'record' and b.deleted_at is null "
               "and b.collection_id = any(%(cids)s)")
        if skip:
            sql += ' and not (b.id = any(%(skip)s))'
            params['skip'] = skip
        if q:
            # titles and every other text field; a title that is a select is matched on its label, below
            sel = [c for c, mt in metas.items() if mt['select_title']]
            params['pat'] = L.like_pattern(q)
            sql += (" and (exists (select 1 from blocks c, jsonb_array_elements(c.properties -> 'fields') f "
                    "where c.id = b.collection_id and f ->> 'type' = 'text' "
                    "and (b.properties ->> (f ->> 'key')) ilike %(pat)s escape '\\')")
            if sel:
                sql += ' or b.collection_id = any(%(sel)s)'
                params['sel'] = sel
            sql += ')'
        sql += ' order by b.updated_at desc, b.position, b.id limit %(cap)s'
        rows = conn.execute(sql, params).fetchall()

    now = clock_now(mem.tz, settings().demo_now)
    today = to_local(now, mem.tz).date()
    found: list[dict] = []
    for r in rows:
        mt = metas[r['collection_id']]
        coll, props = mt['coll'], r['properties']
        title = L.title_text(coll, props)
        if not title:
            continue
        rk = L.rank(title, q)
        body = None
        if rk is None:           # matched in another text field of the row
            tkey = coll.get('titleField')
            body = next((t for k, t in L.text_values(coll, props) if k != tkey and L.norm(q) in L.norm(t)), None)
            if body is None and mt['select_title']:
                continue         # a select title that does not match, read in because its label can't be matched in SQL
            rk = 3
        found.append({'id': str(r['id']), 'app': mt['app'], 'ref': mt['ref'], 'coll_key': mt['key'], 'coll': coll,
                      'props': props, 'title': title, 'rank': rk, 'body': body, 'position': r['position'],
                      'app_idx': mt['app_idx'], 'coll_idx': mt['coll_idx'], 'updated_at': r['updated_at']})
    if q:
        found.sort(key=lambda x: (x['rank'], x['app_idx'], x['coll_idx'], x['position'], x['id']))
        picked = found[:limit]
    else:
        found.sort(key=lambda x: L.recency_key(x, now, mem.tz))
        picked = L.interleave(found, limit)
    return {'hits': [
        {'app': x['app'], 'ref': x['ref'], 'collection': x['coll_key'], 'id': x['id'], 'title': x['title'],
         'snippet': L.excerpt(x['body'], q) if x['body'] else L.snippet(x['coll'], x['props'], mem.tz, today),
         'updated': x['updated_at']} for x in picked]}


# ---------------------------------------------------------------- links

def _link(mem: Member, source: str, target: str, op: str, ref: str | None = None) -> dict:
    """Run one `link` or `unlink` as a gesture change set. `source` and `target` are record ids."""
    ws = mem.workspace_id
    sid, tid = _uuid(source), _uuid(target, 'target')
    with _errors(), db.transaction(ws) as conn:
        info = lookup_records(conn, ws, [sid, tid])
        if ref and str(tid) in info and info[str(tid)]['ref'] != ref:
            raise HTTPException(422, {'error': 'invalid', 'issues': [
                {'loc': ['to', 'ref'], 'msg': f"{target} is in {info[str(tid)]['ref']}, not {ref}"}]})
        names = [(info.get(str(i)) or {}).get('title') for i in (sid, tid)]
        title = ((f'Linked {names[0]} to {names[1]}' if op == 'link' else f'Unlinked {names[0]} from {names[1]}')
                 if all(names) else ('Link' if op == 'link' else 'Unlink'))
        r = run(conn, ws, [{'op': op, 'record_id': str(sid), 'target_id': str(tid)}], actor='user', origin='gesture',
                user_id=mem.user.id, title=title, compute_faces=compute_faces)
    return command_result(r, ws=ws)


@router.post('/records/{id}/links', response_model=m.CommandResult, operation_id='record_link', tags=['records'],
             responses=AUTH)
def record_link(id: str, body: m.LinkCreate, mem: Member = Depends(current_member)) -> Any:
    """Link a record to any record in any app: `{to: {ref, id}}` or `{target_id}`. Applied at once as a gesture with an Undo.
    Already linked (by hand or by a `[[Title]]`): a change set with no events, which Undo does nothing for. 404 for a missing
    record or one in another workspace; 422 `self_link`, 422 `private_target`."""
    target = body.to.id if body.to else body.target_id
    if body.to is not None and body.target_id is not None and body.to.id != body.target_id:
        raise HTTPException(422, {'error': 'invalid', 'issues': [{'loc': ['target_id'], 'msg': 'to.id and target_id differ'}]})
    if not target:
        raise HTTPException(422, {'error': 'invalid', 'issues': [{'loc': ['to'], 'msg': 'name the record to link to: to.id or target_id'}]})
    return _link(mem, id, target, 'link', ref=body.to.ref if body.to else None)


@router.delete('/records/{id}/links/{target_id}', response_model=m.CommandResult, operation_id='record_unlink',
               tags=['records'], responses=AUTH)
def record_unlink(id: str, target_id: str, mem: Member = Depends(current_member)) -> Any:
    """Remove a link made by hand or by a `[[Title]]` (it comes back only when that text is saved with the `[[Title]]` still in
    it). Not linked: a change set with no events. A link to a deleted record can be removed too."""
    return _link(mem, id, target_id, 'unlink')
