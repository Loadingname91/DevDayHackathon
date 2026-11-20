"""The read routes against the live demo workspace (backend.md §10, §7), checked against the frontend's
fixtures in web/src/mocks/fixtures/ (ids differ: live ones are UUIDs, so rows are matched by content).

Resets the demo workspace to the full seed first. Skipped without DATABASE_URL or the demo password.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / 'web/src/mocks/fixtures'
PW = Path(os.path.expanduser('~/.config/quilt/demo-password'))


def _ok() -> bool:
    try:
        from api.settings import settings
        return bool(settings().database_url and settings().demo_workspace_id) and PW.exists()
    except Exception:
        return False


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _ok(), reason='no database or demo password')]

KEYS = ['notes', 'budget', 'subscriptions', 'groceries', 'calendar', 'classes', 'todos', 'workout',
        'calories', 'running', 'cycle', 'meditation']
FACES = {'budget': '$412', 'groceries': '12', 'calendar': '3', 'classes': '2', 'notes': '3', 'todos': '2',
         'workout': '3', 'subscriptions': '$38.46', 'calories': '1,140', 'running': '7', 'meditation': '25',
         'cycle': 'Tue 27 Oct'}


# Where live and fixture differ and the difference is reported, not hidden (see the route report):
KNOWN = {
    # backend.md §10 table: {text: "$38.46", sub: "4 subscriptions"}; the fixture moved to target "a month · 4 …"
    ('subscriptions', 'b_total', 'target'),
    # instruments.py words "41 sessions" with no sub; the fixture splits it "41" / "sessions, 5 skipped"
    ('workout', 'b_done', 'text'), ('workout', 'b_done', 'sub'), ('workout', 'b_week', 'sub'),
}
# Subscriptions on *dated: live "Spotify" at a midnight datetime; fixture "Spotify renews · $11.99" on the day
KNOWN_DATED = {'Spotify renews · $11.99'}


def fixture(name):
    return json.loads((FIX / name).read_text())


@pytest.fixture(scope='module')
def client():
    import httpx
    from fastapi import FastAPI, HTTPException
    from fastapi.exceptions import RequestValidationError
    from fastapi.testclient import TestClient

    from api import db
    from api.index import contract_errors, validation_errors
    from api.routes import read
    from api.seed.load import reset_workspace
    from api.settings import settings

    s = settings()
    ws = s.demo_workspace_id
    with db.transaction(ws) as c:
        reset_workspace(c, ws, 'full')
    tok = httpx.post(f'{s.supabase_url}/auth/v1/token?grant_type=password', headers={'apikey': s.supabase_anon_key},
                     json={'email': 'sam@quilt.demo', 'password': PW.read_text().strip()}).json()['access_token']
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.add_exception_handler(RequestValidationError, validation_errors)
    app.include_router(read.router, prefix='/api')
    with TestClient(app, headers={'Authorization': f'Bearer {tok}'}) as c:
        yield c


def get(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- /apps

def test_apps_faces_and_order(client):
    from api.models import Patch
    apps = get(client, '/api/apps')
    assert sorted(a['key'] for a in apps) == sorted(KEYS)
    for a in apps:
        Patch.model_validate(a)
        assert a['face']['text'] == FACES[a['key']], a
    want = fixture('apps.json')
    assert [a['key'] for a in apps] == [a['key'] for a in want]   # Your apps: last opened first
    for a, w in zip(apps, want):
        for k in ('name', 'icon', 'dye', 'pinned', 'changed', 'lastOpened'):
            assert a[k] == w[k], (a['key'], k, a[k], w[k])
        assert a['face']['label'] == w['face']['label']


def test_unauthorised():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.index import contract_errors
    from fastapi import HTTPException
    from api.routes import read
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.include_router(read.router, prefix='/api')
    r = TestClient(app).get('/api/apps')
    assert r.status_code == 401 and r.json()['error'] == 'no_token'


# ---------------------------------------------------------------- /apps/{id}

def _row_key(props):
    """A record's identity across fixture and live: its scalar text fields (ids and relations differ)."""
    return tuple(sorted((k, v) for k, v in props.items()
                        if isinstance(v, (str, int, float, bool)) and not (isinstance(v, str) and len(v) == 36)))


