"""Clair's loop for text turns (backend.md §13 T4; clair-agent.md §2, §9-§11, §14, §15).

Runs against the live database on the RECORDING account's workspace (settings().demo_record_workspace_id),
reset to the 'before' seed at the start and the end (the other agents use the main demo workspace).
The model is a scripted fake (or the mock client); no Anthropic call is made here.
"""
import json
import os
import sys
import threading
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402


def _ok() -> bool:
    try:
        from api.settings import settings
        return bool(settings().database_url and settings().demo_record_workspace_id)
    except Exception:
        return False


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _ok(), reason='no DATABASE_URL / recording workspace')]

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api import db  # noqa: E402
from api.auth import Member, User, current_member  # noqa: E402
from api.clair import runner  # noqa: E402
from api.clair.runner import ModelError, ModelReply  # noqa: E402
from api.routes import clair as clair_routes  # noqa: E402
from api.routes.me import credits, server_now  # noqa: E402
from api.seed.load import reset_workspace  # noqa: E402
from api.settings import settings  # noqa: E402

WS = UUID(settings().demo_record_workspace_id) if _ok() else None


@pytest.fixture(scope='module')
def member():
    with db.transaction(WS) as c:
        reset_workspace(c, WS, 'before')
        uid = c.execute('select user_id from workspace_members where workspace_id = %s order by created_at limit 1',
                        (WS,)).fetchone()['user_id']
        tz = c.execute('select tz from workspaces where id = %s', (WS,)).fetchone()['tz']
    yield Member(user=User(id=uid, is_anonymous=False, email='sam.record@quilt.demo'), workspace_id=WS, tz=tz)
    runner.set_model_client(None)
    with db.transaction(WS) as c:
        reset_workspace(c, WS, 'before')


@pytest.fixture
def client(member, monkeypatch):
    monkeypatch.setattr(runner, 'RATE_PER_MINUTE', 10_000)
    monkeypatch.setattr(runner, 'FIXTURE_DELAY', 0.0)
    app = FastAPI()

    @app.exception_handler(HTTPException)
    async def errors(_r, exc):
        return JSONResponse(exc.detail if isinstance(exc.detail, dict) else {'error': str(exc.detail)}, exc.status_code)

    app.include_router(clair_routes.router, prefix='/api')
    app.dependency_overrides[current_member] = lambda: member
    yield TestClient(app)
    runner.set_model_client(None)


def sse(text: str) -> list[tuple[str, dict]]:
    out = []
    for chunk in text.strip().split('\n\n'):
        ev = data = None
        for line in chunk.split('\n'):
            if line.startswith('event: '):
                ev = line[7:]
            elif line.startswith('data: '):
                data = json.loads(line[6:])
        if ev:
            out.append((ev, data))
    return out


def left(member) -> int:
    with db.connect() as c:
        return credits(c, WS, 50, server_now(member.tz)).left


class Script:
    """A fake model: returns the scripted replies in order; each may be a callable(messages) -> ModelReply."""
    name = 'fake'

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, *, system, tools, messages, effort, timeout, on_text):
        self.calls.append({'messages': [dict(m) for m in messages], 'effort': effort, 'tools': [t['name'] for t in tools]})
        r = self.replies.pop(0)
        r = r(messages) if callable(r) else r
        if isinstance(r, Exception):
            raise r
        for b in r.content:
            if b.get('type') == 'text':
                on_text(b['text'])
        return r


def use(i, name, inp):
    return {'type': 'tool_use', 'id': f'toolu_{i}', 'name': name, 'input': inp}


LUNCH_OPS = [{'op': 'insert', 'app': 'budget', 'collection': 'spend', 'fields': [
    {'key': 'note', 'value': 'Lunch'}, {'key': 'amount', 'value': '12.00'},
    {'key': 'category', 'value': 'Eating out'}, {'key': 'at', 'value': '2026-11-20T17:45:00-07:00'}]}]


def lunch_script():
    return Script(
        ModelReply(content=[
            use(1, 'report_understanding', {'kind': 'request', 'summary': 'A $12 lunch. That goes in Budget.', 'confidence': 1}),
            use(2, 'propose_changes', {'title': 'Lunch', 'summary': '$12.00 in Eating out.', 'ops': LUNCH_OPS}),
        ], stop_reason='tool_use', model='fake'),
        ModelReply(content=[], stop_reason='end_turn', model='fake'),
    )


