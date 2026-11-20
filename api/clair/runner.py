"""Clair's agent loop for a turn (clair-agent.md §1, §9, §11 "manual loop", §14, §15).

`prepare_turn` does everything that can fail with an HTTP status before the stream opens (read level 403,
rate limit 429, thread 404, busy thread 409, credits 402) and charges the run's credit under the
workspace lock. `start()` then runs the loop in a worker thread, so the run (and its stored basted
change set) finishes even when the client drops the stream (§11 row 39); events go to the SSE queue and
to `agent_runs.events`.

The model sits behind `ModelClient`, so tests and the mock mode use a scripted client:
- `AnthropicClient`: claude-opus-5-5 through the Anthropic Python SDK (streaming, refusal fallback).
- `MockClient` (`CLAIR_MODEL=mock`, or no ANTHROPIC_API_KEY): scripts the tool calls the real model
  makes for the demo sentences; every proposal still goes through the real propose_changes path.

The loop is the spec's manual loop (§11 "Fallback"): it gives the control we need (stop at a refusal
before running tools, a wall clock between iterations, events per tool) and is easy to fake.

Pausing (§11): when an assistant message holds an `ask_user` tool_use, the loop runs the message's other
tool_use blocks, stores a `clair_questions` row (with their results), emits `question` and ends the
request with `done {status: awaiting_input}`. `POST /clair/turns {thread_id, answer}` (`_prepare_answer`)
claims the question with a conditional update, appends the pending tool_results and continues the SAME
agent run (same id, same credits; a build tops the run up to 10 once, §14).
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .. import db
from .. import workspace as wsp
from ..models import AnswerTurn
from ..routes.me import credits as credit_balance
from ..routes.me import month_start, server_now
from . import brief, prompt, snapshot, tools
from .events import Emitter

MODEL = 'claude-opus-5-5'
MAX_TOKENS = 16000
MAX_ITERATIONS = 8
WALL_CLOCK_S = 45.0
CHAT_CREDITS = 1
BUILD_CREDITS = 10
CHANGED_ANSWERS = 'Sam changed the answers: '
UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
RATE_PER_MINUTE = 10
STALE_RUN = timedelta(minutes=3)
FIXTURES = Path(__file__).parent / 'fixtures'
FIXTURE_NAMES = {'planner', 'receipt', 'fridge', 'lunch'}
FIXTURE_DELAY = float(os.environ.get('CLAIR_FIXTURE_DELAY', '0.3'))

PLANNING_RE = re.compile(r'\b(plan|schedule|reschedule|fit in|move\b.*\baround)\b', re.I)
PLANNING_WHAT = re.compile(r'\b(training|workouts?|runs?|lifts?|workout|running)\b', re.I)
PLANNING_WINDOW = re.compile(r'\b(next week|this week|tomorrow)\b', re.I)

PLAN_OFFER = {
    'kind': 'workflow', 'app': 'workout', 'prompt': 'Do this every Sunday at 7 pm?',
    'sentence': "Every Sunday at 7:00 pm, plan next week's training",
    'trigger': {'kind': 'schedule', 'rule': 'FREQ=WEEKLY;BYDAY=SU', 'at': '19:00'},
    'action': {'kind': 'ask_clair', 'text': 'Plan my training for next week'},
}

MESSAGES = {
    'refusal': "Clair can't help with that one.",
    'max_tokens': 'That was too much to read at once. Try fewer pages.',
    'timeout': 'Clair took too long to answer. Try again.',
    'api': "Clair couldn't answer just now. Try again.",
    'budget': "Clair couldn't finish that one. Try again.",
    'store': "Couldn't save the draft. Try again.",
    'fixture': 'This sample no longer matches your apps.',
}


class _Keys(BaseSettings):
    """ANTHROPIC_API_KEY and CLAIR_MODEL from the environment or api/.env (never logged)."""
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / '.env', extra='ignore')
    anthropic_api_key: str | None = None
    clair_model: str | None = None
    # One model per kind of turn (owner, Nov 20: keep spend low; Opus is one setting away)
    clair_model_chat: str = 'claude-haiku-5-5'     # typed notes and questions
    clair_model_plan: str = 'claude-sonnet-5-5'    # planning runs (§12.9)
    clair_model_build: str = 'claude-sonnet-5-5'   # building an app (§12.11)


def _keys() -> _Keys:
    return _Keys()


BUILD_RE = re.compile(r"\b(build|make|create|set up|start)\b.*\b(app|tracker|log)\b|\b(i want to|help me|let me)\s+(track|log|keep track of|count)\b", re.I)


def is_build(text: str) -> bool:
    """A request to make a new app (§7 rule 7); decides the build model up front."""
    return bool(BUILD_RE.search(text))


def is_planning(text: str) -> bool:
    return bool(PLANNING_RE.search(text) and PLANNING_WHAT.search(text) and PLANNING_WINDOW.search(text))


# ---------------------------------------------------------------- model clients

@dataclass
class ModelReply:
    content: list[dict]
    stop_reason: str | None
    model: str
    usage: dict = field(default_factory=dict)
    request_id: str | None = None
    fallback: bool = False


class ModelError(Exception):
    def __init__(self, kind: str, detail: str = ''):
        super().__init__(f'{kind}: {detail}')
        self.kind = kind


class ModelClient(Protocol):
    name: str

    def create(self, *, system: list[dict], tools: list[dict], messages: list[dict], effort: str,
               timeout: float, on_text: Callable[[str], None]) -> ModelReply: ...


class AnthropicClient:
    """One Claude model, streamed; text events go out as text_delta (§9)."""

    def __init__(self, api_key: str, model: str = MODEL):
        import anthropic
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=1)
        self.name = model
        # Haiku has no server-side refusal fallback; the others route a refusal to another model
        self._fallback = {} if 'haiku' in model else {'betas': ['server-side-fallback-2026-07-01'], 'fallbacks': 'default'}
        # Sonnet and Haiku allow at most 24 optional parameters across strict tool schemas (ours have ~47),
        # so only Opus gets `strict`; every input is still validated by Pydantic in tools.py and a bad one
        # goes back to the model as an is_error result (§10).
        self._strict = model.startswith(('claude-opus', 'claude-fable', 'claude-mythos'))

    def create(self, *, system, tools, messages, effort, timeout, on_text) -> ModelReply:
        a = self._anthropic
        if not self._strict:
            tools = [{k: v for k, v in t.items() if k != 'strict'} for t in tools]
        try:
            with self.client.beta.messages.stream(
                model=self.name, max_tokens=MAX_TOKENS, system=system, tools=tools, messages=messages,
                output_config={'effort': effort}, timeout=timeout, **self._fallback,
            ) as stream:
                for event in stream:
                    if event.type == 'text':
                        on_text(event.text)
                msg = stream.get_final_message()
        except a.APITimeoutError as e:
            raise ModelError('timeout', str(e)) from e
        except a.RateLimitError as e:
            raise ModelError('api', f'rate limited: {e}') from e
        except a.APIStatusError as e:
            raise ModelError('api', f'{e.status_code}: {e.message}') from e
        except a.APIConnectionError as e:
            raise ModelError('api', f'connection: {e}') from e
        u = msg.usage
        usage = {'input_tokens': getattr(u, 'input_tokens', 0) or 0, 'output_tokens': getattr(u, 'output_tokens', 0) or 0,
                 'cache_read': getattr(u, 'cache_read_input_tokens', 0) or 0,
                 'cache_write': getattr(u, 'cache_creation_input_tokens', 0) or 0}
        return ModelReply(content=[b.to_dict() for b in msg.content], stop_reason=msg.stop_reason, model=msg.model,
                          usage=usage, request_id=getattr(msg, '_request_id', None), fallback=msg.model != self.name)


_OVERRIDE: ModelClient | None = None


def set_model_client(client: ModelClient | None) -> None:
    """Tests: force a client (None restores the env choice)."""
    global _OVERRIDE
    _OVERRIDE = client


def model_client(kind: str = 'chat', model: str | None = None) -> ModelClient:
    """The client for a kind of turn ('chat' | 'plan' | 'build'), or for a named model (a resumed run keeps its model)."""
    if _OVERRIDE is not None:
        return _OVERRIDE
    k = _keys()
    choice = (os.environ.get('CLAIR_MODEL') or k.clair_model or '').strip().lower()
    key = os.environ.get('ANTHROPIC_API_KEY') or k.anthropic_api_key
    if choice == 'mock' or not key or model == 'mock':
        from .mock import MockClient
        return MockClient()
    if not (model and model.startswith('claude-')):
        model = {'plan': k.clair_model_plan, 'build': k.clair_model_build}.get(kind, k.clair_model_chat)
    return AnthropicClient(key, model)


# ---------------------------------------------------------------- a prepared turn

@dataclass
class Turn:
    ctx: tools.RunContext
    kind: str                         # 'model' | 'fixture'
    client: ModelClient | None = None
    messages: list[dict] = field(default_factory=list)
    new_messages: list[dict] = field(default_factory=list)
    effort: str = 'low'
    credits: int = 0
    fixture: str | None = None
    status_text: str = 'Reading your note…'
    thread: threading.Thread | None = None
    refundable: bool = True           # False on a resume: the run's credits were committed at awaiting_input (§14)
    base_iterations: int = 0          # a resume continues the run's counters
    base_tokens: tuple[int, int] = (0, 0)


def _http(status: int, error: str, **kw) -> HTTPException:
    return HTTPException(status, {'error': error, **kw})


def _workspace(conn, ws: UUID) -> dict:
    return conn.execute('select tz, read_level, settings from workspaces where id = %s', (ws,)).fetchone()


def _thread(conn, ws: UUID, user_id: UUID, thread_id: str | None) -> UUID:
    if thread_id:
        try:
            tid = UUID(thread_id)
        except ValueError:
            raise _http(404, 'not_found', what='thread')
        r = conn.execute('select id from clair_threads where id = %s and workspace_id = %s and user_id = %s',
                         (tid, ws, user_id)).fetchone()
        if r is None:
            raise _http(404, 'not_found', what='thread')
        conn.execute('update clair_threads set last_active_at = now() where id = %s', (tid,))
        return tid
    return conn.execute('insert into clair_threads (workspace_id, user_id) values (%s, %s) returning id',
                        (ws, user_id)).fetchone()['id']


def _run_id(raw: str | None) -> UUID:
    if not raw:
        return uuid.uuid4()
    try:
        return UUID(raw)
    except ValueError:
        raise _http(422, 'invalid', issues=[{'loc': ['body', 'run_id'], 'msg': 'not a UUID'}])


def _insert_run(conn, *, run_id, ws, user_id, thread_id, input_kind, model, effort, credits) -> None:
    # A resumed run keeps its old started_at, so "stale" also needs no transcript message in the window.
    conn.execute("update agent_runs r set status = 'error', error = 'stale', ended_at = now() "
                 "where thread_id = %s and status = 'running' and started_at < now() - %s and not exists "
                 "(select 1 from clair_messages m where m.run_id = r.id and m.created_at > now() - %s)",
                 (thread_id, STALE_RUN, STALE_RUN))
    if conn.execute('select 1 from agent_runs where id = %s', (run_id,)).fetchone():
        raise _http(409, 'run_exists')
    try:
        with conn.transaction():
            conn.execute('insert into agent_runs (id, workspace_id, user_id, thread_id, input_kind, model, effort, credits) '
                         'values (%s, %s, %s, %s, %s, %s, %s, %s)',
                         (run_id, ws, user_id, thread_id, input_kind, model, effort, credits))
    except psycopg.errors.UniqueViolation:
        raise _http(409, 'thread_busy')


def _history(conn, thread_id: UUID) -> list[dict]:
    """Earlier complete runs of the thread, unchanged (§5). Runs that errored are left out."""
    rows = conn.execute(
        "select m.role, m.content from clair_messages m join agent_runs r on r.id = m.run_id "
        "where m.thread_id = %s and r.status = 'complete' order by m.id", (thread_id,)).fetchall()
    return [{'role': r['role'], 'content': r['content']} for r in rows]


def _brief(ld: wsp.Loaded, text: str, read_level: str) -> brief.Brief:
    """The planning brief for a planning run (§12.9): the window the text names, else next week."""
    win = brief.planning_window(text, ld.now) or brief.planning_window('next week', ld.now)
    return brief.build_brief(ld, *win, read_level=read_level)


def prepare_turn(ws: UUID, user_id: UUID, body: dict) -> Turn:
    """Validate and charge; raises HTTPException with the contract's status codes."""
    if 'answer' in body:
        return _prepare_answer(ws, user_id, body)
    if 'fixture' in body:
        return _prepare_fixture(ws, user_id, body)

    text = (body.get('text') or body.get('transcript') or '').strip()
    voice = bool(body.get('voice'))
    if body.get('images') or body.get('files'):
        raise _http(413, 'attachments_not_ready')   # photos and files are D10 (backend.md §13)
    if not text:
        raise _http(422, 'invalid', issues=[{'loc': ['body', 'text'], 'msg': 'a turn needs text'}])
    if len(text) > 4000:
        raise _http(422, 'invalid', issues=[{'loc': ['body', 'text'], 'msg': 'at most 4000 characters'}])
    planning = is_planning(text)
    building = not planning and is_build(text)
    client = model_client('plan' if planning else 'build' if building else 'chat')
    effort = 'medium' if planning or building else 'low'
    run_id = _run_id(body.get('run_id'))

    with db.transaction(ws) as conn:
        w = _workspace(conn, ws)
        if w['read_level'] == 'none':
            raise _http(403, 'clair_off')
        n = conn.execute("select count(*) as n from agent_runs where user_id = %s and started_at > now() - interval '1 minute'",
                         (user_id,)).fetchone()['n']
        if n >= RATE_PER_MINUTE:
            raise _http(429, 'rate_limited')
        thread_id = _thread(conn, ws, user_id, body.get('thread_id'))
        now = server_now(w['tz'])
        bal = credit_balance(conn, ws, int((w['settings'] or {}).get('credits_monthly', 50)), now)
        if bal.left < CHAT_CREDITS:
            raise _http(402, 'no_credits')
        _insert_run(conn, run_id=run_id, ws=ws, user_id=user_id, thread_id=thread_id,
                    input_kind='voice' if voice else 'text', model=client.name, effort=effort, credits=CHAT_CREDITS)
        conn.execute("insert into usage_ledger (workspace_id, user_id, period, kind, credits, run_id) "
                     "values (%s, %s, %s, 'chat', %s, %s)", (ws, user_id, month_start(now), -CHAT_CREDITS, run_id))
        history = _history(conn, thread_id)
        notes = conn.execute('select text, kind from clair_notes where workspace_id = %s and deleted_at is null '
                             'order by created_at limit 50', (ws,)).fetchall()
        ld = wsp.load(conn, ws)

    b = _brief(ld, text, w['read_level']) if planning else None
    ctx = tools.RunContext(workspace_id=ws, user_id=user_id, tz=w['tz'], run_id=run_id, thread_id=thread_id,
                           read_level=w['read_level'], emitter=Emitter(run_id),
                           source_kind='voice' if voice else 'text', source_label='You said' if voice else 'You typed',
                           planning=planning, ld=ld, brief=b)
    snap, seen = snapshot.build(ld, w['read_level'], typed=text, spoken=voice, context=body.get('context'),
                                clair_notes=notes, brief=b)
    ctx.seen |= seen
    user_msg = {'role': 'user', 'content': [{'type': 'text', 'text': snap}, {'type': 'text', 'text': text}]}
    messages = list(history)
    if messages and messages[-1]['role'] == 'user':
        messages[-1] = {'role': 'user', 'content': list(messages[-1]['content']) + user_msg['content']}
    else:
        messages.append(user_msg)
    return Turn(ctx=ctx, kind='model', client=client, messages=messages, new_messages=[user_msg], effort=effort,
                credits=CHAT_CREDITS, status_text='Reading your week…' if planning else 'Reading your note…')