@pytest.mark.parametrize('key', KEYS)
def test_app_detail_matches_fixture(client, key):
    from api.models import AppDetail
    live = get(client, f'/api/apps/{key}')
    AppDetail.model_validate(live)
    want = fixture(f'app.{key}.json')
    assert live['faces'][key]['text'] == want['faces'][key]['text'] == FACES[key]
    assert live['faces'][key]['label'] == want['faces'][key]['label']
    assert live['spec']['key'] == key and live['spec']['name'] == want['spec']['name']
    assert [t['title'] for t in live['spec']['tabs']] == [t['title'] for t in want['spec']['tabs']]
    # every collection the fixture sends is sent
    assert set(want['data']) <= set(live['data']), (set(want['data']), set(live['data']))
    # values: every displayed figure of the fixture's blocks (ids of records differ). The fixtures also
    # carry values for block ids no tab has (Budget b_spent, b_c_*, b_k_*; Calories b_today; Running b_week;
    # Meditation b_min, b_count): stale, nothing draws them, so only blocks in the spec are compared.
    block_ids = {b['id'] for t in want['spec']['tabs'] for b in t['children']}
    for bid, wv in (want.get('values') or {}).items():
        if bid not in block_ids:
            continue
        lv = live['values'].get(bid)
        assert lv is not None, (key, bid)
        for f, x in wv.items():
            if f in ('record_id',) or (key, bid, f) in KNOWN:
                continue
            if f == 'steps':
                assert [(s['name'], s['plan'], s.get('best')) for s in lv[f]] == \
                       [(s['name'], s['plan'], s.get('best')) for s in x], (key, bid)
                continue
            assert lv.get(f) == x, (key, bid, f, lv.get(f), x)
    # status sentence (Workout: the fixture has none, the spec table words one; see report)
    if want.get('status'):
        assert live['status'] == want['status']
    # *dated: every fixture row is in the live rows (live may send a wider window)
    # Google events are seeded only with DEMO_GCAL_FIXTURE=1, so they're left out of the comparison.
    if '*dated' in want['data']:
        got = {(r['at'], r['title']) for r in live['data']['*dated']}
        miss = [(r['at'], r['title']) for r in want['data']['*dated']
                if (r['at'], r['title']) not in got and r.get('source') != 'google' and r['title'] not in KNOWN_DATED]
        assert not miss, (key, miss)


def test_app_by_uuid_and_404(client):
    apps = get(client, '/api/apps')
    budget = next(a for a in apps if a['key'] == 'budget')
    d = get(client, f"/api/apps/{budget['id']}")
    assert d['spec']['id'] == budget['id']
    r = client.get('/api/apps/nope')
    assert r.status_code == 404 and r.json()['error'] == 'not_found'


def test_groceries_rows_match_fixture(client):
    live = get(client, '/api/apps/groceries')
    want = fixture('app.groceries.json')
    def rows(d, status):
        return sorted((r['properties']['name'], r['properties'].get('list'))
                      for r in d['data']['groceries/items'] if r['properties'].get('status') == status)
    # the 22 to buy across 3 lists are the same rows; the seed holds more bought history than the fixture
    assert rows(live, 'to_buy') == rows(want, 'to_buy')
    assert set(rows(want, 'bought')) <= set(rows(live, 'bought'))


# ---------------------------------------------------------------- /home

def test_home(client):
    from api.models import Home
    h = get(client, '/api/home')
    Home.model_validate(h)
    want = fixture('home.json')
    assert h['greeting'] == 'Evening, Sam.'
    assert h['status'] == want['status'] == '**$412** left this month. Pull day at **6 pm**.'
    assert [(r['at'], r['title'], r['sub'], r['app'], r.get('occurrence')) for r in h['nextUp']] == \
           [(r['at'], r['title'], r['sub'], r['app'], r.get('occurrence')) for r in want['nextUp']]
    assert h['needsOk'] == []   # the demo account starts with no basted cards
    assert [a['key'] for a in h['apps']] == [a['key'] for a in want['apps']]
    assert h['server_now'] == '2026-11-20T17:45:00-07:00'