def run_row(run_id):
    with db.connect() as c:
        return c.execute('select * from agent_runs where id = %s', (run_id,)).fetchone()


def check_lunch_card(cs, mode='live'):
    assert cs['status'] == 'basted' and cs['mode'] == mode
    assert cs['targets'] == ['budget']
    assert cs['deltas'] == [{'app': 'budget', 'before': '$412', 'after': '$400'}]
    assert cs['actions']['primary'] == 'Add to Budget'
    assert cs['ops'][0]['op'] == 'insert' and cs['ops'][0]['ref'] == 'budget/spend'
    assert cs['ops'][0]['values']['amount'] == 1200 and cs['ops'][0]['values']['category'] == 'c_eating_out'
    assert cs['lines'][0]['val'] == '$12.00' and 'Eating out' in cs['lines'][0]['what']


def test_lunch_turn(client, member):
    fake = lunch_script()
    runner.set_model_client(fake)
    before = left(member)
    r = client.post('/api/clair/turns', json={'text': 'spent $12 on lunch'})
    assert r.status_code == 200, r.text
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'understood', 'proposal', 'done']
    assert evs[1][1]['summary'].startswith('A $12 lunch')
    cs = evs[2][1]['change_set']
    check_lunch_card(cs)
    assert evs[3][1] == {'status': 'complete', 'sources': ['budget']}
    assert fake.calls[0]['effort'] == 'low'
    assert fake.calls[0]['messages'][-1]['content'][0]['text'].startswith('<snapshot>')
    run = run_row(UUID(r.headers['x-run-id']))
    assert run['status'] == 'complete' and run['model'] == 'fake' and run['credits'] == 1
    assert str(run['change_set_id']) == cs['id'] and len(run['events']) == 4 and run['iterations'] == 1   # no closing call after the card
    assert {'status', 'understood', 'proposal', 'done'} <= set(run['timings'])
    with db.connect() as c:
        row = c.execute('select status, origin, actor, source from change_sets where id = %s', (cs['id'],)).fetchone()
        n_msgs = c.execute('select count(*) as n from clair_messages where run_id = %s', (run['id'],)).fetchone()['n']
        n_tools = c.execute('select count(*) as n from tool_calls where run_id = %s', (run['id'],)).fetchone()['n']
    assert row['status'] == 'basted' and row['origin'] == 'clair' and row['source']['mode'] == 'live'
    assert n_msgs == 3 and n_tools == 2      # user, assistant (tools), user (results); empty final reply not stored
    assert left(member) == before - 1

    # polling fallback and latest thread
    p = client.get(f"/api/clair/runs/{run['id']}/events", params={'after': 1}).json()
    assert p['done'] and p['last'] == 3 and [e['event'] for e in p['events']] == ['proposal', 'done']
    t = client.get('/api/clair/threads/latest')
    assert t.status_code == 200 and t.json()['thread']['id'] == r.headers['x-thread-id']
    assert t.json()['messages'][-1]['change_set_id'] == cs['id']


def test_second_turn_on_busy_thread_is_409(client, member):
    gate = threading.Event()

    def slow(_messages):
        gate.wait(10)
        return ModelReply(content=[{'type': 'text', 'text': 'Done.'}], stop_reason='end_turn', model='fake')
    runner.set_model_client(Script(slow))
    turn = runner.start(runner.prepare_turn(WS, member.user.id, {'text': 'hello'}))
    with pytest.raises(HTTPException) as e:
        runner.prepare_turn(WS, member.user.id, {'text': 'again', 'thread_id': str(turn.ctx.thread_id)})
    assert e.value.status_code == 409 and e.value.detail['error'] == 'thread_busy'
    gate.set()
    turn.thread.join(10)
    assert run_row(turn.ctx.run_id)['status'] == 'complete'
    # once the first run is over, the same thread takes a new turn (and replays the history)
    fake = Script(ModelReply(content=[{'type': 'text', 'text': 'Hi.'}], stop_reason='end_turn', model='fake'))
    runner.set_model_client(fake)
    t2 = runner.start(runner.prepare_turn(WS, member.user.id, {'text': 'again', 'thread_id': str(turn.ctx.thread_id)}),
                      background=False)
    assert [e['event'] for e in t2.ctx.emitter.events] == ['status', 'text_delta', 'done']
    roles = [m['role'] for m in fake.calls[0]['messages']]
    assert roles == ['user', 'assistant', 'user']


