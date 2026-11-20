"""Repeat rules (spec/backend.md §3 "Repeats", §11 rows 15, 16, 27, 28, 29).

A repeat value is {"rule", "start", "log", "skip"}:
- rule:  RRULE subset FREQ=DAILY|WEEKLY|MONTHLY, BYDAY, INTERVAL, UNTIL.
- start: local wall time with no offset ("2026-10-23T20:00"), or a plain day
         ("2026-10-22") for a series on a `date` field (all-day occurrences).
- log:   occurrence days completed. skip: occurrence days skipped.
Occurrences are expanded in naive wall time with dateutil, then the workspace zone is
attached (8 pm stays 8 pm across DST; nonexistent wall times move forward by the gap,
repeated ones take the first).

An occurrence is a dict:
    {"occurrence": "YYYY-MM-DD", "at": datetime | date, "logged": bool, "skipped": bool}

Public API:
    class RepeatError(ValueError)
    validate_rule(rule: str) -> list[str]                      # [] when valid
    normalize_repeat(value, date_value=None, tz=DEFAULT_TZ) -> dict
        A plain rule string becomes {rule, start, log: [], skip: []} with `start` from the
        record's date field value. A dict is returned with log/skip defaulted.
    wall(value, tz) -> str                                     # value as wall-time "start"
    is_all_day(repeat) -> bool
    expand(repeat, lo: date, hi: date, tz, *, include_logged=True, include_skipped=False)
        -> list[occurrence]   # every occurrence whose local day is in [lo, hi] (inclusive)
    occurrence_at(repeat, day: date | str, tz) -> datetime | date
    has_occurrence(repeat, day, tz) -> bool
    next_open(repeat, tz, *, after_day: date | None = None, after: datetime | None = None)
        -> occurrence | None  # first occurrence not logged/skipped, strictly after
                              # `after_day` (by day) or `after` (by instant)
    complete_occurrence(repeat, occurrence, now, tz) -> (new_repeat, next_value: str | None)
    skip_occurrence(repeat, occurrence, now, tz) -> (new_repeat, next_value: str | None)
        Append to log/skip; next_value is the next open occurrence after the later of the
        occurrence and today (ISO; a day for all-day series). None: series is over -> done.
    move_occurrence(record: dict, date_field: str, repeat_field: str, occurrence: str,
                    new_value: str, now, tz) -> (series_updates: dict, one_off_props: dict)
        "Edit this one only" for the date field (§3 Moving one occurrence).
    edit_rule(repeat, new_rule, now, tz) -> new_repeat         # §11 row 27
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone

from dateutil.rrule import rrulestr

from .clock import DEFAULT_TZ, iso, localize, parse_value, to_local, zone


class RepeatError(ValueError):
    pass


_ALLOWED = {"FREQ", "BYDAY", "INTERVAL", "UNTIL"}
_FREQS = {"DAILY", "WEEKLY", "MONTHLY"}
_DAYS = {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}
_UNTIL_RE = re.compile(r"^\d{8}(T\d{6}Z?)?$")
_MAX_ITER = 20000


def validate_rule(rule: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(rule, str) or not rule.strip():
        return ["repeat rule is empty"]
    body = rule.strip()
    if body.upper().startswith("RRULE:"):
        body = body[6:]
    parts = {}
    for part in body.split(";"):
        if not part:
            continue
        if "=" not in part:
            issues.append(f"bad rule part {part!r}")
            continue
        k, v = part.split("=", 1)
        k = k.upper()
        if k not in _ALLOWED:
            issues.append(f"{k} is not supported (use FREQ, BYDAY, INTERVAL, UNTIL)")
        parts[k] = v
    freq = parts.get("FREQ")
    if freq is None:
        issues.append("FREQ is required")
    elif freq.upper() not in _FREQS:
        issues.append(f"FREQ={freq} is not supported (DAILY, WEEKLY, MONTHLY)")
    if "BYDAY" in parts:
        for d in parts["BYDAY"].split(","):
            if d.upper() not in _DAYS:
                issues.append(f"BYDAY value {d!r} is not supported")
    if "INTERVAL" in parts:
        try:
            if int(parts["INTERVAL"]) < 1:
                raise ValueError
        except ValueError:
            issues.append("INTERVAL must be a positive whole number")
    if "UNTIL" in parts and not _UNTIL_RE.match(parts["UNTIL"]):
        issues.append("UNTIL must look like 20261210 or 20261210T235959")
    return issues


def _check(rule: str) -> None:
    issues = validate_rule(rule)
    if issues:
        raise RepeatError("; ".join(issues))


def is_all_day(repeat: dict) -> bool:
    return "T" not in str(repeat.get("start", ""))


def wall(value, tz: str = DEFAULT_TZ) -> str:
    """A date/datetime value as the wall-time `start` string (no offset)."""
    v = parse_value(value, tz)
    if isinstance(v, datetime):
        return to_local(v, tz).strftime("%Y-%m-%dT%H:%M")
    return v.isoformat()


def normalize_repeat(value, date_value=None, tz: str = DEFAULT_TZ) -> dict:
    if isinstance(value, str):
        if date_value is None:
            raise RepeatError("a repeat rule needs the record's date to start from")
        _check(value)
        return {"rule": value, "start": wall(date_value, tz), "log": [], "skip": []}
    if not isinstance(value, dict) or "rule" not in value:
        raise RepeatError("repeat must be a rule string or {rule, start, log, skip}")
    _check(value["rule"])
    start = value.get("start")
    if start is None:
        if date_value is None:
            raise RepeatError("repeat.start is missing")
        start = wall(date_value, tz)
    elif "T" in str(start) and ("+" in str(start)[10:] or str(start).endswith("Z") or "-" in str(start)[10:]):
        start = wall(start, tz)  # an offset slipped in: keep the wall time only
    return {
        "rule": value["rule"],
        "start": start,
        "log": list(value.get("log") or []),
        "skip": list(value.get("skip") or []),
    }


def _start_naive(repeat: dict) -> datetime:
    s = str(repeat["start"])
    if "T" not in s:
        return datetime.combine(date.fromisoformat(s), time(0, 0))
    return datetime.fromisoformat(s[:16]) if len(s) >= 16 else datetime.fromisoformat(s)


def _rule_body(rule: str, tz: str) -> str:
    body = rule.strip()
    if body.upper().startswith("RRULE:"):
        body = body[6:]
    out = []
    for part in body.split(";"):
        if part.upper().startswith("UNTIL=") and part.upper().endswith("Z"):
            # UTC UNTIL -> local wall time, since we expand in naive wall time.
            u = datetime.strptime(part[6:-1], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            part = "UNTIL=" + u.astimezone(zone(tz)).strftime("%Y%m%dT%H%M%S")
        out.append(part)
    return ";".join(out)


def _rrule(repeat: dict, tz: str):
    _check(repeat["rule"])
    return rrulestr(_rule_body(repeat["rule"], tz), dtstart=_start_naive(repeat))


def _occ(repeat: dict, naive: datetime, tz: str) -> dict:
    day = naive.date()
    d = day.isoformat()
    at = day if is_all_day(repeat) else localize(naive, tz)
    return {
        "occurrence": d,
        "at": at,
        "logged": d in (repeat.get("log") or []),
        "skipped": d in (repeat.get("skip") or []),
    }


def expand(repeat: dict, lo: date, hi: date, tz: str = DEFAULT_TZ, *,
           include_logged: bool = True, include_skipped: bool = False) -> list[dict]:
    rr = _rrule(repeat, tz)
    a = datetime.combine(lo, time(0, 0))
    b = datetime.combine(hi + timedelta(days=1), time(0, 0))
    out = []
    for naive in rr.between(a, b, inc=True):
        if naive >= b:
            continue
        o = _occ(repeat, naive, tz)
        if o["skipped"] and not include_skipped:
            continue
        if o["logged"] and not include_logged:
            continue
        out.append(o)
    return out


def _day(d) -> date:
    return d if isinstance(d, date) and not isinstance(d, datetime) else date.fromisoformat(str(d)[:10])


def has_occurrence(repeat: dict, day, tz: str = DEFAULT_TZ) -> bool:
    d = _day(day)
    return bool(expand(repeat, d, d, tz, include_skipped=True))


def occurrence_at(repeat: dict, day, tz: str = DEFAULT_TZ):
    d = _day(day)
    occ = expand(repeat, d, d, tz, include_skipped=True)
    if not occ:
        raise RepeatError(f"{d.isoformat()} is not an occurrence of this series")
    return occ[0]["at"]


def next_open(repeat: dict, tz: str = DEFAULT_TZ, *, after_day: date | None = None,
              after: datetime | None = None) -> dict | None:
    rr = _rrule(repeat, tz)
    done = set(repeat.get("log") or []) | set(repeat.get("skip") or [])
    if after_day is not None:
        cursor = datetime.combine(after_day + timedelta(days=1), time(0, 0))
        inc = True
    elif after is not None:
        cursor = to_local(after, tz).replace(tzinfo=None)
        inc = False
    else:
        raise RepeatError("next_open needs after_day or after")
    for _ in range(_MAX_ITER):
        nxt = rr.after(cursor, inc=inc)
        if nxt is None:
            return None
        inc = False
        cursor = nxt
        o = _occ(repeat, nxt, tz)
        if o["occurrence"] in done:
            continue
        if after is not None and after_day is None and isinstance(o["at"], datetime) and o["at"] <= after:
            continue
        return o
    return None


def _advance(repeat: dict, occurrence: str, kind: str, now: datetime, tz: str):
    occ_day = _day(occurrence)
    if not has_occurrence(repeat, occ_day, tz):
        raise RepeatError(f"{occurrence} is not an occurrence of this series")
    if occurrence in (repeat.get("log") or []) or occurrence in (repeat.get("skip") or []):
        raise RepeatError(f"{occurrence} is already {'done' if occurrence in repeat.get('log', []) else 'skipped'}")
    new = {**repeat, "log": list(repeat.get("log") or []), "skip": list(repeat.get("skip") or [])}
    new[kind].append(occ_day.isoformat())
    today = to_local(now, tz).date()
    nxt = next_open(new, tz, after_day=max(occ_day, today))
    return new, (iso(nxt["at"]) if nxt else None)


def complete_occurrence(repeat: dict, occurrence: str, now: datetime, tz: str = DEFAULT_TZ):
    return _advance(repeat, occurrence, "log", now, tz)


def skip_occurrence(repeat: dict, occurrence: str, now: datetime, tz: str = DEFAULT_TZ):
    return _advance(repeat, occurrence, "skip", now, tz)


def move_occurrence(record: dict, date_field: str, repeat_field: str, occurrence: str,
                    new_value: str, now: datetime, tz: str = DEFAULT_TZ):
    props = record.get("properties", record)
    repeat = props.get(repeat_field)
    if not repeat:
        raise RepeatError("the record has no repeat to move an occurrence of")
    repeat = normalize_repeat(repeat, props.get(date_field), tz)
    occ_day = _day(occurrence)
    occ = expand(repeat, occ_day, occ_day, tz, include_skipped=True)
    if not occ:
        raise RepeatError(f"{occurrence} is not an occurrence of this series")
    o = occ[0]
    if o["logged"]:
        raise RepeatError(f"{occurrence} is already done")
    if o["skipped"]:
        raise RepeatError(f"{occurrence} is already skipped")
    at = o["at"] if isinstance(o["at"], datetime) else localize(datetime.combine(o["at"], time(0)), tz)
    if at <= now:
        raise RepeatError(f"{occurrence} is not in the future")
    new_repeat = {**repeat, "skip": [*repeat["skip"], occ_day.isoformat()]}
    series_updates = {repeat_field: new_repeat}
    nxt = next_open(new_repeat, tz, after=now)
    nxt_value = iso(nxt["at"]) if nxt else None
    if nxt_value != props.get(date_field):
        series_updates[date_field] = nxt_value
    one_off = {k: v for k, v in props.items() if k != repeat_field and not k.startswith("_")}
    one_off[date_field] = iso(parse_value(new_value, tz))
    one_off["_moved_from"] = {"record_id": record.get("id"), "occurrence": occ_day.isoformat()}
    return series_updates, one_off


def edit_rule(repeat: dict, new_rule: str, now: datetime, tz: str = DEFAULT_TZ) -> dict:
    _check(new_rule)
    nxt = next_open(repeat, tz, after=now)
    if nxt is None:
        start_naive = _start_naive(repeat)
        today = to_local(now, tz).date()
        start = datetime.combine(today, start_naive.time())
    else:
        start = datetime.combine(_day(nxt["occurrence"]), _start_naive(repeat).time())
    start_s = start.date().isoformat() if is_all_day(repeat) else start.strftime("%Y-%m-%dT%H:%M")
    return {"rule": new_rule, "start": start_s,
            "log": list(repeat.get("log") or []), "skip": list(repeat.get("skip") or [])}
