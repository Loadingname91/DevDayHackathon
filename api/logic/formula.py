"""Formula engine (spec/backend.md §6; grammar in ui-tech-plan.md §3).

Everything is computed in memory over a workspace's live records at `now` in the
workspace zone. Nothing here touches the database.

Grammar:
    Term   = number | {"setting": key} | Query | {"limit": {"field", "option", "from"?}}
    Value  = Term | {"minus": [Term, Term]}
    Query  = {"agg": sum|count|avg|min|max|last, "from": "<app>/<collection>" | "*dated",
              "field"?, "where"?: [Filter], "window"?: today|week|month|all|{"days": N}}
    Filter = {"field", "op": eq|ne|lt|gt|within|empty, "value"}
    Row formula field: {"key", "type": "formula", "op": add|sub|mul|div, "a", "b"}

Repeating records (a record with a value in the collection's `repeat` field) become one
virtual row per occurrence: the date field is set to the occurrence and `done` is true
when it is in `repeat.log`; skipped ones are left out. As §6 says, a query over them sees
only the logged occurrences of a `count` (Workout's "count, window week" = 3, "window all" = 41) unless
it filters on `done` itself, in which case open occurrences are seen too (To-dos'
"done = false, window today" counts tonight's Take out recycling). With window `all` the
open side is the record itself (its next open occurrence). Other aggregates read the
records themselves (Subscriptions' sum(amount) is one row per subscription).

Semantics: null propagates through `minus` and row formulas; aggregates skip nulls; sum
and count of nothing are 0, avg/min/max/last of nothing are null; errors are values
{"error": "#ERR", "reason"} that propagate and never raise.

Public API:
    class Ctx(apps: list[dict], records: list[dict], now: datetime | None = None,
              tz: str = DEFAULT_TZ)
        .app(key) -> dict | None; .collection(ref) -> dict | None; .records(ref) -> list
        .today -> date
    evaluate(value, ctx: Ctx, app: dict | None = None) -> number | str | None | err
    run_query(query: dict, ctx: Ctx, app: dict | None = None) -> number | str | None | err
    query_rows(query: dict, ctx: Ctx) -> list[dict] | err     # filtered rows (views)
    match_filter(view: dict, flt: dict, ctx: Ctx, types: dict | None = None) -> bool
    get_field(view: dict, key: str, collection: dict | None) -> value  # row formulas too
    row_formula(field: dict, props: dict) -> number | None | err
    face(app: dict, ctx: Ctx) -> {"text", "label", "value"?}
    faces(ctx: Ctx) -> {app_key: face}
    format_term(value, fmt: str, ctx: Ctx, *, face=True) -> str
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from . import fmt as F
from .clock import (DEFAULT_TZ, day_of, instant, iso, now as clock_now, parse_value,
                    to_local, window_bounds, within_days)
from .dated import collection_key, collection_ref, dated_rows, field_types, index_apps, live, repeat_field
from .repeats import expand, normalize_repeat

err = F.err
is_err = F.is_err


class Ctx:
    def __init__(self, apps: list[dict], records: list[dict], now: datetime | None = None,
                 tz: str = DEFAULT_TZ):
        self.tz = tz
        self.now = to_local(now, tz) if now is not None else clock_now(tz)
        self.apps = apps
        self.by_key = {a["key"]: a for a in apps}
        self.idx = index_apps(apps)
        self.all_records = live(records)
        self._by_ref: dict[str, list[dict]] = {}
        for r in self.all_records:
            self._by_ref.setdefault(collection_ref(r), []).append(r)

    @property
    def today(self) -> date:
        return self.now.date()

    def app(self, key):
        return self.by_key.get(key)

    def collection(self, ref):
        hit = self.idx.get(ref)
        return hit[1] if hit else None

    def records(self, ref) -> list[dict]:
        return self._by_ref.get(ref, [])


# ---- fields -------------------------------------------------------------------------

def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        return v
    return None


def _clean(n):
    if isinstance(n, float) and n.is_integer():
        return int(n)
    if isinstance(n, Decimal):
        return int(n) if n == n.to_integral_value() else float(n)
    return n


def row_formula(field: dict, props: dict):
    def operand(x):
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return x
        v = props.get(x)
        if v is None or v == "":
            return None
        if is_err(v):
            return v
        n = _num(v)
        if n is None:
            return err(f"{x} is not a number")
        return n
    a, b = operand(field.get("a")), operand(field.get("b"))
    for x in (a, b):
        if is_err(x):
            return x
    if a is None or b is None:
        return None
    op = field.get("op")
    if op == "add":
        return _clean(a + b)
    if op == "sub":
        return _clean(a - b)
    if op == "mul":
        return _clean(a * b)
    if op == "div":
        if b == 0:
            return err("divide by zero")
        return _clean(Decimal(str(a)) / Decimal(str(b)))
    return err(f"unknown op {op!r}")


def get_field(view: dict, key: str, collection: dict | None = None):
    if collection:
        for f in collection.get("fields") or []:
            if f["key"] == key and f.get("type") == "formula":
                return row_formula(f, view)
    return view.get(key)


# ---- filters ------------------------------------------------------------------------

def _cmp_key(v, tz):
    n = _num(v)
    if n is not None:
        return (0, n)
    if isinstance(v, (date, datetime)) or (isinstance(v, str) and len(v) >= 10 and v[4:5] == "-"):
        try:
            return (1, instant(v, tz))
        except ValueError:
            pass
    return (2, str(v))


def _eq(a, b) -> bool:
    if isinstance(a, list):
        return b in a
    return a == b


def match_filter(view: dict, flt: dict, ctx: Ctx, types: dict | None = None) -> bool:
    key, op, value = flt.get("field"), flt.get("op"), flt.get("value")
    raw = view.get(key)
    if op == "empty":
        return raw is None or raw == "" or raw == []
    v = raw
    ftype = (types or {}).get(key)
    if v is None and (ftype == "bool" or key == "done"):
        v = False
    if op == "eq":
        return _eq(v, value)
    if op == "ne":
        return not _eq(v, value)
    if v is None or v == "":
        return False
    if op in ("lt", "gt"):
        ka, kb = _cmp_key(v, ctx.tz), _cmp_key(value, ctx.tz)
        if ka[0] != kb[0]:
            return False
        return ka < kb if op == "lt" else ka > kb
    if op == "within":
        try:
            if value == "72h":
                at = instant(v, ctx.tz)
                return ctx.now <= at < ctx.now + timedelta(hours=72)
            lo, hi = within_days(value, ctx.now, ctx.tz)
            d = day_of(v, ctx.tz)
        except (ValueError, TypeError):
            return False
        return (lo is None or d >= lo) and (hi is None or d <= hi)
    return False


# ---- rows -------------------------------------------------------------------------

def _in_window(value, bounds, tz) -> bool:
    if value in (None, ""):
        return False
    start, end = bounds
    v = parse_value(value, tz)
    if isinstance(v, datetime):
        return start <= v < end
    return start.date() <= v <= (end - timedelta(seconds=1)).astimezone(start.tzinfo).date()


def _views(record: dict, c: dict, bounds, ctx: Ctx, logged_only: bool = False) -> list[dict]:
    props = dict(record.get("properties") or {})
    props.setdefault("_id", record["id"])
    props.setdefault("_position", record.get("position") or "")
    df = c.get("dateField")
    rf = repeat_field(c)
    rep = props.get(rf) if rf else None
    if not rep or not df:
        if bounds is not None and not _in_window(props.get(df), bounds, ctx.tz):
            return []
        return [props]
    rep = normalize_repeat(rep, props.get(df), ctx.tz)
    log = list(rep.get("log") or [])
    out = []
    if bounds is None:
        for d in log:
            out.append({**props, df: d, "done": True, "_occurrence": d})
        if not logged_only and not props.get("done") and props.get(df):
            out.append(props)
        return out
    lo = bounds[0].date()
    hi = (bounds[1] - timedelta(seconds=1)).astimezone(bounds[0].tzinfo).date()
    seen = set()
    for o in expand(rep, lo, hi, ctx.tz):
        seen.add(o["occurrence"])
        if logged_only and not o["logged"]:
            continue
        out.append({**props, df: iso(o["at"]), "done": o["logged"], "_occurrence": o["occurrence"]})
    for d in log:
        if d not in seen and lo <= date.fromisoformat(d) <= hi:
            out.append({**props, df: d, "done": True, "_occurrence": d})
    return out


def _plain(record: dict, c: dict, bounds, ctx: Ctx) -> list[dict]:
    props = dict(record.get("properties") or {})
    props.setdefault("_id", record["id"])
    props.setdefault("_position", record.get("position") or "")
    if bounds is not None and not _in_window(props.get(c.get("dateField")), bounds, ctx.tz):
        return []
    return [props]


def query_rows(query: dict, ctx: Ctx):
    src = query.get("from")
    window = query.get("window")
    where = query.get("where") or []
    if src == "*dated":
        b = window_bounds(window or "today", ctx.now, ctx.tz)
        if b is None:
            return err("*dated needs a window")
        hi = (b[1] - timedelta(seconds=1)).astimezone(b[0].tzinfo).date()
        rows = dated_rows(ctx.apps, ctx.all_records, b[0].date(), hi, ctx.tz)
        return [r for r in rows if all(match_filter(r, f, ctx) for f in where)]
    c = ctx.collection(src)
    if c is None:
        return err(f"unknown collection {src}")
    bounds = None
    if window not in (None, "all"):
        if not c.get("dateField"):
            return err(f"{src} has no date field for a window")
        try:
            bounds = window_bounds(window, ctx.now, ctx.tz)
        except ValueError as e:
            return err(str(e))
    types = field_types(c)
    # §6: over a repeating collection a query counts logged occurrences, unless it filters
    # on `done` itself (To-dos' "done = false, today" must see today's open occurrence).
    logged_only = not any(f.get("field") == "done" for f in where)
    # Only a count reads occurrences; sum/avg/min/max/last read the records themselves
    # (Subscriptions' "sum(amount)" is one row per subscription, not one per renewal).
    per_occurrence = query.get("agg") in (None, "count")
    out = []
    for r in ctx.records(src):
        views = _views(r, c, bounds, ctx, logged_only) if per_occurrence else _plain(r, c, bounds, ctx)
        for v in views:
            if all(match_filter(v, f, ctx, types) for f in where):
                out.append(v)
    return out


def run_query(query: dict, ctx: Ctx, app: dict | None = None):
    rows = query_rows(query, ctx)
    if is_err(rows):
        return rows
    agg = query.get("agg")
    field = query.get("field")
    c = ctx.collection(query.get("from")) if query.get("from") != "*dated" else None
    if agg == "count" and not field:
        return len(rows)
    vals = []
    for r in rows:
        v = get_field(r, field, c) if field else None
        if is_err(v):
            return v
        if v is None or v == "":
            continue
        vals.append((v, r))
    if agg == "count":
        return len(vals)
    if agg in ("sum", "avg"):
        nums = []
        for v, _ in vals:
            n = _num(v)
            if n is None:
                return err(f"{field} is not a number")
            nums.append(n)
        if agg == "sum":
            return _clean(sum(nums)) if nums else 0
        return _clean(Decimal(str(sum(nums))) / len(nums)) if nums else None
    if agg in ("min", "max"):
        if not vals:
            return None
        keyed = [(_cmp_key(v, ctx.tz), v) for v, _ in vals]
        kinds = {k[0] for k, _ in keyed}
        if len(kinds) > 1:
            return err(f"{field} mixes types")
        pick = (min if agg == "min" else max)(keyed, key=lambda kv: kv[0])
        return pick[1]
    if agg == "last":
        if not vals:
            return None
        df = c.get("dateField") if c else "at"

        def k(item):
            _, r = item
            d = r.get(df)
            return (instant(d, ctx.tz) if d else datetime.min.replace(tzinfo=ctx.now.tzinfo),
                    r.get("_position", ""))
        return max(vals, key=k)[0]
    return err(f"unknown agg {agg!r}")


# ---- terms --------------------------------------------------------------------------

def _option_limit(spec: dict, ctx: Ctx, app: dict | None):
    field, option = spec.get("field"), spec.get("option")
    cols = []
    if spec.get("from"):
        c = ctx.collection(spec["from"])
        cols = [c] if c else []
    elif app:
        cols = app.get("collections") or []
    for c in cols:
        for f in c.get("fields") or []:
            if f["key"] == field:
                for o in f.get("options") or []:
                    if isinstance(o, dict) and o.get("id") == option:
                        return o.get("limit")
                return err(f"no option {option}")
    return err(f"no field {field}")


def evaluate(value, ctx: Ctx, app: dict | None = None):
    if value is None:
        return None
    if isinstance(value, bool):
        return err("a boolean is not a value")
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, dict):
        return err("not a formula")
    if "minus" in value:
        terms = value["minus"]
        if not isinstance(terms, list) or len(terms) != 2:
            return err("minus takes two terms")
        a, b = (evaluate(t, ctx, app) for t in terms)
        for x in (a, b):
            if is_err(x):
                return x
        if a is None or b is None:
            return None
        if _num(a) is None or _num(b) is None:
            return err("minus needs numbers")
        return _clean(a - b)
    if "setting" in value:
        return ((app or {}).get("settings") or {}).get(value["setting"])
    if "limit" in value:
        return _option_limit(value["limit"], ctx, app)
    if "agg" in value:
        return run_query(value, ctx, app)
    return err("not a formula")


def format_term(value, fmt_name: str, ctx: Ctx, *, face: bool = True) -> str:
    return F.format_value(value, fmt_name or "number", ctx.tz, face=face, today=ctx.today)


def face(app: dict, ctx: Ctx) -> dict:
    spec = app.get("face") or {}
    v = evaluate(spec.get("value"), ctx, app)
    if v is None and spec.get("empty"):
        text = spec["empty"]
    else:
        text = format_term(v, spec.get("format", "number"), ctx)
    out = {"text": text, "label": spec.get("label", "")}
    if _num(v) is not None:
        out["value"] = v
    return out


def faces(ctx: Ctx) -> dict:
    return {a["key"]: face(a, ctx) for a in ctx.apps if a.get("face")}