def test_fixture_lunch_replays_through_pipeline(client, member):
    runner.set_model_client(Script())       # no model call may happen
    before = left(member)
    r = client.post('/api/clair/turns', json={'fixture': 'lunch'})
    assert r.status_code == 200, r.text
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'understood', 'proposal', 'done']
    check_lunch_card(evs[2][1]['change_set'], mode='fixture')
    assert evs[3][1]['status'] == 'complete'
    assert left(member) == before
    assert run_row(UUID(r.headers['x-run-id']))['model'] == 'fixture'


def test_model_timeout_ends_in_error_and_refunds(client, member):
    runner.set_model_client(Script(ModelError('timeout', 'read timed out')))
    before = left(member)
    r = client.post('/api/clair/turns', json={'text': 'spent $12 on lunch'})
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'done']
    assert evs[-1][1]['status'] == 'error' and evs[-1][1]['message'] == runner.MESSAGES['timeout']
    run = run_row(UUID(r.headers['x-run-id']))
    assert run['status'] == 'error' and run['credits'] == 0
    assert left(member) == before


def test_model_crash_and_refusal(client, member):
    runner.set_model_client(Script(RuntimeError('boom')))
    evs = sse(client.post('/api/clair/turns', json={'text': 'hi'}).text)
    assert evs[-1][1]['status'] == 'error' and evs[-1][1]['message'] == runner.MESSAGES['api']
    runner.set_model_client(Script(ModelReply(content=[], stop_reason='refusal', model='fake')))
    evs = sse(client.post('/api/clair/turns', json={'text': 'hi'}).text)
    assert evs[-1][1] == {'status': 'error', 'sources': [], 'message': runner.MESSAGES['refusal']}


def test_bad_tool_input_goes_back_as_error(client, member):
    bad = [{'op': 'update', 'app': 'budget', 'collection': 'spend', 'record_id': '00000000-0000-0000-0000-000000000000',
            'fields': [{'key': 'amount', 'value': '1'}]}]
    fake = Script(
        ModelReply(content=[use(1, 'propose_changes', {'title': 'X', 'ops': bad})], stop_reason='tool_use', model='fake'),
        ModelReply(content=[use(2, 'propose_changes', {'title': 'Lunch', 'summary': 's', 'ops': LUNCH_OPS})],
                   stop_reason='tool_use', model='fake'),
        ModelReply(content=[], stop_reason='end_turn', model='fake'))
    runner.set_model_client(fake)
    evs = sse(client.post('/api/clair/turns', json={'text': 'spent $12 on lunch'}).text)
    assert [e for e, _ in evs] == ['status', 'proposal', 'done']
    err = fake.calls[1]['messages'][-1]['content'][0]
    assert err['is_error'] and 'not in the snapshot' in err['content']


def test_credits_at_zero_is_402(client, member):
    with db.transaction(WS) as c:
        c.execute("insert into usage_ledger (workspace_id, period, kind, credits) values (%s, '2026-11-01', 'chat', -1000)", (WS,))
    try:
        runner.set_model_client(Script())
        r = client.post('/api/clair/turns', json={'text': 'hi'})
        assert r.status_code == 402 and r.json() == {'error': 'no_credits'}
    finally:
        with db.transaction(WS) as c:
            c.execute("delete from usage_ledger where workspace_id = %s and credits = -1000", (WS,))


# ---------------------------------------------------------------- the mock client, end to end through the route

