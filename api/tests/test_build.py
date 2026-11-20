"""Building apps: Clair's `propose_app` (clair-agent.md §10, §11, §12.11) and the app routes (backend.md §10,
§11 #21 to #23), against the live database on the DEMO account (sam@quilt.demo).

The workspace is reset to the 8-app 'before' state at the start (Calories, Running, Cycle, Meditation absent) and
back to 'full' at the end. No model call: `propose_app`'s handler is called with the inputs Clair would send.
"""
import copy
import json
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

PW_FILE = os.path.expanduser('~/.config/quilt/demo-password')


def _ok() -> bool:
    try:
        from api.settings import settings
        s = settings()
        return bool(s.database_url and s.demo_workspace_id and os.path.exists(PW_FILE))
    except Exception:
        return False


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _ok(), reason='no database or demo password')]

import httpx  # noqa: E402
from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api import db  # noqa: E402
from api import models as m  # noqa: E402
from api.clair import build  # noqa: E402
from api.clair.events import Emitter  # noqa: E402
from api.clair.tools import RunContext, ToolError  # noqa: E402
from api.index import contract_errors, validation_errors  # noqa: E402
from api.routes import apps as app_routes, write  # noqa: E402
from api.seed.load import load_template, reset_workspace  # noqa: E402
from api.settings import settings  # noqa: E402
from api.workspace import faces, load  # noqa: E402

S = settings()
WS = UUID(S.demo_workspace_id) if _ok() else None


def _reset(state: str) -> None:
    with db.transaction(WS) as c:
        reset_workspace(c, WS, state)


def _keys() -> list[str]:
    with db.connect() as c:
        return [a['key'] for a in load(c, WS).apps]


def _ld():
    with db.connect() as c:
        return load(c, WS)


@pytest.fixture(scope='module')
def seeded():
    _reset('before')
    try:
        yield
    finally:
        _reset('full')


@pytest.fixture(scope='module')
def user_id(seeded):
    with db.connect() as c:
        return c.execute('select user_id from workspace_members where workspace_id = %s order by created_at limit 1',
                         (WS,)).fetchone()['user_id']


@pytest.fixture(scope='module')
def client(seeded):
    pw = open(PW_FILE).read().strip()
    tok = httpx.post(f'{S.supabase_url}/auth/v1/token?grant_type=password', headers={'apikey': S.supabase_anon_key},
                     json={'email': 'sam@quilt.demo', 'password': pw}, timeout=20).json()['access_token']
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.add_exception_handler(RequestValidationError, validation_errors)
    api = APIRouter(prefix='/api')
    api.include_router(write.router)
    api.include_router(app_routes.router)
    app.include_router(api)
    with TestClient(app, headers={'Authorization': f'Bearer {tok}'}) as tc:
        yield tc


def _ctx(user_id) -> RunContext:
    rid = uuid4()
    return RunContext(workspace_id=WS, user_id=user_id, tz='America/Denver', run_id=None, thread_id=None,
                      read_level='full', emitter=Emitter(rid, persist=None), persist_calls=False)


def _fv(d: dict) -> list[dict]:
    return [{'key': k, 'value': v} for k, v in d.items()]


# ---------------------------------------------------------------- the three §12.11 builds

def calories_input() -> dict:
    spec = load_template('calories')
    spec['settings'] = {'target': 2200}
    return {
        'name': 'Calories', 'purpose': 'Track what I eat, calories and protein', 'spec': json.dumps(spec),
        'summary': 'Meals with calories and protein, and foods you save.',
        'examples': [{'collection': 'meals', 'fields': _fv({'name': 'Oatmeal', 'calories': '350', 'protein': '12',
                                                            'meal': 'Breakfast', 'at': '2026-11-20T08:00'})}],
        'plan': [{'app': 'calories', 'text': 'Today: a ring for calories against 2,200'},
                 {'app': 'calories', 'text': 'Log: meals with calories and protein'},
                 {'app': 'calories', 'text': 'Foods: save a food once, tap it to log it again'}],
    }


