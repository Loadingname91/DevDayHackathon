"""Instrument values and status sentences against backend.md §10's worked values at DEMO_NOW."""
import pytest

import seed_rows as S
from api.logic.clock import parse_value
from api.logic.formula import Ctx
from api.logic.instruments import status, values

TZ = S.TZ
NOW = parse_value(S.DEMO_NOW, TZ)


@pytest.fixture(scope="module")
def real():
    apps, records = S.real_workspace()
    return Ctx(apps, records, now=NOW, tz=TZ)


@pytest.fixture(scope="module")
def hand():
    return Ctx(S.APPS, S.RECORDS, now=NOW, tz=TZ)


def v(ctx, app):
    return values(ctx.app(app), ctx)


@pytest.mark.parametrize("which", ["hand", "real"])
def test_budget_gauge_and_bars(which, request):
    ctx = request.getfixturevalue(which)
    got = v(ctx, "budget")
    assert got["b_left"] == {"text": "$412", "target": "left of $1,200", "pct": 66, "sub": "11 days to go"}
    assert got["b_where"]["rows"] == [
        {"label": "Groceries", "text": "$142.00 of $200", "pct": 71},
        {"label": "Eating out", "text": "$165.00 of $150", "pct": 91, "over_pct": 9, "note": "$15 over."},
        {"label": "Transport", "text": "$42.00 of $100", "pct": 42},
        {"label": "Subscriptions", "text": "$26.47 of $40", "pct": 66},
        {"label": "Rent", "text": "$380.00", "note": "No limit"},
        {"label": "Fun", "text": "$32.53", "note": "No limit"}]


def test_budget_after_lunch(real):
    recs = real.all_records + [{"id": "lunch", "collection": "budget/spend", "position": "zz",
                                "properties": {"note": "Lunch", "amount": 1200, "category": "c_eating_out",
                                               "at": "2026-11-20T17:45:00-07:00"}}]
    got = values(real.app("budget"), Ctx(real.apps, recs, now=NOW, tz=TZ))
    assert got["b_left"]["text"] == "$400" and got["b_left"]["pct"] == 67
    eat = got["b_where"]["rows"][1]
    assert eat == {"label": "Eating out", "text": "$177.00 of $150", "pct": 85, "over_pct": 15, "note": "$27 over."}


def test_budget_subscription_bars(real):
    rows = v(real, "budget")["b_subs"]["rows"]
    assert rows[0] == {"label": "Spotify", "text": "$11.99", "note": "Renews Sun 22 Nov"}
    assert [r["text"] for r in rows] == ["$11.99", "$9.99", "$13.49", "$2.99"]


@pytest.mark.parametrize("which", ["hand", "real"])
def test_subscriptions_gauge(which, request):
    ctx = request.getfixturevalue(which)
    assert v(ctx, "subscriptions")["b_total"] == {"text": "$38.46", "sub": "4 subscriptions"}


@pytest.mark.parametrize("which", ["hand", "real"])
def test_calories_ring(which, request):
    ctx = request.getfixturevalue(which)
    assert v(ctx, "calories")["b_ring"] == {"text": "1,140", "target": "of 2,200", "pct": 52, "sub": "70 g protein"}


def test_calories_ring_without_target(real):
    app = {**real.app("calories"), "settings": {}}
    ctx = Ctx(real.apps, [r for r in real.all_records if r["collection"] != "calories/meals"], now=NOW, tz=TZ)
    assert values(app, ctx)["b_ring"] == {"text": "0", "target": "today", "pct": 0,
                                          "sub": "Set a daily target to see a ring"}


@pytest.mark.parametrize("which", ["hand", "real"])
def test_running_countdown_and_strip(which, request):
    ctx = request.getfixturevalue(which)
    got = v(ctx, "running")
    assert got["b_race"] == {"title": "Winter 10K", "text": "22", "unit": "days to go",
                             "sub": "Sat 12 Dec · 9:00 am", "note": "Long runs: 4 → 4.5 → 5 mi"}
    assert got["b_strip"]["days"] == [
        {"dow": "M"}, {"dow": "T", "text": "3 mi", "on": True}, {"dow": "W"},
        {"dow": "T", "text": "4 mi", "on": True}, {"dow": "F", "today": True}, {"dow": "S"}, {"dow": "S"}]


