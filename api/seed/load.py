"""Write the demo seed into a workspace (spec/backend.md §2.2, §2.3; /dev/reset, §10 and §11 #57).

`reset_workspace` wipes one workspace's blocks, change sets, events, Clair history, notes and November ledger, then
inserts the seed as page, collection and record blocks under one `system`/`seed` change set and bumps `epoch`, so
open clients wipe their cache. It never touches the auth user, the membership row's identity, `connections` or any
other workspace. Block ids are uuid5(workspace id, "<app>/<collection>/<human key>"), so they are stable across
reseeds of the same workspace and different between workspaces.
"""
from __future__ import annotations

import copy
import json
import secrets
import uuid
from pathlib import Path
from typing import Any

import httpx
from psycopg.types.json import Jsonb

from . import data
from .data import Ref

TEMPLATES = Path(__file__).resolve().parent.parent / 'templates'
DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


# ---------------------------------------------------------------- pure helpers (tested without a DB)

def int_key(i: int) -> str:
    """The i-th integer key of the fractional-indexing scheme: a0..az, b00..bzz, c000..; byte-ordered."""
    for head, width in (('a', 1), ('b', 2), ('c', 3)):
        n = 62 ** width
        if i < n:
            s = ''
            for _ in range(width):
                i, r = divmod(i, 62)
                s = DIGITS[r] + s
            return head + s
        i -= n
    raise ValueError('too many siblings for the seed')


def load_template(key: str) -> dict:
    return json.loads((TEMPLATES / f'{key}.json').read_text())


def demo_spec(key: str) -> dict:
    """The template plus the demo account's own settings and lists."""
    spec = copy.deepcopy(load_template(key))
    for k, v in data.SPEC_OVERRIDES.get(key, {}).items():
        spec[k] = copy.deepcopy(v)
    if key == 'groceries':
        items = next(c for c in spec['collections'] if c['key'] == 'items')
        next(f for f in items['fields'] if f['key'] == 'list')['options'] = copy.deepcopy(data.GROCERY_LISTS)
    return spec


def block_id(workspace_id: uuid.UUID | str, path: str) -> uuid.UUID:
    return uuid.uuid5(uuid.UUID(str(workspace_id)), path)


def apps_for(state: str) -> list[str]:
    if state == 'full':
        return list(data.APPS)
    if state == 'before':
        return list(data.BEFORE_APPS)
    raise ValueError(f"state must be 'full' or 'before', not {state!r}")


def build_blocks(workspace_id, state: str = 'full', gcal_fixture: bool = False) -> list[dict]:
    """Every block of the seed as {id, parent_id, position, block_type, collection_id, properties}."""
    ws = str(workspace_id)
    keep = apps_for(state)
    recs = data.records(gcal_fixture)

    def resolve(v: Any) -> Any:
        if isinstance(v, Ref):
            return str(block_id(ws, f'{v.coll}/{v.key}'))
        if isinstance(v, list):
            return [resolve(x) for x in v]
        if isinstance(v, dict):
            return {k: resolve(x) for k, x in v.items()}
        return v

    blocks = []
    for pi, app in enumerate(keep):
        spec = demo_spec(app)
        collections = spec.pop('collections')
        page = block_id(ws, app)
        blocks.append({'id': page, 'parent_id': None, 'position': int_key(pi), 'block_type': 'page',
                       'collection_id': None, 'properties': spec})
        for ci, coll in enumerate(collections):
            cid = block_id(ws, f"{app}/{coll['key']}")
            blocks.append({'id': cid, 'parent_id': page, 'position': int_key(ci), 'block_type': 'collection',
                           'collection_id': None, 'properties': coll})
            for ri, (key, props) in enumerate(recs.get(app, {}).get(coll['key'], [])):
                p = resolve(props)
                via = p.get('_via')
                if via and via['app'] not in keep:      # a stitch from an app the "before" state lacks
                    p.pop('_via')
                blocks.append({'id': block_id(ws, f"{app}/{coll['key']}/{key}"), 'parent_id': cid,
                               'position': int_key(ri), 'block_type': 'record', 'collection_id': cid,
                               'properties': p})
    # relations must point at blocks that exist in this state
    ids = {str(b['id']) for b in blocks}
    for b in blocks:
        if b['block_type'] == 'record':
            for v in b['properties'].values():
                if isinstance(v, list) and v and all(isinstance(x, str) and len(x) == 36 for x in v):
                    missing = [x for x in v if x not in ids]
                    if missing:
                        raise ValueError(f'dangling relation in {b["id"]}: {missing}')
    return blocks