def running_input() -> dict:
    return {
        'name': 'Running', 'purpose': "I'm running a 10K on Sat 12 Dec. Track my runs",
        'spec': load_template('running'), 'summary': 'Your runs, and your 10K on Sat 12 Dec.',
        'rows': [{'collection': 'races', 'fields': _fv({'name': '10K', 'at': '2026-12-12T09:00', 'distance': '10K'})}],
        'examples': [{'collection': 'runs', 'fields': _fv({'name': 'Easy run', 'kind': 'easy', 'distance': '3',
                                                           'minutes': '30', 'at': '2026-11-19T17:30',
                                                           'done': 'true'})}],
        'plan': [{'app': 'running', 'text': 'This week: days to your 10K, and a stopwatch that logs each run'},
                 {'app': 'running', 'text': 'Log: runs with distance and time'},
                 {'app': 'running', 'text': 'Races: 10K on Sat 12 Dec'},
                 {'app': 'calendar', 'text': 'Calendar: Race · 10K on Sat 12 Dec'}],
    }


def cycle_input() -> dict:
    spec = load_template('cycle')
    spec.pop('settings')            # the server turns Clair's read switch off on a private (and every Cycle) app
    return {
        'name': 'Cycle', 'purpose': 'Track my cycle and keep it private', 'spec': json.dumps(spec),
        'summary': "A daily log and cycle starts. Private: I won't read it unless you turn that on.",
        'plan': [{'app': 'cycle', 'text': 'Month: tap a day to log flow, energy and symptoms'},
                 {'app': 'cycle', 'text': 'Cycles: when each one started'},
                 {'app': 'cycle', 'text': "Private: Clair won't read it"}],
    }


BUILDS = {'calories': calories_input, 'running': running_input, 'cycle': cycle_input}
CARDS: dict[str, dict] = {}


@pytest.mark.parametrize('key', list(BUILDS))
def test_propose_app_makes_a_basted_build_card(key, user_id):
    ctx = _ctx(user_id)
    out = build.handle(ctx, BUILDS[key]())
    evs = ctx.emitter.events
    assert [e['event'] for e in evs] == ['plan', 'proposal']
    plan = evs[0]['data']
    assert plan['new_app']['key'] == key and 2 <= len(plan['lines']) <= 5
    cs = evs[1]['data']['change_set']
    m.ChangeSet.model_validate(cs)
    assert cs['id'] == out['change_set_id'] and out['preview'] == 'build'
    assert cs['status'] == 'basted' and cs['kind'] == 'app'
    assert cs['actions']['primary'] == 'Make it'
    assert cs['title'] == f'Make a {key.title()} app?'
    assert cs['lines'][0]['apps'] == [key] and cs['lines'][0]['what'].startswith('new app · ')
    p = cs['preview']
    assert p['seq'] == 0 and p['spec']['key'] == key
    assert set(p['data']) >= {f'{key}/{c["key"]}' for c in p['spec']['collections']}
    assert key not in _keys()           # nothing written before Make it
    if key == 'calories':
        assert p['spec']['settings']['target'] == 2200
        meals = p['data']['calories/meals']
        assert len(meals) == 1 and meals[0]['example'] is True
        assert {k: p['faces']['calories'][k] for k in ('text', 'label')} == {'text': '0', 'label': 'today'}     # samples never count
        assert 'b_ring' in p['values']
        assert cs['targets'] == ['calories'] and cs['ops'] == []
    if key == 'running':
        assert cs['targets'] == ['running', 'calendar']
        assert cs['lines'][1] == {'apps': ['calendar'], 'what': 'Race · 10K, Sat 12 Dec', 'val': ''}
        race = p['data']['running/races']
        assert len(race) == 1 and not race[0].get('example')
        assert race[0]['properties']['at'] == '2026-12-12T09:00:00-07:00'
        assert [r.get('example') for r in p['data']['running/runs']] == [True]
        assert cs['ops'] == [{'op': 'insert', 'ref': 'running/races',
                              'values': {'name': '10K', 'at': '2026-12-12T09:00:00-07:00', 'distance': '10K'}}]
        assert p['faces']['running']['label'] == 'mi this week' and p['faces']['running']['text'] == '0'
        assert p['values']['b_race']['title'] == '10K'
    if key == 'cycle':
        assert plan['private'] is True
        assert p['spec']['private'] is True and p['spec']['settings']['clair_read'] is False
        assert cs['lines'][0]['what'].endswith('· private')
    CARDS[key] = cs


