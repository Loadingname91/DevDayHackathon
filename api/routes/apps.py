"""App routes (backend.md §10 "Home and apps", §11 #21 to #23): create, edit, delete, starter templates.

Each write is one change set through the command service (api/commands/apps.py), so it has events (`/sync`) and
Undo (`POST /change-sets/{id}/undo`): `POST /apps`, `PATCH` and `DELETE /apps/{id}` are `actor user` / `origin
gesture`; `POST /templates/apply` is `origin template`. Every write returns the command result.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import db
from .. import models as m
from ..auth import Member, current_member
from ..commands import CommandError, load_model, run
from ..commands.apps import _page_id, dependents
from ..contract import AUTH, E409, R
from ..seed.load import TEMPLATES, load_template
from ..workspace import compute_faces
from .write import _errors, command_result

router = APIRouter()


def _spec(spec: Any) -> dict:
    return spec.model_dump(mode='json', by_alias=True, exclude_none=True)


def _run(mem: Member, ops: list[dict], *, origin: str = 'gesture', title: str | None = None,
         source: dict | None = None) -> dict:
    with _errors(), db.transaction(mem.workspace_id) as conn:
        r = run(conn, mem.workspace_id, ops, actor='user', origin=origin, user_id=mem.user.id, title=title,
                source=source, compute_faces=compute_faces)
    return command_result(r)


def _resolve(conn, ws: UUID, id: str) -> UUID:
    try:
        return _page_id(load_model(conn, ws), id)
    except CommandError as e:
        raise HTTPException(e.status, detail=e.body) from e


@router.post('/apps', status_code=201, response_model=m.CommandResult, operation_id='app_create', tags=['apps'],
             responses=AUTH)
def app_create(body: m.AppCreate, mem: Member = Depends(current_member)) -> Any:
    spec = _spec(body.spec)
    return _run(mem, [{'op': 'create_app', 'spec': spec}], title=f'Add {spec.get("name")}')


@router.patch('/apps/{id}', response_model=m.CommandResult, operation_id='app_update', tags=['apps'],
              responses=R(AUTH, E409))
def app_update(id: str, body: m.AppUpdate, mem: Member = Depends(current_member)) -> Any:
    with db.connect() as conn:
        pid = _resolve(conn, mem.workspace_id, id)
    spec = _spec(body.spec)
    return _run(mem, [{'op': 'update_app', 'app_id': str(pid), 'spec': spec, 'base_version': body.base_version}],
                title=f'Change {spec.get("name")}')


@router.delete('/apps/{id}', response_model=m.CommandResult, operation_id='app_delete', tags=['apps'],
               responses=R(AUTH, {409: {'model': m.Conflict, 'description': 'Without confirm: `{error, dependents}` preview'}}))
def app_delete(id: str, confirm: bool = Query(False), mem: Member = Depends(current_member)) -> Any:
    with db.connect() as conn:
        model = load_model(conn, mem.workspace_id)
        pid = _resolve(conn, mem.workspace_id, id)
        name = model.pages[pid]['properties'].get('name')
        if not confirm:
            raise HTTPException(409, detail={'error': 'dependents', 'dependents': dependents(model, pid)})
    return _run(mem, [{'op': 'delete_app', 'app_id': str(pid)}], title=f'Delete {name}')


@router.post('/templates/apply', response_model=m.CommandResult, operation_id='templates_apply', tags=['apps'],
             responses=AUTH)
def templates_apply(body: m.TemplatesApply, mem: Member = Depends(current_member)) -> Any:
    known = sorted(p.stem for p in TEMPLATES.glob('*.json'))
    bad = [t for t in body.templates if t not in known]
    if bad or not body.templates:
        raise HTTPException(422, detail={'error': 'invalid', 'issues': [
            {'loc': ['body', 'templates'], 'msg': f'unknown template {t!r}; templates: {", ".join(known)}'}
            for t in bad] or [{'loc': ['body', 'templates'], 'msg': 'name at least one template'}]})
    with db.connect() as conn:
        have = set(load_model(conn, mem.workspace_id).pages_by_key)
    keys = [t for t in dict.fromkeys(body.templates) if t not in have]     # idempotent: skip apps already there
    if not keys:
        raise HTTPException(409, detail={'error': 'exists', 'dependents': [
            {'app': t, 'what': 'already in your quilt'} for t in body.templates]})
    ops = [{'op': 'create_app', 'spec': load_template(k), 'strict': False} for k in keys]
    return _run(mem, ops, origin='template', title='Starter apps',
                source={'kind': 'template', 'label': 'Template'})
