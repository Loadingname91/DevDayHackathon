"""Formula engine and faces (backend.md §6, §2.2, §2.3, §5 receipt dry run)."""
import copy

import pytest

import seed_rows as S
from api.logic import fmt
from api.logic.clock import parse_value
from api.logic.formula import Ctx, evaluate, face, faces, row_formula, run_query

TZ = S.TZ
NOW = parse_value(S.DEMO_NOW, TZ)

SEEDS = {"hand": lambda: (S.APPS, S.RECORDS), "real": lambda: S.real_workspace()}

FACES = {
    "budget": ("$412", "left", 41200),
    "groceries": ("12", "to buy", 12),
    "calendar": ("3", "today", 3),
    "classes": ("2", "due this week", 2),
    "notes": ("3", "this week", 3),
    "todos": ("2", "today", 2),
    "workout": ("3", "this week", 3),
    "subscriptions": ("$38.46", "a month", 3846),
    "calories": ("1,140", "today", 1140),
    "running": ("7", "mi this week", 7),
    "meditation": ("25", "min this week", 25),
    "cycle": ("Tue 27 Oct", "last period started", None),
}


@pytest.fixture(params=list(SEEDS))
def ctx(request):
    apps, records = SEEDS[request.param]()
    return Ctx(apps, records, now=NOW, tz=TZ)


def test_every_face_at_demo_now(ctx):
    got = faces(ctx)
    assert set(got) == set(FACES)
    for key, (text, label, value) in FACES.items():
        expect = {"text": text, "label": label}
        if value is not None:
            expect["value"] = value
        assert got[key] == expect, key


def test_before_state_has_eight_apps():
    apps, records = S.real_workspace("before")
    got = faces(Ctx(apps, records, now=NOW, tz=TZ))
    assert len(got) == 8 and got["budget"]["text"] == "$412" and got["calendar"]["text"] == "3"


def test_budget_spend_total_and_october_excluded(ctx):
    q = {"agg": "sum", "from": "budget/spend", "field": "amount", "window": "month"}
    assert run_query(q, ctx) == 78800
    assert run_query({**q, "window": "all"}, ctx) > 78800


def test_receipt_dry_run_moves_three_faces(ctx):
    """§5: trip + 8 closes + stitched spend -> Budget $376, Groceries 4, Calendar 4."""
    recs = copy.deepcopy(ctx.all_records)
    recs.append({"id": "trip_new", "collection": "groceries/trips", "position": "zz",
                 "properties": {"store": "Corner Market", "total": 3583, "at": "2026-11-20T17:41:00-07:00"}})
    recs.append({"id": "spend_new", "collection": "budget/spend", "position": "zz",
                 "properties": {"note": "Corner Market", "amount": 3583, "category": "c_groceries",
                                "at": "2026-11-20T17:41:00-07:00"}})
    receipt = {"Oat milk", "Eggs", "Bananas", "Chicken thighs", "Rice", "Spinach", "Greek yogurt", "Coffee beans"}
    for r in recs:
        p = r["properties"]
        if r["collection"] == "groceries/items" and p.get("list") == "l_weekly" and p.get("status") == "to_buy" \
                and p.get("name") in receipt:
            p["status"] = "bought"
    after = Ctx(ctx.apps, recs, now=NOW, tz=TZ)
    got = faces(after)
    assert got["budget"] == {"text": "$376", "label": "left", "value": 37617}
    assert got["groceries"]["text"] == "4"
    assert got["calendar"]["text"] == "4"
    trips = {"agg": "sum", "from": "groceries/trips", "field": "total", "window": "month"}
    assert run_query(trips, after) == 17783


def test_lunch_draft_moves_budget_to_400(ctx):
    recs = ctx.all_records + [{"id": "lunch", "collection": "budget/spend", "position": "zz",
                               "properties": {"note": "Lunch", "amount": 1200, "category": "c_eating_out",
                                              "at": "2026-11-20T17:45:00-07:00"}}]
    assert faces(Ctx(ctx.apps, recs, now=NOW, tz=TZ))["budget"]["text"] == "$400"


def test_month_rollover_recomputes(ctx):
    dec = Ctx(ctx.apps, ctx.all_records, now=parse_value("2026-12-01T09:00", TZ), tz=TZ)
    assert face(dec.app("budget"), dec)["text"] == "$1,200"


def test_null_setting_gives_empty_text_and_null_propagates(ctx):
    budget = copy.deepcopy(ctx.app("budget"))
    budget["settings"] = {}
    v = evaluate(budget["face"]["value"], ctx, budget)
    assert v is None
    budget["face"].setdefault("empty", "Set a monthly amount")
    assert face(budget, ctx) == {"text": "Set a monthly amount", "label": "left"}
    budget["face"].pop("empty")
    assert face(budget, ctx)["text"] == "—"