def _prepare_fixture(ws: UUID, user_id: UUID, body: dict) -> Turn:
    name = body.get('fixture')
    if name not in FIXTURE_NAMES:
        raise _http(422, 'invalid', issues=[{'loc': ['body', 'fixture'], 'msg': f'one of {sorted(FIXTURE_NAMES)}'}])
    if not (FIXTURES / f'{name}.json').exists():
        raise _http(404, 'not_found', what='fixture')
    run_id = _run_id(body.get('run_id'))
    with db.transaction(ws) as conn:
        w = _workspace(conn, ws)
        thread_id = _thread(conn, ws, user_id, None)
        _insert_run(conn, run_id=run_id, ws=ws, user_id=user_id, thread_id=thread_id, input_kind='fixture',
                    model='fixture', effort=None, credits=0)
        ld = wsp.load(conn, ws)
    ctx = tools.RunContext(workspace_id=ws, user_id=user_id, tz=w['tz'], run_id=run_id, thread_id=thread_id,
                           read_level=w['read_level'], emitter=Emitter(run_id), source_label='Sample run',
                           mode='fixture', ld=ld)
    return Turn(ctx=ctx, kind='fixture', fixture=name)


# ---------------------------------------------------------------- answering a question (§11)

def _merge_roles(messages: list[dict]) -> list[dict]:
    """Consecutive messages of one role become one (an empty final reply is not stored, §10)."""
    out: list[dict] = []
    for m in messages:
        if out and out[-1]['role'] == m['role']:
            out[-1] = {'role': m['role'], 'content': list(out[-1]['content']) + list(m['content'])}
        else:
            out.append({'role': m['role'], 'content': list(m['content'])})
    return out


