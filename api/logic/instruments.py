"""Values for metric, progress and instrument blocks, and the app status sentence
(spec/backend.md §10 "What the server computes for instruments", "Status sentences";
shapes: BlockValue in web/src/api/types.ts).

Public API:
    block_value(block: dict, app: dict, ctx: Ctx) -> dict | None
        metric   -> {text}                       (block `unit` is appended: "12,450 lb")
        progress -> {text, target, pct}
        gauge    -> {text, target?, pct?, sub?}
        ring     -> {text, target, pct, sub?}
        bars     -> {rows: [{label, text, pct?, over_pct?, note?}]}
        countdown-> {title, text, unit, sub, note?} | None (no row today or later)
        strip    -> {days: [{dow, text?, on?, today?}] * 7}
        next     -> {eyebrow, meta, title, action, record_id, occurrence, rest, steps[]} | None
        other kinds -> None
    values(app: dict, ctx: Ctx) -> {block_id: value}      # every block in every tab
    status(app: dict, ctx: Ctx) -> str | None             # "**3** today. …" per starter app
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from . import fmt as F
from .clock import day_of, instant, iso, parse_value, to_local, week_start, window_bounds
from .dated import field_types, repeat_field
from .formula import Ctx, evaluate, face, format_term, get_field, is_err, match_filter, query_rows
from .repeats import expand, next_open, normalize_repeat

REST_SECONDS = 90  # no seed field holds it yet (§10)
_DOW = "MTWTFSS"


def _pct(a, b):
    if a is None or b in (None, 0) or is_err(a) or is_err(b):
        return None
    return int((Decimal(str(a)) * 100 / Decimal(str(b))).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _fmt(v, block, ctx, *, face=True):
    return format_term(v, block.get("format", "number"), ctx, face=face)


def _with_unit(text, unit):
    return f"{text} {unit}" if unit and text not in (F.NULL_TEXT, F.ERR_TEXT) else text


def _first_query(value):
    if isinstance(value, dict):
        if "agg" in value:
            return value
        if "minus" in value:
            for t in value["minus"]:
                q = _first_query(t)
                if q:
                    return q
    return None


def _days_to_window_end(window, ctx):
    b = window_bounds(window, ctx.now, ctx.tz)
    if not b:
        return None
    return (b[1].date() - ctx.today).days


def _field_unit(c, key):
    """A field's `unit`; a row formula takes the unit of its `a` field (volume -> lb)."""
    for f in (c or {}).get("fields") or []:
        if f["key"] == key:
            if f.get("unit"):
                return f["unit"]
            if f.get("type") == "formula" and isinstance(f.get("a"), str):
                return _field_unit(c, f["a"])
    return None


def _named_filter(block, c, ctx):
    """A metric labelled with a related record's name ("Lat pulldown") reads only its rows."""
    for f in (c or {}).get("fields") or []:
        if f.get("type") == "relation" and f.get("target"):
            for r in ctx.records(f["target"]):
                if (r.get("properties") or {}).get("name") == block.get("label"):
                    return {"field": f["key"], "op": "eq", "value": r["id"]}
    return None


def _trend(block, app, ctx, q, c):
    """`max` over {days: N} worded as "first → best unit" (Workout's "100 → 120 lb")."""
    where = list(q.get("where") or [])
    nf = _named_filter(block, c, ctx)
    if nf:
        where.append(nf)
    rows = query_rows({**q, "where": where}, ctx)
    if is_err(rows) or not rows:
        return {"text": F.NULL_TEXT}
    field, df = q["field"], c["dateField"]
    rows = [r for r in rows if r.get(field) is not None and r.get(df)]
    if not rows:
        return {"text": F.NULL_TEXT}
    rows.sort(key=lambda r: (instant(r[df], ctx.tz), r.get("_position", "")))
    first, best = rows[0][field], max(r[field] for r in rows)
    out = {"text": _with_unit(f"{F.number(first)} → {F.number(best)}", _field_unit(c, field))}
    n = q["window"]["days"]
    out["sub"] = f"in {n // 7} weeks" if n % 7 == 0 else f"in {n} days"
    return out


