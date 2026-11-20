"""The planning brief (clair-agent.md §12.9, backend.md §13 check.py 3a), check_plan and the snapshot hook.

No database: the real seed (api/seed + api/templates) is loaded in memory, with the Google fixture.
"""
from __future__ import annotations

import copy
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from seed_rows import DEMO_NOW, TZ, real_workspace  # noqa: E402

from api.clair import snapshot  # noqa: E402
from api.clair.brief import RUNG_PARTS, build_brief, check_plan, planning_window  # noqa: E402
from api.logic.clock import now as clock_now  # noqa: E402
from api.workspace import Loaded  # noqa: E402

MON, SUN = date(2026, 11, 23), date(2026, 11, 29)

# The rung-4 fixture: check.py 3a, "the fixture in clair-agent.md §12.9 line for line".
FIXTURE = '''<brief window="Mon 23 Nov to Sun 29 Nov">
apps read: Calendar, Classes, To-dos, Workout, Running, Calories, Cycle, Meditation, Groceries (9)
booked:
- Classes "MATH 1210" Mon 23 Nov 11:50 am to 12:50 pm [c02]
- Classes "CS 3500" Mon 23 Nov 3:00 to 4:00 pm [c03]
- Classes "Start CS 3500 project" Mon 23 Nov 11:59 pm [d01]
- Google Calendar "Dentist" Tue 24 Nov 7:30 to 8:30 am · source google [g_dentist]
- Classes "ECON 1010" Tue 24 Nov 9:10 to 10:10 am [c01]
- Classes "Homework 11" Tue 24 Nov 11:59 pm [d02]
- Classes "MATH 1210" Wed 25 Nov 11:50 am to 12:50 pm [c02]
- Classes "CS 3500" Wed 25 Nov 3:00 to 4:00 pm [c03]
- Google Calendar "Drive home for Thanksgiving" Wed 25 Nov 5:00 to 9:00 pm · source google [g_drive]
- Google Calendar "Thanksgiving at home" Thu 26 to Sat 28 Nov, all day · source google [g_thanksgiving]
- To-dos "Take out recycling" Fri 27 Nov 8:00 pm [t_recycling]
- Google Calendar "Back to campus" Sun 29 Nov 12:00 to 1:00 pm · source google [g_back]
sessions:
- s_pull occurrence 2026-11-23 "Pull day" Mon 23 Nov 6:00 to 6:45 pm · routine Pull · 45 min · needs Gym [s_pull, ro_pull]
- s_legs occurrence 2026-11-24 "Leg day" Tue 24 Nov 7:00 to 7:35 am · routine Legs · 35 min · needs Gym [s_legs, ro_legs]
- s_push occurrence 2026-11-25 "Push day" Wed 25 Nov 6:00 to 6:40 pm · routine Push · 40 min · needs Gym [s_push, ro_push]
- s_pull occurrence 2026-11-27 "Pull day" Fri 27 Nov 6:00 to 6:45 pm · routine Pull · 45 min · needs Gym [s_pull, ro_pull]
clashes:
- Leg day 2026-11-24 Tue 24 Nov 7:00 to 7:35 am ↔ "Dentist" Tue 24 Nov 7:30 to 8:30 am (overlap) [s_legs, g_dentist]
- Push day 2026-11-25 Wed 25 Nov 6:00 to 6:40 pm ↔ "Drive home for Thanksgiving" Wed 25 Nov 5:00 to 9:00 pm (overlap) [s_push, g_drive]
- Pull day 2026-11-27 Fri 27 Nov 6:00 to 6:45 pm ↔ "Thanksgiving at home" Thu 26 to Sat 28 Nov, all day (overlap) [s_pull, g_thanksgiving]
away: Wed 25 Nov 5:00 pm to Sun 29 Nov 1:00 pm: away from the gym (lifts need Gym; runs can go) [g_drive, g_back, g_thanksgiving]
free:
- Mon 23 Nov: 6:00 to 11:20 am · 1:20 to 2:30 pm · 4:30 to 5:30 pm · 7:15 to 9:00 pm
- Tue 24 Nov: 6:00 to 7:00 am · 10:40 am to 9:00 pm
- Wed 25 Nov (away from 5:00 pm): 6:00 to 11:20 am · 1:20 to 2:30 pm
- Thu 26 Nov (away): 6:00 am to 9:00 pm
- Fri 27 Nov (away): 6:00 am to 7:30 pm
- Sat 28 Nov (away): 6:00 am to 9:00 pm
- Sun 29 Nov (away until 1:00 pm): 6:00 to 11:30 am · 1:30 to 9:00 pm
running:
- race "Winter 10K" Sat 12 Dec, 19 days after the window starts (within 6 weeks) [race_10k]
- last 3 long runs 4, 4.5, 5 mi (Sat 31 Oct, Sat 7 Nov, Sat 14 Nov) [run_1, run_3, run_6]
- this week 3 + 4 = 7 mi [run_7, run_8]
- easy run distance 3 mi (the shortest run in the last 2 weeks) [run_4, run_7]
- long run distance 5.5 mi (last long run 5 mi + 0.5) [run_6]
- planned runs in the window: none
calories: target 2,200; logged per day Mon 1,650 · Tue 1,770 · Wed 1,680 · Thu 1,970 · Fri so far 1,140; protein 80 · 90 · 79 · 88 g; Mon to Thu 1,650 to 1,970 a day [m_1, m_2, m_3, m_4, m_5, m_6, m_7, m_8, m_9, m_10, m_11, m_12, m_13, m_14, m_15]
foods: saved Oatmeal and banana, Chicken and rice, Greek yogurt; breakfasts this week: "Oatmeal and banana" on 3 of 5 mornings [m_1, m_7, m_13, fd_oatmeal, fd_chicken_rice, fd_greek_yogurt]
shop: ingredients of saved foods logged this week that are on no list and in no trip in 60 days: Oats (from "Oatmeal and banana"); default list Weekly shop = l_weekly [m_1, m_7, m_13, fd_oatmeal]
cycle: starts Tue 1 Sep, Tue 29 Sep, Tue 27 Oct (28 days each); expected next Mon 23 to Wed 25 Nov; energy 2 logged on days 1 and 2 of all 3 [cy_sep, cy_sep29, cy_oct, cd_0901, cd_0929, cd_1027, cd_0902, cd_0930, cd_1028]
recovery: Meditation this week: 3 sessions, 25 min (Mon 10:30 pm, Wed 7:40 am, Thu 10:45 pm) [med_1, med_2, med_3]
</brief>'''


