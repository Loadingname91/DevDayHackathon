"""`POST /dev/reset` (backend.md §10, §11 #57, #62). Reseeds only the demo workspaces named in env;
never touches the auth users or another workspace. Guarded by the `X-Demo-Key` header."""
import hmac
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response

from .. import db
from ..connect import sync as connect_sync
from ..seed.load import reset_workspace
from ..settings import settings

router = APIRouter(tags=['dev'])


@router.post('/dev/reset', status_code=204, operation_id='dev_reset')
def dev_reset(state: Literal['full', 'before'] = 'full', x_demo_key: str | None = Header(None)) -> Response:
    key = settings().demo_key
    if not key or not x_demo_key or not hmac.compare_digest(key, x_demo_key):
        raise HTTPException(401, {'error': 'bad_demo_key'})
    ws = settings().demo_record_workspace_id if state == 'before' else settings().demo_workspace_id
    if not ws:
        raise HTTPException(404, {'error': 'no_demo_workspace'})
    gcal = settings().demo_gcal_fixture
    with db.transaction(ws) as conn:
        reset_workspace(conn, ws, state, gcal_fixture=gcal)
    connect_sync.after_reset(UUID(str(ws)))  # backend.md §8a: the reseed keeps the Google connection and syncs again
    return Response(status_code=204)