def _said(msgs: list[dict]) -> str:
    for m in msgs:
        if m['role'] == 'user':
            texts = [b['text'] for b in m['content'] if b.get('type') == 'text' and not b['text'].startswith('<snapshot>')]
            if texts:
                return texts[-1]
    return ''


def _prepare_answer(ws: UUID, user_id: UUID, body: dict) -> Turn:
    """Claim the question (409 answered, 410 expired, 404 unknown) and continue its run."""
    try:
        req = AnswerTurn.model_validate(body)
    except ValidationError as e:
        raise _http(422, 'invalid', issues=[{'loc': ['body', *map(str, err['loc'])], 'msg': err['msg']} for err in e.errors()])
    a = req.answer
    try:
        qid, tid = UUID(a.question_id), UUID(req.thread_id)
    except ValueError:
        raise _http(404, 'not_found', what='question')
    client = model_client()
    expired = False
    with db.transaction(ws) as conn:
        w = _workspace(conn, ws)
        if w['read_level'] == 'none':
            raise _http(403, 'clair_off')
        q = conn.execute('select q.*, t.user_id as thread_user from clair_questions q join clair_threads t on t.id = q.thread_id '
                         'where q.id = %s and q.workspace_id = %s', (qid, ws)).fetchone()
        if q is None or q['thread_id'] != tid or q['thread_user'] != user_id:
            raise _http(404, 'not_found', what='question')
        try:
            result = tools.answer_result(q['options'], q['multi'], a.model_dump(exclude_none=True))
        except tools.AnswerError as e:
            raise _http(422, 'invalid', issues=[{'loc': ['body', 'answer'], 'msg': str(e)}])
        claimed = conn.execute("update clair_questions set status = 'answered', answer = %s, answered_at = now() "
                               "where id = %s and status = 'open' and expires_at > now() returning id",
                               (Jsonb(result), qid)).fetchone()
        change = False
        if claimed is None:
            cur = conn.execute('select status from clair_questions where id = %s for update', (qid,)).fetchone()
            if cur['status'] in ('open', 'expired'):
                conn.execute("update clair_questions set status = 'expired' where id = %s and status = 'open'", (qid,))
                expired = True
            else:
                # Change answers (§11): a card's answer again while the run's change set is still basted.
                run = conn.execute('select r.status, c.status as cs_status from agent_runs r left join change_sets c '
                                   'on c.id = r.change_set_id where r.id = %s', (q['run_id'],)).fetchone()
                if not isinstance(q['options'], dict) or run is None or run['status'] != 'complete' \
                        or run['cs_status'] != 'basted':
                    raise _http(409, 'question_answered')
                conn.execute('update clair_questions set answer = %s, answered_at = now() where id = %s', (Jsonb(result), qid))
                change = True
        if not expired:
            try:
                with conn.transaction():
                    run = conn.execute("update agent_runs set status = 'running', ended_at = null, error = null "
                                       "where id = %s and status = %s returning *",
                                       (q['run_id'], 'complete' if change else 'awaiting_input')).fetchone()
            except psycopg.errors.UniqueViolation:
                raise _http(409, 'thread_busy')
            if run is None:
                raise _http(409, 'question_answered')
            first = conn.execute('select min(id) as id from clair_messages where run_id = %s', (run['id'],)).fetchone()['id']
            prior = conn.execute(
                "select m.role, m.content from clair_messages m join agent_runs r on r.id = m.run_id "
                "where m.thread_id = %s and r.status = 'complete' and m.id < %s order by m.id",
                (tid, first or 0)).fetchall()
            own = conn.execute('select role, content from clair_messages where run_id = %s order by id', (run['id'],)).fetchall()
            n_asks = conn.execute('select count(*) as n from clair_questions where run_id = %s', (run['id'],)).fetchone()['n']
            ld = wsp.load(conn, ws)
    if expired:
        raise _http(410, 'question_expired')

    own = [{'role': m['role'], 'content': m['content']} for m in own]
    if change:
        new = {'role': 'user', 'content': [{'type': 'text', 'text': CHANGED_ANSWERS + json.dumps(result)}]}
    else:
        last = own[-1] if own else {'role': 'user', 'content': []}
        others = {r['tool_use_id']: r for r in q['other_results'] or []}
        content = []
        for b in last['content'] if last['role'] == 'assistant' else []:
            if b.get('type') != 'tool_use':
                continue
            if b['id'] == q['tool_use_id']:
                content.append({'type': 'tool_result', 'tool_use_id': b['id'], 'content': json.dumps(result)})
            else:
                content.append(others.get(b['id']) or {'type': 'tool_result', 'tool_use_id': b['id'], 'is_error': True,
                                                       'content': 'No result was kept for this call.'})
        if not any(r['tool_use_id'] == q['tool_use_id'] for r in content):
            content.append({'type': 'tool_result', 'tool_use_id': q['tool_use_id'], 'content': json.dumps(result)})
        new = {'role': 'user', 'content': content}

    said = _said(own)
    voice = run['input_kind'] == 'voice'
    planning = is_planning(said)
    ctx = tools.RunContext(workspace_id=ws, user_id=user_id, tz=w['tz'], run_id=run['id'], thread_id=tid,
                           read_level=w['read_level'], emitter=Emitter(run['id']),
                           source_kind='voice' if voice else 'text', source_label='You said' if voice else 'You typed',
                           planning=planning, ld=ld, brief=_brief(ld, said, w['read_level']) if planning else None,
                           change_set_id=run['change_set_id'], asks=n_asks,
                           plan_required=isinstance(q['options'], dict) and bool(q['options'].get('plan_after')))
    # "Seen this run" (§10): every record id the run's transcript showed (snapshot and read results).
    ids = {r['id'] for r in ld.records}
    ctx.seen |= set(UUID_RE.findall(json.dumps([m['content'] for m in own]))) & ids
    if run.get('model') and run['model'] != client.name:
        client = model_client(model=run['model'])   # a resumed run keeps the model that started it
    return Turn(ctx=ctx, kind='model', client=client, messages=_merge_roles(prior + own + [new]), new_messages=[new],
                effort=run['effort'] or 'low', credits=run['credits'] or 0, refundable=False,
                base_iterations=run['iterations'] or 0,
                base_tokens=(run['input_tokens'] or 0, run['output_tokens'] or 0),
                status_text='Planning with your answers…' if ctx.plan_required else 'Reading your answer…')


