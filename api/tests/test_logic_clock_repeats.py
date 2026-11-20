"""Clock, windows, repeats, DST (backend.md §3, §11 rows 15, 16, 27, 28, 29; check.py item 6)."""
from datetime import date, datetime, timezone

import pytest

import seed_rows as S
from api.logic import clock, repeats
from api.logic.clock import localize, parse_value, window_bounds

TZ = S.TZ
NOW = parse_value(S.DEMO_NOW, TZ)
RECYCLING = {"rule": "FREQ=WEEKLY;BYDAY=FR", "start": "2026-10-23T20:00",
             "log": ["2026-10-23", "2026-10-30", "2026-11-13"], "skip": ["2026-11-06"]}


def test_now_demo_override_arg_and_env(monkeypatch):
    assert clock.now(TZ, S.DEMO_NOW).isoformat() == "2026-11-20T17:45:00-07:00"
    assert clock.now(TZ, "2026-11-20T17:45").isoformat() == "2026-11-20T17:45:00-07:00"
    monkeypatch.setenv("DEMO_NOW", "2026-11-21T00:45:00Z")
    assert clock.now(TZ).isoformat() == "2026-11-20T17:45:00-07:00"
    monkeypatch.setenv("DEMO_NOW", "1")
    assert clock.now(TZ).isoformat() == "2026-11-20T17:45:00-07:00"
    monkeypatch.delenv("DEMO_NOW")
    assert clock.now(TZ).tzinfo is not None


def test_windows_from_local_midnights():
    s, e = window_bounds("today", NOW, TZ)
    assert (s.isoformat(), e.isoformat()) == ("2026-11-20T00:00:00-07:00", "2026-11-21T00:00:00-07:00")
    s, e = window_bounds("week", NOW, TZ)
    assert (s.isoformat(), e.isoformat()) == ("2026-11-16T00:00:00-07:00", "2026-11-23T00:00:00-07:00")
    s, e = window_bounds("month", NOW, TZ)
    assert (s.isoformat(), e.isoformat()) == ("2026-11-01T00:00:00-06:00", "2026-12-01T00:00:00-07:00")
    assert (e.astimezone(timezone.utc) - s.astimezone(timezone.utc)).total_seconds() == 30 * 86400 + 3600
    assert window_bounds("all", NOW, TZ) is None
    # The day DST ends is 25 hours; built from midnights, not +24 h.
    s, e = window_bounds("today", parse_value("2026-11-01T12:00", TZ), TZ)
    assert (e.astimezone(timezone.utc) - s.astimezone(timezone.utc)).total_seconds() == 25 * 3600


def test_within_days():
    assert clock.within_days("7d", NOW, TZ) == (date(2026, 11, 20), date(2026, 11, 26))
    assert clock.within_days("-7d", NOW, TZ) == (date(2026, 11, 14), date(2026, 11, 20))
    assert clock.within_days("week", NOW, TZ) == (date(2026, 11, 16), date(2026, 11, 22))
    assert clock.within_days("past", NOW, TZ) == (None, date(2026, 11, 19))


def test_parse_wall_time_gets_zone_offset():
    assert parse_value("2026-11-20T17:41", TZ).isoformat() == "2026-11-20T17:41:00-07:00"
    assert parse_value("2026-07-01T09:00", TZ).isoformat() == "2026-07-01T09:00:00-06:00"
    assert parse_value("2026-11-22", TZ) == date(2026, 11, 22)


def test_nonexistent_and_repeated_wall_times():
    # Row 16: 2:30 am on Sun 14 Mar 2027 doesn't exist -> moved forward by the gap.
    assert localize(datetime(2027, 3, 14, 2, 30), TZ).isoformat() == "2027-03-14T03:30:00-06:00"
    # 1:30 am on Sun 7 Nov 2027 happens twice -> the first one (fold=0, MDT).
    assert localize(datetime(2027, 11, 7, 1, 30), TZ).isoformat() == "2027-11-07T01:30:00-06:00"