def _metric(block, app, ctx):
    value = block.get("value")
    q = value if isinstance(value, dict) and "agg" in value else None
    c = ctx.collection(q["from"]) if q and q.get("from") != "*dated" else None
    if q and c and q.get("agg") == "max" and isinstance(q.get("window"), dict) \
            and block.get("format") == "text" and q.get("field"):
        return _trend(block, app, ctx, q, c)
    v = evaluate(value, ctx, app)
    unit = block.get("unit")
    if unit is None and q and c:
        if q.get("agg") in ("sum", "avg", "min", "max") and q.get("field"):
            unit = _field_unit(c, q["field"])
        elif q.get("agg") == "count" and q.get("window") == "all":
            unit = (c.get("name") or c.get("key") or "").lower()
    return {"text": _with_unit(_fmt(v, block, ctx), unit)}


def _progress(block, app, ctx):
    v = evaluate(block.get("value"), ctx, app)
    t = evaluate(block.get("target"), ctx, app)
    # §10: cents on the figure ("$142.00"), whole dollars on the limit ("$200").
    out = {"text": _fmt(v, block, ctx, face=False), "target": _fmt(t, block, ctx)}
    p = _pct(v, t)
    if p is not None:
        out["pct"] = p
    return out


def _gauge(block, app, ctx):
    value = block.get("value")
    v = evaluate(value, ctx, app)
    t = evaluate(block.get("target"), ctx, app) if block.get("target") is not None else None
    out = {"text": _fmt(v, block, ctx)}
    q = _first_query(value)
    if t not in (None, 0) and not is_err(t):
        label = (app.get("face") or {}).get("label", "")
        out["target"] = f"{label} of {_fmt(t, block, ctx)}".strip()
        is_left = isinstance(value, dict) and "minus" in value and value["minus"][0] == block.get("target")
        p = _pct((t - v) if is_left and v is not None and not is_err(v) else v, t)
        if p is not None:
            out["pct"] = p
        if q and q.get("window") in ("month", "week"):
            days = _days_to_window_end(q["window"], ctx)
            out["sub"] = f"{days} day{'s' if days != 1 else ''} to go"
    elif q and q.get("from") and q.get("from") != "*dated":
        c = ctx.collection(q["from"])
        if c:
            n = len(ctx.records(q["from"]))
            name = (c.get("name") or c.get("key") or "").lower()
            out["sub"] = f"{n} {name if n != 1 else name.rstrip('s')}"
    return out


def _ring(block, app, ctx):
    v = evaluate(block.get("value"), ctx, app)
    t = evaluate(block.get("target"), ctx, app)
    q = _first_query(block.get("value"))
    if t is None or is_err(t):
        return {"text": _fmt(v if v is not None else 0, block, ctx), "target": q.get("window", "") if q else "",
                "pct": 0, "sub": "Set a daily target to see a ring"}
    out = {"text": _fmt(v, block, ctx), "target": f"of {_fmt(t, block, ctx)}", "pct": _pct(v, t) or 0}
    c = ctx.collection(q["from"]) if q else None
    if c and "protein" in field_types(c):
        p = evaluate({**q, "field": "protein", "agg": "sum"}, ctx, app)
        out["sub"] = f"{F.number(p)} g protein"
    return out


def _option_label(o):
    return o.get("label") if isinstance(o, dict) else str(o)


def _bars(block, app, ctx):
    q = block.get("value") or {}
    c = ctx.collection(block.get("from") or q.get("from"))
    if not c:
        return {"rows": []}
    by = block.get("by")
    fdef = next((x for x in c.get("fields") or [] if x["key"] == by), {})
    options = [o if isinstance(o, dict) else {"id": o, "label": o} for o in fdef.get("options") or []]
    if not options:  # a text field: one bar per distinct value, in record order
        seen = []
        for r in ctx.records(block.get("from") or q.get("from")):
            v = (r.get("properties") or {}).get(by)
            if v is not None and v not in seen:
                seen.append(v)
        options = [{"id": v, "label": str(v)} for v in seen]
    limited = [o for o in options if o.get("limit") is not None]
    rest = [o for o in options if o.get("limit") is None]
    rows = []
    for o in limited + rest:
        qo = {**q, "where": [*(q.get("where") or []), {"field": by, "op": "eq", "value": o["id"]}]}
        s = evaluate(qo, ctx, app) or 0
        row = {"label": _option_label(o)}
        if is_err(s):
            row["text"] = F.ERR_TEXT
            rows.append(row)
            continue
        lim = o.get("limit")
        if lim is None:
            row["text"] = F.money_row(s)
            if fdef.get("options"):
                row["note"] = "No limit"
            elif c.get("dateField"):  # Subscriptions by name: "Renews Sun 22 Nov"
                rec = next((r["properties"] for r in ctx.records(block.get("from") or q.get("from"))
                            if (r.get("properties") or {}).get(by) == o["id"]), {})
                dv = rec.get(c["dateField"])
                if dv:
                    dlabel = next((x.get("label") for x in c.get("fields") or []
                                   if x["key"] == c["dateField"]), c["dateField"])
                    row["note"] = f"{dlabel} {F.when_label(dv, ctx.tz, ctx.today)}"
        elif s <= lim:
            row["text"] = f"{F.money_row(s)} of {F.money_face(lim)}"
            row["pct"] = _pct(s, lim)
        else:
            row["text"] = f"{F.money_row(s)} of {F.money_face(lim)}"
            row["pct"] = _pct(lim, s)
            row["over_pct"] = _pct(s - lim, s)
            row["note"] = f"{F.money_face(s - lim)} over."
        rows.append(row)
    return {"rows": rows}