def test_second_propose_replaces_the_draft_in_place(user_id):
    ctx = _ctx(user_id)
    first = build.handle(ctx, calories_input())
    changed = calories_input()
    spec = json.loads(changed['spec'])
    spec['settings'] = {}
    changed['spec'] = json.dumps(spec)
    changed['plan'][0]['text'] = 'Today: calories and protein so far, no target'
    second = build.handle(ctx, changed)
    assert second['change_set_id'] == first['change_set_id']
    cs = ctx.emitter.events[-1]['data']['change_set']
    assert cs['version'] == 2 and 'target' not in cs['preview']['spec']['settings']
    assert [e['event'] for e in ctx.emitter.events] == ['plan', 'proposal', 'plan', 'proposal']


def _tool_error(user_id, inp: dict) -> list[dict]:
    with pytest.raises(ToolError) as e:
        build.handle(_ctx(user_id), inp)
    return json.loads(str(e.value))


def _bad(mutate) -> dict:
    inp = running_input()
    spec = copy.deepcopy(inp['spec'])
    mutate(spec)
    inp['spec'] = spec
    return inp


def test_invalid_specs_are_tool_errors(user_id):
    def unknown_kind(s):
        s['tabs'][0]['children'].append({'kind': 'sparkle', 'id': 'b_x'})
    probs = _tool_error(user_id, _bad(unknown_kind))
    assert any('sparkle' in p['problem'] or 'kind' in p['problem'] for p in probs)

    probs = _tool_error(user_id, _bad(lambda s: s.pop('face')))
    assert any('face' in p['field'] for p in probs)

    def bad_stitch(s):
        s['stitches'] = [{'from': 'garden/plants', 'to': 'running/runs', 'map': [{'to': 'name', 'from': 'name'}]}]
    probs = _tool_error(user_id, _bad(bad_stitch))
    assert any("no collection 'garden/plants'" in p['problem'] for p in probs)

    def bad_face(s):
        s['face']['value'] = {'agg': 'sum', 'from': 'running/runs', 'field': 'pace'}
    probs = _tool_error(user_id, _bad(bad_face))
    assert any("no field 'pace'" in p['problem'] for p in probs)

    probs = _tool_error(user_id, _bad(lambda s: s.update(icon='rocket')))
    assert any('icon' in p['field'] for p in probs)

    def tiny(s):
        s['collections'] = [{'key': 'runs', 'name': 'Runs', 'titleField': 'name',
                             'fields': [{'key': 'name', 'label': 'Run', 'type': 'text'}]}]
    probs = _tool_error(user_id, _bad(tiny))
    assert any('at least 3 fields' in p['problem'] for p in probs)

    inp = _bad(lambda s: s.update(key='budget'))
    inp.pop('plan')
    probs = _tool_error(user_id, inp)
    assert any('already exists' in p['problem'] for p in probs)

    inp = running_input()
    inp['rows'][0]['fields'] = _fv({'at': 'not a date'})
    probs = _tool_error(user_id, inp)
    assert any('not a date' in p['problem'] for p in probs) and any("'name' is required" in p['problem'] for p in probs)

    inp = running_input()
    inp['plan'] = inp['plan'][:1]
    assert any('2 to 5' in p['problem'] for p in _tool_error(user_id, inp))