def _pause(turn: Turn, ask: dict, inp: tools.AskUser, uses: list[dict]) -> None:
    """Run the message's other tool_use blocks, store the question, emit it (§11 steps 2 and 3)."""
    ctx = turn.ctx
    other = []
    for b in uses:
        if b is ask:
            continue
        if b['name'] == 'ask_user':
            out, err = 'Ask one question at a time.', True
            tools.record_call(ctx, b['name'], b.get('input'), b['id'], out, err)
        else:
            out, err = tools.call(ctx, b['name'], b.get('input'), b.get('id', ''))
        r = {'type': 'tool_result', 'tool_use_id': b['id'], 'content': out}
        if err:
            r['is_error'] = True
        other.append(r)
    opts = tools.ask_options(inp)
    text = inp.question if inp.questions is None else ' / '.join(q.question for q in inp.questions)
    multi = bool(inp.multi_select) if inp.questions is None else False
    try:
        with db.connect() as conn:
            row = conn.execute(
                'insert into clair_questions (workspace_id, thread_id, run_id, tool_use_id, question, options, multi, '
                'other_results) values (%s, %s, %s, %s, %s, %s, %s, %s) returning id, expires_at',
                (ctx.workspace_id, ctx.thread_id, ctx.run_id, ask['id'], text, Jsonb(opts), multi, Jsonb(other))).fetchone()
            conn.commit()
    except Exception as e:
        raise tools.StoreError(f"Couldn't save the question: {e}") from e
    ctx.asks += 1
    ctx.plan_required = bool(inp.plan_after)
    tools.record_call(ctx, 'ask_user', ask.get('input'), ask['id'], json.dumps({'question_id': str(row['id'])}), False)
    ctx.emitter.emit('question', tools.question_event(str(row['id']), text, opts, multi, row['expires_at'].isoformat()))


