"""How the server words numbers, money and dates (spec/backend.md §6, ui-tech-plan §3).

The client shows these strings as given; it never formats a figure itself.

Public API:
    NULL_TEXT = "—"; ERR_TEXT = "#ERR"
    is_err(v) -> bool                         # {"error": "#ERR", "reason": ...}
    err(reason: str) -> dict
    money_face(cents) -> str                  # "$412", "$376" (from 37617), "$38.46", "$1,200"
    money_row(cents) -> str                   # "$35.83", "$142.00", "$1,200.00"
    number(n) -> str                          # "1,140", "7", "5.5", "12,450"
    count(n) -> str                           # "12"
    duration(minutes) -> str                  # "25 min", "1 h 5 min"
    day_label(d: date, today: date | None) -> str        # "Tue 27 Oct" (+ " 2027" off-year)
    time_label(dt: datetime, short=False) -> str          # "9:00 am"; short: "6 pm"
    when_label(value, tz, today=None) -> str              # "Sat 12 Dec · 9:00 am" / "Sun 22 Nov"
    format_value(value, fmt: str, tz=DEFAULT_TZ, *, face=True, today=None) -> str
        fmt is one of money | count | number | duration | text. Null -> "—", error -> "#ERR".

Money on faces (resolved conflict, see the report): whole dollars when the amount is a
whole number of dollars or at least $100 ("$412", "$376" from $376.17); below $100 with
cents it keeps the cents ("$38.46", Subscriptions' canonical face in §2.3).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from .clock import DEFAULT_TZ, parse_value, to_local

NULL_TEXT = "—"
ERR_TEXT = "#ERR"


def is_err(v) -> bool:
    return isinstance(v, dict) and v.get("error") == "#ERR"


def err(reason: str) -> dict:
    return {"error": "#ERR", "reason": reason}


def _sign(neg: bool) -> str:
    return "-" if neg else ""


def money_face(cents) -> str:
    c = int(Decimal(str(cents)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    neg, c = c < 0, abs(c)
    if c % 100 == 0 or c >= 10000:
        dollars = int((Decimal(c) / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        return f"{_sign(neg)}${dollars:,}"
    return f"{_sign(neg)}${c // 100:,}.{c % 100:02d}"


def money_row(cents) -> str:
    c = int(Decimal(str(cents)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    neg, c = c < 0, abs(c)
    return f"{_sign(neg)}${c // 100:,}.{c % 100:02d}"


def number(n) -> str:
    d = Decimal(str(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d == d.to_integral_value():
        return f"{int(d):,}"
    s = f"{d:,.2f}".rstrip("0").rstrip(".")
    return s


def count(n) -> str:
    return number(n)


def duration(minutes) -> str:
    m = int(Decimal(str(minutes)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if m < 60:
        return f"{m} min"
    h, r = divmod(m, 60)
    return f"{h} h" if r == 0 else f"{h} h {r} min"


def day_label(d: date, today: date | None = None) -> str:
    s = f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"
    if today is not None and d.year != today.year:
        s += f" {d.year}"
    return s


def time_label(dt: datetime, short: bool = False) -> str:
    h = dt.hour % 12 or 12
    ampm = "am" if dt.hour < 12 else "pm"
    if short and dt.minute == 0:
        return f"{h} {ampm}"
    return f"{h}:{dt.minute:02d} {ampm}"


def when_label(value, tz: str = DEFAULT_TZ, today: date | None = None) -> str:
    v = parse_value(value, tz)
    if isinstance(v, datetime):
        lv = to_local(v, tz)
        return f"{day_label(lv.date(), today)} · {time_label(lv)}"
    return day_label(v, today)


def _looks_like_date(v) -> bool:
    return isinstance(v, (date, datetime)) or (
        isinstance(v, str) and len(v) >= 10 and v[4:5] == "-" and v[7:8] == "-" and v[:4].isdigit())


def format_value(value, fmt: str, tz: str = DEFAULT_TZ, *, face: bool = True,
                 today: date | None = None) -> str:
    if is_err(value):
        return ERR_TEXT
    if value is None:
        return NULL_TEXT
    if fmt == "text":
        if _looks_like_date(value):
            return when_label(value, tz, today)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, (int, float, Decimal)):
            return number(value)
        return str(value)
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        if _looks_like_date(value):
            return when_label(value, tz, today)
        return str(value)
    if fmt == "money":
        return money_face(value) if face else money_row(value)
    if fmt == "count":
        return count(value)
    if fmt == "duration":
        return duration(value)
    return number(value)