# ---------------------------------------------------------------- database

WIPE = [
    'delete from events where workspace_id = %(ws)s',
    'update change_sets set run_id = null, undo_of = null where workspace_id = %(ws)s',
    'update agent_runs set change_set_id = null where workspace_id = %(ws)s',
    'delete from tool_calls where workspace_id = %(ws)s',
    'delete from llm_calls where workspace_id = %(ws)s',
    'delete from clair_questions where workspace_id = %(ws)s',
    'delete from clair_messages where workspace_id = %(ws)s',
    'delete from usage_ledger where workspace_id = %(ws)s',
    'delete from clair_notes where workspace_id = %(ws)s',
    'delete from agent_runs where workspace_id = %(ws)s',
    'delete from clair_threads where workspace_id = %(ws)s',
    'delete from change_sets where workspace_id = %(ws)s',
    'delete from blocks where workspace_id = %(ws)s',      # one statement, so the self-references check at its end
]


def reset_workspace(conn, workspace_id, state: str = 'full', *, gcal_fixture: bool = False) -> dict:
    """Reseed one workspace inside the caller's transaction (take the workspace lock first: `db.transaction(ws)`).

    Returns {change_set_id, server_seq, epoch, apps, blocks, records}."""
    ws = str(workspace_id)
    keep = apps_for(state)
    member = conn.execute('select user_id from workspace_members where workspace_id = %s order by created_at limit 1',
                          (ws,)).fetchone()
    if member is None:
        raise ValueError(f'workspace {ws} has no member')
    user_id = member['user_id']

    for sql in WIPE:
        conn.execute(sql, {'ws': ws})

    blocks = build_blocks(ws, state, gcal_fixture)
    with conn.cursor() as cur:
        cur.executemany(
            'insert into blocks (id, workspace_id, parent_id, position, block_type, collection_id, properties) '
            'values (%s, %s, %s, %s, %s, %s, %s)',
            [(b['id'], ws, b['parent_id'], b['position'], b['block_type'], b['collection_id'], Jsonb(b['properties']))
             for b in blocks])

    # Activity history, then the seed change set itself
    for app, title, summary, at in data.HISTORY:
        if app in keep:
            conn.execute(
                "insert into change_sets (workspace_id, actor, user_id, origin, status, source, title, summary, "
                "created_at, updated_at) values (%s, 'clair', %s, 'clair', 'stitched', %s, %s, %s, %s, %s)",
                (ws, user_id, Jsonb({'kind': 'seed_history', 'label': title, 'at': at}), title, summary, at, at))
    n_records = sum(1 for b in blocks if b['block_type'] == 'record')
    cs = conn.execute(
        "insert into change_sets (workspace_id, actor, origin, status, source, title, summary) "
        "values (%s, 'system', 'seed', 'stitched', %s, %s, %s) returning id",
        (ws, Jsonb({'kind': 'seed', 'label': f'Demo seed ({state})', 'state': state, 'gcal_fixture': gcal_fixture}),
         f'Demo seed ({state})', f'{len(keep)} apps, {n_records} records')).fetchone()['id']
    seq = conn.execute(
        "insert into events (workspace_id, change_set_id, block_id, field_path, old, new) "
        "values (%s, %s, null, 'status', null, %s) returning server_seq",
        (ws, cs, Jsonb('stitched'))).fetchone()['server_seq']
    conn.execute('update change_sets set stitched_seq = %s where id = %s', (seq, cs))

    # ledger and Clair notes
    with conn.cursor() as cur:
        cur.executemany(
            'insert into usage_ledger (workspace_id, user_id, period, kind, credits, created_at) '
            'values (%s, %s, %s, %s, %s, %s)',
            [(ws, user_id if kind != 'grant' else None, data.LEDGER_PERIOD, kind, credits, at)
             for kind, credits, at in data.LEDGER])
        cur.executemany(
            'insert into clair_notes (workspace_id, user_id, text, kind, created_at) values (%s, %s, %s, %s, %s)',
            [(ws, user_id, text, kind, at) for text, kind, at in data.CLAIR_NOTES])

    page = {app: str(block_id(ws, app)) for app in keep}
    settings = dict(data.WORKSPACE_SETTINGS, pins=[page[a] for a in data.PINS if a in page])
    epoch = conn.execute(
        'update workspaces set settings = settings || %s, tz = %s, read_level = %s, epoch = epoch + 1 '
        'where id = %s returning epoch',
        (Jsonb(settings), data.WORKSPACE['tz'], data.WORKSPACE['read_level'], ws)).fetchone()['epoch']
    conn.execute(
        'update workspace_members set display_name = %s, app_opens = %s where workspace_id = %s',
        (data.DISPLAY_NAME, Jsonb({page[a]: t for a, t in data.APP_OPENS.items() if a in page}), ws))
    return {'change_set_id': str(cs), 'server_seq': seq, 'epoch': epoch, 'apps': len(keep), 'blocks': len(blocks),
            'records': n_records}


