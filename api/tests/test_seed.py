"""The seed alone, no database: templates are well formed and the rows give the values spec/backend.md §2.2/§2.3 state."""
import json
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `api` imports

from api.seed import data
from api.seed.load import TEMPLATES, build_blocks, demo_spec, int_key

WS = uuid.UUID('00000000-0000-4000-8000-000000000001')
NOW = datetime.fromisoformat(data.DEMO_NOW)
TODAY = NOW.date()
WEEK = (date(2026, 11, 16), date(2026, 11, 22))
R = data.records()


def rows(app, coll):
    return [p for _, p in R[app][coll]]


def day(v: str) -> date:
    return datetime.fromisoformat(v).date() if 'T' in v else date.fromisoformat(v)


def in_week(v):
    return WEEK[0] <= day(v) <= WEEK[1]


# ---------------------------------------------------------------- templates

@pytest.mark.parametrize('key', data.APPS)
def test_template_shape(key):
    spec = json.loads((TEMPLATES / f'{key}.json').read_text())
    for k in ('v', 'key', 'name', 'icon', 'dye', 'collections', 'tabs', 'face', 'stitches', 'settings'):
        assert k in spec, k
    assert spec['key'] == key and 'id' not in spec and 'workflows' not in spec
    refs = {f"{key}/{c['key']}" for c in spec['collections']}
    for c in spec['collections']:
        keys = [f['key'] for f in c['fields']]
        assert c['titleField'] in keys
        for opt in ('dateField', 'amountField'):
            if opt in c:
                assert c[opt] in keys
        if c.get('calendar'):
            assert 'dateField' in c
        for f in c['fields']:
            if f['type'] == 'select':
                assert all(isinstance(o, dict) and {'id', 'label'} <= set(o) for o in f['options'])
    ids = [b['id'] for t in spec['tabs'] for b in [t, *t['children']]]
    assert len(ids) == len(set(ids)), 'block ids unique'
    assert all(t['kind'] == 'page' for t in spec['tabs'])
    assert spec['face']['label']
    assert refs


def test_template_files_are_exactly_the_twelve():
    assert sorted(p.stem for p in Path(TEMPLATES).glob('*.json')) == sorted(data.APPS)


def test_dyes_match_frontend():
    dyes = {k: json.loads((TEMPLATES / f'{k}.json').read_text())['dye'] for k in data.APPS}
    # the frontend's recorded /apps is the source of each demo app's dye (ADR-013 amendment, design/DESIGN.md §2)
    fx = json.loads((TEMPLATES.parent.parent / 'web/src/mocks/fixtures/apps.json').read_text())
    assert dyes == {p['key']: p['dye'] for p in fx if p['key'] in dyes}


def test_template_defaults_vs_demo():
    assert demo_spec('budget')['settings'] == {'limit': 120000}
    assert json.loads((TEMPLATES / 'budget.json').read_text())['settings'] == {}
    assert json.loads((TEMPLATES / 'cycle.json').read_text())['settings'] == {'clair_read': False}
    assert demo_spec('cycle')['settings']['clair_read'] is True
    assert demo_spec('calories')['settings'] == {'target': 2200}
    lists = next(f for c in demo_spec('groceries')['collections'] if c['key'] == 'items'
                 for f in c['fields'] if f['key'] == 'list')['options']
    assert [o['label'] for o in lists] == ['Weekly shop', 'Taco night', 'Costco run']


def test_budget_stitches():
    st = demo_spec('budget')['stitches']
    assert {(s['from'], s.get('on')) for s in st} == {('groceries/trips', None),
                                                       ('subscriptions/subscriptions', 'occurrence')}


# ---------------------------------------------------------------- values the screens show

def test_budget_412_left():
    spend = rows('budget', 'spend')
    nov = [s for s in spend if s['at'].startswith('2026-11')]
    assert len(nov) == 32
    total = sum(s['amount'] for s in nov)
    assert total == 78800
    assert 120000 - total == 41200
    by = {}
    for s in nov:
        by[s['category']] = by.get(s['category'], 0) + s['amount']
    assert by == {'c_rent': 38000, 'c_eating_out': 16500, 'c_groceries': 14200, 'c_transport': 4200,
                  'c_fun': 3253, 'c_subscriptions': 2647}
    blue = [s for s in nov if s['note'] == 'Blue Copper']
    assert len(blue) == 4
    week_eat = [s for s in nov if s['category'] == 'c_eating_out' and date(2026, 11, 16) <= day(s['at']) <= date(2026, 11, 19)]
    assert len(week_eat) == 5 and sum(s['amount'] for s in week_eat) == 3537


def test_groceries_twelve_to_buy_and_142():
    items = rows('groceries', 'items')
    open_ = [i for i in items if i['status'] == 'to_buy']
    assert len([i for i in open_ if i['list'] == 'l_weekly']) == 12
    assert len([i for i in open_ if i['list'] == 'l_taco']) == 5
    assert len([i for i in open_ if i['list'] == 'l_costco']) == 5
    nov_trips = [t for t in rows('groceries', 'trips') if t['at'].startswith('2026-11')]
    assert len(nov_trips) == 8 and sum(t['total'] for t in nov_trips) == 14200
    # October history lies inside Fri 9 to Sat 31 Oct, and each trip total is its items
    for key, p in R['groceries']['trips']:
        if p['at'] < '2026-11':
            assert '2026-10-09' <= p['at'][:10] <= '2026-10-31'
    # fridge-beat usuals: last bought dates
    last = {}
    for i in items:
        if i['status'] == 'bought':
            last[i['name']] = max(last.get(i['name'], ''), i['bought_on'])
    assert (TODAY - date.fromisoformat(last['Butter'])).days == 15
    assert (TODAY - date.fromisoformat(last['Cheddar'])).days == 9
    assert (TODAY - date.fromisoformat(last['Orange juice'])).days == 6
    assert (TODAY - date.fromisoformat(last['Hummus'])).days == 5
    assert 'Oats' not in {i['name'] for i in items}