def loaded(state: str = 'full', gcal: bool = True, mutate=None) -> Loaded:
    apps, recs = real_workspace(state, gcal)
    apps = copy.deepcopy(apps)
    for a in apps:
        a['id'] = a['key']
    if mutate:
        mutate(apps, recs)
    return Loaded(workspace_id=uuid.uuid4(), tz=TZ, epoch=0, settings={}, now=clock_now(TZ, DEMO_NOW),
                  apps=apps, records=recs)


@pytest.fixture(scope='module')
def ld() -> Loaded:
    return loaded()


@pytest.fixture(scope='module')
def brief(ld):
    return build_brief(ld, MON, SUN, rung=4)


def op(op_kind, app, coll, rid=None, occ=None, reason_source=None, also_source=None, **fields):
    return {'op': op_kind, 'app': app, 'collection': coll, 'record_id': rid, 'occurrence': occ,
            'fields': [{'key': k, 'value': str(v)} for k, v in fields.items()],
            'reason': 'r', 'reason_source': reason_source, 'also_source': also_source, 'keep': op_kind == 'keep'}


def canonical_plan():
    """clair-agent.md §12.9 step 3, rung 4, with the seed's ids."""
    return [
        op('keep', 'workout', 'sessions', 's_pull', '2026-11-23', reason_source='c03'),
        op('move_occurrence', 'workout', 'sessions', 's_legs', '2026-11-24', reason_source='g_dentist',
           also_source='cd_1027', at='2026-11-24T17:00'),
        op('move_occurrence', 'workout', 'sessions', 's_push', '2026-11-25', reason_source='g_drive',
           at='2026-11-25T07:00'),
        op('insert', 'running', 'runs', reason_source='g_thanksgiving', name='Easy run', kind='easy', distance=3,
           at='2026-11-26T08:00', done='false'),
        op('insert', 'running', 'runs', reason_source='race_10k', name='Long run', kind='long', distance=5.5,
           at='2026-11-28T09:00', done='false'),
        op('move_occurrence', 'workout', 'sessions', 's_pull', '2026-11-27', reason_source='g_back',
           at='2026-11-29T16:00'),
        op('insert', 'todos', 'todos', reason_source='med_3', title='10 min body scan', due='2026-11-24T21:30'),
        op('insert', 'groceries', 'items', reason_source='m_1', name='Oats', list='l_weekly', status='to_buy'),
    ]