def test_mock_lunch_and_variants(client, member, monkeypatch):
    monkeypatch.setenv('CLAIR_MODEL', 'mock')
    runner.set_model_client(None)
    r = client.post('/api/clair/turns', json={'text': 'spent $12 on lunch'})
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'understood', 'proposal', 'done']
    check_lunch_card(evs[2][1]['change_set'])
    assert run_row(UUID(r.headers['x-run-id']))['model'] == 'mock'
    evs = sse(client.post('/api/clair/turns', json={'text': 'Spent $5.50 on gas'}).text)
    cs = evs[2][1]['change_set']
    assert cs['ops'][0]['values']['amount'] == 550 and cs['ops'][0]['values']['category'] == 'c_transport'
    assert cs['deltas'] == [{'app': 'budget', 'before': '$412', 'after': '$407'}]   # faces round over $100


def test_mock_other_text(client, member, monkeypatch):
    monkeypatch.setenv('CLAIR_MODEL', 'mock')
    runner.set_model_client(None)
    evs = sse(client.post('/api/clair/turns', json={'text': "what's the weather"}).text)
    assert [e for e, _ in evs] == ['status', 'text_delta', 'done'] and evs[-1][1]['status'] == 'complete'


@pytest.fixture
def full_seed(member):
    with db.transaction(WS) as c:
        reset_workspace(c, WS, 'full', gcal_fixture=True)
    yield
    with db.transaction(WS) as c:
        reset_workspace(c, WS, 'before')


def _check_plan(cs):
    kinds = [o['op'] for o in cs['ops']]
    assert kinds.count('keep') == 1 and kinds.count('move_occurrence') == 3
    moves = {(o['occurrence'], o['fields'][0]['value']) for o in cs['ops'] if o['op'] == 'move_occurrence'}
    assert moves == {('2026-11-24', '2026-11-24T17:00:00-07:00'), ('2026-11-25', '2026-11-25T07:00:00-07:00'),
                     ('2026-11-27', '2026-11-29T16:00:00-07:00')}
    assert set(cs['targets']) == {'workout', 'calendar'} and cs['actions']['primary'] == 'Add to 2 apps'
    assert cs['title'] == "Next week's training" and cs['summary'].startswith('4 lifts (1 kept, 3 moved)')
    assert all(r.get('reason') for r in cs['review'])


def test_mock_planner(client, member, full_seed, monkeypatch):
    monkeypatch.setenv('CLAIR_MODEL', 'mock')
    runner.set_model_client(None)
    r = client.post('/api/clair/turns', json={'text': 'Plan my training for next week'})
    evs = sse(r.text)
    names = [e for e, _ in evs]
    assert names[0] == 'status' and names[-3:] == ['proposal', 'offer', 'done'] and 'understood' in names
    cs = evs[names.index('proposal')][1]['change_set']
    _check_plan(cs)
    assert cs['mode'] == 'live'
    assert run_row(UUID(r.headers['x-run-id']))['effort'] == 'medium'
    # the mock takes its facts from the planning brief, as the model does
    und = evs[names.index('understood')][1]['summary']
    assert und.startswith('Read ') and 'Calendar' in und and 'Workout' in und
    reasons = sorted(x['reason'] for x in cs['review'])
    assert any(x.startswith('Dentist at 7:30') for x in reasons), reasons
    assert any(x.startswith('Back to campus') for x in reasons), reasons


def test_fixture_planner(client, member, full_seed):
    runner.set_model_client(Script())
    evs = sse(client.post('/api/clair/turns', json={'fixture': 'planner'}).text)
    names = [e for e, _ in evs]
    assert names == ['status', 'understood', 'status', 'proposal', 'offer', 'done']
    cs = evs[3][1]['change_set']
    _check_plan(cs)
    assert cs['mode'] == 'fixture'


def test_fixture_that_no_longer_resolves_is_frayed(client, member):
    # 'before' seed has no Google events: the planner sample can't resolve "Dentist"
    runner.set_model_client(Script())
    evs = sse(client.post('/api/clair/turns', json={'fixture': 'planner'}).text)
    assert evs[-1][1]['status'] == 'error' and evs[-1][1]['message'] == runner.MESSAGES['fixture']


# ---------------------------------------------------------------- ask_user: pause and resume (§2, §10, §11)

from types import SimpleNamespace  # noqa: E402
from uuid import uuid4  # noqa: E402

from api.clair import tools as clair_tools  # noqa: E402
from api.models import QuestionCard, SingleQuestion  # noqa: E402

