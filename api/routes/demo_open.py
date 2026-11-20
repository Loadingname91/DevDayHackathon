"""`POST /demo/enter`: open-room demo entry. Hands out a sign-in token for the demo user so anyone with the link
can try the app with no form. Off unless DEMO_OPEN=1 on the server; unset it after the demo (spec/split.md §7)."""
import httpx
from fastapi import APIRouter, HTTPException

from ..settings import settings

router = APIRouter(tags=['auth'])


@router.post('/demo/enter', operation_id='demo_enter', include_in_schema=False)
def demo_enter() -> dict:
    s = settings()
    if not s.demo_open:
        raise HTTPException(404, {'error': 'demo_open_off'})
    r = httpx.post(f'{s.supabase_url}/auth/v1/admin/generate_link',
                   headers={'apikey': s.supabase_service_role_key, 'Authorization': f'Bearer {s.supabase_service_role_key}'},
                   json={'type': 'magiclink', 'email': s.demo_open_email}, timeout=15)
    if r.status_code != 200:
        raise HTTPException(502, {'error': 'demo_link_failed'})
    return {'email': s.demo_open_email, 'token_hash': r.json()['hashed_token']}