# ---------------------------------------------------------------- running

def start(turn: Turn, background: bool = True) -> Turn:
    turn.ctx.emitter.emit('status', {'text': turn.status_text if turn.kind == 'model' else _fixture_status(turn)})
    target = run_fixture if turn.kind == 'fixture' else run_model
    if background:
        turn.thread = threading.Thread(target=target, args=(turn,), daemon=True, name=f'clair-{turn.ctx.run_id}')
        turn.thread.start()
    else:
        target(turn)
    return turn


def _save_message(ctx: tools.RunContext, msg: dict) -> None:
    with db.connect() as conn:
        conn.execute('insert into clair_messages (thread_id, workspace_id, run_id, role, content) values (%s, %s, %s, %s, %s)',
                     (ctx.thread_id, ctx.workspace_id, ctx.run_id, msg['role'], Jsonb(msg['content'])))
        conn.execute('update clair_threads set last_active_at = now() where id = %s', (ctx.thread_id,))
        conn.commit()


def _log_call(ctx, iteration: int, reply: ModelReply | None, latency_ms: int, model: str) -> None:
    try:
        u = reply.usage if reply else {}
        with db.connect() as conn:
            conn.execute(
                'insert into llm_calls (run_id, workspace_id, iteration, model, request_id, input_tokens, output_tokens, '
                'cache_read_tokens, cache_write_tokens, stop_reason, fallback, latency_ms) '
                'values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (ctx.run_id, ctx.workspace_id, iteration, reply.model if reply else model, reply and reply.request_id,
                 u.get('input_tokens'), u.get('output_tokens'), u.get('cache_read'), u.get('cache_write'),
                 reply and reply.stop_reason, bool(reply and reply.fallback), latency_ms))
            conn.commit()
    except Exception:
        pass


