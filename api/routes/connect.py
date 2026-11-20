"""The Google Calendar connection routes (backend.md §8a, §10), over api/connect/.

    GET    /connect                        the caller's connections (never the token)
    POST   /connect/google/start           {url, connected?}: Google's consent URL, or (fixture mode) connect at once
    GET    /connect/google/callback        from Google (no bearer; `state` is the proof) → 302 to the site
    POST   /connect/google/sync            {added, changed, removed, last_synced_at}
    DELETE /connect/google                 disconnect: delete the imported events and the connection (204)

Three states, switched by environment variables (api/settings.py):
  (a) not configured (no GOOGLE_*): GET /connect works (an empty list); start answers 503 {error: google_not_configured}.
  (b) fixture (DEMO_GCAL_FIXTURE=1): start connects the demo account with the four seeded events and no Google call.
      Wins over (c) when both are set: it is the explicit fallback for a day Google sign-in doesn't work.
  (c) configured: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI all set → the real OAuth flow.

What the owner creates in Google Cloud for (c) (configuration, not code):
  1. A project, with the Google Calendar API turned on (APIs & Services → Library).
  2. The OAuth consent screen: user type External, publishing status "Testing", the demo Google account added as a
     test user, scope `.../auth/calendar.readonly` (nothing else: no openid, no email; the account's email comes from
     the primary calendar's id). An unreviewed app shows Google's "unverified app" screen and, in testing mode, its
     refresh tokens expire after 7 days: reconnect before the pitch.
  3. Credentials → OAuth client ID, type "Web application", Authorized redirect URI exactly
     `https://<railway-host>/api/connect/google/callback` (add `http://localhost:8002/api/connect/google/callback`
     to try it locally). No JavaScript origins are needed: the browser only navigates.
  4. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI (the same URI) on the Railway service.
     Optionally CONNECT_STATE_SECRET (any long random string) to sign the OAuth `state`; without it the server's
     Supabase service-role key signs it. WEB_ORIGIN must be the site's origin: the callback redirects there.

The callback lands on `{WEB_ORIGIN}/app/calendar?connected=google`, or `?connected=failed` (consent denied, a bad or
expired `state`, Google refused or was down). Those are the route and the query the client already handles.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from .. import models as m
from ..auth import Member, current_member
from ..connect import google as G
from ..connect import sync
from ..contract import E401, E404, E409, R
from ..settings import settings

router = APIRouter(tags=['connect'])
log = logging.getLogger('quilt.connect')

E503 = {503: {'model': m.ErrorBody, 'description': 'google_not_configured: no Google OAuth client on this server'}}
E502 = {502: {'model': m.ErrorBody, 'description': 'google_unavailable: Google refused or could not be reached'}}
CALENDAR_PATH = '/app/calendar'


def google_http() -> Iterator[httpx.Client]:
    """The client for Google calls; a test overrides this dependency with a `httpx.MockTransport` client."""
    with httpx.Client(timeout=15.0) as client:
        yield client


@contextmanager
def _errors() -> Iterator[None]:
    try:
        yield
    except sync.ConnectError as e:
        raise HTTPException(e.status, detail=e.body) from e


def _state_secret() -> str:
    s = settings()
    return s.connect_state_secret or s.supabase_service_role_key


def _back(ok: bool) -> RedirectResponse:
    origin = settings().web_origin.rstrip('/')
    return RedirectResponse(f"{origin}{CALENDAR_PATH}?connected={'google' if ok else 'failed'}", status_code=302)


@router.get('/connect', response_model=list[m.Connection], operation_id='connect_list', tags=['connect'],
            responses=R(E401))
def connect_list(mem: Member = Depends(current_member)) -> Any:
    return sync.list_connections(mem.workspace_id)


@router.post('/connect/google/start', response_model=m.ConnectStart, operation_id='connect_google_start',
             tags=['connect'], responses=R(E401, E503, E502))
def connect_google_start(mem: Member = Depends(current_member)) -> Any:
    if sync.fixture_mode():
        with _errors():
            sync.connect_fixture(mem.workspace_id, mem.user.id)
        return {'url': f'{CALENDAR_PATH}?connected=google', 'connected': True}   # a path: the client navigates in-app
    cfg = G.config_from(settings())
    if cfg is None:
        raise HTTPException(503, detail=sync.not_configured().body)
    state = G.sign_state(_state_secret(), mem.user.id, mem.workspace_id)
    return {'url': G.consent_url(cfg, state)}


@router.get('/connect/google/callback', status_code=302, response_class=RedirectResponse, response_model=None,
            operation_id='connect_google_callback', tags=['connect'],
            responses=R({302: {'description': 'To {WEB_ORIGIN}/app/calendar?connected=google, or ?connected=failed'}}))
def connect_google_callback(code: str | None = Query(None), state: str | None = Query(None),
                            error: str | None = Query(None), http: httpx.Client = Depends(google_http)) -> Any:
    """No bearer token: Google sends the browser here. Whatever goes wrong, the person lands back on Calendar with
    "Google Calendar wasn't connected." and never on a JSON error."""
    if error or not code:   # `error=access_denied` when the person says no
        return _back(False)
    try:
        user_id, ws = G.verify_state(_state_secret(), state)
    except G.StateError:
        return _back(False)
    try:
        if not sync.is_member(ws, user_id):
            return _back(False)
        sync.connect_google(ws, user_id, code, http)
    except sync.ConnectError:
        return _back(False)
    except Exception as e:  # noqa: BLE001  a redirect flow shows the friendly line, not a stack trace
        log.warning('google callback failed: %s', type(e).__name__)
        return _back(False)
    return _back(True)


@router.post('/connect/google/sync', response_model=m.ConnectSyncResult, operation_id='connect_google_sync',
             tags=['connect'], responses=R(E401, E404, E409, E502))
def connect_google_sync(mem: Member = Depends(current_member), http: httpx.Client = Depends(google_http)) -> Any:
    with _errors():
        return sync.run_sync(mem.workspace_id, http).api()


@router.delete('/connect/google', status_code=204, response_class=Response, response_model=None,
               operation_id='connect_google_delete', tags=['connect'], responses=R(E401, E404))
def connect_google_delete(mem: Member = Depends(current_member), http: httpx.Client = Depends(google_http)) -> Response:
    with _errors():
        sync.disconnect(mem.workspace_id, http)
    return Response(status_code=204)