def _date_value(props, c):
    return props.get(c.get("dateField"))


def _countdown(block, app, ctx):
    ref = block.get("source")
    c = ctx.collection(ref)
    if not c:
        return None
    rows = []
    for r in ctx.records(ref):
        p = r.get("properties") or {}
        v = _date_value(p, c)
        if v and not p.get("done") and day_of(v, ctx.tz) >= ctx.today:
            rows.append((instant(v, ctx.tz), r.get("position", ""), p, v))
    if not rows:
        return None
    _, _, p, v = min(rows, key=lambda x: (x[0], x[1]))
    days = (day_of(v, ctx.tz) - ctx.today).days
    out = {"title": str(p.get(c.get("titleField") or "name", "")), "text": str(days),
           "unit": "day to go" if days == 1 else "days to go",
           "sub": F.when_label(v, ctx.tz, ctx.today)}
    # Running: the distances of the last three done Long runs, oldest first.
    for c2 in app.get("collections") or []:
        types = field_types(c2)
        if "distance" in types and "kind" in types and c2 is not c:
            ref2 = f"{app['key']}/{c2.get('key')}"
            longs = [(instant(x["properties"][c2["dateField"]], ctx.tz), x["properties"]["distance"])
                     for x in ctx.records(ref2)
                     if str(x["properties"].get("kind", "")).lower() == "long" and x["properties"].get("done")
                     and x["properties"].get(c2.get("dateField"))]
            longs.sort()
            if longs:
                out["note"] = "Long runs: " + " → ".join(F.number(d) for _, d in longs[-3:]) + " mi"
    return out


def _title_of(ctx, ref_list, target_ref, field="name"):
    if not ref_list:
        return None
    rid = ref_list[0] if isinstance(ref_list, list) else ref_list
    for r in ctx.records(target_ref):
        if r["id"] == rid:
            return r["properties"].get(field)
    return None


def _strip(block, app, ctx):
    q = block.get("value") or {}
    ref = q.get("from")
    c = ctx.collection(ref)
    ws = week_start(ctx.today)
    days = [{"dow": _DOW[i]} for i in range(7)]
    for i in range(7):
        if ws + timedelta(days=i) == ctx.today:
            days[i]["today"] = True
    if not c:
        return {"days": days}
    rf = repeat_field(c)
    if rf:  # Workout: a done occurrence shows its routine; today's open one shows its time
        rel = next((f for f in c.get("fields") or [] if f.get("type") == "relation"), None)
        for r in ctx.records(ref):
            p = r["properties"]
            rep = p.get(rf)
            if not rep:
                continue
            rep = normalize_repeat(rep, p.get(c["dateField"]), ctx.tz)
            occs = {o["occurrence"]: o for o in expand(rep, ws, ws + timedelta(days=6), ctx.tz)}
            for d in rep.get("log") or []:
                if ws <= date.fromisoformat(d) <= ws + timedelta(days=6):
                    occs.setdefault(d, {"occurrence": d, "at": date.fromisoformat(d), "logged": True})
            for d, o in occs.items():
                i = (date.fromisoformat(d) - ws).days
                if o["logged"]:
                    name = None
                    if rel:
                        name = _title_of(ctx, p.get(rel["key"]), rel.get("target"))
                    days[i]["text"] = name or p.get(c.get("titleField"))
                    days[i]["on"] = True
                elif date.fromisoformat(d) == ctx.today and isinstance(o["at"], datetime):
                    days[i].setdefault("text", F.time_label(to_local(o["at"], ctx.tz), short=True))
        return {"days": days}
    unit = block.get("unit")
    if unit is None and q.get("field") == "distance":
        unit = "mi"
    rows = query_rows({**q, "window": "week"}, ctx)
    if is_err(rows):
        return {"days": days}
    sums: dict[int, object] = {}
    for r in rows:
        v = r.get(c["dateField"])
        if not v:
            continue
        i = (day_of(v, ctx.tz) - ws).days
        if not 0 <= i < 7:
            continue
        if q.get("agg") == "count" or not q.get("field"):
            sums[i] = sums.get(i, 0) + 1
        else:
            x = get_field(r, q["field"], c)
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                sums[i] = sums.get(i, 0) + x
    for i, s in sums.items():
        days[i]["text"] = _with_unit(F.number(s), unit)
        days[i]["on"] = True
    return {"days": days}


