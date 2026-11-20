"""Bearer-token check (backend.md §8, §10). Supabase signs access tokens with ES256 and publishes
its keys at /auth/v1/.well-known/jwks.json, so the API verifies them with no shared secret.

`current_user` gives the user id and whether they're anonymous; `current_member` also resolves
their workspace (one per user for DevDay, §12). A missing or bad token is 401; no workspace is 404.
"""
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request

from . import db
from .settings import settings


@dataclass(frozen=True)
class User:
    id: UUID
    is_anonymous: bool
    email: str | None


@dataclass(frozen=True)
class Member:
    user: User
    workspace_id: UUID
    tz: str


@lru_cache
def _jwks() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f'{settings().supabase_url}/auth/v1/.well-known/jwks.json', cache_keys=True, lifespan=3600)


def verify(token: str) -> User:
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=['ES256', 'RS256'], audience='authenticated',
                            issuer=f'{settings().supabase_url}/auth/v1', options={'require': ['sub', 'exp']})
    except jwt.PyJWTError as e:
        raise HTTPException(401, {'error': 'bad_token', 'detail': str(e)}) from e
    return User(id=UUID(claims['sub']), is_anonymous=bool(claims.get('is_anonymous')), email=claims.get('email') or None)


def current_user(request: Request) -> User:
    header = request.headers.get('authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(401, {'error': 'no_token'})
    return verify(token)


def current_member(user: User = Depends(current_user)) -> Member:
    with db.connect() as conn:
        row = conn.execute(
            'select m.workspace_id, w.tz from workspace_members m join workspaces w on w.id = m.workspace_id '
            'where m.user_id = %s order by m.created_at limit 1', (user.id,)).fetchone()
    if not row:
        raise HTTPException(404, {'error': 'no_workspace'})
    return Member(user=user, workspace_id=row['workspace_id'], tz=row['tz'])
