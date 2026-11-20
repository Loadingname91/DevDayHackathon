"""SSE events of a Clair run (clair-agent.md §2): validate, persist, format.

Every event is validated against the contract's `ClairEvent` union (api/models.py), appended to
`agent_runs.events` (the polling fallback, `GET /clair/runs/{id}/events`), and pushed to the live
stream's queue. The stream always ends with `done`.
"""
from __future__ import annotations

import json
import queue
import time
from typing import Any, Callable
from uuid import UUID

from psycopg.types.json import Jsonb
from pydantic import TypeAdapter

from .. import db
from ..models import ClairEvent

_EVENT = TypeAdapter(ClairEvent)
END = object()   # queue sentinel: the run is over


def validate(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """The event as JSON-ready dict `{event, data}`; raises if it breaks the contract."""
    ev = _EVENT.validate_python({'event': name, 'data': data})
    return ev.model_dump(mode='json', by_alias=True, exclude_none=True)


def sse(index: int, ev: dict[str, Any]) -> str:
    return f"id: {index}\nevent: {ev['event']}\ndata: {json.dumps(ev['data'], separators=(',', ':'))}\n\n"


def persist_db(run_id: UUID, ev: dict[str, Any]) -> None:
    with db.connect() as conn:
        conn.execute('update agent_runs set events = events || %s where id = %s', (Jsonb([ev]), run_id))
        conn.commit()


class Emitter:
    """One per run. `emit()` is safe to call from the worker thread; the HTTP stream reads `q`."""

    def __init__(self, run_id: UUID, persist: Callable[[UUID, dict], None] | None = persist_db):
        self.run_id = run_id
        self.events: list[dict[str, Any]] = []
        self.q: queue.Queue = queue.Queue()
        self.persist = persist
        self.t0 = time.monotonic()
        self.timings: dict[str, int] = {}
        self.closed = False

    def emit(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        if self.closed:
            return {}
        ev = validate(name, data)
        self.events.append(ev)
        self.timings.setdefault(name, int((time.monotonic() - self.t0) * 1000))
        if self.persist is not None:
            try:
                self.persist(self.run_id, ev)
            except Exception:   # the live stream still carries it; polling loses only this event
                pass
        self.q.put(ev)
        if name == 'done':
            self.closed = True
            self.q.put(END)
        return ev

    def stream(self, heartbeat: float = 15.0):
        """Sync generator of SSE text for StreamingResponse. Ends after `done`."""
        i = 0
        while True:
            try:
                ev = self.q.get(timeout=heartbeat)
            except queue.Empty:
                yield ': keep-alive\n\n'
                continue
            if ev is END:
                return
            yield sse(i, ev)
            i += 1