def _next(block, app, ctx):
    ref = block.get("source")
    c = ctx.collection(ref)
    if not c:
        return None
    rf = repeat_field(c)
    best = None
    for r in ctx.records(ref):
        p = r["properties"]
        if p.get("done"):
            continue
        rep = p.get(rf) if rf else None
        if rep:
            o = next_open(normalize_repeat(rep, p.get(c["dateField"]), ctx.tz), ctx.tz, after=ctx.now)
            if o is None:
                continue
            at, occ = o["at"], o["occurrence"]
        else:
            v = p.get(c.get("dateField"))
            if not v:
                continue
            at, occ = parse_value(v, ctx.tz), None
            if instant(at, ctx.tz) < ctx.now:
                continue
        key = (instant(at, ctx.tz), r.get("position", ""))
        if best is None or key < best[0]:
            best = (key, r, at, occ)
    if best is None:
        return None
    _, r, at, occ = best
    p = r["properties"]
    title = str(p.get(c.get("titleField") or "name", ""))
    at_l = to_local(at, ctx.tz) if isinstance(at, datetime) else at
    d = at_l.date() if isinstance(at_l, datetime) else at_l
    when = "today" if d == ctx.today else ("tomorrow" if d == ctx.today + timedelta(days=1)
                                           else F.day_label(d, ctx.today))
    if isinstance(at_l, datetime):
        when += " " + F.time_label(at_l, short=True)
    out = {"eyebrow": f"Next up · {when}", "title": title, "action": f"Start {title.lower()}",
           "record_id": r["id"], "occurrence": occ or d.isoformat(), "rest": REST_SECONDS, "steps": []}
    app_key = app["key"]
    routine_ids = p.get("routine") or []
    routine = next((x for x in ctx.records(f"{app_key}/routines") if x["id"] in routine_ids), None)
    exercises = [x for x in ctx.records(f"{app_key}/exercises") if set(x["properties"].get("routine") or []) & set(routine_ids)]
    exercises.sort(key=lambda x: (x["properties"].get("order") or 0, x.get("position", "")))
    log_ref = block.get("log")
    logged = ctx.records(log_ref) if log_ref else []
    for ex in exercises:
        e = ex["properties"]
        sets, reps, weight = e.get("sets") or 0, e.get("reps") or 0, e.get("weight") or 0
        plan = f"{sets} × {reps}" + (" · bodyweight" if not weight else "")
        step = {"id": ex["id"], "name": e.get("name"), "plan": plan, "sets": sets, "reps": reps,
                "weight": weight, "unit": "lb"}
        mine = [s["properties"] for s in logged if ex["id"] in (s["properties"].get("exercise") or [])]
        if mine:
            b = max(mine, key=lambda s: (s.get("weight") or 0, s.get("reps") or 0))
            bw, br = b.get("weight") or 0, b.get("reps") or 0
            step["best"] = {"reps": br, "weight": bw,
                            "text": f"best {F.number(bw)} lb × {br}" if bw else f"best {br} reps"}
        out["steps"].append(step)
    meta = f"{len(exercises)} exercise{'s' if len(exercises) != 1 else ''}"
    if routine and routine["properties"].get("minutes"):
        meta += f" · about {routine['properties']['minutes']} min"
    out["meta"] = meta
    return out


_KINDS = {"metric": _metric, "progress": _progress, "gauge": _gauge, "ring": _ring, "bars": _bars,
          "countdown": _countdown, "strip": _strip, "next": _next}


def block_value(block: dict, app: dict, ctx: Ctx):
    fn = _KINDS.get(block.get("kind"))
    return fn(block, app, ctx) if fn else None