# ---------------------------------------------------------------- window

def test_planning_window():
    now = clock_now(TZ, DEMO_NOW)
    assert planning_window('Plan my training for next week', now) == (MON, SUN)
    assert planning_window('fit in my runs this week', now) == (date(2026, 11, 20), date(2026, 11, 22))
    assert planning_window('plan workouts tomorrow', now) == (date(2026, 11, 21), date(2026, 11, 21))
    assert planning_window('plan my training', now) is None
    sunday = clock_now(TZ, '2026-11-22T19:00:00-07:00')
    assert planning_window('Plan my training for next week', sunday) == (MON, SUN)


# ---------------------------------------------------------------- the fixture (check.py 3a)

def test_brief_equals_fixture_line_for_line(brief):
    assert brief.text().splitlines() == FIXTURE.splitlines()


def test_brief_facts(brief):
    assert len(brief.data['clashes']) == 3
    assert {c['booked'] for c in brief.data['clashes']} == {'g_dentist', 'g_drive', 'g_thanksgiving'}
    assert [v for k, v in sorted(brief.data['calories']['per_day'].items())][:4] == [1650, 1770, 1680, 1970]
    assert brief.data['shop']['items'] == ['Oats']
    assert brief.data['cycle']['expected'] == (date(2026, 11, 23), date(2026, 11, 25))
    assert brief.data['running']['long_runs'] == ['run_1', 'run_3', 'run_6']
    assert brief.data['running']['distances'] == {3, 5.5}
    assert brief.understanding() == ('Read 9 apps: Calendar, Classes, To-dos, Workout, Running, Calories, Cycle, '
                                     'Meditation and Groceries.')
    assert brief.seen >= {'c03', 'g_dentist', 'g_drive', 'g_thanksgiving', 'g_back', 'race_10k', 'med_3', 'm_1',
                          'cd_1027'}


def test_no_advice_words(brief):
    t = brief.text().lower()
    for w in ('should', 'healthy', 'too few', 'too many', 'recommend', 'eat more', 'eat less'):
        assert w not in t


# ---------------------------------------------------------------- privacy and read level

def _cycle_off(apps, recs):
    next(a for a in apps if a['key'] == 'cycle')['settings']['clair_read'] = False


def test_cycle_switch_off_leaves_cycle_out():
    ld = loaded(mutate=_cycle_off)
    b = build_brief(ld, MON, SUN, rung=4)
    assert 'cycle' not in b.parts
    assert 'cycle:' not in b.text()
    cycle_ids = {r['id'] for r in ld.records if r['collection'].startswith('cycle/')}
    assert not (b.seen & cycle_ids)
    assert 'Cycle' not in b.understanding()
    snap, seen = snapshot.build(ld, 'full', typed='Plan my training for next week', spoken=False, brief=b)
    assert not (seen & cycle_ids)
    assert 'cy_' not in snap and 'cd_' not in snap and 'energy 2' not in snap


def test_cycle_switch_on_is_read_though_private(ld):
    assert next(a for a in ld.apps if a['key'] == 'cycle').get('private')
    snap, seen = snapshot.build(ld, 'full', typed='x', spoken=False)
    assert 'private: not read' not in snap.split('cycle "Cycle"')[1].splitlines()[0]


