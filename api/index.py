"""Quilt API (spec/backend.md §10). Run from the repo root: uvicorn api.index:app --host 0.0.0.0 --port $PORT"""
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import db
from .settings import settings

app = FastAPI(title='Quilt API', version=settings().version, docs_url='/api/docs', openapi_url='/api/openapi.json')

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted({settings().web_origin, 'http://localhost:5173'}),
    allow_methods=['*'],
    allow_headers=['Authorization', 'Content-Type', 'X-Demo-Key', 'X-Cron-Key'],
    expose_headers=['X-Run-Id', 'X-Thread-Id'],  # the client needs the thread id to answer a question
)

api = APIRouter(prefix='/api')


@app.exception_handler(HTTPException)
async def contract_errors(_request, exc: HTTPException):
    """Error bodies are `{error, ...}` (backend.md §10 status codes), not FastAPI's `{detail}`."""
    body = exc.detail if isinstance(exc.detail, dict) else {'error': str(exc.detail)}
    if isinstance(body.get('issues'), list):  # the command service words issues as {field, problem, code}
        body = {**body, 'issues': [i if 'msg' in i else {'loc': [str(i.get('field') or i.get('index', ''))], 'msg': i.get('problem', ''),
                                   **({'code': i['code']} if i.get('code') else {})} for i in body['issues']]}
    return JSONResponse(body, status_code=exc.status_code, headers=getattr(exc, 'headers', None))


@app.exception_handler(RequestValidationError)
async def validation_errors(_request, exc: RequestValidationError):
    issues = [{'loc': [str(p) for p in e.get('loc', [])], 'msg': e.get('msg', '')} for e in exc.errors()]
    return JSONResponse({'error': 'invalid', 'issues': issues}, status_code=422)


class Health(BaseModel):
    ok: bool
    db: bool
    version: str


@api.get('/health', response_model=Health, tags=['system'])
def health() -> Health:
    ok = db.ping()
    return Health(ok=ok, db=ok, version=settings().version)


from .routes import apps, clair, dev, me, read, write  # noqa: E402

api.include_router(me.router)
api.include_router(read.router)
api.include_router(write.router)
api.include_router(apps.router)
api.include_router(clair.router)
api.include_router(dev.router)
app.include_router(api)
