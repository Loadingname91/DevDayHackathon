"""The Google Calendar connection against the live database (backend.md §8a), with Google mocked by
`httpx.MockTransport` (no test reaches Google).

Each test makes one throwaway workspace named 'test-<uuid>' holding the real Calendar template, and deletes it
(cascade: its blocks, change sets, events and connection) at the end. It never touches the demo workspaces.
Skipped without DATABASE_URL.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402


def _db_ok() -> bool:
    try:
        from api.settings import settings
        return bool(settings().database_url)
    except Exception:
        return bool(os.environ.get('DATABASE_URL'))


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _db_ok(), reason='no DATABASE_URL')]

import httpx  # noqa: E402
from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

from api.auth import Member, User, current_member  # noqa: E402
from api.connect import fixture, sync  # noqa: E402
from api.db import connect  # noqa: E402
from api.index import contract_errors, validation_errors  # noqa: E402
from api.routes import connect as routes, write  # noqa: E402

TZ = 'America/Denver'
NOW = '2026-11-20T17:45:00-07:00'
NOW_DT = datetime(2026, 11, 20, 17, 45, tzinfo=timezone(__import__('datetime').timedelta(hours=-7)))
TEMPLATE = json.loads((Path(__file__).resolve().parents[1] / 'templates' / 'calendar.json').read_text())


@pytest.fixture
def env():
    with connect() as conn:
        user = conn.execute('select id from auth.users order by created_at limit 1').fetchone()
        if user is None:
            pytest.skip('no auth user to own the connection row')
        ws = conn.execute('insert into workspaces (name, tz) values (%s, %s) returning id',
                          (f'test-{uuid.uuid4()}', TZ)).fetchone()['id']
        page = {k: v for k, v in TEMPLATE.items() if k != 'collections'}
        pid = conn.execute("insert into blocks (workspace_id, position, block_type, properties) "
                           "values (%s, 'a0', 'page', %s) returning id", (ws, Jsonb(page))).fetchone()['id']
        coll = conn.execute("insert into blocks (workspace_id, parent_id, position, block_type, properties) "
                            "values (%s, %s, 'a0', 'collection', %s) returning id",
                            (ws, pid, Jsonb(TEMPLATE['collections'][0]))).fetchone()['id']
        conn.commit()
    try:
        yield SimpleNamespace(ws=ws, coll=coll, user=user['id'])
    finally:
        with connect() as conn:
            conn.execute("delete from workspaces where id = %s and name like 'test-%%'", (ws,))
            conn.commit()


@pytest.fixture
def use(monkeypatch):
    """Patch the settings the connection code reads (the database url stays real)."""
    from api.settings import settings

    def _use(**kw):
        s = settings().model_copy(update={'demo_now': NOW, 'demo_gcal_fixture': False, 'google_client_id': None,
                                          'google_client_secret': None, 'google_redirect_uri': None,
                                          'demo_gcal_email': 'demo@gmail.test', **kw})
        monkeypatch.setattr(sync, 'settings', lambda: s)
        monkeypatch.setattr(routes, 'settings', lambda: s)
        return s
    _use()
    return _use


GOOGLE = dict(google_client_id='cid.test', google_client_secret='client-secret-test',
              google_redirect_uri='https://api.test/api/connect/google/callback')


def records(env, *, deleted=False):
    with connect() as conn:
        return conn.execute(
            'select id, properties, deleted_at from blocks where workspace_id = %s and collection_id = %s '
            'and block_type = %s and (deleted_at is not null) = %s order by id', (env.ws, env.coll, 'record', deleted)).fetchall()


def google_props(env):
    return {r['properties']['ext_id']: r['properties'] for r in records(env) if r['properties'].get('source') == 'google'}


def connector_sets(env):
    with connect() as conn:
        return conn.execute("select * from change_sets where workspace_id = %s and origin = 'connector' order by created_at, id",
                            (env.ws,)).fetchall()


def conn_row(env):
    with connect() as conn:
        return conn.execute('select * from connections where workspace_id = %s', (env.ws,)).fetchone()


# ---------------------------------------------------------------- fixture mode

def test_fixture_connect_writes_the_four_events_once_and_a_second_sync_writes_nothing(env, use):
    use(demo_gcal_fixture=True)
    out = sync.connect_fixture(env.ws, env.user)
    assert (out.added, out.changed, out.removed) == (4, 0, 0)

    from api.seed.data import GOOGLE_EVENTS
    assert google_props(env) == {p['ext_id']: p for _, p in GOOGLE_EVENTS}

    assert sync.list_connections(env.ws) == [{'provider': 'google', 'account_email': 'demo@gmail.test',
                                              'last_synced_at': NOW_DT, 'needs_reconnect': False}]
    [cs] = connector_sets(env)
    assert (cs['actor'], cs['origin'], cs['status']) == ('system', 'connector', 'stitched')
    assert cs['source']['label'] == 'Google Calendar' and cs['summary'] == '4 added, 0 changed, 0 removed'

    again = sync.run_sync(env.ws)
    assert (again.added, again.changed, again.removed) == (0, 0, 0)
    assert len(connector_sets(env)) == 1          # an empty diff writes nothing

    # not offered for Undo
    from api.commands import CommandError, undo
    from api.db import transaction
    with pytest.raises(CommandError) as ei, transaction(env.ws) as conn:
        undo(conn, env.ws, cs['id'])
    assert ei.value.status == 409 and ei.value.body['error'] == 'not_undoable'


def test_fixture_row_needs_a_reconnect_once_the_flag_is_off(env, use):
    use(demo_gcal_fixture=True)
    sync.connect_fixture(env.ws, env.user)
    use(demo_gcal_fixture=False)
    assert sync.list_connections(env.ws)[0]['needs_reconnect'] is True
    with pytest.raises(sync.ConnectError) as ei:
        sync.run_sync(env.ws)
    assert ei.value.status == 409 and ei.value.body['error'] == 'needs_reconnect'
    assert len(google_props(env)) == 4            # what was imported stays


def test_sync_applies_inserts_updates_and_deletes_as_one_change_set(env, use, monkeypatch):
    use(demo_gcal_fixture=True)
    sync.connect_fixture(env.ws, env.user)
    resp = json.loads(json.dumps(fixture.GOOGLE_RESPONSE))
    by_id = {e['id']: e for e in resp}
    by_id['fixture-dentist']['summary'] = 'Dentist (moved)'
    by_id['fixture-dentist']['start'] = {'dateTime': '2026-11-24T09:00:00-07:00'}
    by_id['fixture-dentist']['end'] = {'dateTime': '2026-11-24T10:00:00-07:00'}
    by_id['fixture-thanksgiving']['end'] = {'date': '2026-11-27'}                 # now a one-day event: `ends` goes
    resp = [e for e in resp if e['id'] not in ('fixture-drive', 'fixture-back')]   # gone from the window / cancelled below
    resp.append({'id': 'new1', 'status': 'confirmed', 'summary': '', 'start': {'date': '2026-12-01'}, 'end': {'date': '2026-12-02'}})
    resp.append({'id': 'fixture-back', 'status': 'cancelled'})                     # cancelled
    monkeypatch.setattr(sync, 'GOOGLE_RESPONSE', resp)

    out = sync.run_sync(env.ws)
    assert (out.added, out.changed, out.removed) == (1, 2, 2)
    p = google_props(env)
    assert set(p) == {'fixture-dentist', 'fixture-thanksgiving', 'new1'}
    assert p['fixture-dentist']['title'] == 'Dentist (moved)' and p['fixture-dentist']['at'] == '2026-11-24T09:00:00-07:00'
    assert 'ends' not in p['fixture-thanksgiving'] and p['fixture-thanksgiving']['at'] == '2026-11-26'
    assert p['new1']['title'] == 'Busy' and p['new1']['at'] == '2026-12-01' and 'ends' not in p['new1']
    assert len(records(env, deleted=True)) == 2
    sets = connector_sets(env)
    assert len(sets) == 2 and sets[1]['summary'] == '1 added, 2 changed, 2 removed'    # one change set for the whole sync

    assert sync.run_sync(env.ws).added == 0 and len(connector_sets(env)) == 2         # the same response again: nothing


def test_more_changes_than_the_op_limit_go_in_as_several_change_sets_in_one_transaction(env, use, monkeypatch):
    use(demo_gcal_fixture=True)
    monkeypatch.setattr(sync, 'MAX_OPS', 3)
    monkeypatch.setattr(sync, 'GOOGLE_RESPONSE', [
        {'id': f'e{i}', 'status': 'confirmed', 'summary': f'Event {i}', 'start': {'date': f'2026-12-{i + 1:02d}'},
         'end': {'date': f'2026-12-{i + 2:02d}'}} for i in range(7)])
    assert sync.connect_fixture(env.ws, env.user).added == 7
    assert len(connector_sets(env)) == 3 and len(google_props(env)) == 7        # 3 + 3 + 1


def test_a_calendar_without_events_collection_is_a_clear_error_and_stores_nothing(env, use):
    use(demo_gcal_fixture=True)
    with connect() as conn:
        conn.execute("update blocks set deleted_at = now() where id = %s", (env.coll,))
        conn.commit()
    with pytest.raises(sync.ConnectError) as ei:
        sync.connect_fixture(env.ws, env.user)
    assert ei.value.status == 409 and ei.value.body['error'] == 'no_calendar'
    assert conn_row(env) is None


# ---------------------------------------------------------------- the real flow, Google mocked

class FakeGoogle:
    """A MockTransport handler that behaves like the three Google endpoints we use, and remembers what it was asked."""

    def __init__(self):
        self.events = []
        self.refresh_token = 'rt-test-1'      # what the code exchange hands out (None: a repeat consent without one)
        self.valid_refresh = {'rt-test-1', 'rt-test-2'}
        self.calls = []
        self.revoked = None
        self.fail_events = False

    def __call__(self, req: httpx.Request) -> httpx.Response:
        path = req.url.path
        self.calls.append(path)
        if path == '/token':
            form = parse_qs(req.content.decode())
            assert form['client_secret'] == ['client-secret-test']
            if form['grant_type'] == ['authorization_code']:
                body = {'access_token': 'at-1'}
                if self.refresh_token:
                    body['refresh_token'] = self.refresh_token
                return httpx.Response(200, json=body)
            if form['refresh_token'][0] not in self.valid_refresh:
                return httpx.Response(400, json={'error': 'invalid_grant'})
            return httpx.Response(200, json={'access_token': 'at-2'})
        if path == '/revoke':
            self.revoked = parse_qs(req.content.decode())['token'][0]
            return httpx.Response(200)
        assert req.headers['authorization'].startswith('Bearer at-')
        if path == '/calendar/v3/calendars/primary':
            return httpx.Response(200, json={'id': 'sam@gmail.test'})
        if path == '/calendar/v3/calendars/primary/events':
            if self.fail_events:
                return httpx.Response(503, text='try later')
            q = parse_qs(req.url.query.decode())
            assert q['timeMin'] == ['2026-11-14T00:45:00Z'] and q['timeMax'] == ['2027-01-20T00:45:00Z']   # DEMO_NOW ± 7d / 60d
            return httpx.Response(200, json={'items': self.events})
        raise AssertionError(f'unexpected call {req.method} {path}')

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self))


def gev(eid, title, start='2026-11-24T07:30:00-07:00', end='2026-11-24T08:30:00-07:00'):
    return {'id': eid, 'status': 'confirmed', 'summary': title, 'start': {'dateTime': start}, 'end': {'dateTime': end}}


def test_connect_sync_reconnect_and_disconnect_against_mocked_google(env, use):
    use(**GOOGLE)
    g = FakeGoogle()
    g.events = [gev('a', 'Dentist'), gev('b', 'Gym', '2026-11-25T18:00:00Z', '2026-11-25T19:00:00Z')]

    # the callback: code → tokens → email → first sync, stored together
    out = sync.connect_google(env.ws, env.user, 'the-code', g.client())
    assert (out.added, out.changed, out.removed) == (2, 0, 0) and out.last_synced_at == NOW_DT
    row = conn_row(env)
    assert row['account_email'] == 'sam@gmail.test' and row['refresh_token'] == 'rt-test-1' and row['user_id'] == env.user
    [pub] = sync.list_connections(env.ws)
    assert pub == {'provider': 'google', 'account_email': 'sam@gmail.test', 'last_synced_at': NOW_DT, 'needs_reconnect': False}
    assert google_props(env)['b']['at'] == '2026-11-25T11:00:00-07:00'

    # a refresh: Google moved one, cancelled one, added one
    g.events = [gev('a', 'Dentist', '2026-11-24T08:00:00-07:00', '2026-11-24T09:00:00-07:00'),
                {'id': 'b', 'status': 'cancelled'}, gev('c', 'Haircut', '2026-11-27T10:00:00-07:00', '2026-11-27T11:00:00-07:00')]
    out = sync.run_sync(env.ws, g.client())
    assert (out.added, out.changed, out.removed) == (1, 1, 1)
    assert set(google_props(env)) == {'a', 'c'}

    # the refresh token is revoked at Google: needs_reconnect, no crash, imported events stay
    g.valid_refresh = set()
    with pytest.raises(sync.ConnectError) as ei:
        sync.run_sync(env.ws, g.client())
    assert ei.value.status == 409 and ei.value.body['error'] == 'needs_reconnect'
    assert conn_row(env)['refresh_token'] == '' and sync.list_connections(env.ws)[0]['needs_reconnect'] is True
    assert set(google_props(env)) == {'a', 'c'}
    before = len(g.calls)
    with pytest.raises(sync.ConnectError):        # a dead connection doesn't call Google again
        sync.run_sync(env.ws, g.client())
    assert len(g.calls) == before

    # reconnect: a new token replaces it
    g.valid_refresh = {'rt-test-2'}
    g.refresh_token = 'rt-test-2'
    sync.connect_google(env.ws, env.user, 'code-2', g.client())
    assert conn_row(env)['refresh_token'] == 'rt-test-2' and sync.list_connections(env.ws)[0]['needs_reconnect'] is False

    # a repeat consent that carries no refresh token keeps the one we have
    g.refresh_token = None
    sync.connect_google(env.ws, env.user, 'code-3', g.client())
    assert conn_row(env)['refresh_token'] == 'rt-test-2'

    # disconnect: imported events and the row go, the token is revoked at Google
    n = len(connector_sets(env))
    sync.disconnect(env.ws, g.client())
    assert g.revoked == 'rt-test-2'
    assert conn_row(env) is None and google_props(env) == {} and sync.list_connections(env.ws) == []
    assert len(connector_sets(env)) == n + 1      # one connector change set deleted them
    with pytest.raises(sync.ConnectError) as ei:
        sync.disconnect(env.ws, g.client())
    assert ei.value.status == 404


def test_a_failed_callback_stores_nothing(env, use):
    use(**GOOGLE)
    g = FakeGoogle()
    g.events = [gev('a', 'Dentist')]
    g.fail_events = True
    with pytest.raises(sync.ConnectError) as ei:
        sync.connect_google(env.ws, env.user, 'c', g.client())
    assert ei.value.status == 502 and ei.value.body['error'] == 'google_unavailable'
    assert conn_row(env) is None and google_props(env) == {} and connector_sets(env) == []

    g.fail_events, g.refresh_token = False, None          # first consent but no refresh token: also nothing
    with pytest.raises(sync.ConnectError):
        sync.connect_google(env.ws, env.user, 'c', g.client())
    assert conn_row(env) is None and google_props(env) == {}


def test_not_configured_and_no_connection_errors(env, use):
    with pytest.raises(sync.ConnectError) as ei:
        sync.connect_google(env.ws, env.user, 'c', FakeGoogle().client())
    assert ei.value.status == 503 and ei.value.body['error'] == 'google_not_configured'
    with pytest.raises(sync.ConnectError) as ei:
        sync.run_sync(env.ws)
    assert ei.value.status == 404
    assert sync.list_connections(env.ws) == []


# ---------------------------------------------------------------- reset hook

def test_after_reset_restamps_a_fixture_connection_and_never_raises(env, use):
    use(demo_gcal_fixture=True)
    sync.after_reset(env.ws)                      # no connection: nothing happens
    assert conn_row(env) is None
    sync.connect_fixture(env.ws, env.user)
    with connect() as conn:
        conn.execute("update connections set last_synced_at = '2020-01-01T00:00:00Z' where workspace_id = %s", (env.ws,))
        conn.commit()
    sync.after_reset(env.ws)
    assert conn_row(env)['last_synced_at'] == NOW_DT
    use(demo_gcal_fixture=False)                  # a fixture row with the flag off: the sync is refused, the reset still works
    sync.after_reset(env.ws)


# ---------------------------------------------------------------- through the routes

def make_client(env, g: FakeGoogle | None = None) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.add_exception_handler(RequestValidationError, validation_errors)
    api = APIRouter(prefix='/api')
    api.include_router(routes.router)
    api.include_router(write.router)
    app.include_router(api)
    app.dependency_overrides[current_member] = lambda: Member(user=User(env.user, False, None), workspace_id=env.ws, tz=TZ)
    if g:
        app.dependency_overrides[routes.google_http] = g.client
    return TestClient(app, follow_redirects=False)


def test_routes_in_fixture_mode_and_google_records_are_read_only(env, use):
    use(demo_gcal_fixture=True)
    tc = make_client(env)
    assert tc.get('/api/connect').json() == []

    r = tc.post('/api/connect/google/start')
    assert r.status_code == 200 and r.json() == {'url': '/app/calendar?connected=google', 'connected': True}
    r = tc.get('/api/connect')
    [c] = r.json()
    assert c['provider'] == 'google' and c['account_email'] == 'demo@gmail.test' and c['needs_reconnect'] is False
    assert 'refresh_token' not in r.text and 'fixture' not in r.text

    r = tc.post('/api/connect/google/sync')
    assert r.status_code == 200 and (r.json()['added'], r.json()['changed'], r.json()['removed']) == (0, 0, 0)

    # read-only: a gesture on a Google record is 422 from_google
    rec = next(r for r in records(env) if r['properties'].get('source') == 'google')
    r = tc.patch(f"/api/records/{rec['id']}", json={'fields': {'title': 'Nope'}, 'base_version': 1})
    assert r.status_code == 422 and r.json()['error'] == 'from_google'
    r = tc.delete(f"/api/records/{rec['id']}")
    assert r.status_code == 422 and r.json()['error'] == 'from_google'
    r = tc.post('/api/records', json={'collection_id': str(env.coll), 'fields': {'title': 'Fake', 'source': 'google'}})
    assert r.status_code == 422 and r.json()['error'] == 'from_google'
    assert len(google_props(env)) == 4 and records(env, deleted=True) == []

    # an ordinary event is still editable, and the sync leaves it alone
    r = tc.post('/api/records', json={'collection_id': str(env.coll), 'fields': {'title': 'Coffee', 'at': '2026-11-21T10:00'}})
    assert r.status_code == 201
    assert tc.post('/api/connect/google/sync').json()['removed'] == 0

    # the activity list copes with a connector change set
    assert tc.get('/api/change-sets').status_code == 200

    # disconnect (fixture mode: no Google call)
    assert tc.delete('/api/connect/google').status_code == 204
    assert tc.get('/api/connect').json() == [] and google_props(env) == {}
    assert tc.post('/api/connect/google/sync').status_code == 404
    assert tc.delete('/api/connect/google').status_code == 404
    assert [r['properties']['title'] for r in records(env)] == ['Coffee']


def test_routes_not_configured(env, use):
    tc = make_client(env)
    assert tc.get('/api/connect').json() == []
    r = tc.post('/api/connect/google/start')
    assert r.status_code == 503 and r.json()['error'] == 'google_not_configured'
    assert tc.post('/api/connect/google/sync').status_code == 404


def _state_from(tc) -> str:
    from urllib.parse import urlparse
    return parse_qs(urlparse(tc.post('/api/connect/google/start').json()['url']).query)['state'][0]


def test_callback_connects_only_a_member_of_the_workspace_in_the_state(env, use):
    use(**GOOGLE, web_origin='https://quilt.test')
    g = FakeGoogle()
    g.events = [gev('a', 'Dentist'), gev('b', 'Gym')]
    tc = make_client(env, g)
    state = _state_from(tc)

    # the throwaway workspace has no member, so the state's user does not belong to it: refused, nothing stored
    assert sync.is_member(env.ws, env.user) is False
    r = tc.get('/api/connect/google/callback', params={'code': 'the-code', 'state': state})
    assert r.status_code == 302 and r.headers['location'] == 'https://quilt.test/app/calendar?connected=failed'
    assert conn_row(env) is None and google_props(env) == {} and g.calls == []

    sync_is_member = sync.is_member
    try:
        sync.is_member = lambda ws, user: True
        r = tc.get('/api/connect/google/callback', params={'code': 'the-code', 'state': state})
    finally:
        sync.is_member = sync_is_member
    assert r.headers['location'] == 'https://quilt.test/app/calendar?connected=google'
    assert conn_row(env)['account_email'] == 'sam@gmail.test' and len(google_props(env)) == 2

    # the person said no at Google: back to Calendar with failed, nothing changes
    r = tc.get('/api/connect/google/callback', params={'error': 'access_denied', 'state': state})
    assert r.headers['location'] == 'https://quilt.test/app/calendar?connected=failed'
    assert len(google_props(env)) == 2
