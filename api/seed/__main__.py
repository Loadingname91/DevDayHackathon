"""Seed the demo account: `python -m api.seed --state full|before|both [--gcal-fixture]`.

Creates the demo auth users if missing (Supabase Admin API, confirmed email), their workspaces and memberships, then
reseeds. `full` reseeds DEMO_WORKSPACE_ID (sam@quilt.demo); `before` reseeds DEMO_RECORD_WORKSPACE_ID (the recording's
8-app state, its own user so the API's "caller's only membership" rule holds). The password comes from DEMO_PASSWORD
or ~/.config/quilt/demo-password (made once, mode 600) and is never printed. New ids are appended to api/.env only
when the key is absent. Prints ids and counts only.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from ..db import transaction
from ..settings import settings
from . import load

ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


def env_keys() -> dict[str, str]:
    out = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            m = re.match(r'\s*([A-Z0-9_]+)\s*=\s*(.*)$', line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip('"\'')
    return out


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or env_keys().get(name) or default


def append_env(key: str, value: str) -> None:
    if key in os.environ or key in env_keys():
        return
    text = ENV_FILE.read_text() if ENV_FILE.exists() else ''
    with ENV_FILE.open('a') as f:
        if text and not text.endswith('\n'):
            f.write('\n')
        f.write(f'{key}={value}\n')
    print(f'appended {key} to api/.env')


def seed_one(state: str, email: str, ws_env: str, user_env: str, password: str, gcal: bool) -> None:
    s = settings()
    user_id = load.ensure_demo_user(s.supabase_url, s.supabase_service_role_key, email, password)
    with transaction() as conn:
        ws = load.ensure_workspace(conn, user_id, env(ws_env))
    with transaction(ws) as conn:
        result = load.reset_workspace(conn, ws, state, gcal_fixture=gcal)
        per_app = load.counts(conn, ws)
    append_env(ws_env, ws)
    append_env(user_env, user_id)
    print(f'[{state}] user {user_id} workspace {ws} epoch {result["epoch"]} change_set {result["change_set_id"]}')
    print(f'[{state}] {result["apps"]} apps, {result["records"]} records: '
          + ', '.join(f'{k} {v}' for k, v in per_app.items()))


def main() -> None:
    ap = argparse.ArgumentParser(prog='python -m api.seed')
    ap.add_argument('--state', choices=['full', 'before', 'both'], default='full')
    ap.add_argument('--gcal-fixture', action='store_true', default=env('DEMO_GCAL_FIXTURE') == '1',
                    help='write the four Google events as fixtures (DEMO_GCAL_FIXTURE=1)')
    args = ap.parse_args()
    password = load.demo_password(os.environ.get('DEMO_PASSWORD'))
    if args.state in ('full', 'both'):
        seed_one('full', env('DEMO_EMAIL', 'sam@quilt.demo'), 'DEMO_WORKSPACE_ID', 'DEMO_USER_ID', password,
                 args.gcal_fixture)
    if args.state in ('before', 'both'):
        seed_one('before', env('DEMO_RECORD_EMAIL', 'sam.record@quilt.demo'), 'DEMO_RECORD_WORKSPACE_ID',
                 'DEMO_RECORD_USER_ID', password, args.gcal_fixture)


if __name__ == '__main__':
    main()