CARD = {'plan_after': True, 'questions': [
    {'id': 'target', 'header': 'Daily target', 'question': 'Do you want a daily calorie target?',
     'options': [{'label': 'Set a number', 'description': 'You choose it', 'input': {'placeholder': 'Calories a day', 'numeric': True}},
                 {'label': 'No target', 'description': 'Just totals for the day'}]},
    {'id': 'logging', 'header': 'Logging', 'question': 'How do you log meals?', 'multi_select': True,
     'options': [{'label': 'Type them'}, {'label': 'Pick from foods you save'}]}]}
ANSWERS = {'target': {'choices': ['Set a number'], 'other': '2200'}, 'logging': {'choices': ['Type them', 'Pick from foods you save']}}
PLAN = [{'app': 'calories', 'text': 'Today: a ring for calories against 2,200'},
        {'app': 'calories', 'text': 'Log: meals with calories and protein'}]
END = ModelReply(content=[], stop_reason='end_turn', model='fake')


def charged(run_id) -> int:
    """Credits this run took (other agents share the workspace, so not the balance)."""
    with db.connect() as c:
        return -c.execute('select coalesce(sum(credits), 0) as n from usage_ledger where run_id = %s',
                          (run_id,)).fetchone()['n']


def q_row(qid):
    with db.connect() as c:
        return c.execute('select * from clair_questions where id = %s', (qid,)).fetchone()


def answer(client, r, **ans):
    qid = ans.pop('question_id', None) or [d for e, d in sse(r.text) if e == 'question'][0]['id']
    return client.post('/api/clair/turns', json={'thread_id': r.headers['x-thread-id'], 'answer': {'question_id': qid, **ans}})


@pytest.fixture
def no_build(monkeypatch):
    monkeypatch.setattr(clair_tools, 'build_module', lambda: None)


@pytest.fixture
def fake_build(monkeypatch):
    """A stand-in for api/clair/build.py: emits `plan` like the real one, then stores a draft through
    propose_changes (which emits `proposal`)."""
    calls = []

    def handle(ctx, inp):
        calls.append(inp)
        ctx.emitter.emit('plan', {'title': 'Calories', 'new_app': inp['spec'], 'lines': inp['plan']})
        return clair_tools.propose_changes(ctx, clair_tools.ProposeChanges.model_validate(
            {'title': 'Make a Calories app?', 'summary': 's', 'ops': LUNCH_OPS}))
    mod = SimpleNamespace(TOOL={'name': 'propose_app', 'description': 'Build an app.',
                                'input_schema': {'type': 'object', 'properties': {}}}, handle=handle)
    monkeypatch.setattr(clair_tools, 'build_module', lambda: mod)
    return calls