def _finish(turn: Turn, status: str, *, kind: str | None = None, error: str | None = None,
            iterations: int = 0, tokens: tuple[int, int] = (0, 0), stop_reason: str | None = None) -> None:
    ctx = turn.ctx
    message = MESSAGES.get(kind or '', MESSAGES['api']) if status == 'error' else None
    try:
        with db.transaction(ctx.workspace_id) as conn:
            credits = turn.credits
            if status == 'error' and turn.refundable:
                if turn.credits:
                    w = _workspace(conn, ctx.workspace_id)
                    conn.execute("insert into usage_ledger (workspace_id, user_id, period, kind, credits, run_id) "
                                 "values (%s, %s, %s, 'refund', %s, %s)",
                                 (ctx.workspace_id, ctx.user_id, month_start(server_now(w['tz'])), turn.credits, ctx.run_id))
                credits = 0
            elif status != 'error' and ctx.built and credits < BUILD_CREDITS:
                # A build costs 10 in place of the 1 (§14), once per run, however many times answers change.
                w = _workspace(conn, ctx.workspace_id)
                conn.execute("insert into usage_ledger (workspace_id, user_id, period, kind, credits, run_id) "
                             "values (%s, %s, %s, 'build', %s, %s)",
                             (ctx.workspace_id, ctx.user_id, month_start(server_now(w['tz'])),
                              -(BUILD_CREDITS - credits), ctx.run_id))
                credits = BUILD_CREDITS
            turn.credits = credits
            timings = dict(ctx.emitter.timings)
            timings['done'] = int((time.monotonic() - ctx.emitter.t0) * 1000)
            conn.execute(
                'update agent_runs set status = %s, iterations = %s, input_tokens = %s, output_tokens = %s, '
                'credits = %s, stop_reason = %s, timings = timings || %s, error = %s, ended_at = now(), '
                'change_set_id = coalesce(%s, change_set_id) where id = %s',
                (status, turn.base_iterations + iterations, turn.base_tokens[0] + tokens[0],
                 turn.base_tokens[1] + tokens[1], credits, stop_reason,
                 Jsonb(timings), error and error[:2000], ctx.change_set_id, ctx.run_id))
    except Exception as e:   # the stream must still end with done
        print(f'clair: could not finish run {ctx.run_id}: {e!r}')
    ctx.emitter.emit('done', {'status': status, 'sources': ctx.sources, **({'message': message} if message else {})})