def test_field_names_level_has_no_brief(ld):
    b = build_brief(ld, MON, SUN, rung=4, read_level='field_names')
    assert b.parts == {} and b.text() == '' and b.seen == set()


def test_without_google_no_clashes():
    b = build_brief(loaded(gcal=False), MON, SUN, rung=4)
    assert b.data['clashes'] == []
    assert b.text().count('clashes: none') == 1
    assert 'calendar' not in b.apps


def test_before_state_has_no_later_parts():
    b = build_brief(loaded(state='before'), MON, SUN, rung=4)
    assert set(b.parts) == {'booked', 'sessions', 'clashes', 'free', 'away'}


# ---------------------------------------------------------------- rungs

@pytest.mark.parametrize('rung', [1, 2, 3, 4])
def test_rungs(ld, rung):
    b = build_brief(ld, MON, SUN, rung=rung)
    assert set(b.parts) == RUNG_PARTS[rung] - {'other'}   # the demo has no app beyond the starters
    want = {1: {'workout'}, 2: {'workout', 'running'}, 3: {'workout', 'running'},
            4: {'workout', 'running', 'todos', 'groceries'}}[rung]
    assert b.writable_apps() == want
    if rung < 3:
        assert not any(i.startswith(('cd_', 'cy_', 'm_')) for i in b.seen)


def test_rung_from_env(ld, monkeypatch):
    monkeypatch.setenv('PLANNER_RUNG', '2')
    assert build_brief(ld, MON, SUN).rung == 2


# ---------------------------------------------------------------- check_plan

def test_canonical_plan_passes(ld, brief):
    assert check_plan(canonical_plan(), brief, ld) == []


def test_canonical_rung1_plan_passes(ld):
    b = build_brief(ld, MON, SUN, rung=1)
    plan = canonical_plan()[:3] + canonical_plan()[5:6]
    plan[1]['also_source'] = None                     # rung 1 has no cycle part, so no "also" line
    assert check_plan(plan, b, ld) == []
    plan[1]['also_source'] = 'cd_1027'
    assert check_plan(plan, b, ld) == ['op 1: also_source cd_1027 is not a record in the brief']


def test_rejects_lift_on_thanksgiving(ld, brief):
    plan = canonical_plan()
    plan[5] = op('move_occurrence', 'workout', 'sessions', 's_pull', '2026-11-27', reason_source='g_back',
                 at='2026-11-27T07:00')
    probs = check_plan(plan, brief, ld)
    assert len(probs) == 1 and 'away' in probs[0]


def test_rejects_keeping_a_clash(ld, brief):
    plan = canonical_plan()
    plan[5] = op('keep', 'workout', 'sessions', 's_pull', '2026-11-27', reason_source='g_back')
    probs = check_plan(plan, brief, ld)
    assert any('clashes' in p for p in probs) and any('away' in p for p in probs)


def test_rejects_time_inside_dentist(ld, brief):
    plan = canonical_plan()
    plan[1] = op('move_occurrence', 'workout', 'sessions', 's_legs', '2026-11-24', reason_source='g_dentist',
                 at='2026-11-24T08:00')
    probs = check_plan(plan, brief, ld)
    assert len(probs) == 1 and 'Dentist' in probs[0] and '30 min' in probs[0]


def test_rejects_wrong_run_distance(ld, brief):
    plan = canonical_plan()
    plan[4] = op('insert', 'running', 'runs', reason_source='race_10k', name='Long run', kind='long', distance=6,
                 at='2026-11-28T09:00')
    probs = check_plan(plan, brief, ld)
    assert len(probs) == 1 and '3 mi or 5.5 mi' in probs[0]


def test_rejects_reason_source_not_seen(ld, brief):
    plan = canonical_plan()
    plan[0]['reason_source'] = 'sp_01'
    plan[1]['also_source'] = 'made_up'
    probs = check_plan(plan, brief, ld)
    assert len(probs) == 2 and all('not a record in the brief' in p for p in probs)


