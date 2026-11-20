"""Every endpoint of spec/backend.md §10, declared for OpenAPI only.

The app mounts this router under /api. Handlers here raise 501: the real ones live in
their own modules and must keep the same method, path, models and operation_id.
"""
from __future__ import annotations

from typing import Any, Literal, NoReturn

from fastapi import APIRouter, Header, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from . import models as m

router = APIRouter()

# Shared response declarations.
E401 = {401: {'model': m.ErrorBody, 'description': 'No or bad token'}}
E402 = {402: {'model': m.ErrorBody, 'description': 'Out of credits'}}
E403 = {403: {'model': m.ErrorBody, 'description': 'Read level none, or a guest making a join code'}}
E404 = {404: {'model': m.ErrorBody, 'description': 'Not found or not yours'}}
E409 = {409: {'model': m.Conflict, 'description': 'State conflict'}}
E409S = {409: {'model': m.StatusConflict, 'description': 'The change set is not in the expected status'}}
E422 = {422: {'model': m.ValidationErrorBody, 'description': 'Validation failed'}}
E429 = {429: {'model': m.ErrorBody, 'description': 'Rate limited'}}


def R(*parts: dict[int, Any]) -> dict[int | str, dict[str, Any]]:
    """Merge response declarations. Every route declares 422 as ValidationErrorBody, so FastAPI's
    default HTTPValidationError never enters the contract (backend.md §10: `422 {error, issues[]}`)."""
    out: dict[int | str, dict[str, Any]] = dict(E422)
    for p in parts:
        out.update(p)
    return out


AUTH = R(E401, E404, E422)


def todo() -> NoReturn:
    raise HTTPException(status_code=501, detail='not implemented')


# ---- system ---------------------------------------------------------------

@router.get('/health', response_model=m.Health, operation_id='health', tags=['system'])
def health() -> Any:
    todo()


@router.post('/cron/sweep', status_code=204, response_class=Response, response_model=None, operation_id='cron_sweep', tags=['system'],
             responses=R(E401))
def cron_sweep(x_cron_key: str = Header()) -> Any:
    todo()


@router.post('/dev/reset', status_code=204, response_class=Response, response_model=None, operation_id='dev_reset', tags=['system'],
             responses=R(E401))
def dev_reset(x_demo_key: str = Header(), state: Literal['before'] | None = Query(None)) -> Any:
    todo()


# ---- me -------------------------------------------------------------------

@router.post('/me/bootstrap', response_model=m.BootstrapResponse, operation_id='me_bootstrap', tags=['me'], responses=AUTH)
def me_bootstrap(body: m.BootstrapRequest) -> Any:
    todo()


@router.get('/me', response_model=m.Me, operation_id='me_get', tags=['me'], responses=R(E401))
def me_get() -> Any:
    todo()


@router.patch('/me', response_model=m.MePatchResponse, operation_id='me_patch', tags=['me'], responses=AUTH)
def me_patch(body: m.MePatch) -> Any:
    todo()


@router.patch('/settings', response_model=m.SettingsResponse, operation_id='settings_patch', tags=['me'], responses=AUTH)
def settings_patch(body: m.SettingsPatch) -> Any:
    todo()


@router.get('/usage', response_model=m.Usage, operation_id='usage_get', tags=['me'], responses=R(E401))
def usage_get() -> Any:
    todo()


# ---- Google connection ----------------------------------------------------

@router.post('/connect/google/start', response_model=m.ConnectStart, operation_id='connect_google_start',
             tags=['connect'], responses=R(E401, {
                 502: {'model': m.ErrorBody, 'description': 'google_unavailable: Google refused or could not be reached'},
                 503: {'model': m.ErrorBody, 'description': 'google_not_configured: no Google OAuth client on this server'}}))
def connect_google_start() -> Any:
    todo()


@router.get('/connect/google/callback', status_code=302, response_class=RedirectResponse, response_model=None,
            operation_id='connect_google_callback', tags=['connect'],
            responses=R({302: {'description': 'To {WEB_ORIGIN}/app/calendar?connected=google, or ?connected=failed'}}))
def connect_google_callback(code: str | None = Query(None), state: str | None = Query(None),
                            error: str | None = Query(None)) -> Any:
    todo()


@router.get('/connect', response_model=list[m.Connection], operation_id='connect_list', tags=['connect'], responses=R(E401))
def connect_list() -> Any:
    todo()


@router.post('/connect/google/sync', response_model=m.ConnectSyncResult, operation_id='connect_google_sync',
             tags=['connect'], responses=R(E401, E404, E409, {
                 502: {'model': m.ErrorBody, 'description': 'google_unavailable: Google refused or could not be reached'}}))
def connect_google_sync() -> Any:
    todo()


@router.delete('/connect/google', status_code=204, response_class=Response, response_model=None, operation_id='connect_google_delete',
               tags=['connect'], responses=R(E401, E404))
def connect_google_delete() -> Any:
    todo()


# ---- Home and apps --------------------------------------------------------