CARD_TOOLS = ('propose_changes', 'propose_app')


def run_model(turn: Turn) -> None:
    ctx, client = turn.ctx, turn.client
    deadline = time.monotonic() + WALL_CLOCK_S
    iterations, tin, tout, stop = 0, 0, 0, None
    system = prompt.system_blocks()
    tool_defs = tools.definitions(strict=True)
    messages = turn.messages
    if hasattr(client, 'use_brief'):      # the mock planner takes its facts from the same brief (§12.9)
        client.use_brief(ctx.brief)
    try:
        for m in turn.new_messages:
            _save_message(ctx, m)
        while iterations < MAX_ITERATIONS:
            remaining = deadline - time.monotonic()
            if remaining <= 1:
                raise ModelError('timeout', 'wall clock')
            iterations += 1
            t0 = time.monotonic()
            try:
                reply = client.create(system=system, tools=tool_defs, messages=messages, effort=turn.effort,
                                      timeout=remaining, on_text=lambda t: t and ctx.emitter.emit('text_delta', {'text': t}))
            except ModelError:
                _log_call(ctx, turn.base_iterations + iterations, None, int((time.monotonic() - t0) * 1000), client.name)
                raise
            except Exception as e:
                _log_call(ctx, turn.base_iterations + iterations, None, int((time.monotonic() - t0) * 1000), client.name)
                raise ModelError('api', repr(e)) from e
            _log_call(ctx, turn.base_iterations + iterations, reply, int((time.monotonic() - t0) * 1000), client.name)
            tin += reply.usage.get('input_tokens', 0) or 0
            tout += reply.usage.get('output_tokens', 0) or 0
            stop = reply.stop_reason
            if reply.content:
                msg = {'role': 'assistant', 'content': reply.content}
                messages.append(msg)
                _save_message(ctx, msg)
            if stop in ('refusal', 'max_tokens'):
                return _finish(turn, 'error', kind=stop, error=stop, iterations=iterations, tokens=(tin, tout), stop_reason=stop)
            uses = [b for b in reply.content if b.get('type') == 'tool_use']
            if not uses:
                break
            ask = next((b for b in uses if b['name'] == 'ask_user'), None)
            ask_err = None
            if ask is not None:
                try:
                    inp = tools.check_ask(ctx, ask.get('input'))
                except tools.ToolError as e:
                    ask_err = str(e)
                else:
                    _pause(turn, ask, inp, uses)
                    return _finish(turn, 'awaiting_input', iterations=iterations, tokens=(tin, tout), stop_reason=stop)
            results, carded = [], False
            for b in uses:
                if b['name'] == 'ask_user':
                    out, is_err = (ask_err if b is ask else 'Ask one question at a time.'), True
                    tools.record_call(ctx, b['name'], b.get('input'), b.get('id', ''), out, is_err)
                else:
                    out, is_err = tools.call(ctx, b['name'], b.get('input'), b.get('id', ''))
                    carded |= b['name'] in CARD_TOOLS and not is_err
                r = {'type': 'tool_result', 'tool_use_id': b['id'], 'content': out}
                if is_err:
                    r['is_error'] = True
                results.append(r)
            msg = {'role': 'user', 'content': results}
            messages.append(msg)
            _save_message(ctx, msg)
            if carded:
                # Owner, Nov 20: the card is the answer. Stop here instead of a closing model call, so the
                # offer and done follow the proposal at once (about 6 to 18 s sooner). The saved transcript
                # ends on the tool results; the next turn's text joins that user message (_merge_roles).
                break
        else:
            if ctx.change_set_id is None:
                return _finish(turn, 'error', kind='budget', error='max_iterations', iterations=iterations,
                               tokens=(tin, tout), stop_reason=stop)
        _maybe_offer(ctx)
        _finish(turn, 'complete', iterations=iterations, tokens=(tin, tout), stop_reason=stop)
    except ModelError as e:
        _finish(turn, 'error', kind=e.kind, error=str(e), iterations=iterations, tokens=(tin, tout), stop_reason=stop)
    except tools.StoreError as e:
        _finish(turn, 'error', kind='store', error=str(e), iterations=iterations, tokens=(tin, tout), stop_reason=stop)
    except Exception as e:
        _finish(turn, 'error', kind='api', error=repr(e), iterations=iterations, tokens=(tin, tout), stop_reason=stop)