def test_rejects_op_on_google_record(ld, brief):
    plan = canonical_plan() + [op('update', 'calendar', 'events', 'g_dentist', reason_source='g_dentist',
                                  at='2026-11-24T10:00')]
    probs = check_plan(plan, brief, ld)
    assert len(probs) == 1 and 'Google Calendar' in probs[0]


def test_rejects_insert_without_a_part(ld):
    b = build_brief(ld, MON, SUN, rung=1)
    probs = check_plan(canonical_plan(), b, ld)
    assert sorted(p for p in probs if 'no part' in p) == [
        'op 3: the brief has no part that plans running; leave it out',
        'op 4: the brief has no part that plans running; leave it out',
        'op 6: the brief has no part that plans todos; leave it out',
        'op 7: the brief has no part that plans groceries; leave it out']


def test_rejects_unknown_occurrence(ld, brief):
    plan = canonical_plan()
    plan[2]['occurrence'] = '2026-11-26'
    assert any('no session' in p for p in check_plan(plan, brief, ld))


# ---------------------------------------------------------------- snapshot

def test_snapshot_carries_brief(ld, brief):
    snap, seen = snapshot.build(ld, 'full', typed='Plan my training for next week', spoken=False, brief=brief)
    assert FIXTURE in snap and snap.endswith('</brief>\n</snapshot>')
    assert brief.seen <= seen
    snap2, seen2 = snapshot.build(ld, 'full', typed='Plan my training for next week', spoken=False,
                                  brief=brief.text())
    assert snap2 == snap and seen2 == seen
    plain, plain_seen = snapshot.build(ld, 'full', typed='hi', spoken=False)
    assert '<brief' not in plain and 'g_dentist' not in plain_seen


# ---------------------------------------------------------------- generic apps (any app beyond the starters)

def _with_reminders(apps, recs):
    """A Clair-built app the planner knows nothing about: Reminders, on Calendar."""
    apps.append({'v': 1, 'id': 'reminders', 'key': 'reminders', 'name': 'Reminders', 'icon': 'bell', 'dye': 'sage',
                 'collections': [{'key': 'reminders', 'name': 'Reminders', 'titleField': 'title', 'dateField': 'at',
                                  'calendar': True, 'label': 'Reminder',
                                  'fields': [{'key': 'title', 'type': 'text'}, {'key': 'at', 'type': 'datetime'},
                                             {'key': 'done', 'type': 'bool'}]}],
                 'tabs': [], 'face': {'value': {'agg': 'count', 'from': 'reminders/reminders'}, 'label': 'reminders'}})
    recs.append({'id': 'rem-1', 'collection': 'reminders/reminders', 'position': 'z1',
                 'properties': {'title': 'Pick up the bike', 'at': '2026-11-23T17:30:00-07:00', 'done': False}})


def test_demo_brief_unchanged_by_generic_part(ld):
    assert 'other' not in build_brief(ld, date(2026, 11, 23), date(2026, 11, 29)).parts


def test_any_new_app_joins_the_plan_generically():
    g = loaded(mutate=_with_reminders)
    b = build_brief(g, date(2026, 11, 23), date(2026, 11, 29), rung=1)
    text = b.text()
    assert 'Reminders "Reminder · Pick up the bike" Mon 23 Nov 5:30 pm [rem-1]' in text   # booked time
    assert 'Reminders: 1 reminders' in text         # its face is stated
    assert 'rem-1' in b.seen and 'reminders' in b.writable_apps()
    assert 'Reminders' in b.understanding()
    # a plan may write to it, and must keep clear of its booked time (Mon 5:30 pm)
    ok = [{'op': 'insert', 'app': 'reminders', 'collection': 'reminders',
           'fields': [{'key': 'title', 'value': 'Charge the lights'}, {'key': 'at', 'value': '2026-11-24T13:00:00-07:00'}],
           'reason_source': 'rem-1'}]
    assert check_plan(ok, b, g) == []
    # the same generic checks apply: inside the Google dentist slot is refused
    bad = [dict(ok[0], fields=[{'key': 'title', 'value': 'Charge the lights'}, {'key': 'at', 'value': '2026-11-24T08:00:00-07:00'}])]
    assert any('Dentist' in p for p in check_plan(bad, b, g))