@router.get('/home', response_model=m.Home, operation_id='home_get', tags=['home'], responses=R(E401))
def home_get() -> Any:
    todo()


@router.get('/apps', response_model=list[m.Patch], operation_id='apps_list', tags=['apps'], responses=R(E401))
def apps_list() -> Any:
    todo()


@router.get('/apps/{id}', response_model=m.AppDetail, operation_id='app_get', tags=['apps'], responses=R(E401, E404))
def app_get(id: str) -> Any:
    todo()


@router.post('/apps/{id}/opened', status_code=204, response_class=Response, response_model=None, operation_id='app_opened', tags=['apps'],
             responses=R(E401, E404))
def app_opened(id: str) -> Any:
    todo()


@router.post('/apps', status_code=201, response_model=m.CommandResult, operation_id='app_create', tags=['apps'],
             responses=AUTH)
def app_create(body: m.AppCreate) -> Any:
    todo()


@router.patch('/apps/{id}', response_model=m.CommandResult, operation_id='app_update', tags=['apps'],
              responses=R(AUTH, E409))
def app_update(id: str, body: m.AppUpdate) -> Any:
    todo()


@router.delete('/apps/{id}', response_model=m.CommandResult, operation_id='app_delete', tags=['apps'],
               responses=R(AUTH, {409: {'model': m.Conflict, 'description': 'Without confirm: `{error, dependents}` preview'}}))
def app_delete(id: str, confirm: bool = Query(False)) -> Any:
    todo()


@router.post('/templates/apply', response_model=m.CommandResult, operation_id='templates_apply', tags=['apps'],
             responses=AUTH)
def templates_apply(body: m.TemplatesApply) -> Any:
    todo()


# ---- workflows (spec/workflows.md, Engine v1) ------------------------------

@router.post('/apps/{id}/workflows', response_model=m.CommandResult, operation_id='workflow_create', tags=['workflows'],
             responses=AUTH)
def workflow_create(id: str, body: m.WorkflowCreate) -> Any:
    todo()


@router.patch('/apps/{id}/workflows/{wid}', response_model=m.CommandResult, operation_id='workflow_update',
              tags=['workflows'], responses=AUTH)
def workflow_update(id: str, wid: str, body: m.WorkflowPatch) -> Any:
    todo()


@router.post('/apps/{id}/workflows/{wid}/run', response_model=m.RunStarted, operation_id='workflow_run',
             tags=['workflows'], responses=R(E401, E402, E404, {409: {'model': m.Conflict, 'description': 'The rule is off'}}, E429))
def workflow_run(id: str, wid: str) -> Any:
    todo()


# ---- collections (select options) ----------------------------------------

@router.post('/collections/{id}/options', response_model=m.CommandResult, operation_id='option_create',
             tags=['collections'], responses=AUTH)
def option_create(id: str, body: m.OptionCreate) -> Any:
    todo()


@router.patch('/collections/{id}/options/{option_id}', response_model=m.CommandResult, operation_id='option_rename',
              tags=['collections'], responses=AUTH)
def option_rename(id: str, option_id: str, body: m.OptionRename) -> Any:
    todo()


@router.delete('/collections/{id}/options/{option_id}', response_model=m.CommandResult, operation_id='option_delete',
               tags=['collections'],
               responses=R(AUTH, {409: {'model': m.Conflict, 'description': 'Items remain and `items` is missing: `{error, count}`'}}))
def option_delete(id: str, option_id: str, body: m.OptionDelete) -> Any:
    todo()


# ---- records (gestures) ---------------------------------------------------

@router.post('/records', status_code=201, response_model=m.CommandResult, operation_id='record_create', tags=['records'],
             responses=AUTH)
def record_create(body: m.RecordCreate) -> Any:
    todo()


@router.patch('/records/{id}', response_model=m.CommandResult, operation_id='record_update', tags=['records'],
              responses=AUTH)
def record_update(id: str, body: m.RecordUpdate) -> Any:
    todo()


@router.post('/records/{id}/move', response_model=m.CommandResult, operation_id='record_move', tags=['records'],
             responses=AUTH)
def record_move(id: str, body: m.RecordMove) -> Any:
    todo()


@router.post('/records/{id}/complete', response_model=m.CommandResult, operation_id='record_complete', tags=['records'],
             responses=AUTH)
def record_complete(id: str, body: m.RecordComplete) -> Any:
    todo()


@router.post('/records/{id}/skip', response_model=m.CommandResult, operation_id='record_skip', tags=['records'],
             responses=AUTH)
def record_skip(id: str, body: m.RecordSkip) -> Any:
    todo()


@router.delete('/records/{id}', response_model=m.CommandResult, operation_id='record_delete', tags=['records'],
               responses=R(E401, E404))
def record_delete(id: str) -> Any:
    todo()


@router.post('/records/{id}/links', response_model=m.CommandResult, operation_id='record_link', tags=['records'],
             responses=R(E401, E404))