def ensure_workspace(conn, user_id, workspace_id=None) -> str:
    """Return the user's workspace, creating it and the membership if missing. Prefers `workspace_id` if it exists."""
    if workspace_id:
        row = conn.execute('select id from workspaces where id = %s', (str(workspace_id),)).fetchone()
        if row:
            conn.execute('insert into workspace_members (workspace_id, user_id, display_name) values (%s, %s, %s) '
                         'on conflict do nothing', (str(workspace_id), str(user_id), data.DISPLAY_NAME))
            return str(row['id'])
    row = conn.execute('select workspace_id from workspace_members where user_id = %s order by created_at limit 1',
                       (str(user_id),)).fetchone()
    if row:
        return str(row['workspace_id'])
    ws = conn.execute('insert into workspaces (name, tz, read_level, settings) values (%s, %s, %s, %s) returning id',
                      (data.WORKSPACE['name'], data.WORKSPACE['tz'], data.WORKSPACE['read_level'],
                       Jsonb(data.WORKSPACE_SETTINGS))).fetchone()['id']
    conn.execute('insert into workspace_members (workspace_id, user_id, display_name) values (%s, %s, %s)',
                 (ws, str(user_id), data.DISPLAY_NAME))
    return str(ws)


# ---------------------------------------------------------------- auth (Supabase Admin API; server key only)

PASSWORD_FILE = Path.home() / '.config' / 'quilt' / 'demo-password'


def demo_password(env_password: str | None = None) -> str:
    """DEMO_PASSWORD if set, else the saved one, else a new one saved with mode 600. Never printed."""
    if env_password:
        return env_password
    if PASSWORD_FILE.exists():
        return PASSWORD_FILE.read_text().strip()
    PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    pw = secrets.token_urlsafe(18)
    PASSWORD_FILE.touch(mode=0o600)
    PASSWORD_FILE.chmod(0o600)
    PASSWORD_FILE.write_text(pw + '\n')
    return pw


def ensure_demo_user(supabase_url: str, service_key: str, email: str, password: str) -> str:
    """Create the confirmed email+password user if missing; otherwise make sure its password and confirmation match.
    Returns the user id."""
    base = supabase_url.rstrip('/') + '/auth/v1/admin/users'
    headers = {'apikey': service_key, 'Authorization': f'Bearer {service_key}'}
    with httpx.Client(timeout=20, headers=headers) as http:
        user = _find_user(http, base, email)
        if user is None:
            r = http.post(base, json={'email': email, 'password': password, 'email_confirm': True,
                                      'user_metadata': {'display_name': data.DISPLAY_NAME}})
            if r.status_code >= 400:
                raise RuntimeError(f'creating {email} failed: HTTP {r.status_code} {r.json().get("msg", "")}')
            return r.json()['id']
        r = http.put(f"{base}/{user['id']}", json={'password': password, 'email_confirm': True})
        if r.status_code >= 400:
            raise RuntimeError(f'updating {email} failed: HTTP {r.status_code}')
        return user['id']


def _find_user(http: httpx.Client, base: str, email: str) -> dict | None:
    page = 1
    while True:
        r = http.get(base, params={'page': page, 'per_page': 200})
        r.raise_for_status()
        users = r.json().get('users', [])
        for u in users:
            if (u.get('email') or '').lower() == email.lower():
                return u
        if len(users) < 200:
            return None
        page += 1


def counts(conn, workspace_id) -> dict[str, Any]:
    """Apps and live records per app, for verification."""
    rows = conn.execute(
        "select p.properties->>'key' as app, count(r.id) as n from blocks p "
        "left join blocks c on c.parent_id = p.id and c.deleted_at is null "
        "left join blocks r on r.collection_id = c.id and r.deleted_at is null "
        "where p.workspace_id = %s and p.block_type = 'page' and p.deleted_at is null group by 1 order by 1",
        (str(workspace_id),)).fetchall()
    return {r['app']: r['n'] for r in rows}
