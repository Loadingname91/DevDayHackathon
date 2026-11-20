"""Google Calendar connection, no database and no network (backend.md §8a): state signing, the event mapping,
the diff, the HTTP calls against `httpx.MockTransport`, and the routes with the database layer stubbed.
Google is never contacted: every test that reaches an HTTP call uses a MockTransport client."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.auth import Member, User, current_member  # noqa: E402
from api.connect import fixture, google as G, sync  # noqa: E402
from api.index import contract_errors, validation_errors  # noqa: E402
from api.logic.clock import now as clock_now  # noqa: E402
from api.routes import connect as routes  # noqa: E402

TZ = 'America/Denver'
CFG = G.GoogleConfig('cid.apps.test', 'SECRET-VALUE-XYZ', 'https://api.test/api/connect/google/callback')
SECRET = 'state-secret-for-tests'


# ---------------------------------------------------------------- state

def test_state_round_trip():
    u, w = uuid4(), uuid4()
    s = G.sign_state(SECRET, u, w, now=1000)
    assert G.verify_state(SECRET, s, now=1100) == (u, w)


def test_state_rejects_tampering_expiry_and_garbage():
    u, w = uuid4(), uuid4()
    s = G.sign_state(SECRET, u, w, ttl=600, now=1000)
    body, mac = s.split('.')
    forged = G.sign_state(SECRET, uuid4(), w, now=1000).split('.')[0]
    for bad in (None, '', 'abc', 'a.b.c', f'{forged}.{mac}', f'{body}.{mac[:-2]}xx', s.replace('.', 'x', 1)):
        with pytest.raises(G.StateError):
            G.verify_state(SECRET, bad, now=1100)
    with pytest.raises(G.StateError, match='bad signature'):
        G.verify_state('another-secret', s, now=1100)
    with pytest.raises(G.StateError, match='expired'):
        G.verify_state(SECRET, s, now=1000 + 601)
    G.verify_state(SECRET, s, now=1000 + 599)


def test_state_nonce_makes_every_state_different():
    u, w = uuid4(), uuid4()
    assert G.sign_state(SECRET, u, w, now=1) != G.sign_state(SECRET, u, w, now=1)


def test_consent_url_has_the_flow_parameters():
    q = parse_qs(urlparse(G.consent_url(CFG, 'ST')).query)
    assert urlparse(G.consent_url(CFG, 'ST')).netloc == 'accounts.google.com'
    assert q['scope'] == ['https://www.googleapis.com/auth/calendar.readonly']
    assert q['access_type'] == ['offline'] and q['prompt'] == ['consent'] and q['response_type'] == ['code']
    assert q['client_id'] == [CFG.client_id] and q['redirect_uri'] == [CFG.redirect_uri] and q['state'] == ['ST']
    assert 'client_secret' not in q


def test_config_from_needs_all_three_and_hides_the_secret():
    s = SimpleNamespace(google_client_id='a', google_client_secret='b', google_redirect_uri='c')
    assert G.config_from(s) == G.GoogleConfig('a', 'b', 'c')
    for k in ('google_client_id', 'google_client_secret', 'google_redirect_uri'):
        assert G.config_from(SimpleNamespace(**{**vars(s), k: None})) is None
        assert G.config_from(SimpleNamespace(**{**vars(s), k: ''})) is None
    assert 'SECRET-VALUE-XYZ' not in repr(CFG) and 'SECRET-VALUE-XYZ' not in str(CFG)


# ---------------------------------------------------------------- mapping

def ev(eid='e1', summary='Dentist', start=None, end=None, **kw):
    return {'id': eid, 'status': 'confirmed', 'summary': summary,
            'start': start or {'dateTime': '2026-11-24T07:30:00-07:00'},
            'end': end or {'dateTime': '2026-11-24T08:30:00-07:00'}, **kw}


def test_timed_event():
    f = G.map_event(ev(), TZ)
    assert f == {'title': 'Dentist', 'at': '2026-11-24T07:30:00-07:00', 'ends': '2026-11-24T08:30:00-07:00',
                 'source': 'google', 'ext_id': 'e1'}


def test_timed_event_in_utc_and_other_zones_lands_in_the_workspace_zone():
    f = G.map_event(ev(start={'dateTime': '2026-11-25T03:00:00Z'}, end={'dateTime': '2026-11-25T04:00:00Z'}), TZ)
    assert f['at'] == '2026-11-24T20:00:00-07:00' and f['ends'] == '2026-11-24T21:00:00-07:00'   # the 24th, not the 25th
    f = G.map_event(ev(start={'dateTime': '2026-11-24T15:30:00+01:00'}, end={'dateTime': '2026-11-24T16:30:00+01:00'}), TZ)
    assert f['at'] == '2026-11-24T07:30:00-07:00'


def test_dateTime_without_offset_uses_the_event_zone_then_the_workspace_zone():
    f = G.map_event(ev(start={'dateTime': '2026-11-24T09:30:00', 'timeZone': 'America/New_York'},
                       end={'dateTime': '2026-11-24T10:30:00', 'timeZone': 'America/New_York'}), TZ)
    assert f['at'] == '2026-11-24T07:30:00-07:00'
    f = G.map_event(ev(start={'dateTime': '2026-11-24T07:30:00'}, end={'dateTime': '2026-11-24T08:30:00'}), TZ)
    assert f['at'] == '2026-11-24T07:30:00-07:00'


def test_all_day_event_stores_the_day_before_google_exclusive_end():
    f = G.map_event(ev('t', 'Thanksgiving at home', {'date': '2026-11-26'}, {'date': '2026-11-29'}), TZ)
    assert f['at'] == '2026-11-26' and f['ends'] == '2026-11-28'


def test_one_day_all_day_event_has_no_ends():
    f = G.map_event(ev('t', 'Holiday', {'date': '2026-11-26'}, {'date': '2026-11-27'}), TZ)
    assert f['at'] == '2026-11-26' and 'ends' not in f
    f = G.map_event(ev('t', 'Holiday', {'date': '2026-11-26'}, {}), TZ)   # no end at all
    assert f['at'] == '2026-11-26' and 'ends' not in f


def test_empty_title_is_busy():
    for summary in ('', '   ', None):
        assert G.map_event(ev(summary=summary), TZ)['title'] == 'Busy'
    e = ev()
    del e['summary']
    assert G.map_event(e, TZ)['title'] == 'Busy'
    assert G.map_event(ev(summary='  Lunch  '), TZ)['title'] == 'Lunch'


def test_unmappable_events_are_skipped():
    assert G.map_event({'status': 'confirmed', 'summary': 'x', 'start': {'date': '2026-11-26'}}, TZ) is None   # no id
    assert G.map_event({'id': 'x', 'summary': 'x'}, TZ) is None                                              # no start
    assert G.map_event(ev(start={'dateTime': 'not a date'}), TZ) is None


def test_description_attendees_location_are_not_stored():
    f = G.map_event(ev(description='secret plans', location='Dentist office', attendees=[{'email': 'a@b.c'}],
                       htmlLink='https://x'), TZ)
    assert set(f) == {'title', 'at', 'ends', 'source', 'ext_id'}


def test_map_events_splits_live_and_cancelled():
    items = [ev('a'), {'id': 'b', 'status': 'cancelled'}, ev('c', 'Gym'), {'status': 'cancelled'}, ev('d', start={'timeZone': 'UTC'})]
    live, cancelled = G.map_events(items, TZ)
    assert set(live) == {'a', 'c'} and cancelled == {'b'}


def test_dst_fall_back_two_distinct_1_30_am():
    # Sun 1 Nov 2026: Denver goes from MDT (-06:00) to MST (-07:00) at 2:00 am, so 1:30 am happens twice.
    first = G.map_event(ev(start={'dateTime': '2026-11-01T07:30:00Z'}, end={'dateTime': '2026-11-01T08:00:00Z'}), TZ)
    second = G.map_event(ev(start={'dateTime': '2026-11-01T08:30:00Z'}, end={'dateTime': '2026-11-01T09:00:00Z'}), TZ)
    assert first['at'] == '2026-11-01T01:30:00-06:00' and second['at'] == '2026-11-01T01:30:00-07:00'
    assert first['at'] != second['at']
    # and the day after the change keeps its wall time under the new offset
    assert G.map_event(ev(start={'dateTime': '2026-11-02T07:30:00-07:00'}, end={'dateTime': '2026-11-02T08:00:00-07:00'}),
                       TZ)['at'] == '2026-11-02T07:30:00-07:00'


def test_dst_spring_forward_and_an_event_across_it():
    # Sun 8 Mar 2026: 2:00 am MST jumps to 3:00 am MDT. 09:00Z is 3:00 am MDT.
    f = G.map_event(ev(start={'dateTime': '2026-03-08T09:00:00Z'}, end={'dateTime': '2026-03-08T10:00:00Z'}), TZ)
    assert f['at'] == '2026-03-08T03:00:00-06:00' and f['ends'] == '2026-03-08T04:00:00-06:00'
    f = G.map_event(ev(start={'dateTime': '2026-03-08T00:30:00-07:00'}, end={'dateTime': '2026-03-08T03:30:00-06:00'}), TZ)
    assert f['at'] == '2026-03-08T00:30:00-07:00' and f['ends'] == '2026-03-08T03:30:00-06:00'


def test_all_day_event_on_a_dst_day_is_just_days():
    f = G.map_event(ev('x', 'Clocks', {'date': '2026-11-01'}, {'date': '2026-11-02'}), TZ)
    assert f['at'] == '2026-11-01' and 'ends' not in f


def test_window_is_7_days_before_to_60_days_after_the_workspace_clock():
    now = clock_now(TZ, '2026-11-20T17:45:00-07:00')
    lo, hi = G.window(now)
    assert lo.astimezone(timezone.utc) == datetime(2026, 11, 14, 0, 45, tzinfo=timezone.utc)
    assert hi.astimezone(timezone.utc) == datetime(2027, 1, 20, 0, 45, tzinfo=timezone.utc)
    assert (lo.date().isoformat(), hi.date().isoformat()) == ('2026-11-13', '2027-01-19')


# ---------------------------------------------------------------- the diff

CID = str(uuid4())


def stored(rid, ext, title='Dentist', at='2026-11-24T07:30:00-07:00', ends='2026-11-24T08:30:00-07:00'):
    p = {'title': title, 'at': at, 'source': 'google', 'ext_id': ext}
    if ends:
        p['ends'] = ends
    return {'id': rid, 'properties': p}


def want(ext, title='Dentist', at='2026-11-24T07:30:00-07:00', ends='2026-11-24T08:30:00-07:00'):
    f = {'title': title, 'at': at, 'source': 'google', 'ext_id': ext}
    if ends:
        f['ends'] = ends
    return f


def test_diff_nothing_changed_is_an_empty_diff():
    ops, counts = G.diff([stored('r1', 'a')], {'a': want('a')}, set(), TZ, collection_id=CID)
    assert ops == [] and counts == {'added': 0, 'changed': 0, 'removed': 0}


def test_diff_same_instant_in_another_offset_is_not_a_change():
    ops, _ = G.diff([stored('r1', 'a', at='2026-11-24T14:30:00+00:00', ends='2026-11-24T15:30:00Z')],
                    {'a': want('a')}, set(), TZ, collection_id=CID)
    assert ops == []


def test_diff_insert_update_delete_in_one_pass():
    existing = [stored('r1', 'a'), stored('r2', 'b', title='Old'), stored('r3', 'c')]
    live = {'a': want('a'), 'b': want('b', title='New', at='2026-11-24T09:00:00-07:00'), 'd': want('d', title='Gym')}
    ops, counts = G.diff(existing, live, {'c'}, TZ, collection_id=CID)
    assert counts == {'added': 1, 'changed': 1, 'removed': 1}
    assert ops[0] == {'op': 'delete', 'record_id': 'r3'}
    assert ops[1] == {'op': 'update', 'record_id': 'r2', 'fields': {'title': 'New', 'at': '2026-11-24T09:00:00-07:00'}}
    assert ops[2]['op'] == 'insert' and ops[2]['collection_id'] == CID and ops[2]['fields']['ext_id'] == 'd'
    assert ops[2]['fields']['source'] == 'google'


def test_diff_update_carries_only_the_changed_fields_and_clears_ends_with_none():
    ops, _ = G.diff([stored('r1', 'a')], {'a': want('a', ends=None)}, set(), TZ, collection_id=CID)
    assert ops == [{'op': 'update', 'record_id': 'r1', 'fields': {'ends': None}}]
    ops, _ = G.diff([stored('r1', 'a', ends=None)], {'a': want('a')}, set(), TZ, collection_id=CID)
    assert ops == [{'op': 'update', 'record_id': 'r1', 'fields': {'ends': '2026-11-24T08:30:00-07:00'}}]


def test_diff_a_timed_event_made_all_day_is_a_change():
    ops, _ = G.diff([stored('r1', 'a')], {'a': want('a', at='2026-11-24', ends=None)}, set(), TZ, collection_id=CID)
    assert ops == [{'op': 'update', 'record_id': 'r1', 'fields': {'at': '2026-11-24', 'ends': None}}]


def test_diff_duplicates_and_records_without_an_ext_id_are_deleted():
    existing = [stored('r1', 'a'), stored('r2', 'a'), {'id': 'r3', 'properties': {'title': 'x', 'source': 'google'}}]
    ops, counts = G.diff(existing, {'a': want('a')}, set(), TZ, collection_id=CID)
    assert ops == [{'op': 'delete', 'record_id': 'r2'}, {'op': 'delete', 'record_id': 'r3'}]
    assert counts['removed'] == 2


def test_diff_empty_window_deletes_everything_stored():
    ops, counts = G.diff([stored('r1', 'a'), stored('r2', 'b')], {}, set(), TZ, collection_id=CID)
    assert [o['op'] for o in ops] == ['delete', 'delete'] and counts['removed'] == 2


def test_diff_inserts_come_in_start_order():
    live = {'z': want('z', at='2026-11-23T09:00:00-07:00'), 'y': want('y', at='2026-11-22T09:00:00-07:00'), 'x': want('x', at='2026-11-26', ends=None)}
    ops, _ = G.diff([], live, set(), TZ, collection_id=CID)
    assert [o['fields']['ext_id'] for o in ops] == ['y', 'z', 'x']


def test_the_fixture_is_the_seed():
    """The fixture Google response, mapped, equals the four records the seed writes with DEMO_GCAL_FIXTURE=1."""
    from api.seed.data import GOOGLE_EVENTS
    live, cancelled = G.map_events(fixture.GOOGLE_RESPONSE, TZ)
    assert cancelled == set()
    seeded = {p['ext_id']: p for _, p in GOOGLE_EVENTS}
    assert live == seeded
    ops, _ = G.diff([{'id': f'r-{k}', 'properties': p} for k, p in seeded.items()], live, set(), TZ, collection_id=CID)
    assert ops == []   # syncing right after a fixture seed changes nothing


# ---------------------------------------------------------------- the HTTP calls (MockTransport, never Google)

def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_exchange_code_posts_the_form_and_returns_both_tokens():
    seen = {}

    def handler(req: httpx.Request):
        seen['url'], seen['form'] = str(req.url), parse_qs(req.content.decode())
        return httpx.Response(200, json={'access_token': 'at-1', 'refresh_token': 'rt-1', 'expires_in': 3599})

    t = G.exchange_code(client_for(handler), CFG, 'the-code')
    assert (t.access_token, t.refresh_token) == ('at-1', 'rt-1')
    assert seen['url'] == G.TOKEN_URL
    assert seen['form']['code'] == ['the-code'] and seen['form']['grant_type'] == ['authorization_code']
    assert seen['form']['redirect_uri'] == [CFG.redirect_uri] and seen['form']['client_secret'] == [CFG.client_secret]
    # a repeat consent may carry no refresh token
    t = G.exchange_code(client_for(lambda r: httpx.Response(200, json={'access_token': 'at-2'})), CFG, 'c')
    assert t.refresh_token is None


def test_refresh_invalid_grant_is_its_own_error_and_leaks_no_token():
    def handler(req):
        return httpx.Response(400, json={'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})

    with pytest.raises(G.GoogleError) as ei:
        G.refresh_access_token(client_for(handler), CFG, 'rt-secret-value')
    assert ei.value.code == 'invalid_grant'
    assert 'rt-secret-value' not in str(ei.value) and CFG.client_secret not in str(ei.value)


def test_other_failures_are_rejected_or_unavailable():
    def refresh(client):
        return G.refresh_access_token(client, CFG, 'rt')

    with pytest.raises(G.GoogleError) as ei:
        refresh(client_for(lambda r: httpx.Response(401, json={'error': 'invalid_client'})))
    assert ei.value.code == 'rejected'
    for status in (429, 500, 503):
        with pytest.raises(G.GoogleError) as ei:
            refresh(client_for(lambda r, s=status: httpx.Response(s, text='busy')))
        assert ei.value.code == 'unavailable'

    def boom(req):
        raise httpx.ConnectError('no route', request=req)

    with pytest.raises(G.GoogleError) as ei:
        refresh(client_for(boom))
    assert ei.value.code == 'unavailable'
    with pytest.raises(G.GoogleError) as ei:
        refresh(client_for(lambda r: httpx.Response(200, text='<html>')))
    assert ei.value.code == 'bad_response'
    with pytest.raises(G.GoogleError) as ei:
        refresh(client_for(lambda r: httpx.Response(200, json={'nope': 1})))
    assert ei.value.code == 'bad_response'


def test_primary_email_is_the_primary_calendar_id():
    def handler(req):
        assert req.url.path == '/calendar/v3/calendars/primary' and req.headers['authorization'] == 'Bearer at-1'
        return httpx.Response(200, json={'id': 'sam@gmail.test', 'summary': 'Sam'})

    assert G.primary_email(client_for(handler), 'at-1') == 'sam@gmail.test'
    with pytest.raises(G.GoogleError):
        G.primary_email(client_for(lambda r: httpx.Response(200, json={})), 'at')
    with pytest.raises(G.GoogleError) as ei:
        G.primary_email(client_for(lambda r: httpx.Response(403, json={'error': {'status': 'PERMISSION_DENIED'}})), 'at')
    assert ei.value.code == 'rejected' and 'PERMISSION_DENIED' in str(ei.value)


def test_list_events_asks_for_the_window_expanded_with_cancelled_and_follows_pages():
    calls = []

    def handler(req: httpx.Request):
        q = parse_qs(req.url.query.decode())
        calls.append(q)
        assert req.url.path == '/calendar/v3/calendars/primary/events' and req.headers['authorization'] == 'Bearer at-1'
        if 'pageToken' not in q:
            return httpx.Response(200, json={'items': [ev('a')], 'nextPageToken': 'p2'})
        assert q['pageToken'] == ['p2']
        return httpx.Response(200, json={'items': [ev('b'), {'id': 'c', 'status': 'cancelled'}]})

    lo = datetime(2026, 11, 13, 17, 45, tzinfo=timezone.utc)
    hi = datetime(2027, 1, 19, 17, 45, tzinfo=timezone.utc)
    items = G.list_events(client_for(handler), 'at-1', lo, hi)
    assert [e['id'] for e in items] == ['a', 'b', 'c'] and len(calls) == 2
    q = calls[0]
    assert q['singleEvents'] == ['true'] and q['showDeleted'] == ['true']
    assert q['timeMin'] == ['2026-11-13T17:45:00Z'] and q['timeMax'] == ['2027-01-19T17:45:00Z']


def test_revoke_is_best_effort():
    seen = {}

    def ok(req):
        seen['form'] = parse_qs(req.content.decode())
        return httpx.Response(200)

    assert G.revoke(client_for(ok), 'rt-1') is True and seen['form'] == {'token': ['rt-1']}
    assert G.revoke(client_for(lambda r: httpx.Response(400)), 'rt-1') is False

    def boom(req):
        raise httpx.ConnectError('down', request=req)

    assert G.revoke(client_for(boom), 'rt-1') is False


# ---------------------------------------------------------------- the row as a client sees it

def row(token='rt-secret', email='sam@gmail.test', at=None):
    return {'account_email': email, 'refresh_token': token, 'last_synced_at': at or datetime(2026, 11, 20, 17, 45, tzinfo=timezone.utc)}


def fake_settings(**kw):
    base = dict(web_origin='https://quilt.test', connect_state_secret=SECRET, supabase_service_role_key='service-role',
                google_client_id=None, google_client_secret=None, google_redirect_uri=None, demo_gcal_fixture=False,
                demo_gcal_email='demo@gmail.test', demo_now='2026-11-20T17:45:00-07:00', version='0')
    return SimpleNamespace(**{**base, **kw})


@pytest.fixture
def cfg(monkeypatch):
    """Patch the settings both modules read; returns a function to change them."""
    def use(**kw):
        s = fake_settings(**kw)
        monkeypatch.setattr(routes, 'settings', lambda: s)
        monkeypatch.setattr(sync, 'settings', lambda: s)
        return s
    use()
    return use


def test_public_row_never_carries_the_token_and_flags_needs_reconnect(cfg):
    p = sync.public(row())
    assert p == {'provider': 'google', 'account_email': 'sam@gmail.test', 'needs_reconnect': False,
                 'last_synced_at': datetime(2026, 11, 20, 17, 45, tzinfo=timezone.utc)}
    assert 'rt-secret' not in str(p)
    assert sync.public(row(token=''))['needs_reconnect'] is True            # a dead token is stored as ''
    assert sync.public(row(token=fixture.FIXTURE_TOKEN))['needs_reconnect'] is True   # a fixture row, flag off
    cfg(demo_gcal_fixture=True)
    assert sync.public(row(token=fixture.FIXTURE_TOKEN))['needs_reconnect'] is False


# ---------------------------------------------------------------- the routes (database layer stubbed)

WS, USER = uuid4(), uuid4()


def make_client(monkeypatch, http_handler=None):
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.add_exception_handler(RequestValidationError, validation_errors)
    from fastapi import APIRouter
    api = APIRouter(prefix='/api')
    api.include_router(routes.router)
    app.include_router(api)
    app.dependency_overrides[current_member] = lambda: Member(user=User(USER, False, None), workspace_id=WS, tz=TZ)
    if http_handler:
        app.dependency_overrides[routes.google_http] = lambda: client_for(http_handler)
    return TestClient(app, follow_redirects=False)


def outcome(a=0, c=0, r=0):
    return sync.Outcome(a, c, r, datetime(2026, 11, 20, 17, 45, tzinfo=timezone.utc))


def test_list_is_empty_when_not_connected_and_has_no_token_when_connected(monkeypatch, cfg):
    tc = make_client(monkeypatch)
    monkeypatch.setattr(sync, 'list_connections', lambda ws: [])
    r = tc.get('/api/connect')
    assert r.status_code == 200 and r.json() == []
    monkeypatch.setattr(sync, 'list_connections', lambda ws: [sync.public(row())])
    r = tc.get('/api/connect')
    assert r.json() == [{'provider': 'google', 'account_email': 'sam@gmail.test',
                         'last_synced_at': '2026-11-20T17:45:00Z', 'needs_reconnect': False}]
    assert 'rt-secret' not in r.text


def test_start_not_configured_is_503(monkeypatch, cfg):
    r = make_client(monkeypatch).post('/api/connect/google/start')
    assert r.status_code == 503 and r.json()['error'] == 'google_not_configured'


def test_start_configured_returns_the_consent_url_with_a_verifiable_state(monkeypatch, cfg):
    cfg(google_client_id=CFG.client_id, google_client_secret=CFG.client_secret, google_redirect_uri=CFG.redirect_uri)
    r = make_client(monkeypatch).post('/api/connect/google/start')
    assert r.status_code == 200 and 'connected' not in r.json() or r.json()['connected'] is None
    q = parse_qs(urlparse(r.json()['url']).query)
    assert q['scope'] == [G.SCOPE] and q['access_type'] == ['offline'] and q['prompt'] == ['consent']
    assert G.verify_state(SECRET, q['state'][0]) == (USER, WS)
    assert CFG.client_secret not in r.text


def test_state_falls_back_to_the_service_role_key_when_no_state_secret(monkeypatch, cfg):
    cfg(google_client_id='a', google_client_secret='b', google_redirect_uri='https://x/cb', connect_state_secret=None)
    r = make_client(monkeypatch).post('/api/connect/google/start')
    q = parse_qs(urlparse(r.json()['url']).query)
    assert G.verify_state('service-role', q['state'][0]) == (USER, WS)


def test_start_in_fixture_mode_connects_the_demo_without_google(monkeypatch, cfg):
    cfg(demo_gcal_fixture=True)
    calls = []
    monkeypatch.setattr(sync, 'connect_fixture', lambda ws, user: calls.append((ws, user)) or outcome(4))

    def no_google(req):
        raise AssertionError('fixture mode must not call Google')

    r = make_client(monkeypatch, no_google).post('/api/connect/google/start')
    assert r.status_code == 200 and r.json() == {'url': '/app/calendar?connected=google', 'connected': True}
    assert calls == [(WS, USER)]


def test_fixture_wins_when_google_is_also_configured(monkeypatch, cfg):
    cfg(demo_gcal_fixture=True, google_client_id='a', google_client_secret='b', google_redirect_uri='c')
    monkeypatch.setattr(sync, 'connect_fixture', lambda ws, user: outcome(4))
    assert make_client(monkeypatch).post('/api/connect/google/start').json()['connected'] is True


def test_callback_bad_requests_go_back_to_calendar_with_failed(monkeypatch, cfg):
    cfg(google_client_id='a', google_client_secret='b', google_redirect_uri='c')
    monkeypatch.setattr(sync, 'connect_google', lambda *a, **k: pytest.fail('must not connect'))
    tc = make_client(monkeypatch)
    good = G.sign_state(SECRET, USER, WS)
    expired = G.sign_state(SECRET, USER, WS, now=1)
    for qs in ('', '?code=c', '?state=' + good, '?error=access_denied&state=' + good, '?code=c&state=garbage',
               '?code=c&state=' + expired, '?code=c&state=' + G.sign_state('other', USER, WS)):
        r = tc.get('/api/connect/google/callback' + qs)
        assert r.status_code == 302 and r.headers['location'] == 'https://quilt.test/app/calendar?connected=failed', qs


def test_callback_good_state_connects_and_redirects(monkeypatch, cfg):
    cfg(google_client_id='a', google_client_secret='b', google_redirect_uri='c')
    seen = []
    monkeypatch.setattr(sync, 'is_member', lambda ws, user: True)
    monkeypatch.setattr(sync, 'connect_google', lambda ws, user, code, client=None: seen.append((ws, user, code)) or outcome(4))
    r = make_client(monkeypatch).get('/api/connect/google/callback', params={'code': 'abc', 'state': G.sign_state(SECRET, USER, WS)})
    assert r.status_code == 302 and r.headers['location'] == 'https://quilt.test/app/calendar?connected=google'
    assert seen == [(WS, USER, 'abc')]


def test_callback_for_someone_who_left_the_workspace_or_a_google_failure_is_failed(monkeypatch, cfg):
    cfg(google_client_id='a', google_client_secret='b', google_redirect_uri='c')
    st = G.sign_state(SECRET, USER, WS)
    tc = make_client(monkeypatch)
    monkeypatch.setattr(sync, 'is_member', lambda ws, user: False)
    assert tc.get('/api/connect/google/callback', params={'code': 'c', 'state': st}).headers['location'].endswith('failed')
    monkeypatch.setattr(sync, 'is_member', lambda ws, user: True)

    def refused(*a, **k):
        raise sync.ConnectError(502, 'google_unavailable')

    def crash(*a, **k):
        raise RuntimeError('database exploded')

    for boom in (refused, crash):
        monkeypatch.setattr(sync, 'connect_google', boom)
        r = tc.get('/api/connect/google/callback', params={'code': 'c', 'state': st})
        assert r.status_code == 302 and r.headers['location'].endswith('?connected=failed')


def test_sync_route_result_and_errors(monkeypatch, cfg):
    tc = make_client(monkeypatch, lambda req: httpx.Response(500))
    monkeypatch.setattr(sync, 'run_sync', lambda ws, client=None: outcome(1, 2, 3))
    r = tc.post('/api/connect/google/sync')
    assert r.status_code == 200 and r.json() == {'added': 1, 'changed': 2, 'removed': 3, 'last_synced_at': '2026-11-20T17:45:00Z'}
    for err, status in ((sync.needs_reconnect_error(), 409), (sync.ConnectError(404, 'not_found'), 404),
                        (sync.ConnectError(502, 'google_unavailable'), 502)):
        monkeypatch.setattr(sync, 'run_sync', lambda ws, client=None, e=err: (_ for _ in ()).throw(e))
        r = tc.post('/api/connect/google/sync')
        assert r.status_code == status and r.json()['error'] == err.body['error']


def test_disconnect_route(monkeypatch, cfg):
    tc = make_client(monkeypatch, lambda req: httpx.Response(200))
    monkeypatch.setattr(sync, 'disconnect', lambda ws, client=None: None)
    assert tc.delete('/api/connect/google').status_code == 204
    monkeypatch.setattr(sync, 'disconnect', lambda ws, client=None: (_ for _ in ()).throw(sync.ConnectError(404, 'not_found')))
    r = tc.delete('/api/connect/google')
    assert r.status_code == 404 and r.json()['error'] == 'not_found'
