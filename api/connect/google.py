"""Google Calendar, read-only (backend.md §8a): OAuth authorization-code flow, `events.list`, and the mapping of a
Google event to a `calendar/events` record. No database and no settings in here: every function takes what it needs,
so the tests run it with `httpx.MockTransport` and never reach Google.

Everything Google-specific is from Google's documentation as of this writing; confirm in the OAuth spike (§8a).

Nothing in this module logs or returns a token or the client secret. Errors carry Google's own `error` code only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx

from ..logic.clock import iso, parse_value, to_local

SCOPE = 'https://www.googleapis.com/auth/calendar.readonly'
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REVOKE_URL = 'https://oauth2.googleapis.com/revoke'
CALENDAR_API = 'https://www.googleapis.com/calendar/v3'

PROVIDER_DB = 'google_calendar'   # connections.provider
PROVIDER_API = 'google'           # what the client matches on (web/src/api/types.ts Connection)
SOURCE = 'google'                 # records' `source`
WINDOW_BEFORE = timedelta(days=7)
WINDOW_AFTER = timedelta(days=60)
STATE_TTL = 600                   # seconds (§8a: 10 minutes)
MAX_PAGES = 20                    # 5000 events at 250 a page; a safety stop, not a limit anyone should reach


# ---------------------------------------------------------------- errors and config

class GoogleError(Exception):
    """A Google call failed. `code`: `invalid_grant` (the refresh token is revoked or expired: reconnect),
    `unavailable` (network, 5xx, 429), `rejected` (any other refusal: bad client, API off, no access),
    `bad_response`. The message never holds a token or a secret."""

    def __init__(self, code: str, detail: str = ''):
        super().__init__(f'{code}: {detail}' if detail else code)
        self.code = code


@dataclass(frozen=True)
class GoogleConfig:
    client_id: str
    client_secret: str
    redirect_uri: str

    def __repr__(self) -> str:  # never let the secret reach a log line or a traceback
        return f'GoogleConfig(client_id={self.client_id!r}, client_secret=***, redirect_uri={self.redirect_uri!r})'


def config_from(s: Any) -> GoogleConfig | None:
    """The three settings as one object, or None when any is missing or empty ("not configured")."""
    cid, sec, uri = (getattr(s, k, None) for k in ('google_client_id', 'google_client_secret', 'google_redirect_uri'))
    if cid and sec and uri:
        return GoogleConfig(cid, sec, uri)
    return None


# ---------------------------------------------------------------- state (HMAC, 10 minutes)

class StateError(Exception):
    """The OAuth `state` is malformed, forged or expired."""


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def _mac(secret: str, body: str) -> str:
    return _b64(hmac.new(secret.encode(), b'quilt/connect-state/v1.' + body.encode(), hashlib.sha256).digest())


def sign_state(secret: str, user_id: UUID | str, workspace_id: UUID | str, *, ttl: int = STATE_TTL,
               now: float | None = None) -> str:
    """`<payload>.<mac>`: user id, workspace id, a nonce and an expiry (real time, not the demo clock)."""
    exp = int((time.time() if now is None else now) + ttl)
    body = _b64(json.dumps({'u': str(user_id), 'w': str(workspace_id), 'n': secrets.token_hex(8), 'exp': exp},
                           separators=(',', ':')).encode())
    return f'{body}.{_mac(secret, body)}'


def verify_state(secret: str, state: str | None, *, now: float | None = None) -> tuple[UUID, UUID]:
    """(user id, workspace id) from a state `sign_state` made; StateError if it is bad, tampered or expired."""
    if not state or state.count('.') != 1:
        raise StateError('malformed')
    body, mac = state.split('.')
    if not hmac.compare_digest(mac, _mac(secret, body)):
        raise StateError('bad signature')
    try:
        p = json.loads(_unb64(body))
        if int(p['exp']) < (time.time() if now is None else now):
            raise StateError('expired')
        return UUID(p['u']), UUID(p['w'])
    except StateError:
        raise
    except (ValueError, KeyError, TypeError) as e:
        raise StateError('malformed') from e


def consent_url(cfg: GoogleConfig, state: str) -> str:
    return AUTH_URL + '?' + urlencode({
        'client_id': cfg.client_id, 'redirect_uri': cfg.redirect_uri, 'response_type': 'code', 'scope': SCOPE,
        'access_type': 'offline', 'prompt': 'consent', 'state': state})


# ---------------------------------------------------------------- the HTTP calls

def _error_code(r: httpx.Response) -> str:
    try:
        e = r.json().get('error')
        return e if isinstance(e, str) else (e or {}).get('status') or 'error'
    except (ValueError, AttributeError):
        return 'error'


def _call(client: httpx.Client, method: str, url: str, **kw) -> httpx.Response:
    try:
        r = client.request(method, url, **kw)
    except httpx.HTTPError as e:
        raise GoogleError('unavailable', type(e).__name__) from e
    if r.status_code >= 500 or r.status_code == 429:
        raise GoogleError('unavailable', str(r.status_code))
    return r


def _token_call(client: httpx.Client, form: dict[str, str]) -> dict:
    r = _call(client, 'POST', TOKEN_URL, data=form)
    if r.status_code != 200:
        code = _error_code(r)
        raise GoogleError('invalid_grant' if code == 'invalid_grant' else 'rejected', code)
    try:
        body = r.json()
    except ValueError as e:
        raise GoogleError('bad_response', 'token response is not JSON') from e
    if not isinstance(body, dict) or not body.get('access_token'):
        raise GoogleError('bad_response', 'no access token')
    return body


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str | None   # Google sends it with access_type=offline + prompt=consent; may be absent on a repeat


def exchange_code(client: httpx.Client, cfg: GoogleConfig, code: str) -> Tokens:
    b = _token_call(client, {'code': code, 'client_id': cfg.client_id, 'client_secret': cfg.client_secret,
                             'redirect_uri': cfg.redirect_uri, 'grant_type': 'authorization_code'})
    return Tokens(b['access_token'], b.get('refresh_token') or None)


def refresh_access_token(client: httpx.Client, cfg: GoogleConfig, refresh_token: str) -> str:
    """A short-lived access token. `invalid_grant` means the user revoked access or the testing-mode token expired."""
    b = _token_call(client, {'client_id': cfg.client_id, 'client_secret': cfg.client_secret,
                             'refresh_token': refresh_token, 'grant_type': 'refresh_token'})
    return b['access_token']


def _api_get(client: httpx.Client, path: str, access_token: str, params: dict | None = None) -> dict:
    r = _call(client, 'GET', f'{CALENDAR_API}{path}', params=params, headers={'Authorization': f'Bearer {access_token}'})
    if r.status_code != 200:
        raise GoogleError('rejected', f'{r.status_code} {_error_code(r)}')
    try:
        body = r.json()
    except ValueError as e:
        raise GoogleError('bad_response', 'not JSON') from e
    if not isinstance(body, dict):
        raise GoogleError('bad_response', 'not an object')
    return body


def primary_email(client: httpx.Client, access_token: str) -> str:
    """The account's email: the id of its primary calendar. Works under calendar.readonly, so the consent
    screen asks for nothing but the calendar (no `openid email` scope, no id token)."""
    cid = _api_get(client, '/calendars/primary', access_token).get('id')
    if not isinstance(cid, str) or not cid:
        raise GoogleError('bad_response', 'no calendar id')
    return cid


def list_events(client: httpx.Client, access_token: str, time_min: datetime, time_max: datetime) -> list[dict]:
    """`events.list` on `primary`: recurring events expanded into single events, cancelled ones included (so
    they can be removed), every page."""
    out: list[dict] = []
    params: dict[str, Any] = {
        'singleEvents': 'true', 'showDeleted': 'true', 'maxResults': 250, 'orderBy': 'startTime',
        'timeMin': time_min.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'timeMax': time_max.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    for _ in range(MAX_PAGES):
        body = _api_get(client, '/calendars/primary/events', access_token, params)
        out.extend(e for e in body.get('items') or [] if isinstance(e, dict))
        token = body.get('nextPageToken')
        if not token:
            return out
        params = {**params, 'pageToken': token}
    raise GoogleError('bad_response', 'too many pages')


def revoke(client: httpx.Client, token: str) -> bool:
    """Best effort (§8a Disconnect): True if Google revoked it. Never raises."""
    try:
        return client.post(REVOKE_URL, data={'token': token}).status_code == 200
    except httpx.HTTPError:
        return False


def window(now: datetime) -> tuple[datetime, datetime]:
    """7 days before `now` to 60 days after (§8a). `now` is the workspace clock, so DEMO_NOW pins it."""
    return now - WINDOW_BEFORE, now + WINDOW_AFTER


# ---------------------------------------------------------------- mapping (§8a table)

def _when(v: dict, tz: str) -> str | None:
    """A Google `start` / `end` object as a record value: an ISO datetime with offset in the workspace zone, or a day."""
    if not isinstance(v, dict):
        return None
    if v.get('dateTime'):
        s = str(v['dateTime'])
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        if dt.tzinfo is None:   # Google always sends an offset unless it names the zone beside it
            dt = dt.replace(tzinfo=ZoneInfo(v.get('timeZone') or tz))
        return dt.astimezone(ZoneInfo(tz)).isoformat()
    if v.get('date'):
        return date.fromisoformat(str(v['date'])[:10]).isoformat()
    return None


def map_event(ev: dict, tz: str) -> dict | None:
    """One Google event as the fields of a `calendar/events` record, or None if it can't be one (no id, no start).

    summary → title (empty → "Busy"); `start/end.dateTime` → `at` / `ends` in the workspace zone; an all-day event's
    `start/end.date` → days, and Google's end day is exclusive so `ends` is the day before (left out for a one-day
    event); id → `ext_id`; `source: "google"`. Description, attendees, location and links are not stored."""
    ext_id = ev.get('id')
    if not ext_id or not isinstance(ext_id, str):
        return None
    try:
        at = _when(ev.get('start'), tz)
        if at is None:
            return None
        ends = None
        if (ev.get('start') or {}).get('date'):
            last = date.fromisoformat(str((ev.get('end') or {}).get('date') or at)[:10]) - timedelta(days=1)
            ends = last.isoformat() if last > date.fromisoformat(at) else None
        else:
            ends = _when(ev.get('end'), tz)
    except (ValueError, TypeError):
        return None
    title = str(ev.get('summary') or '').strip() or 'Busy'
    out = {'title': title, 'at': at, 'source': SOURCE, 'ext_id': ext_id}
    if ends:
        out['ends'] = ends
    return out


def map_events(items: list[dict], tz: str) -> tuple[dict[str, dict], set[str]]:
    """`(live, cancelled)`: `live` is `{ext_id: fields}`; `cancelled` is the ids Google says are gone."""
    live: dict[str, dict] = {}
    cancelled: set[str] = set()
    for ev in items:
        eid = ev.get('id')
        if ev.get('status') == 'cancelled':
            if isinstance(eid, str):
                cancelled.add(eid)
            continue
        f = map_event(ev, tz)
        if f is not None:
            live[f['ext_id']] = f
    return live, cancelled


# ---------------------------------------------------------------- the diff

def _same_when(a: Any, b: Any, tz: str) -> bool:
    if a in (None, '') and b in (None, ''):
        return True
    if a in (None, '') or b in (None, ''):
        return False
    try:
        pa, pb = parse_value(a, tz), parse_value(b, tz)
    except (ValueError, TypeError):
        return a == b
    if isinstance(pa, datetime) != isinstance(pb, datetime):
        return False
    return iso(to_local(pa, tz) if isinstance(pa, datetime) else pa) == iso(to_local(pb, tz) if isinstance(pb, datetime) else pb)


def diff(existing: list[dict], live: dict[str, dict], cancelled: set[str], tz: str, *,
         collection_id: str) -> tuple[list[dict], dict[str, int]]:
    """Command-service ops that make the stored Google records match `live`, matched on `ext_id` (§8a):
    new → insert, changed → update (only the changed fields; a cleared `ends` is None), and a stored record that
    is cancelled, gone from the window, a duplicate, or has no `ext_id` → delete. Returns `(ops, counts)`
    with counts `{added, changed, removed}`. An empty list means there is nothing to write.

    `existing`: `[{id, properties}]`, the live records of the calendar's events collection with `source: "google"`.
    `cancelled` is informational: a cancelled id is simply not in `live`, so it is deleted like any other that is gone."""
    del cancelled
    deletes: list[dict] = []
    updates: list[dict] = []
    seen: set[str] = set()
    for r in existing:
        props = r.get('properties') or {}
        ext = props.get('ext_id')
        if not ext or ext in seen or ext not in live:
            deletes.append({'op': 'delete', 'record_id': str(r['id'])})
            continue
        seen.add(ext)
        want = live[ext]
        changes: dict[str, Any] = {}
        if (props.get('title') or '') != want['title']:
            changes['title'] = want['title']
        if not _same_when(props.get('at'), want['at'], tz):
            changes['at'] = want['at']
        if not _same_when(props.get('ends'), want.get('ends'), tz):
            changes['ends'] = want.get('ends')     # None clears it
        if changes:
            updates.append({'op': 'update', 'record_id': str(r['id']), 'fields': changes})
    inserts = [{'op': 'insert', 'collection_id': collection_id, 'fields': dict(f)}
               for ext, f in sorted(live.items(), key=lambda kv: (kv[1]['at'], kv[0])) if ext not in seen]
    counts = {'added': len(inserts), 'changed': len(updates), 'removed': len(deletes)}
    return deletes + updates + inserts, counts