def test_repeat_expansion_through_nonexistent_time():
    rep = {"rule": "FREQ=DAILY", "start": "2027-03-13T02:30", "log": [], "skip": []}
    occ = repeats.expand(rep, date(2027, 3, 13), date(2027, 3, 15), TZ)
    assert [o["at"].isoformat() for o in occ] == [
        "2027-03-13T02:30:00-07:00", "2027-03-14T03:30:00-06:00", "2027-03-15T02:30:00-06:00"]
    rep = {"rule": "FREQ=DAILY", "start": "2027-11-06T01:30", "log": [], "skip": []}
    occ = repeats.expand(rep, date(2027, 11, 7), date(2027, 11, 7), TZ)
    assert occ[0]["at"].isoformat() == "2027-11-07T01:30:00-06:00"


def test_dst_wall_time_holds():
    # Row 15: 8 pm Friday chore across Nov 1: -06:00 -> -07:00, wall time unchanged.
    occ = repeats.expand(RECYCLING, date(2026, 10, 23), date(2026, 11, 27), TZ, include_skipped=True)
    ats = {o["occurrence"]: o["at"].isoformat() for o in occ}
    assert ats["2026-10-30"] == "2026-10-30T20:00:00-06:00"
    assert ats["2026-11-20"] == "2026-11-20T20:00:00-07:00"
    assert len(occ) == 6
    flags = {o["occurrence"]: (o["logged"], o["skipped"]) for o in occ}
    assert flags["2026-11-06"] == (False, True) and flags["2026-11-13"] == (True, False)
    # Default: skipped occurrences are dropped.
    assert "2026-11-06" not in [o["occurrence"] for o in repeats.expand(RECYCLING, date(2026, 11, 1), date(2026, 11, 30), TZ)]


def test_validate_rule_subset():
    assert repeats.validate_rule("FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20261210T235959") == []
    assert repeats.validate_rule("FREQ=MONTHLY;INTERVAL=2") == []
    assert repeats.validate_rule("FREQ=YEARLY")
    assert repeats.validate_rule("FREQ=WEEKLY;COUNT=3")
    assert repeats.validate_rule("FREQ=WEEKLY;BYDAY=XX")
    with pytest.raises(repeats.RepeatError):
        repeats.normalize_repeat("FREQ=HOURLY", "2026-11-20T20:00:00-07:00", TZ)


def test_plain_rule_string_is_normalized():
    rep = repeats.normalize_repeat("FREQ=WEEKLY;BYDAY=FR", "2026-11-20T20:00:00-07:00", TZ)
    assert rep == {"rule": "FREQ=WEEKLY;BYDAY=FR", "start": "2026-11-20T20:00", "log": [], "skip": []}


def test_complete_occurrence_moves_due():
    new, nxt = repeats.complete_occurrence(RECYCLING, "2026-11-20", NOW, TZ)
    assert new["log"][-1] == "2026-11-20"
    assert nxt == "2026-11-27T20:00:00-07:00"
    assert RECYCLING["log"][-1] == "2026-11-13"  # input untouched


def test_complete_overdue_does_not_pile_up():
    # Row 28: missed weeks; completing an old one jumps past today.
    rep = {"rule": "FREQ=WEEKLY;BYDAY=FR", "start": "2026-10-23T20:00", "log": [], "skip": []}
    new, nxt = repeats.complete_occurrence(rep, "2026-10-30", NOW, TZ)
    assert new["log"] == ["2026-10-30"]
    assert nxt == "2026-11-27T20:00:00-07:00"


def test_skip_occurrence():
    new, nxt = repeats.skip_occurrence(RECYCLING, "2026-11-20", NOW, TZ)
    assert new["skip"][-1] == "2026-11-20" and nxt == "2026-11-27T20:00:00-07:00"


