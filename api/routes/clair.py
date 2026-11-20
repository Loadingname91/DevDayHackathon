"""Clair routes (backend.md §10 "/clair" rows; clair-agent.md §2). Operation ids match api/contract.py.

`POST /clair/turns` answers `text/event-stream`. Status codes that can be known before the stream opens
(403 Clair off, 404 thread, 409 thread busy, 402 credits, 410 question, 413 attachments, 429) are real
HTTP statuses; anything later arrives as `done {status: error, message}`.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from .. import db
from ..auth import Member, current_member
from ..clair import runner
from ..models import LatestThread, RunEvents

router = APIRouter(tags=['clair'])


@router.post('/clair/turns', operation_id='clair_turn', response_class=StreamingResponse,
             responses={200: {'content': {'text/event-stream': {'schema': {'type': 'string'}}},
                              'description': 'SSE stream of ClairEvent'}})
async def clair_turn(request: Request, m: Member = Depends(current_member)) -> Any:
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict):
        raise HTTPException(422, {'error': 'invalid', 'issues': [{'loc': ['body'], 'msg': 'a JSON object'}]})
    from starlette.concurrency import run_in_threadpool
    turn = await run_in_threadpool(runner.prepare_turn, m.workspace_id, m.user.id, body)
    runner.start(turn)
    return StreamingResponse(turn.ctx.emitter.stream(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                                      'X-Run-Id': str(turn.ctx.run_id), 'X-Thread-Id': str(turn.ctx.thread_id)})


@router.get('/clair/threads/latest', response_model=LatestThread, operation_id='clair_thread_latest',
            responses={204: {'description': 'No thread active within 24 h'}})
def clair_thread_latest(m: Member = Depends(current_member)) -> Any:
    with db.connect() as conn:
        t = conn.execute("select id, created_at, last_active_at from clair_threads where workspace_id = %s and user_id = %s "
                         "and last_active_at > now() - interval '24 hours' order by last_active_at desc limit 1",
                         (m.workspace_id, m.user.id)).fetchone()
        if t is None:
            return Response(status_code=204)
        runs = conn.execute('select id, change_set_id, started_at, ended_at from agent_runs where thread_id = %s '
                            'order by started_at', (t['id'],)).fetchall()
        msgs = conn.execute('select run_id, role, content, created_at from clair_messages where thread_id = %s order by id',
                            (t['id'],)).fetchall()
    out = []
    for r in runs:
        mine = [x for x in msgs if x['run_id'] == r['id']]
        said = next((b['text'] for x in mine if x['role'] == 'user' for b in reversed(x['content'])
                     if b.get('type') == 'text' and not b['text'].startswith('<snapshot>')), None)
        if said:
            out.append({'role': 'user', 'text': said, 'at': mine[0]['created_at']})
        reply = ''.join(b.get('text', '') for x in mine if x['role'] == 'assistant' for b in x['content']
                        if b.get('type') == 'text')
        if reply or r['change_set_id']:
            out.append({'role': 'clair', 'text': reply, 'at': r['ended_at'] or r['started_at'],
                        **({'change_set_id': str(r['change_set_id'])} if r['change_set_id'] else {})})
    return LatestThread.model_validate({'thread': {'id': str(t['id']), 'started_at': t['created_at'],
                                                   'last_at': t['last_active_at']}, 'messages': out})


@router.get('/clair/runs/{id}/events', response_model=RunEvents, operation_id='clair_run_events')
def clair_run_events(id: str, after: int = Query(-1, description='Index of the last event seen; -1 for all'),
                     m: Member = Depends(current_member)) -> Any:
    try:
        rid = UUID(id)
    except ValueError:
        raise HTTPException(404, {'error': 'not_found', 'what': 'run'})
    with db.connect() as conn:
        r = conn.execute('select status, events from agent_runs where id = %s and workspace_id = %s',
                         (rid, m.workspace_id)).fetchone()
    if r is None:
        raise HTTPException(404, {'error': 'not_found', 'what': 'run'})
    evs = r['events'] or []
    start = max(after + 1, 0)
    done = any(e.get('event') == 'done' for e in evs)
    return RunEvents.model_validate({'events': evs[start:], 'last': len(evs) - 1, 'done': done})
