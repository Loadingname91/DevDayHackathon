"""The virtual `*dated` source and Home's Next up (spec/backend.md §3, §8a).

For each collection with `calendar: true` and a `dateField`, every live, not-done record
dated inside the window becomes a row; a record with a repeat value contributes its
occurrences instead (logged and skipped ones are left out). A record with an `ends` value
is in the window when its span overlaps it (Thanksgiving at home, Thu 26 to Sat 28 Nov).

Row shape (web/src/api/types.ts DatedRow):
    {"at": "2026-11-20T18:00:00-07:00" | "2026-11-22", "title", "sub", "app", "record_id",
     "occurrence"?, "ends"?, "all_day"?, "source"?}
- title: "<label> · <record title>" when the collection has a `label`; a collection may
  instead give `datedTitle`, a template like "{name} renews · {amount}" (money fields
  are worded with cents).
- sub: the app's name; "Google Calendar" for a record with source "google".
- all_day: true for every row whose `at` is a plain day.

Public API:
    index_apps(apps: list[dict]) -> dict[str, tuple[dict, dict]]   # ref -> (app, collection)
    collection_ref(record: dict) -> str
    live(records: list[dict]) -> list[dict]                        # drops deleted_at rows
    repeat_field(collection: dict) -> str | None
    dated_rows(apps, records, lo: date, hi: date, tz=DEFAULT_TZ, *, app_keys=None)
        -> list[row] sorted by time (inclusive day bounds, in the workspace zone)
    dated_window(apps, records, window, now, tz=DEFAULT_TZ) -> list[row]
        window: today | week | month | all-not-allowed | {"days": N} | (lo, hi) dates
    next_up(apps, records, now, tz=DEFAULT_TZ, *, hours=72, limit=3) -> list[row]
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from . import fmt
from .clock import DEFAULT_TZ, day_of, instant, iso, parse_value, to_local, window_bounds
from .repeats import expand, normalize_repeat


def collection_key(c: dict) -> str:
    return c.get("key") or c.get("id")


def index_apps(apps: list[dict]) -> dict:
    out = {}
    for a in apps:
        for c in a.get("collections") or []:
            out[f"{a['key']}/{collection_key(c)}"] = (a, c)
    return out


def collection_ref(record: dict) -> str:
    return record.get("collection") or record.get("ref")


def live(records: list[dict]) -> list[dict]:
    return [r for r in records if not r.get("deleted_at")]


def field_types(collection: dict) -> dict:
    return {f["key"]: f.get("type") for f in collection.get("fields") or []}


def repeat_field(collection: dict) -> str | None:
    for f in collection.get("fields") or []:
        if f.get("type") == "repeat":
            return f["key"]
    return None


_TPL = re.compile(r"\{(\w+)\}")


def _title(app: dict, c: dict, props: dict) -> str:
    types = field_types(c)
    tpl = c.get("datedTitle")
    if tpl:
        def sub(m):
            k = m.group(1)
            v = props.get(k)
            if v is None:
                return ""
            if types.get(k) == "money":
                return fmt.money_row(v)
            return str(v)
        return _TPL.sub(sub, tpl)
    t = props.get(c.get("titleField") or "title")
    t = "" if t is None else str(t)
    label = c.get("label")
    return f"{label} · {t}" if label else t


def _base(app, c, record, props):
    row = {"title": _title(app, c, props),
           "sub": "Google Calendar" if props.get("source") == "google" else app.get("name", app["key"]),
           "app": app["key"], "record_id": record["id"]}
    return row


def _row(base: dict, at, ends=None, occurrence=None, source=None) -> dict:
    row = {"at": iso(at), **base}
    if occurrence:
        row["occurrence"] = occurrence
    if ends is not None:
        row["ends"] = iso(ends)
    if isinstance(at, date) and not isinstance(at, datetime):
        row["all_day"] = True
    if source:
        row["source"] = source
    return row


def _sort_key(row: dict, tz: str):
    return (instant(row["at"], tz), row["title"], row["record_id"])


def dated_rows(apps: list[dict], records: list[dict], lo: date, hi: date,
               tz: str = DEFAULT_TZ, *, app_keys=None) -> list[dict]:
    idx = index_apps(apps)
    rows = []
    for r in live(records):
        ref = collection_ref(r)
        if ref not in idx:
            continue
        app, c = idx[ref]
        if app_keys is not None and app["key"] not in app_keys:
            continue
        if not c.get("calendar") or not c.get("dateField"):
            continue
        props = r.get("properties") or {}
        if props.get("done") is True:
            continue
        df = c["dateField"]
        base = _base(app, c, r, props)
        source = props.get("source")
        rf = repeat_field(c)
        rep = props.get(rf) if rf else None
        if rep:
            rep = normalize_repeat(rep, props.get(df), tz)
            span = None
            if props.get("ends") and props.get(df):
                a0, e0 = parse_value(props[df], tz), parse_value(props["ends"], tz)
                if isinstance(a0, datetime) and isinstance(e0, datetime):
                    span = e0 - a0
            ftype = next((f.get("type") for f in c.get("fields", []) if f.get("key") == df), None)
            day_only = ftype == "date" or (isinstance(props.get(df), str) and len(props[df]) == 10)
            for o in expand(rep, lo, hi, tz, include_logged=False):
                at = o["at"]
                if day_only and isinstance(at, datetime):
                    at = to_local(at, tz).date()  # a date field repeats as all-day rows, whatever start holds
                ends = at + span if span is not None and isinstance(at, datetime) else None
                rows.append(_row(base, at, ends, o["occurrence"], source))
            continue
        val = props.get(df)
        if val in (None, ""):
            continue
        at = parse_value(val, tz)
        start_day = day_of(at, tz)
        ends = parse_value(props["ends"], tz) if props.get("ends") else None
        end_day = day_of(ends, tz) if ends is not None else start_day
        if end_day < start_day:
            end_day = start_day
        if start_day > hi or end_day < lo:
            continue
        at_out = to_local(at, tz) if isinstance(at, datetime) else at
        ends_out = (to_local(ends, tz) if isinstance(ends, datetime) else ends) if ends is not None else None
        rows.append(_row(base, at_out, ends_out, None, source))
    rows.sort(key=lambda row: _sort_key(row, tz))
    return rows


def dated_window(apps, records, window, now: datetime, tz: str = DEFAULT_TZ, **kw) -> list[dict]:
    if isinstance(window, tuple):
        lo, hi = window
    else:
        b = window_bounds(window, now, tz)
        if b is None:
            raise ValueError("*dated needs a bounded window")
        lo = b[0].date()
        hi = (b[1] - timedelta(seconds=1)).astimezone(b[0].tzinfo).date()
    return dated_rows(apps, records, lo, hi, tz, **kw)


def next_up(apps, records, now: datetime, tz: str = DEFAULT_TZ, *, hours: int = 72,
            limit: int = 3) -> list[dict]:
    now_l = to_local(now, tz)
    end = now_l + timedelta(hours=hours)
    today = now_l.date()
    rows = dated_rows(apps, records, today, to_local(end, tz).date(), tz)
    out = []
    for row in rows:
        at = parse_value(row["at"], tz)
        if isinstance(at, datetime):
            if not (now_l <= at < end):
                continue
        else:
            if at < today or instant(at, tz) >= end:
                continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
