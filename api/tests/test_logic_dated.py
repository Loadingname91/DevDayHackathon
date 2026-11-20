"""`*dated` and Next up (backend.md §3, §2.3 Calendar; check.py items 3 and 6)."""
from datetime import date

import pytest

import seed_rows as S
from api.logic import repeats
from api.logic.clock import parse_value
from api.logic.dated import dated_rows, dated_window, next_up

TZ = S.TZ
NOW = parse_value(S.DEMO_NOW, TZ)

SEEDS = {"hand": lambda: (S.APPS, S.RECORDS), "real": lambda: S.real_workspace()}


@pytest.fixture(params=list(SEEDS))
def ws(request):
    return SEEDS[request.param]()


def _week(apps, records):
    return dated_rows(apps, records, date(2026, 11, 23), date(2026, 11, 29), TZ)


def test_next_week_holds_sessions_google_no_run_no_econ_thursday(ws):
    apps, records = ws
    rows = _week(apps, records)
    sessions = [(r["title"], r["at"]) for r in rows if r["app"] == "workout"]
    assert sessions == [("Pull day", "2026-11-23T18:00:00-07:00"), ("Leg day", "2026-11-24T07:00:00-07:00"),
                        ("Push day", "2026-11-25T18:00:00-07:00"), ("Pull day", "2026-11-27T18:00:00-07:00")]
    google = [r for r in rows if r.get("source") == "google"]
    assert [g["title"] for g in google] == ["Dentist", "Drive home for Thanksgiving", "Thanksgiving at home",
                                            "Back to campus"]
    assert all(g["sub"] == "Google Calendar" for g in google)
    tg = next(g for g in google if g["title"] == "Thanksgiving at home")
    assert tg["at"] == "2026-11-26" and tg["ends"] == "2026-11-28" and tg["all_day"] is True
    dentist = google[0]
    assert dentist["at"] == "2026-11-24T07:30:00-07:00" and dentist["ends"] == "2026-11-24T08:30:00-07:00"
    assert not [r for r in rows if r["app"] == "running"]
    econ = [r["at"] for r in rows if r["title"] == "ECON 1010"]
    assert econ == ["2026-11-24T09:10:00-07:00"]  # Thu 26 Nov skipped
    classes = [(r["title"], r["at"][:10]) for r in rows if r["app"] == "classes" and r.get("occurrence")]
    assert ("MATH 1210", "2026-11-23") in classes and ("CS 3500", "2026-11-25") in classes
    dues = [r["title"] for r in rows if r["app"] == "classes" and not r.get("occurrence")]
    assert dues == ["Start CS 3500 project", "Homework 11"]
    todos = [(r["title"], r["at"]) for r in rows if r["app"] == "todos"]
    assert todos == [("Take out recycling", "2026-11-27T20:00:00-07:00")]
    ats = [parse_value(r["at"], TZ) for r in rows]
    assert [r["at"] for r in rows] == sorted((r["at"] for r in rows), key=lambda a: _key(a))
    assert len(ats) == len(rows)


def _key(a):
    from api.logic.clock import instant
    return instant(a, TZ)


def test_today_rows_are_calendars_three(ws):
    apps, records = ws
    rows = dated_window(apps, records, "today", NOW, TZ)
    assert [(r["title"], r["app"], r.get("occurrence")) for r in rows] == [
        ("Pull day", "workout", "2026-11-20"),
        ("Take out recycling", "todos", "2026-11-20"),
        ("Return library books", "todos", None)]
    assert rows[0]["sub"] == "Workout" and rows[0]["at"] == "2026-11-20T18:00:00-07:00"


def test_next_up_is_tonight(ws):
    apps, records = ws
    rows = next_up(apps, records, NOW, TZ)
    assert [r["title"] for r in rows] == ["Pull day", "Take out recycling", "Return library books"]
    more = next_up(apps, records, NOW, TZ, limit=10)
    titles = [r["title"] for r in more]
    assert "Coffee with Maya" in titles and "Call home" in titles
    assert "DevDay demo" not in titles  # done, and past


def test_logged_occurrences_and_done_records_are_left_out(ws):
    apps, records = ws
    rows = dated_rows(apps, records, date(2026, 11, 16), date(2026, 11, 19), TZ)
    assert not [r for r in rows if r["app"] == "workout"]  # Mon/Tue/Wed sessions logged
    assert not [r for r in rows if r["app"] == "running"]  # runs are done
    assert "Homework 10" not in [r["title"] for r in rows]


def test_label_and_receipt_trip(ws):
    apps, records = ws
    trip = {"id": "new_trip", "collection": "groceries/trips",
            "properties": {"store": "Corner Market", "total": 3583, "at": "2026-11-20T17:41:00-07:00"}}
    rows = dated_window(apps, records + [trip], "today", NOW, TZ)
    assert len(rows) == 4 and rows[0]["title"] == "Grocery trip · Corner Market"
    race = dated_rows(apps, records, date(2026, 12, 12), date(2026, 12, 12), TZ)
    assert [r["title"] for r in race if r["app"] == "running"] == ["Race · Winter 10K"]


def test_deleted_records_are_ignored(ws):
    apps, records = ws
    lib = next(r for r in records if r["properties"].get("title") == "Return library books")
    rows = dated_window(apps, [r for r in records if r is not lib] + [{**lib, "deleted_at": "x"}], "today", NOW, TZ)
    assert len(rows) == 2


def test_move_occurrence_shows_leg_day_once_at_five(ws):
    apps, records = ws
    legs = next(r for r in records if r["id"] == "s_legs")
    series, one_off = repeats.move_occurrence(legs, "at", "repeat", "2026-11-24", "2026-11-24T17:00", NOW, TZ)
    moved = {**legs, "properties": {**legs["properties"], **series}}
    new = {"id": "s_legs_once", "collection": "workout/sessions", "properties": one_off, "position": "zz"}
    recs = [moved if r is legs else r for r in records] + [new]
    rows = dated_rows(apps, recs, date(2026, 11, 24), date(2026, 11, 24), TZ)
    legs_rows = [r for r in rows if r["title"] == "Leg day"]
    assert [(r["at"], r["record_id"]) for r in legs_rows] == [("2026-11-24T17:00:00-07:00", "s_legs_once")]


def test_subscription_renewal_dated_title():
    rows = dated_rows(S.APPS, S.RECORDS, date(2026, 11, 22), date(2026, 11, 22), TZ)
    sp = next(r for r in rows if r["app"] == "subscriptions")
    assert sp["title"] == "Spotify renews · $11.99" and sp["at"] == "2026-11-22" and sp["occurrence"] == "2026-11-22"
