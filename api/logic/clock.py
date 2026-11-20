"""Server clock and workspace-zone helpers (spec/backend.md §3).

Public API:
    DEFAULT_TZ: str = "America/Denver"
    DEMO_NOW_CANONICAL: str = "2026-11-20T17:45:00-07:00"
    zone(tz: str) -> ZoneInfo
    now(tz: str = DEFAULT_TZ, demo_now: str | datetime | None = None) -> datetime
        Aware datetime in `tz`. `demo_now` wins; else env DEMO_NOW; else the UTC clock.
        DEMO_NOW may be ISO with an offset, naive ISO (wall time in `tz`) or "1"/"true"
        (the canonical Fri 20 Nov 2026 5:45 pm).
    localize(naive: datetime, tz: str) -> datetime
        Attach the zone to a wall time. Nonexistent times move forward by the gap
        (2:30 am on a spring-forward day -> 3:30 am); repeated times take the first (fold=0).
    parse_value(value: str | date | datetime, tz: str) -> date | datetime
        "YYYY-MM-DD" -> date; ISO with offset -> aware datetime; ISO without offset ->
        wall time in `tz` (localize).
    to_local(dt: datetime, tz: str) -> datetime
    day_of(value, tz: str) -> date          # the local day of a date or datetime value
    midnight(d: date, tz: str) -> datetime  # local midnight as an aware datetime
    instant(value, tz: str) -> datetime     # a date is read as its local midnight
    window_bounds(window, now: datetime, tz: str) -> tuple[datetime, datetime] | None
        "today" | "week" | "month" | "all" | {"days": N}. Built from local midnights,
        never by adding 24 hours. None for "all". End is exclusive.
    within_days(spec: str, now: datetime, tz: str) -> tuple[date | None, date | None]
        Day bounds (inclusive) for the `within` filter: today, week, past, future, 7d, -7d.
    iso(value) -> str                       # date -> "YYYY-MM-DD"; datetime -> ISO with offset
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

DEFAULT_TZ = "America/Denver"
DEMO_NOW_CANONICAL = "2026-11-20T17:45:00-07:00"


@lru_cache(maxsize=64)
def zone(tz: str) -> ZoneInfo:
    return ZoneInfo(tz)


def localize(naive: datetime, tz: str) -> datetime:
    """Wall time -> aware datetime in tz. Nonexistent: forward by the gap. Repeated: first."""
    z = zone(tz)
    aware = naive.replace(tzinfo=z, fold=0)
    # Round-trip through UTC: for a wall time inside a spring-forward gap, fold=0 uses the
    # offset before the gap, which lands on the instant "gap minutes later" on the far side.
    return aware.astimezone(timezone.utc).astimezone(z)


def to_local(dt: datetime, tz: str) -> datetime:
    if dt.tzinfo is None:
        return localize(dt, tz)
    return dt.astimezone(zone(tz))


def _parse_demo_now(raw: str | datetime, tz: str) -> datetime:
    if isinstance(raw, datetime):
        return to_local(raw, tz)
    raw = raw.strip()
    if raw.lower() in ("1", "true", "yes", "on", "demo"):
        raw = DEMO_NOW_CANONICAL
    v = parse_value(raw, tz)
    if isinstance(v, datetime):
        return to_local(v, tz)
    return midnight(v, tz)


def now(tz: str = DEFAULT_TZ, demo_now: str | datetime | None = None) -> datetime:
    if demo_now is not None:
        return _parse_demo_now(demo_now, tz)
    env = os.environ.get("DEMO_NOW")
    if env:
        return _parse_demo_now(env, tz)
    return datetime.now(timezone.utc).astimezone(zone(tz))


def parse_value(value: str | date | datetime, tz: str) -> date | datetime:
    if isinstance(value, datetime):
        return to_local(value, tz) if value.tzinfo is None else value
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if len(s) == 10 and "T" not in s:
        return date.fromisoformat(s)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return localize(dt, tz)
    return dt


def is_datetime_str(value) -> bool:
    return isinstance(value, datetime) or (isinstance(value, str) and "T" in value)


def midnight(d: date, tz: str) -> datetime:
    return localize(datetime(d.year, d.month, d.day), tz)


def day_of(value, tz: str) -> date:
    v = parse_value(value, tz)
    if isinstance(v, datetime):
        return v.astimezone(zone(tz)).date()
    return v


def instant(value, tz: str) -> datetime:
    v = parse_value(value, tz)
    if isinstance(v, datetime):
        return v
    return midnight(v, tz)


def iso(value) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def window_bounds(window, now_: datetime, tz: str):
    today = to_local(now_, tz).date()
    if window is None or window == "all":
        return None
    if isinstance(window, dict) and "days" in window:
        n = int(window["days"])
        return midnight(today - timedelta(days=n - 1), tz), midnight(today + timedelta(days=1), tz)
    if window == "today":
        return midnight(today, tz), midnight(today + timedelta(days=1), tz)
    if window == "week":
        ws = week_start(today)
        return midnight(ws, tz), midnight(ws + timedelta(days=7), tz)
    if window == "month":
        first = today.replace(day=1)
        nxt = (first + timedelta(days=32)).replace(day=1)
        return midnight(first, tz), midnight(nxt, tz)
    raise ValueError(f"unknown window {window!r}")


def within_days(spec: str, now_: datetime, tz: str):
    """Inclusive day bounds (lo, hi) for `within`; None means unbounded."""
    today = to_local(now_, tz).date()
    if spec == "today":
        return today, today
    if spec == "week":
        ws = week_start(today)
        return ws, ws + timedelta(days=6)
    if spec == "past":
        return None, today - timedelta(days=1)
    if spec == "future":
        return today + timedelta(days=1), None
    if spec == "7d":
        return today, today + timedelta(days=6)
    if spec == "-7d":
        return today - timedelta(days=6), today
    raise ValueError(f"unknown within {spec!r}")