def record_link(id: str, body: m.LinkCreate) -> Any:
    """Link a record to any record in any app (a gesture change set with an Undo). A repeat is a no-op change set."""
    todo()


@router.delete('/records/{id}/links/{target_id}', response_model=m.CommandResult, operation_id='record_unlink',
               tags=['records'], responses=R(E401, E404))
def record_unlink(id: str, target_id: str) -> Any:
    todo()


# ---- change sets ----------------------------------------------------------

@router.get('/change-sets', response_model=list[m.ChangeSet], operation_id='change_sets_list', tags=['change-sets'],
            responses=R(E401, E422))
def change_sets_list(status: m.ChangeSetStatus | None = Query(None)) -> Any:
    todo()


@router.patch('/change-sets/{id}', response_model=m.ChangeSet, operation_id='change_set_update', tags=['change-sets'],
              responses=R(AUTH, E409))
def change_set_update(id: str, body: m.ChangeSetPatch) -> Any:
    todo()


@router.post('/change-sets/{id}/confirm', response_model=m.CommandResult, operation_id='change_set_confirm',
             tags=['change-sets'], responses=R(AUTH, E409S))
def change_set_confirm(id: str) -> Any:
    todo()


@router.post('/change-sets/{id}/undo', response_model=m.CommandResult, operation_id='change_set_undo',
             tags=['change-sets'], responses=R(AUTH, E409S))
def change_set_undo(id: str) -> Any:
    todo()


@router.post('/change-sets/{id}/dismiss', status_code=204, response_class=Response, response_model=None, operation_id='change_set_dismiss',
             tags=['change-sets'], responses=R(E401, E404, E409S))
def change_set_dismiss(id: str) -> Any:
    todo()


# ---- Clair (clair-agent.md §2) --------------------------------------------

@router.post(
    '/clair/turns',
    response_model=list[m.ClairEvent],
    operation_id='clair_turn',
    tags=['clair'],
    description=(
        'Streams `text/event-stream`: each SSE message has `event: <name>` and `data: <payload JSON>`, '
        'matching one member of ClairEvent. If SSE is buffered, the same events arrive as one JSON array '
        'at the end and the client polls /clair/runs/{id}/events.'
    ),
    responses=R(
        {200: {'content': {'text/event-stream': {'schema': {'type': 'string'}}}, 'description': 'SSE stream of ClairEvent'}},
        AUTH, E402, E403, {409: {'model': m.Conflict, 'description': 'Thread busy'}},
        {410: {'model': m.ErrorBody, 'description': 'Menu question expired'}},
        {413: {'model': m.ErrorBody, 'description': 'Attachment too large'}}, E429,
    ),
)
def clair_turn(body: m.ClairTurnRequest) -> Any:
    todo()


@router.get('/clair/threads/latest', response_model=m.LatestThread, operation_id='clair_thread_latest', tags=['clair'],
            responses=R(E401, {204: {'description': 'No thread active within 24 h'}}))
def clair_thread_latest() -> Any:
    todo()


@router.get('/clair/runs/{id}/events', response_model=m.RunEvents, operation_id='clair_run_events', tags=['clair'],
            responses=R(E401, E404))
def clair_run_events(id: str, after: int = Query(-1, description='Index of the last event seen; -1 for all')) -> Any:
    todo()


@router.get('/clair/notes', response_model=list[m.Note], operation_id='clair_notes_list', tags=['clair'], responses=R(E401))
def clair_notes_list() -> Any:
    todo()


@router.delete('/clair/notes/{id}', status_code=204, response_class=Response, response_model=None, operation_id='clair_note_delete',
               tags=['clair'], responses=R(E401, E404))
def clair_note_delete(id: str) -> Any:
    todo()


# ---- search, sync, join codes ---------------------------------------------

@router.get('/search', response_model=m.SearchResponse, operation_id='search', tags=['search'], responses=R(E401))
def search(q: str = Query('', description='Matched case-insensitively against titles and text (trimmed, cut at 200 characters); empty lists recent records across apps ("Suggested")'),
           app: str | None = Query(None, description='Limit to one app key'),
           exclude: list[str] | None = Query(None, description='Record ids to leave out (the record being edited); repeatable'),
           limit: int = Query(20, ge=1, le=50)) -> Any:
    todo()


@router.get('/sync', response_model=m.SyncResponse, operation_id='sync', tags=['sync'], responses=R(E401))
def sync(since: int = Query(0, ge=0)) -> Any:
    todo()


@router.post('/join-codes', response_model=m.JoinCode, operation_id='join_code_create', tags=['auth'],
             responses=R(E401, E403))
def join_code_create() -> Any:
    todo()


@router.post('/join-codes/redeem', response_model=m.JoinRedeemed, operation_id='join_code_redeem', tags=['auth'],
             responses=R(E422, {404: {'model': m.ErrorBody, 'description': 'Unknown code'}},
                         {410: {'model': m.ErrorBody, 'description': 'Expired'}}, E429))
def join_code_redeem(body: m.JoinRedeem) -> Any:
    todo()