def test_mock_build_asks_then_answers(client, member, monkeypatch):
    """The recorded Calories build (§12.11) end to end on the 'before' seed: ask, answer, propose_app through
    the real build.handle, Change answers in place."""
    monkeypatch.setenv('CLAIR_MODEL', 'mock')
    runner.set_model_client(None)
    r = client.post('/api/clair/turns', json={'text': 'I want to track my calories'})
    assert r.status_code == 200, r.text
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'text_delta', 'question', 'done']
    card = QuestionCard.model_validate(evs[2][1])
    assert card.plan_after and [q.id for q in card.questions] == ['target', 'logging']
    assert card.questions[0].options[0].input.numeric and card.questions[1].multi
    assert evs[3][1] == {'status': 'awaiting_input', 'sources': []}
    run_id = UUID(r.headers['x-run-id'])
    run = run_row(run_id)
    assert run['status'] == 'awaiting_input' and run['credits'] == 1
    q = q_row(UUID(card.id))
    assert q['status'] == 'open' and q['run_id'] == run_id and q['tool_use_id'] == 'mock_0_0'
    assert q['options']['plan_after'] is True and q['other_results'] == []
    assert 23 * 3600 < (q['expires_at'] - q['created_at']).total_seconds() <= 24 * 3600
    assert charged(run_id) == 1

    r2 = answer(client, r, answers=ANSWERS)
    assert r2.status_code == 200, r2.text
    assert r2.headers['x-run-id'] == str(run_id)                 # the same run continues
    evs2 = sse(r2.text)
    assert [e for e, _ in evs2] == ['status', 'plan', 'proposal', 'done'], run_row(run_id)['error']
    assert evs2[-1][1]['status'] == 'complete'
    plan = evs2[1][1]
    assert plan['title'] == 'Calories' and plan['new_app']['key'] == 'calories'
    assert [ln['text'] for ln in plan['lines']] == ['Today: a ring for calories against 2,200',
                                                    'Log: meals with calories and protein',
                                                    'Foods: save a food once, tap it to log it again']
    cs = evs2[2][1]['change_set']
    assert cs['status'] == 'basted' and cs['kind'] == 'app' and 'calories' in cs['targets']
    assert cs['title'] == 'Make a Calories app?'
    run = run_row(run_id)
    assert run['status'] == 'complete' and run['credits'] == 10 and run['iterations'] == 2
    assert str(run['change_set_id']) == cs['id']
    assert [e['event'] for e in run['events']].count('done') == 2
    assert q_row(UUID(card.id))['status'] == 'answered'
    assert q_row(UUID(card.id))['answer'] == {'answers': {'target': {'choices': ['Set a number'], 'other': '2200'},
                                                          'logging': {'choices': ['Type them', 'Pick from foods you save']}}}
    assert charged(run_id) == 10                                 # a build: 10 once, in place of the 1 (§14)

    # Change answers: the same change set, replaced in place (version + 1), no target this time
    r3 = answer(client, r, answers={'target': {'choices': ['No target']}, 'logging': {'choices': ['Type them']}})
    assert r3.status_code == 200, r3.text
    evs3 = sse(r3.text)
    assert [e for e, _ in evs3] == ['status', 'plan', 'proposal', 'done']
    assert evs3[1][1]['lines'][0]['text'] == 'Today: calories and protein so far, no target'
    cs2 = evs3[2][1]['change_set']
    assert cs2['id'] == cs['id'] and cs2['version'] == cs['version'] + 1
    assert 'target' not in (cs2['preview']['spec'].get('settings') or {})
    assert charged(run_id) == 10

    with db.transaction(WS) as c:                                # confirmed or dismissed: answers are closed
        c.execute("update change_sets set status = 'dismissed' where id = %s", (cs['id'],))
    r4 = answer(client, r, answers=ANSWERS)
    assert r4.status_code == 409 and r4.json() == {'error': 'question_answered'}


def test_mock_build_without_build_tool_answers_in_words(client, member, monkeypatch, no_build):
    monkeypatch.setenv('CLAIR_MODEL', 'mock')
    runner.set_model_client(None)
    r = client.post('/api/clair/turns', json={'text': 'I want to track my calories'})
    evs2 = sse(answer(client, r, skip=True).text)
    assert [e for e, _ in evs2] == ['status', 'text_delta', 'done'] and 'no target' in evs2[1][1]['text']
    assert run_row(UUID(r.headers['x-run-id']))['credits'] == 1


