"""The canonical demo seed as plain dicts, copied from spec/backend.md §2.2 and §2.3.

Used by the logic tests as their oracle. Times are America/Denver; after Nov 1 the
offset is -07:00, before it -06:00. Money is cents.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TZ = "America/Denver"
DEMO_NOW = "2026-11-20T17:45:00-07:00"

_n = 0


def rec(ref: str, rid: str | None = None, **props) -> dict:
    global _n
    _n += 1
    return {"id": rid or f"{ref.split('/')[1]}_{_n}", "collection": ref,
            "properties": props, "position": f"a{_n:04d}"}


def f(key, type_="text", **kw):
    return {"key": key, "label": key.title(), "type": type_, **kw}


def opts(*pairs):
    return [{"id": i, "label": l} for i, l in pairs]


def nov(day: int, hm: str = "12:00") -> str:
    return f"2026-11-{day:02d}T{hm}:00-07:00"


# ---------------------------------------------------------------- specs

BUDGET = {
    "key": "budget", "name": "Budget", "settings": {"limit": 120000},
    "collections": [{
        "key": "spend", "titleField": "note", "dateField": "at", "amountField": "amount",
        "fields": [f("note"), f("amount", "money"), f("at", "datetime"),
                   f("category", "select", options=[
                       {"id": "c_groceries", "label": "Groceries", "limit": 20000},
                       {"id": "c_eating_out", "label": "Eating out", "limit": 15000},
                       {"id": "c_rent", "label": "Rent"},
                       {"id": "c_fun", "label": "Fun"},
                       {"id": "c_transport", "label": "Transport", "limit": 10000},
                       {"id": "c_subscriptions", "label": "Subscriptions", "limit": 4000}])]}],
    "face": {"value": {"minus": [{"setting": "limit"},
                                 {"agg": "sum", "from": "budget/spend", "field": "amount", "window": "month"}]},
             "format": "money", "label": "left", "status": True, "empty": "Set a monthly amount"},
    "tabs": [{"kind": "page", "id": "t_overview", "title": "Overview", "children": [
        {"kind": "gauge", "id": "b_left", "label": "Left this month",
         "value": {"minus": [{"setting": "limit"},
                             {"agg": "sum", "from": "budget/spend", "field": "amount", "window": "month"}]},
         "target": {"setting": "limit"}, "format": "money"},
        {"kind": "bars", "id": "b_where", "label": "Where it went", "from": "budget/spend", "by": "category",
         "value": {"agg": "sum", "from": "budget/spend", "field": "amount", "window": "month"}}]}],
}

SUBSCRIPTIONS = {
    "key": "subscriptions", "name": "Subscriptions",
    "collections": [{
        "key": "subscriptions", "titleField": "name", "dateField": "renews", "amountField": "amount",
        "calendar": True, "datedTitle": "{name} renews · {amount}",
        "fields": [f("name"), f("amount", "money"), f("renews", "date"), f("repeat", "repeat"), f("remind")]}],
    "face": {"value": {"agg": "sum", "from": "subscriptions/subscriptions", "field": "amount"},
             "format": "money", "label": "a month"},
    "tabs": [{"kind": "page", "id": "t_main", "title": "Subscriptions", "children": [
        {"kind": "gauge", "id": "b_total", "label": "A month",
         "value": {"agg": "sum", "from": "subscriptions/subscriptions", "field": "amount"},
         "target": None, "format": "money"}]}],
}

GROCERIES = {
    "key": "groceries", "name": "Groceries",
    "collections": [
        {"key": "items", "titleField": "name",
         "fields": [f("name"), f("list", "select", options=[
             {"id": "l_weekly", "label": "Weekly shop"},
             {"id": "l_taco", "label": "Taco night", "hint": "Sat 21 Nov"},
             {"id": "l_costco", "label": "Costco run", "hint": "Once a month"}]),
             f("status", "select", options=opts(("to_buy", "To buy"), ("bought", "Bought"))),
             f("qty"), f("price", "money"), f("bought_on", "date"),
             f("trip", "relation", target="groceries/trips"),
             f("usual", "select", options=opts(("auto", "Auto"), ("yes", "Yes"), ("no", "No")))]},
        {"key": "trips", "titleField": "store", "dateField": "at", "amountField": "total",
         "calendar": True, "label": "Grocery trip",
         "fields": [f("store"), f("total", "money"), f("at", "datetime")]}],
    "face": {"value": {"agg": "count", "from": "groceries/items", "window": "all",
                       "where": [{"field": "status", "op": "eq", "value": "to_buy"},
                                 {"field": "list", "op": "eq", "value": "l_weekly"}]},
             "format": "count", "label": "to buy"},
    "tabs": [{"kind": "page", "id": "t_list", "title": "List", "children": [
        {"kind": "progress", "id": "b_spend", "label": "Spent on groceries this month",
         "value": {"agg": "sum", "from": "groceries/trips", "field": "total", "window": "month"},
         "target": 20000, "format": "money"}]}],
}

CALENDAR = {
    "key": "calendar", "name": "Calendar",
    "collections": [{"key": "events", "titleField": "title", "dateField": "at", "calendar": True,
                     "fields": [f("title"), f("at", "datetime"), f("ends", "datetime"), f("repeat", "repeat"),
                                f("kind", "select", options=opts(("doctor", "Doctor"), ("dentist", "Dentist"),
                                                                 ("barber", "Barber"), ("other", "Other"))),
                                f("remind"), f("source"), f("ext_id")]}],
    "face": {"value": {"agg": "count", "from": "*dated", "window": "today"}, "format": "count", "label": "today"},
    "tabs": [],
}

CLASSES = {
    "key": "classes", "name": "Classes",
    "collections": [
        {"key": "classes", "titleField": "name", "dateField": "time", "calendar": True,
         "fields": [f("name"), f("title"), f("room"), f("time", "datetime"), f("repeat", "repeat")]},
        {"key": "due", "titleField": "title", "dateField": "at", "calendar": True,
         "fields": [f("title"), f("kind", "select", options=opts(("assignment", "Assignment"), ("exam", "Exam"))),
                    f("at", "datetime"), f("class", "relation", target="classes/classes"), f("done", "bool")]}],
    "face": {"value": {"agg": "count", "from": "classes/due",
                       "where": [{"field": "done", "op": "eq", "value": False},
                                 {"field": "at", "op": "within", "value": "7d"}]},
             "format": "count", "label": "due this week"},
    "tabs": [],
}

NOTES = {
    "key": "notes", "name": "Notes",
    "collections": [
        {"key": "notebooks", "titleField": "name", "fields": [f("name"), f("class", "relation")]},
        {"key": "notes", "titleField": "title", "dateField": "at",
         "fields": [f("title"), f("body", multiline=True), f("notebook", "relation", many=True), f("at", "datetime")]}],
    "face": {"value": {"agg": "count", "from": "notes/notes", "window": "week"}, "format": "count", "label": "this week"},
    "tabs": [],
}

TODOS = {
    "key": "todos", "name": "To-dos",
    "collections": [{"key": "todos", "titleField": "title", "dateField": "due", "calendar": True,
                     "fields": [f("title"), f("due", "datetime"), f("place"), f("done", "bool"),
                                f("repeat", "repeat"), f("remind")]}],
    "face": {"value": {"agg": "count", "from": "todos/todos", "window": "today",
                       "where": [{"field": "done", "op": "eq", "value": False}]},
             "format": "count", "label": "today"},
    "tabs": [],
}

_SESSIONS_DONE_WEEK = {"agg": "count", "from": "workout/sessions", "window": "week",
                       "where": [{"field": "done", "op": "eq", "value": True}]}

WORKOUT = {
    "key": "workout", "name": "Workout",
    "collections": [
        {"key": "sessions", "titleField": "name", "dateField": "at", "calendar": True,
         "fields": [f("name"), f("routine", "relation", target="workout/routines"), f("at", "datetime"),
                    f("repeat", "repeat"), f("done", "bool"), f("started_at", "datetime"), f("minutes", "number")]},
        {"key": "routines", "titleField": "name", "fields": [f("name"), f("minutes", "number"), f("needs")]},
        {"key": "exercises", "titleField": "name",
         "fields": [f("name"), f("routine", "relation", target="workout/routines"), f("sets", "number"),
                    f("reps", "number"), f("weight", "number"), f("order", "number")]},
        {"key": "sets", "titleField": "exercise", "dateField": "at",
         "fields": [f("exercise", "relation", target="workout/exercises"),
                    f("session", "relation", target="workout/sessions"),
                    f("reps", "number"), f("weight", "number"), f("at", "datetime"),
                    {"key": "volume", "label": "Volume", "type": "formula", "op": "mul", "a": "weight", "b": "reps"}]}],
    "face": {"value": _SESSIONS_DONE_WEEK, "format": "count", "label": "this week"},
    "tabs": [{"kind": "page", "id": "t_today", "title": "Today", "children": [
        {"kind": "next", "id": "b_next", "source": "workout/sessions", "log": "workout/sets", "fields": ["reps", "weight"]},
        {"kind": "metric", "id": "b_lifted", "label": "Lifted this week", "unit": "lb", "format": "number",
         "value": {"agg": "sum", "from": "workout/sets", "field": "volume", "window": "week"}},
        {"kind": "metric", "id": "b_since", "label": "Done since September", "unit": "sessions", "format": "count",
         "value": {"agg": "count", "from": "workout/sessions",
                   "where": [{"field": "done", "op": "eq", "value": True}]}},
        {"kind": "progress", "id": "b_sessions", "label": "Sessions this week", "format": "count",
         "value": _SESSIONS_DONE_WEEK,
         "target": {"agg": "count", "from": "workout/sessions", "window": "week"}},
        {"kind": "strip", "id": "b_strip", "label": "This week",
         "value": {"agg": "count", "from": "workout/sessions", "window": "week"}}]}],
}

CALORIES = {
    "key": "calories", "name": "Calories", "settings": {"target": 2200},
    "collections": [
        {"key": "meals", "titleField": "name", "dateField": "at",
         "fields": [f("name"), f("calories", "number"), f("protein", "number"), f("meal", "select"), f("at", "datetime")]},
        {"key": "foods", "titleField": "name", "fields": [f("name"), f("calories", "number"), f("protein", "number")]}],
    "face": {"value": {"agg": "sum", "from": "calories/meals", "field": "calories", "window": "today"},
             "format": "number", "label": "today"},
    "tabs": [{"kind": "page", "id": "t_today", "title": "Today", "children": [
        {"kind": "ring", "id": "b_ring", "label": "Today",
         "value": {"agg": "sum", "from": "calories/meals", "field": "calories", "window": "today"},
         "target": {"setting": "target"}, "format": "number"}]}],
}

RUNNING = {
    "key": "running", "name": "Running",
    "collections": [
        {"key": "runs", "titleField": "name", "dateField": "at", "calendar": True, "label": "Run",
         "fields": [f("name"), f("kind", "select", options=opts(("Easy", "Easy"), ("Long", "Long"), ("Tempo", "Tempo"),
                                                                ("Intervals", "Intervals"), ("Race", "Race"))),
                    f("distance", "number"), f("minutes", "number"), f("at", "datetime"), f("done", "bool")]},
        {"key": "races", "titleField": "name", "dateField": "at", "calendar": True, "label": "Race",
         "fields": [f("name"), f("at", "datetime"), f("distance")]}],
    "face": {"value": {"agg": "sum", "from": "running/runs", "field": "distance", "window": "week",
                       "where": [{"field": "done", "op": "eq", "value": True}]},
             "format": "number", "label": "mi this week"},
    "tabs": [{"kind": "page", "id": "t_week", "title": "This week", "children": [
        {"kind": "countdown", "id": "b_race", "source": "running/races"},
        {"kind": "strip", "id": "b_strip", "label": "This week",
         "value": {"agg": "sum", "from": "running/runs", "field": "distance", "window": "week"}}]}],
}

MEDITATION = {
    "key": "meditation", "name": "Meditation",
    "collections": [{"key": "sessions", "titleField": "kind", "dateField": "at",
                     "fields": [f("kind", "select"), f("minutes", "number"), f("at", "datetime"),
                                f("mood_before", "number"), f("mood_after", "number"), f("note")]}],
    "face": {"value": {"agg": "sum", "from": "meditation/sessions", "field": "minutes", "window": "week"},
             "format": "number", "label": "min this week"},
    "tabs": [{"kind": "page", "id": "t_sit", "title": "Sit", "children": [
        {"kind": "strip", "id": "b_strip", "label": "This week",
         "value": {"agg": "sum", "from": "meditation/sessions", "field": "minutes", "window": "week"}}]}],
}

CYCLE = {
    "key": "cycle", "name": "Cycle", "settings": {"clair_read": True},
    "collections": [
        {"key": "days", "titleField": "date", "dateField": "date",
         "fields": [f("date", "date"), f("flow", "select"), f("symptoms"), f("energy", "number"), f("note")]},
        {"key": "cycles", "titleField": "start", "dateField": "start",
         "fields": [f("start", "date"), f("length", "number")]}],
    "face": {"value": {"agg": "max", "from": "cycle/cycles", "field": "start"},
             "format": "text", "label": "last period started"},
    "tabs": [],
}

APPS = [NOTES, BUDGET, SUBSCRIPTIONS, GROCERIES, CALENDAR, CLASSES, TODOS, WORKOUT,
        CALORIES, RUNNING, CYCLE, MEDITATION]

# ---------------------------------------------------------------- records

RECORDS: list[dict] = []
add = RECORDS.append

# Budget: November spend (§2.3), $788.00 in all, plus October rows Search finds.
_SPEND = [
    (1, "November rent", "c_rent", 38000), (1, "Cafe Rio", "c_eating_out", 1148),
    (2, "Hulu", "c_subscriptions", 999), (2, "Lime scooter", "c_transport", 560),
    (3, "Adobe CC, student", "c_subscriptions", 1349), (3, "Blue Copper", "c_eating_out", 525),
    (4, "Chipotle", "c_eating_out", 1235), (5, "Smith's", "c_groceries", 4137),
    (6, "Blue Copper", "c_eating_out", 525), (7, "Costa Vida", "c_eating_out", 1320),
    (7, "Megaplex movie", "c_fun", 1250), (9, "Corner Market", "c_groceries", 862),
    (9, "iCloud 50 GB", "c_subscriptions", 299), (10, "Corner Market", "c_groceries", 429),
    (10, "Blue Copper", "c_eating_out", 525), (11, "Smith's", "c_groceries", 2715),
    (12, "Corner Market", "c_groceries", 429), (12, "Sushi with Maya", "c_eating_out", 2240),
    (13, "Corner Market", "c_groceries", 778), (13, "Thai Siam", "c_eating_out", 2800),
    (14, "Smith's", "c_groceries", 4501), (14, "Cafe Rio", "c_eating_out", 1148),
    (14, "Lime scooter", "c_transport", 840), (14, "Thrift shop", "c_fun", 2003),
    (15, "Corner Market", "c_groceries", 349), (15, "Bagel Project", "c_eating_out", 1497),
    (16, "Cafe Rio", "c_eating_out", 962), (17, "Blue Copper", "c_eating_out", 525),
    (17, "Gas", "c_transport", 2800), (18, "Taco Bell", "c_eating_out", 687),
    (19, "Union food court", "c_eating_out", 1140), (19, "Union vending", "c_eating_out", 223),
]
for d, note, cat, cents in _SPEND:
    add(rec("budget/spend", note=note, category=cat, amount=cents, at=nov(d)))
for at, note, cents in [("2026-10-03T12:00:00-06:00", "Blue Copper", 525),
                        ("2026-10-11T12:00:00-06:00", "Blue Copper", 525),
                        ("2026-10-19T12:00:00-06:00", "Starbucks", 610)]:
    add(rec("budget/spend", note=note, category="c_eating_out", amount=cents, at=at))

# Subscriptions: monthly; passed November renewals are logged (the sweep made spends).
for rid, name, cents, renews, start, log in [
        ("sub_spotify", "Spotify", 1199, "2026-11-22", "2026-11-22", []),
        ("sub_hulu", "Hulu", 999, "2026-12-02", "2026-11-02", ["2026-11-02"]),
        ("sub_adobe", "Adobe CC, student", 1349, "2026-12-03", "2026-11-03", ["2026-11-03"]),
        ("sub_icloud", "iCloud 50 GB", 299, "2026-12-09", "2026-11-09", ["2026-11-09"])]:
    add(rec("subscriptions/subscriptions", rid, name=name, amount=cents, renews=renews,
            repeat={"rule": "FREQ=MONTHLY", "start": start, "log": log, "skip": []}))

# Groceries: 22 open items on three lists, November trips, bought items linked to them.
_OPEN = {
    "l_weekly": ["Oat milk", "Eggs", "Bananas", "Chicken thighs", "Rice", "Spinach", "Greek yogurt",
                 "Coffee beans", "Coffee filters", "Tortillas", "Olive oil", "Dish soap"],
    "l_taco": ["Ground beef", "Avocados", "Limes", "Salsa", "Shredded cheese"],
    "l_costco": ["Paper towels", "Laundry pods", "Frozen berries", "Almonds", "Toilet paper"],
}
for lst, names in _OPEN.items():
    for name in names:
        add(rec("groceries/items", name=name, list=lst, status="to_buy", usual="auto"))
_TRIPS = [(5, "Smith's", 4137, [("Coffee beans", 299), ("Butter", 479)]),
          (9, "Corner Market", 862, [("Chicken thighs", 862)]),
          (10, "Corner Market", 429, [("Greek yogurt", 429)]),
          (11, "Smith's", 2715, [("Spinach", 329), ("Cheddar", 399)]),
          (12, "Corner Market", 429, [("Eggs", 429)]),
          (13, "Corner Market", 778, [("Oat milk", 349), ("Parmesan", 429)]),
          (14, "Smith's", 4501, [("Bananas", 187), ("Orange juice", 369)]),
          (15, "Corner Market", 349, [("Hummus", 349)])]
for d, store, total, items in _TRIPS:
    trip = rec("groceries/trips", store=store, total=total, at=nov(d, "17:00"))
    add(trip)
    for name, price in items:
        add(rec("groceries/items", name=name, status="bought", price=price,
                bought_on=f"2026-11-{d:02d}", trip=[trip["id"]], usual="auto"))

# Calendar: own events and the four Google events.
for rid, at in [("e_haircut_aug", "2026-08-08T11:00:00-06:00"), ("e_haircut_sep", "2026-09-12T11:00:00-06:00"),
                ("e_haircut_oct", "2026-10-17T11:00:00-06:00")]:
    add(rec("calendar/events", rid, title="Haircut", at=at, kind="barber"))
add(rec("calendar/events", "e_coffee", title="Coffee with Maya", at=nov(21, "10:00")))
add(rec("calendar/events", "g_dentist", title="Dentist", at=nov(24, "07:30"), ends=nov(24, "08:30"),
        source="google", ext_id="g1"))
add(rec("calendar/events", "g_drive", title="Drive home for Thanksgiving", at=nov(25, "17:00"),
        ends=nov(25, "21:00"), source="google", ext_id="g2"))
add(rec("calendar/events", "g_thanksgiving", title="Thanksgiving at home", at="2026-11-26",
        ends="2026-11-28", source="google", ext_id="g3"))
add(rec("calendar/events", "g_back", title="Back to campus", at=nov(29, "12:00"), ends=nov(29, "13:00"),
        source="google", ext_id="g4"))

# Classes.
add(rec("classes/classes", "c01", name="ECON 1010", title="Principles of Microeconomics", room="Kendall 104",
        time="2026-11-24T09:10:00-07:00",
        repeat={"rule": "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20261210T235959", "start": "2026-08-25T09:10",
                "log": [], "skip": ["2026-11-26"]}))
add(rec("classes/classes", "c02", name="MATH 1210", title="Calculus I", room="JWB 335",
        time="2026-11-23T11:50:00-07:00",
        repeat={"rule": "FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959", "start": "2026-08-24T11:50",
                "log": [], "skip": []}))
add(rec("classes/classes", "c03", name="CS 3500", title="Software Practice", room="WEB L104",
        time="2026-11-23T15:00:00-07:00",
        repeat={"rule": "FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959", "start": "2026-08-24T15:00",
                "log": [], "skip": []}))
add(rec("classes/due", "d01", title="Start CS 3500 project", kind="assignment", at=nov(23, "23:59"),
        **{"class": ["c03"]}, done=False))
add(rec("classes/due", "d02", title="Homework 11", kind="assignment", at=nov(24, "23:59"),
        **{"class": ["c02"]}, done=False))
add(rec("classes/due", "d03", title="Homework 10", kind="assignment", at=nov(17, "23:59"),
        **{"class": ["c02"]}, done=True))

# Notes.
add(rec("notes/notebooks", "nb_econ", name="ECON 1010", **{"class": ["c01"]}))
add(rec("notes/notebooks", "nb_math", name="MATH 1210", **{"class": ["c02"]}))
add(rec("notes/notebooks", "nb_cs3500", name="CS 3500", **{"class": ["c03"]}))
add(rec("notes/notebooks", "nb_personal", name="Personal"))
for at, nb, title in [(nov(10), ["nb_math"], "Related rates examples"), (nov(15), ["nb_personal"], "Gift ideas for mom"),
                      (nov(16, "15:50"), ["nb_cs3500"], "Unit testing with mocks"),
                      (nov(18, "15:55"), ["nb_cs3500"], "Dependency injection"),
                      (nov(19, "10:30"), ["nb_econ"], "Price elasticity"),
                      # the three added for links (Nov 20), all dated before Mon 16 Nov
                      (nov(9, "11:20"), ["nb_math"], "Chain rule recap"),
                      (nov(15, "10:30"), ["nb_math", "nb_econ"], "Finals study plan"),
                      (nov(14, "18:30"), ["nb_personal"], "Chicken and rice")]:
    add(rec("notes/notes", title=title, notebook=nb, at=at))

# To-dos.
add(rec("todos/todos", "t_library", title="Return library books", due=nov(20, "21:00"),
        place="Marriott Library", done=False))
add(rec("todos/todos", "t_recycling", title="Take out recycling", due=nov(20, "20:00"), done=False,
        repeat={"rule": "FREQ=WEEKLY;BYDAY=FR", "start": "2026-10-23T20:00",
                "log": ["2026-10-23", "2026-10-30", "2026-11-13"], "skip": ["2026-11-06"]}))
add(rec("todos/todos", "t_call_home", title="Call home", due="2026-11-22", done=False))
add(rec("todos/todos", "t_maya", title="Pay Maya back for pizza ($14)", done=False))
add(rec("todos/todos", "t_devday", title="DevDay demo", due=nov(20, "15:00"), place="Lassonde Studios", done=True))
add(rec("todos/todos", "t_flu", title="Book flu shot", place="Student health", done=True))


# Workout: three series from Tue 1 Sep; every non-skipped occurrence up to Thu 19 Nov is logged.
def _days(first: date, last: date, weekdays: set[int], skip: set[str]) -> list[str]:
    out, d = [], first
    while d <= last:
        if d.weekday() in weekdays and d.isoformat() not in skip:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


_S, _E = date(2026, 9, 1), date(2026, 11, 19)
_PULL_SKIP = ["2026-09-07", "2026-10-12", "2026-10-16"]
add(rec("workout/sessions", "s_pull", name="Pull day", routine=["ro_pull"], at=nov(20, "18:00"), done=False,
        repeat={"rule": "FREQ=WEEKLY;BYDAY=MO,FR", "start": "2026-09-01T18:00",
                "log": _days(_S, _E, {0, 4}, set(_PULL_SKIP)), "skip": _PULL_SKIP}))
# Leg day moved from 6 pm to 7 am on Tue 17 Nov: per §11 row 27 `start` resets there.
add(rec("workout/sessions", "s_legs", name="Leg day", routine=["ro_legs"], at=nov(24, "07:00"), done=False,
        repeat={"rule": "FREQ=WEEKLY;BYDAY=TU", "start": "2026-11-17T07:00",
                "log": _days(_S, _E, {1}, {"2026-10-13"}), "skip": ["2026-10-13"]}))
add(rec("workout/sessions", "s_push", name="Push day", routine=["ro_push"], at=nov(25, "18:00"), done=False,
        repeat={"rule": "FREQ=WEEKLY;BYDAY=WE", "start": "2026-09-02T18:00",
                "log": _days(_S, _E, {2}, {"2026-10-14"}), "skip": ["2026-10-14"]}))
add(rec("workout/routines", "ro_pull", name="Pull", minutes=45, needs="Gym"))
add(rec("workout/routines", "ro_push", name="Push", minutes=40, needs="Gym"))
add(rec("workout/routines", "ro_legs", name="Legs", minutes=35, needs="Gym"))
_EX = [("ex_pull_ups", "Pull-ups", "ro_pull", 3, 8, 0), ("ex_lat_pulldown", "Lat pulldown", "ro_pull", 3, 10, 120),
       ("ex_cable_row", "Seated cable row", "ro_pull", 3, 12, 100), ("ex_face_pulls", "Face pulls", "ro_pull", 3, 15, 40),
       ("ex_hammer_curl", "Hammer curl", "ro_pull", 3, 12, 25),
       ("ex_push_ups", "Push-ups", "ro_push", 3, 12, 0), ("ex_db_bench", "Dumbbell bench", "ro_push", 3, 10, 40),
       ("ex_goblet", "Goblet squat", "ro_legs", 3, 10, 45), ("ex_lunges", "Walking lunges", "ro_legs", 3, 12, 0)]
for i, (rid, name, ro, s, r, w) in enumerate(_EX):
    add(rec("workout/exercises", rid, name=name, routine=[ro], sets=s, reps=r, weight=w, order=i + 1))
# This week's sets, one row per set at the plan (Lat pulldown at 120 on Mon 16 Nov).
for day, hm, sess, exs in [(16, "18:00", "s_pull", ["ex_lat_pulldown", "ex_cable_row", "ex_face_pulls",
                                                     "ex_hammer_curl", "ex_pull_ups"]),
                           (17, "07:00", "s_legs", ["ex_goblet", "ex_lunges"]),
                           (18, "18:00", "s_push", ["ex_db_bench", "ex_push_ups"])]:
    for ex in exs:
        _, _, _, s, r, w = next(e for e in _EX if e[0] == ex)
        for _ in range(s):
            add(rec("workout/sets", exercise=[ex], session=[sess], reps=r, weight=w, at=nov(day, hm)))
# One earlier Lat pulldown set (Mon 2 Nov at 115) so `best` has to pick.
add(rec("workout/sets", exercise=["ex_lat_pulldown"], session=["s_pull"], reps=10, weight=115, at=nov(2, "18:00")))

# Calories.
_MEALS = [
    (16, [("Oatmeal and banana", 350, 10, "08:00"), ("Turkey sandwich", 520, 28, "12:30"), ("Pasta with chicken", 780, 42, "19:00")]),
    (17, [("Greek yogurt and granola", 310, 18, "08:00"), ("Leftover pasta", 640, 34, "12:30"), ("Tacos", 820, 38, "19:00")]),
    (18, [("Oatmeal and banana", 350, 10, "08:00"), ("Taco Bell burrito", 690, 24, "12:30"), ("Chicken and rice", 640, 45, "19:00")]),
    (19, [("Eggs and toast", 380, 22, "08:00"), ("Union food court rice bowl", 690, 30, "12:30"), ("Frozen pizza", 900, 36, "19:00")]),
    (20, [("Oatmeal and banana", 350, 10, "08:10"), ("Chicken and rice", 640, 45, "12:30"), ("Greek yogurt", 150, 15, "15:40")]),
]
for d, meals in _MEALS:
    for name, cal, prot, hm in meals:
        add(rec("calories/meals", name=name, calories=cal, protein=prot, at=nov(d, hm)))
for name, cal, prot in [("Oatmeal and banana", 350, 10), ("Chicken and rice", 640, 45), ("Greek yogurt", 150, 15)]:
    add(rec("calories/foods", name=name, calories=cal, protein=prot))

# Running.
add(rec("running/races", "race_10k", name="Winter 10K", at="2026-12-12T09:00:00-07:00", distance="10K"))
for at, kind, dist, mins in [
        ("2026-10-31T09:00:00-06:00", "Long", 4, 40), (nov(7, "09:00"), "Long", 4.5, 44), (nov(14, "09:00"), "Long", 5, 49),
        (nov(3, "17:30"), "Easy", 3, 30), (nov(10, "17:30"), "Easy", 3, 29), (nov(12, "17:30"), "Easy", 3.5, 34),
        (nov(17, "17:30"), "Easy", 3, 29), (nov(19, "16:30"), "Easy", 4, 38)]:
    add(rec("running/runs", name=f"{kind} run", kind=kind, distance=dist, minutes=mins, at=at, done=True))

# Meditation.
for at, kind, mins, mb, ma in [(nov(16, "22:30"), "Sleep", 10, 2, 4), (nov(18, "07:40"), "Breathing", 5, 3, 4),
                               (nov(19, "22:45"), "Body scan", 10, 2, 3)]:
    add(rec("meditation/sessions", kind=kind, minutes=mins, at=at, mood_before=mb, mood_after=ma))

# Cycle.
add(rec("cycle/cycles", "cy_1", start="2026-09-01", length=28))
add(rec("cycle/cycles", "cy_2", start="2026-09-29", length=28))
add(rec("cycle/cycles", "cy_3", start="2026-10-27"))
for d1 in [date(2026, 9, 1), date(2026, 9, 29), date(2026, 10, 27)]:
    add(rec("cycle/days", date=d1.isoformat(), flow="Medium", symptoms="cramps", energy=2))
    add(rec("cycle/days", date=(d1 + timedelta(days=1)).isoformat(), flow="Heavy", symptoms="cramps", energy=2))
    add(rec("cycle/days", date=(d1 + timedelta(days=2)).isoformat(), flow="Light", energy=3))


# ---------------------------------------------------------------- the real seed (api/templates + api/seed)

def real_workspace(state: str = "full", gcal_fixture: bool = True):
    """(apps, records) from api/templates/*.json and api/seed/data.py, ids = human keys."""
    from api.seed import data
    from api.seed.load import apps_for, demo_spec

    def resolve(v):
        if isinstance(v, data.Ref):
            return v.key
        if isinstance(v, list):
            return [resolve(x) for x in v]
        if isinstance(v, dict):
            return {k: resolve(x) for k, x in v.items()}
        return v

    keys = apps_for(state)
    apps = [demo_spec(k) for k in keys]
    recs = data.records(gcal_fixture)
    out, n = [], 0
    for app in keys:
        for coll, rows in recs.get(app, {}).items():
            for key, props in rows:
                n += 1
                out.append({"id": key, "collection": f"{app}/{coll}", "properties": resolve(props),
                            "position": f"a{n:05d}"})
    return apps, out