def test_every_block_kind_is_allowed(user_id):
    inp = running_input()
    spec = inp['spec']
    spec['tabs'].append({'kind': 'page', 'id': 't_more', 'title': 'More', 'children': [
        {'kind': 'gauge', 'id': 'b_g', 'label': 'Week', 'value': {'agg': 'sum', 'from': 'running/runs', 'field': 'distance'},
         'target': 20, 'format': 'number'},
        {'kind': 'bars', 'id': 'b_b', 'label': 'By kind', 'from': 'running/runs', 'by': 'kind',
         'value': {'agg': 'sum', 'from': 'running/runs', 'field': 'distance'}},
        {'kind': 'chart', 'id': 'b_c', 'type': 'bar', 'from': 'running/runs', 'x': 'at',
         'y': {'agg': 'sum', 'from': 'running/runs', 'field': 'distance'}, 'window': 'month'},
        {'kind': 'month', 'id': 'b_m', 'source': 'running/runs', 'dateField': 'at', 'mark': 'kind', 'fields': ['distance']},
        {'kind': 'form', 'id': 'b_f', 'collection': 'running/runs', 'fields': ['name', 'distance'], 'submit': 'Log'},
    ]})
    out = build.handle(_ctx(user_id), inp)
    assert out['preview'] == 'build'


# ---------------------------------------------------------------- Make it, Undo

def test_make_it_creates_the_app_and_undo_removes_it(client):
    cs = CARDS['running']
    assert len(_keys()) == 8
    r = client.post(f'/api/change-sets/{cs["id"]}/confirm')
    assert r.status_code == 200, r.text
    res = m.CommandResult.model_validate(r.json())
    assert res.faces['running'].text == '0' and res.faces['running'].label == 'mi this week'
    assert _keys()[-1] == 'running' and len(_keys()) == 9
    ld = _ld()
    races = [x for x in ld.records if x['collection'] == 'running/races']
    assert [x['properties']['name'] for x in races] == ['10K']
    assert not [x for x in ld.records if x['collection'] == 'running/runs']      # examples are never saved
    assert faces(ld, ['running'])['running']['text'] == '0'
    # the race reaches Calendar through *dated
    from api.logic.dated import dated_rows
    from datetime import date
    rows = dated_rows(ld.apps, ld.records, date(2026, 12, 12), date(2026, 12, 12), ld.tz)
    assert any(x['app'] == 'running' and '10K' in x['title'] for x in rows)
    # the card now reads stitched, with the real page id in its preview
    listed = {c['id']: c for c in client.get('/api/change-sets').json()}
    assert listed[cs['id']]['status'] == 'stitched'
    assert listed[cs['id']]['preview']['spec']['id'] == ld.page_ids['running']
    assert client.post(f'/api/change-sets/{cs["id"]}/confirm').status_code == 409

    r = client.post(f'/api/change-sets/{cs["id"]}/undo')
    assert r.status_code == 200, r.text
    assert 'running' not in _keys() and len(_keys()) == 8
    assert not [x for x in _ld().records if x['collection'].startswith('running/')]
    listed = {c['id']: c for c in client.get('/api/change-sets').json()}
    assert listed[cs['id']]['status'] == 'basted'          # a Clair card is basted again after Undo

    # Make it again works (a fresh page id), then dismissing isn't possible any more
    r = client.post(f'/api/change-sets/{cs["id"]}/confirm')
    assert r.status_code == 200, r.text
    assert 'running' in _keys()
    r = client.post(f'/api/change-sets/{cs["id"]}/undo')
    assert r.status_code == 200 and 'running' not in _keys()


def test_confirm_refuses_when_the_key_is_taken_since(client, user_id):
    out = build.handle(_ctx(user_id), cycle_input())
    spec = load_template('cycle')
    r = client.post('/api/apps', json={'spec': spec})
    assert r.status_code == 201, r.text
    r2 = client.post(f'/api/change-sets/{out["change_set_id"]}/confirm')
    assert r2.status_code == 409 and r2.json()['error'] == 'changed'
    assert client.post(f'/api/change-sets/{r.json()["change_set_id"]}/undo').status_code == 200
    assert 'cycle' not in _keys()