def test_countdown_hides_after_race(real):
    later = Ctx(real.apps, real.all_records, now=parse_value("2026-12-13T09:00", TZ), tz=TZ)
    assert "b_race" not in values(later.app("running"), later)


@pytest.mark.parametrize("which", ["hand", "real"])
def test_meditation_strip(which, request):
    ctx = request.getfixturevalue(which)
    assert v(ctx, "meditation")["b_strip"]["days"] == [
        {"dow": "M", "text": "10", "on": True}, {"dow": "T"}, {"dow": "W", "text": "5", "on": True},
        {"dow": "T", "text": "10", "on": True}, {"dow": "F", "today": True}, {"dow": "S"}, {"dow": "S"}]


@pytest.mark.parametrize("which", ["hand", "real"])
def test_workout_instruments(which, request):
    ctx = request.getfixturevalue(which)
    got = v(ctx, "workout")
    assert got["b_lifted"] == {"text": "12,450 lb"}
    assert got["b_since"] == {"text": "41 sessions"}
    assert got["b_strip"]["days"] == [
        {"dow": "M", "text": "Pull", "on": True}, {"dow": "T", "text": "Legs", "on": True},
        {"dow": "W", "text": "Push", "on": True}, {"dow": "T"}, {"dow": "F", "today": True, "text": "6 pm"},
        {"dow": "S"}, {"dow": "S"}]
    n = got["b_next"]
    assert {k: n[k] for k in ("eyebrow", "meta", "title", "action", "record_id", "occurrence", "rest")} == {
        "eyebrow": "Next up · today 6 pm", "meta": "5 exercises · about 45 min", "title": "Pull day",
        "action": "Start pull day", "record_id": "s_pull", "occurrence": "2026-11-20", "rest": 90}
    assert len(n["steps"]) == 5
    lat = next(s for s in n["steps"] if s["name"] == "Lat pulldown")
    assert {k: lat[k] for k in ("plan", "sets", "reps", "weight", "unit", "best")} == {
        "plan": "3 × 10", "sets": 3, "reps": 10, "weight": 120, "unit": "lb",
        "best": {"reps": 10, "weight": 120, "text": "best 120 lb × 10"}}
    pull_ups = n["steps"][0]
    assert pull_ups["name"] == "Pull-ups" and pull_ups["plan"] == "3 × 8 · bodyweight"
    assert pull_ups["best"]["text"] == "best 8 reps"


def test_workout_real_template_blocks(real):
    got = v(real, "workout")
    assert got["b_sessions"] == {"text": "3", "target": "4", "pct": 75}
    assert got["b_lat"] == {"text": "100 → 120 lb", "sub": "in 8 weeks"}
    assert got["b_volume"] == {"text": "12,450 lb"}
    assert got["b_week"] == {"text": "3"}


def test_groceries_progress(real):
    assert v(real, "groceries")["b_spend"] == {"text": "$142.00", "target": "$200", "pct": 71}


STATUS = {
    "groceries": "**22** to buy across 3 lists. **$142.00** of $200 spent this month.",
    "calendar": "**3** today. Dates from every app, in one place.",
    "todos": "**2** left today.",
    "workout": "**3** of 4 sessions this week. Pull day at **6 pm**.",
    "running": "**7 mi** this week. Winter 10K in **22 days**.",
    "meditation": "**25 min** this week across **3** sessions.",
    "calories": "**1,140** of 2,200 today across **3** meals.",
    "cycle": "Last period started **Tue 27 Oct**.",
    "classes": "**2** due this week. Next: Start CS 3500 project, **Mon 23 Nov**.",
    "subscriptions": "Next: **Spotify** renews **Sun 22 Nov**, $11.99.",
    "notes": "**3** notes this week.",
    "budget": None,
}


@pytest.mark.parametrize("which", ["hand", "real"])
def test_status_sentences(which, request):
    ctx = request.getfixturevalue(which)
    for key, sentence in STATUS.items():
        assert status(ctx.app(key), ctx) == sentence, key