def test_aggregates_of_nothing(ctx):
    base = {"from": "calories/meals", "field": "calories", "window": "today",
            "where": [{"field": "name", "op": "eq", "value": "nothing"}]}
    assert run_query({**base, "agg": "sum"}, ctx) == 0
    assert run_query({**base, "agg": "count"}, ctx) == 0
    for agg in ("avg", "min", "max", "last"):
        assert run_query({**base, "agg": agg}, ctx) is None


def test_avg_min_max_last(ctx):
    base = {"from": "calories/meals", "field": "calories", "window": "today"}
    assert run_query({**base, "agg": "avg"}, ctx) == 380
    assert run_query({**base, "agg": "min"}, ctx) == 150
    assert run_query({**base, "agg": "max"}, ctx) == 640
    assert run_query({**base, "agg": "last"}, ctx) == 150  # Greek yogurt, 3:40 pm


def test_window_without_date_field_is_an_error_value(ctx):
    v = run_query({"agg": "count", "from": "calories/foods", "window": "week"}, ctx)
    assert fmt.is_err(v)
    assert fmt.format_value(v, "count") == "#ERR"


def test_minus_propagates_errors(ctx):
    v = evaluate({"minus": [1000, {"agg": "sum", "from": "nope/nope", "field": "x"}]}, ctx)
    assert fmt.is_err(v)


def test_within_and_empty_filters(ctx):
    q = {"agg": "count", "from": "todos/todos", "where": [{"field": "due", "op": "empty", "value": True}]}
    assert run_query(q, ctx) == 2  # Pay Maya back, Book flu shot (Someday)
    q = {"agg": "count", "from": "classes/due", "where": [{"field": "at", "op": "within", "value": "past"}]}
    assert run_query(q, ctx) == 1  # Homework 10
    q = {"agg": "count", "from": "calories/meals", "where": [{"field": "at", "op": "within", "value": "-7d"}]}
    assert run_query(q, ctx) == 15
    q = {"agg": "count", "from": "classes/due", "where": [{"field": "at", "op": "within", "value": "future"}]}
    assert run_query(q, ctx) == 2


def test_lt_gt_and_relation_eq(ctx):
    q = {"agg": "count", "from": "calories/meals", "where": [{"field": "calories", "op": "gt", "value": 700}]}
    assert run_query(q, ctx) == 3  # Pasta with chicken 780, Tacos 820, Frozen pizza 900
    q["where"][0]["op"] = "lt"
    q["where"][0]["value"] = 200
    assert run_query(q, ctx) == 1  # Greek yogurt 150
    q = {"agg": "count", "from": "classes/due", "where": [{"field": "class", "op": "eq", "value": "c02"}]}
    if run_query(q, ctx) == 0:  # the real seed names classes by human key
        q["where"][0]["value"] = next(r["id"] for r in ctx.records("classes/classes")
                                      if r["properties"]["name"] == "MATH 1210")
    assert run_query(q, ctx) == 2


def test_repeat_counts_logged_occurrences(ctx):
    sessions = "workout/sessions"
    assert run_query({"agg": "count", "from": sessions, "window": "week"}, ctx) == 3
    assert run_query({"agg": "count", "from": sessions, "window": "all"}, ctx) == 41
    # Filtering on done sees open occurrences too: Friday's Pull day is the planned 4th.
    q = {"agg": "count", "from": sessions, "window": "week", "where": [{"field": "done", "op": "eq", "value": False}]}
    assert run_query(q, ctx) == 1


def test_row_formula():
    f = {"key": "volume", "type": "formula", "op": "mul", "a": "weight", "b": "reps"}
    assert row_formula(f, {"weight": 120, "reps": 10}) == 1200
    assert row_formula(f, {"weight": None, "reps": 10}) is None
    assert row_formula({**f, "op": "div", "b": 0}, {"weight": 5}) == {"error": "#ERR", "reason": "divide by zero"}
    assert row_formula({**f, "op": "div", "a": "amount", "b": 12}, {"amount": 1200}) == 100
    assert fmt.is_err(row_formula(f, {"weight": "heavy", "reps": 1}))


def test_sum_over_row_formula(ctx):
    q = {"agg": "sum", "from": "workout/sets", "field": "volume", "window": "week"}
    assert run_query(q, ctx) == 12450


def test_formatting():
    assert fmt.money_face(41200) == "$412"
    assert fmt.money_face(37617) == "$376"
    assert fmt.money_face(3846) == "$38.46"
    assert fmt.money_face(120000) == "$1,200"
    assert fmt.money_face(-1200) == "-$12"
    assert fmt.money_row(3583) == "$35.83"
    assert fmt.money_row(14200) == "$142.00"
    assert fmt.number(1140) == "1,140" and fmt.number(7) == "7" and fmt.number(5.5) == "5.5"
    assert fmt.number(12450) == "12,450"
    assert fmt.duration(25) == "25 min" and fmt.duration(65) == "1 h 5 min"
    assert fmt.format_value(None, "money") == "—"
    assert fmt.format_value("2026-10-27", "text", TZ) == "Tue 27 Oct"
    assert fmt.format_value("2026-12-12T09:00:00-07:00", "text", TZ) == "Sat 12 Dec · 9:00 am"