def _maybe_offer(ctx: tools.RunContext) -> None:
    """A planning run's card gets the Sunday rule offer when Workout has no such rule yet (§12.9 step 5)."""
    if not ctx.planning or ctx.change_set_id is None:
        return
    a = ctx.loaded().app('workout')
    if a is None or any(w.get('sentence') == PLAN_OFFER['sentence'] for w in a.get('workflows') or []):
        return
    ctx.emitter.emit('offer', PLAN_OFFER)


# ---------------------------------------------------------------- Use sample (fixtures)

class FixtureError(Exception):
    pass


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f'{name}.json').read_text())


def _fixture_status(turn: Turn) -> str:
    try:
        return load_fixture(turn.fixture).get('status') or 'Reading…'
    except Exception:
        return 'Reading…'


def resolve_fixture(fx: dict, ld: wsp.Loaded) -> tuple[dict, set[str]]:
    """Resolve `{ref, name}` record pointers and `{now}` to the current seed (backend.md §11 row 59)."""
    seen: set[str] = set()

    def find(p: dict) -> str:
        ref, name = p['ref'], tools._norm(p['name'])
        app_key, coll_key = ref.split('/', 1)
        a = ld.app(app_key)
        c = next((c for c in (a or {}).get('collections') or [] if c['key'] == coll_key), None)
        for r in ld.records:
            if r['collection'] == ref and tools._norm(tools._title_of(c, r['properties'])) == name:
                seen.add(r['id'])
                return r['id']
        raise FixtureError(f"no {ref} record named {p['name']!r}")

    def walk(v):
        if isinstance(v, dict):
            if set(v) == {'ref', 'name'}:
                return find(v)
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, str) and v == '{now}':
            return ld.now.isoformat()
        return v
    return walk(fx), seen


def run_fixture(turn: Turn) -> None:
    ctx = turn.ctx
    try:
        fx = load_fixture(turn.fixture)
        fx, seen = resolve_fixture(fx, ctx.loaded())
        ctx.seen |= seen
        for app in fx.get('sources') or []:
            ctx.source(app)
        time.sleep(FIXTURE_DELAY)
        if fx.get('understood'):
            tools.call(ctx, 'report_understanding', fx['understood'], 'fixture_understood')
        for s in fx.get('statuses') or []:
            time.sleep(FIXTURE_DELAY)
            ctx.emitter.emit('status', {'text': s})
        time.sleep(FIXTURE_DELAY)
        out, is_err = tools.call(ctx, 'propose_changes', fx['propose'], 'fixture_propose')
        if is_err:
            raise FixtureError(out)
        if fx.get('offer'):
            ctx.emitter.emit('offer', fx['offer'])
        _finish(turn, 'complete')
    except (FixtureError, KeyError, ValueError) as e:
        _finish(turn, 'error', kind='fixture', error=f'fixture: {e}')
    except tools.StoreError as e:
        _finish(turn, 'error', kind='store', error=str(e))
    except Exception as e:
        _finish(turn, 'error', kind='api', error=repr(e))