def values(app: dict, ctx: Ctx) -> dict:
    out = {}
    for tab in app.get("tabs") or []:
        for b in (tab.get("children") or []) if tab.get("kind") == "page" else [tab]:
            v = block_value(b, app, ctx)
            if v is not None:
                out[b["id"]] = v
    return out


# ---- status sentences ---------------------------------------------------------------

def _b(s) -> str:
    return f"**{s}**"


def _count(ctx, q) -> int:
    rows = query_rows(q, ctx)
    return 0 if is_err(rows) else len(rows)


def _planned(ctx: Ctx, ref: str, window) -> int:
    """Occurrences planned in the window (logged or open, not skipped) plus one-off rows."""
    rows = query_rows({"from": ref, "window": window,
                       "where": [{"field": "done", "op": "ne", "value": "__any__"}]}, ctx)
    return 0 if is_err(rows) else len(rows)


def status(app: dict, ctx: Ctx) -> str | None:
    key = app["key"]
    fc = face(app, ctx)
    if key == "calendar":
        return f"{_b(fc['text'])} today. Dates from every app, in one place."
    if key == "todos":
        return f"{_b(fc['text'])} left today."
    if key == "notes":
        return f"{_b(fc['text'])} notes this week."
    if key == "cycle":
        return f"Last period started {_b(fc['text'])}."
    if key == "groceries":
        n = _count(ctx, {"from": "groceries/items", "where": [{"field": "status", "op": "eq", "value": "to_buy"}]})
        lists = [o for f in (ctx.collection("groceries/items") or {}).get("fields", []) if f["key"] == "list"
                 for o in f.get("options") or []]
        spend = evaluate({"agg": "sum", "from": "groceries/trips", "field": "total", "window": "month"}, ctx, app)
        target = next((b.get("target") for t in app.get("tabs") or [] for b in t.get("children") or []
                       if b.get("id") == "b_spend"), 20000)
        return (f"{_b(n)} to buy across {len(lists)} lists. "
                f"{_b(F.money_row(spend or 0))} of {F.money_face(target)} spent this month.")
    if key == "workout":
        done = evaluate({"agg": "count", "from": "workout/sessions", "window": "week",
                         "where": [{"field": "done", "op": "eq", "value": True}]}, ctx, app)
        planned = _planned(ctx, "workout/sessions", "week")
        s = f"{_b(done)} of {planned} sessions this week."
        today = [r for r in query_rows({"from": "workout/sessions", "window": "today",
                                        "where": [{"field": "done", "op": "eq", "value": False}]}, ctx) or []]
        if today and not is_err(today):
            r = today[0]
            at = to_local(parse_value(r["at"], ctx.tz), ctx.tz)
            s += f" {r['name']} at {_b(F.time_label(at, short=True))}."
        return s
    if key == "running":
        s = f"{_b(fc['text'] + ' mi')} this week."
        cd = _countdown({"source": "running/races"}, app, ctx)
        if cd:
            s += f" {cd['title']} in {_b(cd['text'] + ' days')}."
        return s
    if key == "meditation":
        n = _count(ctx, {"from": "meditation/sessions", "window": "week"})
        return f"{_b(fc['text'] + ' min')} this week across {_b(n)} sessions."
    if key == "calories":
        n = _count(ctx, {"from": "calories/meals", "window": "today"})
        t = (app.get("settings") or {}).get("target")
        mid = f" of {F.number(t)}" if t else ""
        return f"{_b(fc['text'])}{mid} today across {_b(n)} meals."
    if key == "classes":
        s = f"{_b(fc['text'])} due this week."
        rows = query_rows({"from": "classes/due", "where": [{"field": "done", "op": "eq", "value": False},
                                                            {"field": "at", "op": "within", "value": "future"}]}, ctx)
        if rows and not is_err(rows):
            first = min(rows, key=lambda r: instant(r["at"], ctx.tz))
            s += f" Next: {first['title']}, {_b(F.day_label(day_of(first['at'], ctx.tz), ctx.today))}."
        return s
    if key == "subscriptions":
        rows = [r["properties"] for r in ctx.records("subscriptions/subscriptions")
                if r["properties"].get("renews") and day_of(r["properties"]["renews"], ctx.tz) >= ctx.today]
        if not rows:
            return None
        r = min(rows, key=lambda p: day_of(p["renews"], ctx.tz))
        return (f"Next: {_b(r['name'])} renews {_b(F.day_label(day_of(r['renews'], ctx.tz), ctx.today))}, "
                f"{F.money_row(r['amount'])}.")
    return None
