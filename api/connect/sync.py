"""The database side of the Google Calendar connection (backend.md §8a): the `connections` row, and the sync.

A sync has two phases so the workspace lock is never held across a network call:
1. fetch: ask Google (or the fixture) for the window's events and map them (no database lock);
2. apply: under the workspace lock, read the stored Google records, diff, and write ONE change set
   (`actor system`, `origin connector`, so it is never offered for Undo and writes only what changed). An empty diff
   writes nothing. More than 100 changes (the command service's op limit) go in as several change sets in the same
   transaction, so they still land together or not at all.

`needs_reconnect` has no column in `connections` (no migration for it): a dead refresh token is stored as the empty
string, so "needs reconnect" is `refresh_token = ''`. A fixture connection (DEMO_GCAL_FIXTURE=1) stores the marker
`fixture` instead, and counts as needing a reconnect once the flag is off.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

import httpx

from .. import db
from ..commands import CommandError, load_model, run
from ..commands.ops import MAX_OPS
from ..logic.clock import now as clock_now
from ..settings import settings
from . import google as G
from .fixture import FIXTURE_TOKEN, GOOGLE_RESPONSE

log = logging.getLogger('quilt.connect')

TARGET = 'calendar/events'
CS_SOURCE = {'kind': 'sweep', 'label': 'Google Calendar'}   # how the Activity card words an automatic change (api/cards.py)


class ConnectError(Exception):
    """A refusal the routes turn into `status` and `{error, ...}`."""

    def __init__(self, status: int, error: str, message: str = ''):
        super().__init__(f'{status} {error}')
        self.status = status
        self.body = {'error': error, **({'message': message} if message else {})}


def not_configured() -> ConnectError:
    return ConnectError(503, 'google_not_configured', 'Google Calendar is not set up on this server.')


def needs_reconnect_error() -> ConnectError:
    return ConnectError(409, 'needs_reconnect', 'Reconnect Google Calendar.')


@dataclass(frozen=True)
class Outcome:
    added: int
    changed: int
    removed: int
    last_synced_at: datetime

    def api(self) -> dict:
        return {'added': self.added, 'changed': self.changed, 'removed': self.removed,
                'last_synced_at': self.last_synced_at}


# ---------------------------------------------------------------- the connection row

def fixture_mode() -> bool:
    return bool(settings().demo_gcal_fixture)


def get_connection(conn, ws: UUID) -> dict | None:
    return conn.execute('select * from connections where workspace_id = %s and provider = %s',
                        (ws, G.PROVIDER_DB)).fetchone()


def needs_reconnect(row: dict) -> bool:
    tok = row['refresh_token']
    return tok == '' or (tok == FIXTURE_TOKEN and not fixture_mode())


def public(row: dict) -> dict:
    """The row as a client may see it: never the token."""
    return {'provider': G.PROVIDER_API, 'account_email': row['account_email'],
            'last_synced_at': row['last_synced_at'], 'needs_reconnect': needs_reconnect(row)}


def list_connections(ws: UUID) -> list[dict]:
    with db.connect() as conn:
        row = get_connection(conn, ws)
    return [public(row)] if row else []


def is_member(ws: UUID, user_id: UUID) -> bool:
    with db.connect() as conn:
        return conn.execute('select 1 as ok from workspace_members where workspace_id = %s and user_id = %s',
                            (ws, user_id)).fetchone() is not None


def mark_needs_reconnect(ws: UUID) -> None:
    """The refresh token is dead (revoked, or a testing-mode token that expired): drop it. Imported events stay."""
    with db.connect() as conn:
        conn.execute("update connections set refresh_token = '' where workspace_id = %s and provider = %s",
                     (ws, G.PROVIDER_DB))
        conn.commit()


# ---------------------------------------------------------------- phase 1: fetch

@contextmanager
def _http(client: httpx.Client | None) -> Iterator[httpx.Client]:
    if client is not None:
        yield client
    else:
        with httpx.Client(timeout=15.0) as c:
            yield c


def _workspace(ws: UUID) -> tuple[str, datetime]:
    """The workspace zone and its clock (`DEMO_NOW` pins it)."""
    with db.connect() as conn:
        r = conn.execute('select tz from workspaces where id = %s', (ws,)).fetchone()
    if r is None:
        raise ConnectError(404, 'not_found', 'no workspace')
    return r['tz'], clock_now(r['tz'], settings().demo_now)


def _google_failed(e: G.GoogleError) -> ConnectError:
    log.warning('google call failed: %s', e.code)
    return ConnectError(502, 'google_unavailable', 'Google Calendar could not be reached. Try again.')


def _fetch(client: httpx.Client | None, tz: str, now: datetime, *, refresh_token: str | None = None,
           access_token: str | None = None) -> tuple[dict[str, dict], set[str]]:
    """The window's events, mapped. In fixture mode the "Google response" is the four seeded events: no network, and
    no window (the fixture is the whole calendar), so it stays the same whatever the clock says."""
    if fixture_mode():
        return G.map_events(GOOGLE_RESPONSE, tz)
    cfg = G.config_from(settings())
    if cfg is None:
        raise not_configured()
    with _http(client) as c:
        token = access_token or G.refresh_access_token(c, cfg, refresh_token or '')
        lo, hi = G.window(now)
        return G.map_events(G.list_events(c, token, lo, hi), tz)


# ---------------------------------------------------------------- phase 2: apply

def _stored(conn, ws: UUID, collection_id) -> list[dict]:
    return conn.execute(
        "select id, properties from blocks where workspace_id = %s and collection_id = %s and block_type = 'record' "
        "and deleted_at is null and properties ->> 'source' = %s order by position, id",
        (ws, collection_id, G.SOURCE)).fetchall()


def _write(conn, ws: UUID, ops: list[dict], counts: dict[str, int]) -> None:
    summary = f"{counts['added']} added, {counts['changed']} changed, {counts['removed']} removed"
    for i in range(0, len(ops), MAX_OPS):
        try:
            run(conn, ws, ops[i:i + MAX_OPS], actor='system', origin='connector', title='Google Calendar synced',
                summary=summary, source=CS_SOURCE)
        except CommandError as e:
            issues = e.body.get('issues') or [{}]
            raise ConnectError(409, 'sync_failed', str(issues[0].get('problem') or issues[0].get('msg') or e.body)) from e


def _apply(ws: UUID, tz: str, now: datetime, live: dict[str, dict], cancelled: set[str],
           upsert: dict | None = None) -> Outcome:
    """Make the stored Google records match `live` (one change set), stamp `last_synced_at`, and when `upsert` is
    given (`{user_id, email, token}`) create or replace the connection row in the same transaction."""
    with db.transaction(ws) as conn:
        coll = load_model(conn, ws).colls_by_ref.get(TARGET)
        if coll is None:
            raise ConnectError(409, 'no_calendar', 'This quilt has no Calendar app to put events in.')
        ops, counts = G.diff(_stored(conn, ws, coll['id']), live, cancelled, tz, collection_id=str(coll['id']))
        if ops:
            _write(conn, ws, ops, counts)
        if upsert:
            conn.execute(
                'insert into connections (workspace_id, user_id, provider, account_email, refresh_token, last_synced_at) '
                'values (%s, %s, %s, %s, %s, %s) on conflict (workspace_id, provider) do update set '
                'user_id = excluded.user_id, account_email = excluded.account_email, '
                'refresh_token = excluded.refresh_token, sync_token = null, last_synced_at = excluded.last_synced_at',
                (ws, upsert['user_id'], G.PROVIDER_DB, upsert['email'], upsert['token'], now))
        else:
            conn.execute('update connections set last_synced_at = %s where workspace_id = %s and provider = %s',
                         (now, ws, G.PROVIDER_DB))
    return Outcome(counts['added'], counts['changed'], counts['removed'], now)


# ---------------------------------------------------------------- what the routes call

def run_sync(ws: UUID, client: httpx.Client | None = None) -> Outcome:
    """`POST /connect/google/sync`, and the server's own calls (a Clair run, `/dev/reset`).

    ConnectError: 404 no connection; 409 `needs_reconnect` (a revoked or expired token marks the row); 502 Google down."""
    with db.connect() as conn:
        row = get_connection(conn, ws)
    if row is None:
        raise ConnectError(404, 'not_found', 'Google Calendar is not connected.')
    if needs_reconnect(row):
        raise needs_reconnect_error()
    tz, now = _workspace(ws)
    try:
        live, cancelled = _fetch(client, tz, now, refresh_token=row['refresh_token'])
    except G.GoogleError as e:
        if e.code == 'invalid_grant':
            mark_needs_reconnect(ws)
            raise needs_reconnect_error() from e
        raise _google_failed(e) from e
    return _apply(ws, tz, now, live, cancelled)


def connect_fixture(ws: UUID, user_id: UUID) -> Outcome:
    """DEMO_GCAL_FIXTURE=1: connect the demo account without Google and sync the four seeded events."""
    tz, now = _workspace(ws)
    live, cancelled = _fetch(None, tz, now)
    return _apply(ws, tz, now, live, cancelled,
                  upsert={'user_id': user_id, 'email': settings().demo_gcal_email, 'token': FIXTURE_TOKEN})


def connect_google(ws: UUID, user_id: UUID, code: str, client: httpx.Client | None = None) -> Outcome:
    """The callback: exchange `code`, read the account's email, fetch the window, then store the connection and the
    first sync together. Nothing is stored if any step fails."""
    cfg = G.config_from(settings())
    if cfg is None:
        raise not_configured()
    tz, now = _workspace(ws)
    try:
        with _http(client) as c:
            tokens = G.exchange_code(c, cfg, code)
            email = G.primary_email(c, tokens.access_token)
            live, cancelled = _fetch(c, tz, now, access_token=tokens.access_token)
    except G.GoogleError as e:
        raise _google_failed(e) from e
    refresh = tokens.refresh_token
    if not refresh:   # a repeat consent can omit it; keep the one we have
        with db.connect() as conn:
            old = get_connection(conn, ws)
        refresh = old['refresh_token'] if old and old['refresh_token'] not in ('', FIXTURE_TOKEN) else None
    if not refresh:
        raise ConnectError(502, 'google_unavailable', 'Google did not give a refresh token. Connect again.')
    return _apply(ws, tz, now, live, cancelled, upsert={'user_id': user_id, 'email': email, 'token': refresh})


def disconnect(ws: UUID, client: httpx.Client | None = None) -> None:
    """`DELETE /connect/google` (§8a): delete the imported events (a `connector` change set) and the connection,
    then revoke the token at Google if we can (best effort)."""
    with db.transaction(ws) as conn:
        row = get_connection(conn, ws)
        if row is None:
            raise ConnectError(404, 'not_found', 'Google Calendar is not connected.')
        coll = load_model(conn, ws).colls_by_ref.get(TARGET)
        stored = _stored(conn, ws, coll['id']) if coll else []
        if stored:
            ops = [{'op': 'delete', 'record_id': str(r['id'])} for r in stored]
            _write(conn, ws, ops, {'added': 0, 'changed': 0, 'removed': len(ops)})
        conn.execute('delete from connections where workspace_id = %s and provider = %s', (ws, G.PROVIDER_DB))
    token = row['refresh_token']
    if token and token != FIXTURE_TOKEN and not fixture_mode():
        with _http(client) as c:
            G.revoke(c, token)


def after_reset(ws: UUID) -> None:
    """`/dev/reset` (§8a): the reseed keeps the connection row, so sync again (in fixture mode the seed already wrote
    the four events: this just stamps `last_synced_at`). Never fails the reset."""
    try:
        with db.connect() as conn:
            if get_connection(conn, ws) is None:
                return
        run_sync(ws)
    except Exception as e:  # noqa: BLE001
        log.warning('sync after reset failed: %s', getattr(e, 'body', type(e).__name__))