def test_complete_last_occurrence_ends_series():
    # Row 29: UNTIL passed -> no next occurrence (done).
    rep = {"rule": "FREQ=WEEKLY;BYDAY=FR;UNTIL=20261120T235959", "start": "2026-10-23T20:00", "log": [], "skip": []}
    _, nxt = repeats.complete_occurrence(rep, "2026-11-20", NOW, TZ)
    assert nxt is None
    assert repeats.expand(rep, date(2026, 11, 21), date(2026, 12, 31), TZ) == []


def test_complete_unknown_or_repeated_occurrence_fails():
    with pytest.raises(repeats.RepeatError):
        repeats.complete_occurrence(RECYCLING, "2026-11-19", NOW, TZ)
    with pytest.raises(repeats.RepeatError):
        repeats.complete_occurrence(RECYCLING, "2026-11-13", NOW, TZ)


def test_date_only_series():
    rep = {"rule": "FREQ=MONTHLY", "start": "2026-11-22", "log": [], "skip": []}
    occ = repeats.expand(rep, date(2026, 11, 1), date(2027, 1, 31), TZ)
    assert [o["at"] for o in occ] == [date(2026, 11, 22), date(2026, 12, 22), date(2027, 1, 22)]
    _, nxt = repeats.complete_occurrence(rep, "2026-11-22", NOW, TZ)
    assert nxt == "2026-12-22"


def _legs():
    return next(r for r in S.RECORDS if r["id"] == "s_legs")


def test_move_occurrence_leg_day():
    # check.py item 6: Leg day 2026-11-24 to 5:00 pm.
    legs = _legs()
    series, one_off = repeats.move_occurrence(legs, "at", "repeat", "2026-11-24", "2026-11-24T17:00", NOW, TZ)
    assert "2026-11-24" in series["repeat"]["skip"]
    assert series["at"] == "2026-12-01T07:00:00-07:00"  # the series' next open occurrence
    assert one_off["at"] == "2026-11-24T17:00:00-07:00"
    assert "repeat" not in one_off and one_off["name"] == "Leg day"
    assert one_off["_moved_from"] == {"record_id": "s_legs", "occurrence": "2026-11-24"}


def test_move_occurrence_validation():
    legs = _legs()
    with pytest.raises(repeats.RepeatError):  # in the past (and logged)
        repeats.move_occurrence(legs, "at", "repeat", "2026-11-17", "2026-11-25T17:00", NOW, TZ)
    with pytest.raises(repeats.RepeatError):  # not an occurrence
        repeats.move_occurrence(legs, "at", "repeat", "2026-11-25", "2026-11-25T17:00", NOW, TZ)
    pull = next(r for r in S.RECORDS if r["id"] == "s_pull")
    with pytest.raises(repeats.RepeatError):  # already skipped
        later = parse_value("2026-09-01T00:00", TZ)
        repeats.move_occurrence(pull, "at", "repeat", "2026-09-07", "2026-09-08T17:00", later, TZ)


def test_edit_rule_starts_at_next_open_occurrence():
    # Row 27: weekly -> every 2 weeks from the next open occurrence; log and skip kept.
    new = repeats.edit_rule(RECYCLING, "FREQ=WEEKLY;INTERVAL=2;BYDAY=FR", NOW, TZ)
    assert new["start"] == "2026-11-20T20:00"
    assert new["log"] == RECYCLING["log"] and new["skip"] == RECYCLING["skip"]
    occ = repeats.expand(new, date(2026, 11, 20), date(2026, 12, 31), TZ)
    assert [o["occurrence"] for o in occ] == ["2026-11-20", "2026-12-04", "2026-12-18"]


def test_next_open():
    o = repeats.next_open(RECYCLING, TZ, after=NOW)
    assert o["at"].isoformat() == "2026-11-20T20:00:00-07:00"
    o = repeats.next_open(RECYCLING, TZ, after_day=date(2026, 11, 20))
    assert o["occurrence"] == "2026-11-27"