def test_answer_resumes_with_sibling_results_plan_and_change_answers(client, member, fake_build):
    def propose(messages):
        return ModelReply(content=[use(10 + len(messages), 'propose_app', {'name': 'Calories', 'spec': {
            'key': 'calories', 'name': 'Calories', 'icon': 'flame', 'dye': 'pear'}, 'plan': PLAN})],
            stop_reason='tool_use', model='fake')
    fake = Script(
        ModelReply(content=[{'type': 'text', 'text': 'A few questions first.'}, use(1, 'list_apps', {}),
                            use(2, 'ask_user', CARD)], stop_reason='tool_use', model='fake'),
        # after the answer: propose_app without a plan is refused, then with one
        ModelReply(content=[use(3, 'propose_app', {'name': 'Calories', 'spec': {}})], stop_reason='tool_use', model='fake'),
        propose,              # the card ends the run: no closing call
        # Change answers
        propose)
    runner.set_model_client(fake)
    r = client.post('/api/clair/turns', json={'text': 'I want to track my calories'})
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'text_delta', 'question', 'done']
    qid = evs[2][1]['id']
    q = q_row(UUID(qid))
    assert q['tool_use_id'] == 'toolu_2' and [x['tool_use_id'] for x in q['other_results']] == ['toolu_1']
    assert not q['other_results'][0].get('is_error') and 'budget' in q['other_results'][0]['content']
    assert 'propose_app' in fake.calls[0]['tools'] and 'ask_user' in fake.calls[0]['tools']

    r2 = answer(client, r, answers=ANSWERS)
    assert r2.status_code == 200, r2.text
    evs2 = sse(r2.text)
    assert [e for e, _ in evs2] == ['status', 'plan', 'proposal', 'done'], run_row(UUID(r.headers['x-run-id']))['error']
    assert evs2[0][1]['text'] == 'Planning with your answers…'
    assert evs2[1][1] == {'title': 'Calories', 'new_app': {'key': 'calories', 'name': 'Calories', 'icon': 'flame',
                                                           'dye': 'pear'}, 'lines': PLAN}
    cs_id = evs2[2][1]['change_set']['id']
    # the fake model saw one user message with every pending tool_result, in the tool_use order
    resumed = fake.calls[1]['messages']
    assert resumed[-2]['role'] == 'assistant' and resumed[-1]['role'] == 'user'
    res = resumed[-1]['content']
    assert [b['tool_use_id'] for b in res] == ['toolu_1', 'toolu_2'] and all(b['type'] == 'tool_result' for b in res)
    assert res[0] == q['other_results'][0]
    assert json.loads(res[1]['content']) == {'answers': {'target': {'choices': ['Set a number'], 'other': '2200'},
                                                         'logging': {'choices': ['Type them', 'Pick from foods you save']}}}
    refused = fake.calls[2]['messages'][-1]['content'][0]
    assert refused['is_error'] and 'plan' in refused['content']
    assert len(fake_build) == 1
    run = run_row(UUID(r.headers['x-run-id']))
    assert run['status'] == 'complete' and run['credits'] == 10 and str(run['change_set_id']) == cs_id
    assert charged(run['id']) == 10                              # a build costs 10 once (§14)

    # Change answers while the change set is basted: accepted, same change set replaced in place
    r3 = answer(client, r, answers={'target': {'choices': ['No target']}, 'logging': {'choices': ['Type them']}})
    assert r3.status_code == 200, r3.text
    evs3 = sse(r3.text)
    assert [e for e, _ in evs3] == ['status', 'plan', 'proposal', 'done']
    assert evs3[2][1]['change_set']['id'] == cs_id
    said = fake.calls[3]['messages'][-1]['content'][-1]
    assert said['type'] == 'text' and said['text'].startswith('Sam changed the answers: ')
    assert json.loads(said['text'].split(': ', 1)[1])['answers']['target'] == {'choices': ['No target']}
    assert charged(run['id']) == 10
    assert q_row(UUID(qid))['answer']['answers']['target'] == {'choices': ['No target']}

    # once dismissed, another answer is 409
    with db.transaction(WS) as c:
        c.execute("update change_sets set status = 'dismissed' where id = %s", (cs_id,))
    r4 = answer(client, r, answers=ANSWERS)
    assert r4.status_code == 409