# ---------------------------------------------------------------- /sync and /opened

def test_sync(client):
    from api.models import SyncResponse
    full = get(client, '/api/sync?since=0')
    SyncResponse.model_validate(full)
    assert full['seq'] > 0
    assert sum(b['block_type'] == 'page' for b in full['blocks']) == 12
    assert sum(b['block_type'] == 'record' for b in full['blocks']) > 500
    assert sorted(full['touched_apps']) == sorted(KEYS)
    assert {k: v['text'] for k, v in full['faces'].items()} == FACES
    assert any(cs['source']['kind'] == 'seed' for cs in full['change_sets'])
    none = get(client, f"/api/sync?since={full['seq']}")
    assert none['blocks'] == [] and none['change_sets'] == [] and none['touched_apps'] == [] and none['faces'] == {}
    assert none['seq'] == full['seq'] and none['epoch'] == full['epoch']


def test_opened_and_changed(client):
    from api import db
    from api.commands import service
    from api.settings import settings
    ws = settings().demo_workspace_id
    r = client.post('/api/apps/todos/opened')
    assert r.status_code == 204
    todos = next(a for a in get(client, '/api/apps') if a['key'] == 'todos')
    assert todos['lastOpened'] == '2026-11-20T17:45:00-07:00' and todos['changed'] is False
    assert get(client, '/api/apps')[0]['key'] == 'todos'
    assert client.post('/api/apps/nope/opened').status_code == 404

    # a gesture on To-dos marks To-dos (and Calendar: todos are calendar rows) changed, and shows in /sync
    seq0 = get(client, '/api/sync?since=0')['seq']
    detail = get(client, '/api/apps/todos')
    rec = next(r for r in detail['data']['todos/todos'] if not r['properties'].get('done'))
    with db.transaction(ws) as c:
        service.run_gesture(c, ws, None, [{'op': 'update', 'record_id': rec['id'], 'fields': {'place': 'Library'}}])
    apps = {a['key']: a for a in get(client, '/api/apps')}
    assert apps['todos']['changed'] and apps['calendar']['changed'] and not apps['budget']['changed']
    inc = get(client, f'/api/sync?since={seq0}')
    assert [b['id'] for b in inc['blocks']] == [rec['id']]
    assert set(inc['touched_apps']) == {'todos', 'calendar'} and set(inc['faces']) == {'todos', 'calendar'}
    assert client.post('/api/apps/todos/opened').status_code == 204
    assert not {a['key']: a for a in get(client, '/api/apps')}['todos']['changed']

    # a basted Clair card shows in Needs your OK and in /sync's change_sets
    seq1 = get(client, '/api/sync?since=0')['seq']
    with db.transaction(ws) as c:
        cs = service.create_change_set(c, ws, 'clair', 'clair', [
            {'op': 'insert', 'app': 'todos', 'collection': 'todos',
             'fields': [{'key': 'title', 'value': 'Study for ECON 1010'}], 'reason': 'Exam Thu'}],
            title='One to-do', source={'kind': 'text', 'label': 'You said', 'at': '2026-11-20T17:45:00-07:00'})
    h = get(client, '/api/home')
    assert [c['change_set']['id'] for c in h['needsOk']] == [str(cs)]
    card = h['needsOk'][0]['change_set']
    assert card['status'] == 'basted' and card['ops'][0]['op'] == 'insert' and card['ops'][0]['ref'] == 'todos/todos'
    inc = get(client, f'/api/sync?since={seq1}')
    assert [x['id'] for x in inc['change_sets']] == [str(cs)] and inc['blocks'] == []

    # put the seed back for anyone after us
    from api.seed.load import reset_workspace
    with db.transaction(ws) as c:
        reset_workspace(c, ws, 'full')
