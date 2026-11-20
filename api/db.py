"""Database access: one short connection per request through Supabase's transaction-mode pooler.

prepare_threshold=None turns off server-side prepared statements, which the transaction pooler
can't keep across transactions (backend.md §11 #44). Every command runs inside `transaction()`
and takes the workspace's advisory lock first, so server_seq order equals commit order (§5, #45).
"""
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .settings import settings


def connect() -> psycopg.Connection:
    return psycopg.connect(settings().database_url, prepare_threshold=None, row_factory=dict_row, connect_timeout=10)


@contextmanager
def transaction(workspace_id: UUID | None = None) -> Iterator[psycopg.Connection]:
    """A real Postgres transaction; with a workspace id, it holds that workspace's lock until commit."""
    with connect() as conn:
        with conn.transaction():
            if workspace_id is not None:
                conn.execute('select pg_advisory_xact_lock(hashtextextended(%s::text, 0))', (str(workspace_id),))
            yield conn


def ping() -> bool:
    try:
        with connect() as conn:
            return conn.execute('select 1 as ok').fetchone()['ok'] == 1
    except psycopg.Error:
        return False