def test_single_question_answer_and_skip(client, member, no_build):
    menu = {'question': 'Which list?', 'options': [{'label': 'Weekly shop', 'description': 'The default list'},
                                                   {'label': 'Taco night'}], 'multi_select': True}
    fake = Script(ModelReply(content=[use(1, 'ask_user', menu)], stop_reason='tool_use', model='fake'),
                  ModelReply(content=[{'type': 'text', 'text': 'Done.'}], stop_reason='end_turn', model='fake'))
    runner.set_model_client(fake)
    r = client.post('/api/clair/turns', json={'text': 'add butter'})
    evs = sse(r.text)
    sq = SingleQuestion.model_validate(evs[1][1])
    assert sq.text == 'Which list?' and sq.multi and [o.label for o in sq.options] == ['Weekly shop', 'Taco night']
    assert sq.options[0].hint == 'The default list' and sq.expires_at is not None
    bad = answer(client, r, choices=['Party list'])
    assert bad.status_code == 422
    r2 = answer(client, r, choices=[sq.options[1].id, 'Weekly shop'], other='stopped buying orange juice')
    assert [e for e, _ in sse(r2.text)] == ['status', 'text_delta', 'done']
    res = fake.calls[1]['messages'][-1]['content']
    assert res == [{'type': 'tool_result', 'tool_use_id': 'toolu_1',
                    'content': json.dumps({'choices': ['Taco night', 'Weekly shop'], 'other': 'stopped buying orange juice'})}]
    assert answer(client, r, choices=['Weekly shop']).status_code == 409    # a single question can't be changed

    # skip on a card
    fake = Script(ModelReply(content=[use(1, 'ask_user', CARD)], stop_reason='tool_use', model='fake'), END)
    runner.set_model_client(fake)
    r = client.post('/api/clair/turns', json={'text': 'I want to track my calories'})
    assert answer(client, r, answers={'target': {'choices': ['No target']}}).status_code == 422   # every question answered
    r2 = answer(client, r, skip=True)
    assert sse(r2.text)[-1][1]['status'] == 'complete'
    assert json.loads(fake.calls[1]['messages'][-1]['content'][0]['content']) == {'skipped': True}


def test_answer_expired_unknown_and_busy(client, member, no_build):
    runner.set_model_client(Script(ModelReply(content=[use(1, 'ask_user', CARD)], stop_reason='tool_use', model='fake')))
    r = client.post('/api/clair/turns', json={'text': 'I want to track my calories'})
    qid = [d for e, d in sse(r.text) if e == 'question'][0]['id']
    # unknown question, malformed id, another thread
    assert answer(client, r, question_id=str(uuid4()), skip=True).status_code == 404
    assert answer(client, r, question_id='q_nope', skip=True).status_code == 404
    other = client.post('/api/clair/turns', json={'thread_id': str(uuid4()), 'answer': {'question_id': qid, 'skip': True}})
    assert other.status_code == 404
    assert client.post('/api/clair/turns', json={'answer': {'question_id': qid}}).status_code == 422   # no thread_id
    # late: past expires_at → 410, and the row reads expired
    with db.transaction(WS) as c:
        c.execute("update clair_questions set expires_at = now() - interval '1 minute' where id = %s", (qid,))
    late = answer(client, r, question_id=qid, skip=True)
    assert late.status_code == 410 and late.json() == {'error': 'question_expired'}
    assert q_row(UUID(qid))['status'] == 'expired'
    assert answer(client, r, question_id=qid, skip=True).status_code == 410


def test_bad_ask_goes_back_as_error_and_limit(client, member, no_build):
    long_header = {'questions': [{**CARD['questions'][0], 'header': 'A header too long'}], 'plan_after': True}
    menu = {'question': 'Which list?', 'options': [{'label': 'A'}, {'label': 'B'}]}
    fake = Script(
        ModelReply(content=[use(1, 'ask_user', long_header)], stop_reason='tool_use', model='fake'),
        ModelReply(content=[use(2, 'ask_user', menu)], stop_reason='tool_use', model='fake'),
        ModelReply(content=[use(3, 'ask_user', menu)], stop_reason='tool_use', model='fake'),
        ModelReply(content=[use(4, 'ask_user', menu)], stop_reason='tool_use', model='fake'),
        END)
    runner.set_model_client(fake)
    r = client.post('/api/clair/turns', json={'text': 'add butter'})
    evs = sse(r.text)
    assert [e for e, _ in evs] == ['status', 'question', 'done']
    err = fake.calls[1]['messages'][-1]['content'][0]
    assert err['is_error'] and 'header' in err['content']
    r2 = answer(client, r, choices=['A'])
    evs2 = sse(r2.text)
    assert [e for e, _ in evs2] == ['status', 'question', 'done']          # the second ask of the run
    r3 = client.post('/api/clair/turns', json={'thread_id': r.headers['x-thread-id'],
                                               'answer': {'question_id': evs2[1][1]['id'], 'choices': ['B']}})
    assert sse(r3.text)[-1][1]['status'] == 'complete'
    third = fake.calls[4]['messages'][-1]['content'][0]
    assert third['is_error'] and third['content'].startswith('Question limit reached')