# ---------------------------------------------------------------- /apps routes

def _page(key: str) -> dict:
    ld = _ld()
    return ld.app(key)


def test_post_patch_delete_apps(client):
    spec = load_template('meditation')
    r = client.post('/api/apps', json={'spec': spec})
    assert r.status_code == 201, r.text
    created = r.json()
    m.CommandResult.model_validate(created)
    assert 'meditation' in created['faces'] and _keys()[-1] == 'meditation'
    assert client.post('/api/apps', json={'spec': spec}).status_code == 422          # key unique per workspace

    a = _page('meditation')
    stale = dict(a)
    stale.pop('version')
    body = {'spec': {**stale, 'name': 'Calm'}, 'base_version': a['version'] - 1 if a['version'] > 1 else 99}
    r = client.patch(f'/api/apps/{a["id"]}', json=body)
    assert r.status_code == 409 and r.json()['error'] == 'version'

    r = client.patch(f'/api/apps/{a["id"]}', json={'spec': {**stale, 'name': 'Calm'}, 'base_version': a['version']})
    assert r.status_code == 200, r.text
    assert _page('meditation')['name'] == 'Calm' and _page('meditation')['version'] == a['version'] + 1
    r_undo = client.post(f'/api/change-sets/{r.json()["change_set_id"]}/undo')
    assert r_undo.status_code == 200 and _page('meditation')['name'] == 'Meditation'

    # a face that reads a field the edit removes is refused
    bad = copy.deepcopy(stale)
    sess = next(c for c in bad['collections'] if c['key'] == 'sessions')
    sess['fields'] = [f for f in sess['fields'] if f['key'] != 'minutes']
    r = client.patch(f'/api/apps/{a["id"]}', json={'spec': bad, 'base_version': _page('meditation')['version']})
    assert r.status_code == 422, r.text

    # delete: preview first (dependents), then confirm; undo restores
    r = client.delete('/api/apps/budget')
    assert r.status_code == 409 and r.json()['error'] == 'dependents'
    assert isinstance(r.json()['dependents'], list)
    r = client.delete('/api/apps/groceries')
    assert r.status_code == 409
    assert any(d['app'] == 'budget' for d in r.json()['dependents'])        # Budget's stitch reads groceries/trips

    r = client.delete(f'/api/apps/{a["id"]}?confirm=true')
    assert r.status_code == 200, r.text
    assert 'meditation' not in _keys()
    r = client.post(f'/api/change-sets/{r.json()["change_set_id"]}/undo')
    assert r.status_code == 200 and 'meditation' in _keys()
    assert client.delete('/api/apps/nope').status_code == 404

    r = client.delete(f'/api/apps/{a["id"]}?confirm=true')
    assert r.status_code == 200 and 'meditation' not in _keys()


def test_templates_apply(client):
    before = len(_keys())
    r = client.post('/api/templates/apply', json={'templates': ['calories', 'meditation', 'budget']})
    assert r.status_code == 200, r.text
    assert set(r.json()['faces']) == {'calories', 'meditation'}       # Budget is already there: skipped
    assert len(_keys()) == before + 2
    with db.connect() as c:
        row = c.execute('select origin, actor, status from change_sets where id = %s',
                        (r.json()['change_set_id'],)).fetchone()
    assert (row['origin'], row['actor'], row['status']) == ('template', 'user', 'stitched')
    assert client.post('/api/templates/apply', json={'templates': ['calories']}).status_code == 409
    assert client.post('/api/templates/apply', json={'templates': ['garden']}).status_code == 422
    r = client.post(f'/api/change-sets/{r.json()["change_set_id"]}/undo')
    assert r.status_code == 200 and len(_keys()) == before


def test_tool_definition_is_strict_ready():
    t = build.TOOL
    assert t['name'] == 'propose_app' and t['strict'] is True

    def walk(n):
        if isinstance(n, dict):
            if n.get('type') == 'object':
                assert n.get('additionalProperties') is False
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(t['input_schema'])