def test_october_trip_rule():
    for _, day_, store, total, items in data.october_trips():
        assert store == ("Smith's" if len(items) >= 3 else 'Corner Market')
        assert data.cents(total) == sum(data.cents(p) for _, p in items)
    oct_spends = [s for s in rows('budget', 'spend') if s['at'] < '2026-11' and s['category'] == 'c_groceries']
    assert len(oct_spends) == len(data.october_trips())


def test_subscriptions_3846():
    subs = rows('subscriptions', 'subscriptions')
    assert len(subs) == 4 and sum(s['amount'] for s in subs) == 3846
    assert min(subs, key=lambda s: s['renews'])['name'] == 'Spotify'


def test_calories_1140_today():
    meals = rows('calories', 'meals')
    assert len(meals) == 15
    today = [m for m in meals if day(m['at']) == TODAY]
    assert sum(m['calories'] for m in today) == 1140 and sum(m['protein'] for m in today) == 70
    per_day = {}
    for m in meals:
        per_day[day(m['at'])] = per_day.get(day(m['at']), 0) + m['calories']
    assert [per_day[date(2026, 11, d)] for d in (16, 17, 18, 19)] == [1650, 1770, 1680, 1970]
    assert len(rows('calories', 'foods')) == 3


def test_meditation_25_min():
    s = rows('meditation', 'sessions')
    assert len(s) == 3 and sum(x['minutes'] for x in s if in_week(x['at'])) == 25


def test_running_7_mi():
    runs = rows('running', 'runs')
    assert len(runs) == 8 and all(r['done'] for r in runs)
    assert sum(r['distance'] for r in runs if in_week(r['at'])) == 7
    assert [r['distance'] for r in runs if r['kind'] == 'long'] == [4, 4.5, 5]
    assert rows('running', 'races')[0]['name'] == 'Winter 10K'


def test_cycle():
    assert max(c['start'] for c in rows('cycle', 'cycles')) == '2026-10-27'
    days = rows('cycle', 'days')
    assert len(days) == 9 and sum(1 for d in days if d['energy'] == 2) == 6


def test_todos_two_today():
    t = rows('todos', 'todos')
    assert len(t) == 6 and sum(1 for x in t if not x['done']) == 4
    assert sum(1 for x in t if not x['done'] and x.get('due') and day(x['due']) == TODAY) == 2


def test_classes_two_due_this_week():
    due = rows('classes', 'due')
    soon = [d for d in due if not d['done'] and 0 <= (day(d['at']) - TODAY).days < 7]
    assert len(soon) == 2
    econ = rows('classes', 'classes')[0]
    assert econ['repeat']['skip'] == ['2026-11-26']
    assert all('FR' not in c['repeat']['rule'].split('BYDAY=')[1] for c in rows('classes', 'classes'))


def test_notes_three_this_week():
    n = rows('notes', 'notes')
    assert len(n) == 5 and sum(1 for x in n if in_week(x['at'])) == 3
    assert len(rows('notes', 'notebooks')) == 4


def test_workout():
    ses = rows('workout', 'sessions')
    logs = [d for s in ses for d in s['repeat']['log']]
    skips = [d for s in ses for d in s['repeat']['skip']]
    assert len(logs) + len(skips) == 46 and len(logs) == 41 and len(skips) == 5
    assert sum(1 for d in logs if in_week(d)) == 3
    sets = rows('workout', 'sets')
    week_sets = [s for s in sets if in_week(s['at'])]
    assert sum(s['weight'] * s['reps'] for s in week_sets) == 12450
    lat = [s for s in sets if s['exercise'][0].key == 'ex_lat_pulldown']
    assert min(s['weight'] for s in lat) == 100 and max(s['weight'] for s in lat) == 120
    assert len(rows('workout', 'routines')) == 3 and len(rows('workout', 'exercises')) == 9


def test_calendar_events():
    ev = rows('calendar', 'events')
    assert [e['title'] for e in ev] == ['Haircut', 'Haircut', 'Haircut', 'Coffee with Maya']
    with_g = [p for _, p in data.calendar(gcal_fixture=True)['events']]
    assert sum(1 for e in with_g if e.get('source') == 'google') == 4


def test_ledger_32_left():
    assert sum(c for _, c, _ in data.LEDGER) == 32


# ---------------------------------------------------------------- blocks

def test_blocks_full_and_before():
    full = build_blocks(WS, 'full')
    before = build_blocks(WS, 'before')
    pages = lambda bs: [b['properties']['key'] for b in bs if b['block_type'] == 'page']
    assert pages(full) == data.APPS and len(pages(before)) == 8
    assert set(pages(before)) == set(data.APPS) - {'calories', 'running', 'cycle', 'meditation'}
    assert len({b['id'] for b in full}) == len(full)
    assert build_blocks(WS, 'full')[5]['id'] == full[5]['id'], 'ids stable across reseeds'
    for b in full:
        assert all(not isinstance(v, data.Ref) for v in b['properties'].values())
        if b['block_type'] == 'page':
            assert 'collections' not in b['properties']


def test_positions_sort_by_byte():
    keys = [int_key(i) for i in range(5000)]
    assert keys == sorted(keys, key=lambda s: s.encode()) and len(set(keys)) == 5000
