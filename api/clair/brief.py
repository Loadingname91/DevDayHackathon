"""The planning brief (clair-agent.md §12.9): every fact the training planner needs, built in Python.

The model arranges and words; it does not compute. Every line of the brief carries the ids of the
records it rests on, in square brackets, and those ids join the run's seen set. A part is left out
when its app doesn't exist, has no rows, or isn't readable (Cycle with `settings.clair_read` false,
an app marked private, or a read level below full). The rung (`PLANNER_RUNG`, 1 to 4) leaves the
later parts out, so a lower rung never sees data it shouldn't act on.

Public API:
    planning_window(text, now) -> (date, date) | None      # "next week" | "this week" | "tomorrow"
    build_brief(ld, window_start, window_end, *, rung=None, read_level='full') -> Brief
    check_plan(ops, brief, ld) -> list[str]                 # §12.9 step 4; [] when the plan is fine
    planner_rung() -> int                                   # PLANNER_RUNG, default 4

Decisions the spec leaves open (resolved here, see the report in the hand-off):
- booked = every *dated row in the window except Workout's own sessions (those are `sessions`).
- A timed row without `ends` lasts 60 min in calendar/events and classes/classes, 0 min elsewhere
  (deadlines, to-dos, renewals). An all-day row covers its whole days.
- A clash is a session and a booked row that overlap or sit less than 30 min apart, all-day rows
  included (Fri Pull day vs Thanksgiving at home).
- away = every all-day row, plus each trip out (drive, flight, train, bus) joined to the next trip
  back ("back to", "return") within 14 days; spans less than a day apart merge. The time check of
  new times ignores all-day rows (a run can go on Thanksgiving); the away check keeps lifts out.
- free = 6:00 am to 9:00 pm each day, minus every timed booked row and every kept session, each
  widened by 30 min, keeping blocks of 45 min or more. Days inside an away span are marked.
- running gives the two distances the prompt's rule needs (shortest run in the last 14 days; last
  long run + 0.5 mi), so the model never does the arithmetic; check_plan holds inserted runs to them.
- shop: ingredients of the saved foods Sam logged this week (a small fixed word list, INGREDIENTS),
  that are on no list and in no trip in the last 60 days. Unknown words are never suggested.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from ..logic import fmt
from ..logic.clock import instant, localize, parse_value, to_local, week_start
from ..logic.dated import dated_rows, index_apps

BUFFER = timedelta(minutes=30)
FREE_FROM, FREE_TO = time(6, 0), time(21, 0)
FREE_MIN = timedelta(minutes=45)
DEFAULT_MINUTES = {'calendar/events': 60, 'classes/classes': 60}
SESSION_DEFAULT_MIN = 60
RUN_DEFAULT_MIN = 60
RACE_WEEKS = 6
LONG_STEP = 0.5
SHOP_DAYS = 60
LOW_ENERGY = 2

APP_ORDER = ['calendar', 'classes', 'todos', 'workout', 'running', 'calories', 'cycle', 'meditation', 'groceries']
PART_ORDER = ['booked', 'sessions', 'clashes', 'away', 'free', 'running', 'calories', 'foods', 'shop',
              'cycle', 'recovery', 'other']
# The starter apps whose parts are written out above. Any other readable app (one Clair or Sam
# built) joins a plan generically: its calendar rows are already in booked/clashes/free, and the
# `other` part states its face and cites its latest records, and the plan may write to it.
STARTER_KEYS = {'notes', 'budget', 'subscriptions', 'groceries', 'classes', 'workout', 'todos', 'calories',
                'running', 'meditation', 'cycle', 'calendar'}
OTHER_CITES = 3
RUNG_PARTS = {
    1: {'booked', 'sessions', 'clashes', 'free', 'other'},
    2: {'booked', 'sessions', 'clashes', 'free', 'running', 'away', 'other'},
    3: {'booked', 'sessions', 'clashes', 'free', 'running', 'away', 'cycle', 'calories', 'other'},
    4: set(PART_ORDER),
}
# Which app a part lets the plan write to (§12.9 rung table: targets).
PART_WRITES = {'sessions': 'workout', 'running': 'running', 'recovery': 'todos', 'shop': 'groceries'}

# Saved-food words -> the grocery item they need. Only these are ever suggested.
INGREDIENTS = {
    'oatmeal': 'Oats', 'oats': 'Oats', 'banana': 'Bananas', 'bananas': 'Bananas',
    'chicken': 'Chicken thighs', 'rice': 'Rice', 'greek yogurt': 'Greek yogurt', 'yogurt': 'Greek yogurt',
    'granola': 'Granola', 'eggs': 'Eggs', 'egg': 'Eggs', 'spinach': 'Spinach', 'tortillas': 'Tortillas',
    'pasta': 'Pasta', 'toast': 'Bread', 'peanut butter': 'Peanut butter', 'milk': 'Milk',
}

_TRIP_OUT = re.compile(r'\b(drive|driving|flight|fly|flying|train|bus)\b', re.I)
_TRIP_BACK = re.compile(r'\b(back to|return|returning)\b', re.I)


# ---------------------------------------------------------------- window and rung

def planner_rung() -> int:
    try:
        r = int(os.environ.get('PLANNER_RUNG', '4'))
    except ValueError:
        r = 4
    return min(4, max(1, r))


def planning_window(text: str, now: datetime) -> tuple[date, date] | None:
    """The days a planning run covers, in the workspace zone of `now`. None when the text names none."""
    today = now.date()
    t = (text or '').lower()
    if re.search(r'\bnext week\b', t):
        start = week_start(today) + timedelta(days=7)
        return start, start + timedelta(days=6)
    if re.search(r'\bthis week\b', t):
        return today, week_start(today) + timedelta(days=6)
    if re.search(r'\btomorrow\b', t):
        d = today + timedelta(days=1)
        return d, d
    return None


# ---------------------------------------------------------------- formatting

def _day(d: date) -> str:
    return fmt.day_label(d)


def _hm(dt: datetime) -> str:
    return fmt.time_label(dt)


def _span(a: datetime, b: datetime | None) -> str:
    """'Tue 24 Nov 7:30 to 8:30 am' · 'Wed 25 Nov 5:00 to 9:00 pm' · 'Mon 23 Nov 6:00 pm'."""
    if b is None or b == a:
        return f'{_day(a.date())} {_hm(a)}'
    if a.date() == b.date():
        if (a.hour < 12) == (b.hour < 12):
            return f"{_day(a.date())} {_hm(a).rsplit(' ', 1)[0]} to {_hm(b)}"
        return f'{_day(a.date())} {_hm(a)} to {_hm(b)}'
    return f'{_day(a.date())} {_hm(a)} to {_day(b.date())} {_hm(b)}'


def _days(a: date, b: date) -> str:
    if a == b:
        return f'{_day(a)}, all day'
    if a.month == b.month:
        return f"{a.strftime('%a')} {a.day} to {_day(b)}, all day"
    return f'{_day(a)} to {_day(b)}, all day'


def _range(a: date, b: date) -> str:
    """'Mon 23 to Wed 25 Nov'."""
    if a.month == b.month and a.year == b.year:
        return f"{a.strftime('%a')} {a.day} to {_day(b)}"
    return f'{_day(a)} to {_day(b)}'


def _n(x) -> str:
    return fmt.number(x)


def _ids(ids) -> str:
    ids = [i for i in ids if i]
    return f" [{', '.join(ids)}]" if ids else ''


def _and(names: list[str]) -> str:
    if len(names) <= 1:
        return ''.join(names)
    return ', '.join(names[:-1]) + ' and ' + names[-1]


def _norm(s: str) -> str:
    s = (s or '').strip().lower()
    return s[:-1] if s.endswith('s') else s


# ---------------------------------------------------------------- the brief

@dataclass
class Line:
    text: str
    ids: list[str] = field(default_factory=list)

    def render(self) -> str:
        return self.text + _ids(self.ids)


@dataclass
class Brief:
    start: date
    end: date
    rung: int
    read_level: str
    parts: dict[str, list[Line]] = field(default_factory=dict)   # part -> lines, in PART_ORDER
    data: dict[str, Any] = field(default_factory=dict)          # part -> structured facts
    apps: list[str] = field(default_factory=list)               # app keys with a part, in reading order
    app_names: dict[str, str] = field(default_factory=dict)
    # Facts check_plan needs whatever the rung (never rendered unless the part is in):
    booked_spans: list[dict] = field(default_factory=list)
    away_spans: list[tuple[datetime, datetime, list[str]]] = field(default_factory=list)
    sessions_all: list[dict] = field(default_factory=list)
    tz: str = 'America/Denver'

    @property
    def window_label(self) -> str:
        return _day(self.start) if self.start == self.end else f'{_day(self.start)} to {_day(self.end)}'

    @property
    def seen(self) -> set[str]:
        return {i for lines in self.parts.values() for ln in lines for i in ln.ids}

    def has(self, part: str) -> bool:
        return part in self.parts

    def writable_apps(self) -> set[str]:
        return {app for part, app in PART_WRITES.items() if part in self.parts} | set(self.data.get('other_apps', []))

    def understanding(self) -> str:
        """The report_understanding summary: names only apps that have a part (§12.9 step 1)."""
        names = [self.app_names.get(k, k) for k in self.apps]
        return f"Read {len(names)} app{'s' if len(names) != 1 else ''}: {_and(names)}."

    def text(self) -> str:
        if not self.parts:
            return ''
        out = [f'<brief window="{self.window_label}">']
        if self.apps:
            out.append(f"apps read: {', '.join(self.app_names.get(k, k) for k in self.apps)} ({len(self.apps)})")
        for part in PART_ORDER:
            lines = self.parts.get(part)
            if lines is None:
                continue
            if len(lines) == 1 and '\n' not in lines[0].text and part not in ('booked', 'sessions', 'clashes', 'free'):
                out.append(f'{part}: {lines[0].render()}')
                continue
            if not lines:
                out.append(f'{part}: none')
                continue
            out.append(f'{part}:')
            out.extend(f'- {ln.render()}' for ln in lines)
        out.append('</brief>')
        return '\n'.join(out)


# ---------------------------------------------------------------- helpers over Loaded

def _readable(app: dict | None, read_level: str) -> bool:
    if app is None or read_level != 'full':
        return False
    return clair_can_read(app)


def clair_can_read(app: dict) -> bool:
    """`settings.clair_read` decides (clair-agent.md §12.11: "private" and the read switch are separate).
    A private app with no switch set is not read; any app with the switch off is not read."""
    st = app.get('settings') or {}
    if st.get('clair_read') is True:
        return True
    return not (app.get('private') or st.get('clair_read') is False)


def _app(ld, key: str) -> dict | None:
    for a in ld.apps:
        if a.get('key') == key:
            return a
    return None


def _rows(ld, ref: str) -> list[dict]:
    return [r for r in ld.records if r.get('collection') == ref and not r.get('deleted_at')]


def _rel_id(v) -> str | None:
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, dict):
        v = v.get('id') or v.get('key')
    return str(v) if v else None


def _local(v, tz: str):
    p = parse_value(v, tz)
    return to_local(p, tz) if isinstance(p, datetime) else p


def _interval(row: dict, tz: str) -> tuple[datetime, datetime, bool]:
    """(start, end, all_day) of a *dated row."""
    at = _local(row['at'], tz)
    if not isinstance(at, datetime):
        end_day = _local(row['ends'], tz) if row.get('ends') else at
        if isinstance(end_day, datetime):
            end_day = end_day.date()
        return localize(datetime.combine(at, time()), tz), localize(datetime.combine(end_day + timedelta(days=1), time()), tz), True
    if row.get('ends'):
        e = _local(row['ends'], tz)
        e = e if isinstance(e, datetime) else localize(datetime.combine(e + timedelta(days=1), time()), tz)
        return at, e, False
    ref = f"{row['app']}/{row.get('_coll', '')}"
    return at, at + timedelta(minutes=DEFAULT_MINUTES.get(ref, 0)), False


def _gap(a0, a1, b0, b1) -> timedelta:
    """Time between two intervals; zero or negative when they overlap."""
    return max(b0 - a1, a0 - b1)


# ---------------------------------------------------------------- build

def build_brief(ld, window_start: date, window_end: date, *, rung: int | None = None,
                read_level: str = 'full') -> Brief:
    tz = ld.tz
    rung = planner_rung() if rung is None else min(4, max(1, int(rung)))
    allowed = RUNG_PARTS[rung]
    now = to_local(ld.now, tz)
    b = Brief(start=window_start, end=window_end, rung=rung, read_level=read_level, tz=tz,
              app_names={a['key']: a.get('name', a['key']) for a in ld.apps})
    if read_level != 'full':
        return b
    readable = [a for a in ld.apps if _readable(a, read_level)]
    keys = {a['key'] for a in readable}
    idx = index_apps(readable)
    read_order: list[str] = []

    def note(app_key: str):
        if app_key not in read_order:
            read_order.append(app_key)

    # --- *dated rows in the window, split into booked and sessions
    rows = dated_rows(readable, ld.records, window_start, window_end, tz, app_keys=keys)
    by_id = {r['id']: r for r in ld.records}
    coll_of = {}
    for r in ld.records:
        coll_of[r['id']] = r.get('collection', '')
    booked, sessions = [], []
    for row in rows:
        ref = coll_of.get(row['record_id'], '')
        row = dict(row, _coll=ref.split('/', 1)[1] if '/' in ref else '')
        (sessions if ref == 'workout/sessions' else booked).append(row)

    booked_spans = []
    booked_lines = []
    for row in booked:
        s, e, all_day = _interval(row, tz)
        title = row['title']
        app_name = 'Google Calendar' if row.get('source') == 'google' else b.app_names.get(row['app'], row['app'])
        if all_day:
            when = _days(s.date(), (e - timedelta(days=1)).date())
        else:
            when = _span(s, e if e != s else None)
        extra = ' · source google' if row.get('source') else ''
        booked_lines.append(Line(f'{app_name} "{title}" {when}{extra}', [row['record_id']]))
        booked_spans.append({'id': row['record_id'], 'title': title, 'start': s, 'end': e, 'all_day': all_day,
                             'app': row['app'], 'source': row.get('source')})
        note(row['app'])
    b.booked_spans = booked_spans
    b.data['booked'] = booked_spans

    # --- sessions
    workout = _app(ld, 'workout')
    has_workout = workout is not None and 'workout' in keys
    sess = []
    if has_workout:
        routines = {r['id']: r for r in _rows(ld, 'workout/routines')}
        for row in sessions:
            rec = by_id.get(row['record_id'], {})
            props = rec.get('properties') or {}
            ro = routines.get(_rel_id(props.get('routine')) or '')
            rp = (ro or {}).get('properties') or {}
            minutes = props.get('minutes') or rp.get('minutes') or SESSION_DEFAULT_MIN
            at = _local(row['at'], tz)
            if not isinstance(at, datetime):
                continue
            sess.append({'record_id': row['record_id'], 'occurrence': row.get('occurrence') or at.date().isoformat(),
                         'name': props.get('name') or row['title'], 'routine': rp.get('name'),
                         'routine_id': ro['id'] if ro else None, 'minutes': int(minutes),
                         'needs': rp.get('needs'), 'start': at, 'end': at + timedelta(minutes=int(minutes))})
    b.sessions_all = sess

    # --- clashes
    clashes = []
    for s in sess:
        for bk in booked_spans:
            if _gap(s['start'], s['end'], bk['start'], bk['end']) < BUFFER:
                clashes.append((s, bk))
    clash_keys = {(s['record_id'], s['occurrence']) for s, _ in clashes}

    # --- away
    away = _away(booked_spans)
    b.away_spans = away

    # --- free
    free = _free(window_start, window_end, tz, booked_spans,
                 [s for s in sess if (s['record_id'], s['occurrence']) not in clash_keys], away)

    if 'booked' in allowed:
        b.parts['booked'] = booked_lines
    if has_workout and 'sessions' in allowed:
        lines = []
        for s in sess:
            needs = f" · needs {s['needs']}" if s['needs'] else ''
            ro = f" · routine {s['routine']}" if s['routine'] else ''
            lines.append(Line(f"{s['record_id']} occurrence {s['occurrence']} \"{s['name']}\" "
                              f"{_span(s['start'], s['end'])}{ro} · {s['minutes']} min{needs}",
                              [s['record_id']] + ([s['routine_id']] if s['routine_id'] else [])))
        b.parts['sessions'] = lines
        b.data['sessions'] = sess
        note('workout')
    if 'clashes' in allowed and has_workout:
        lines = []
        for s, bk in clashes:
            other = _days(bk['start'].date(), (bk['end'] - timedelta(days=1)).date()) if bk['all_day'] \
                else _span(bk['start'], bk['end'])
            how = 'overlap' if _gap(s['start'], s['end'], bk['start'], bk['end']) <= timedelta(0) else 'under 30 min apart'
            lines.append(Line(f"{s['name']} {s['occurrence']} {_span(s['start'], s['end'])} ↔ "
                              f"\"{bk['title']}\" {other} ({how})", [s['record_id'], bk['id']]))
        b.parts['clashes'] = lines
        b.data['clashes'] = [{'record_id': s['record_id'], 'occurrence': s['occurrence'], 'booked': bk['id']}
                             for s, bk in clashes]
    if 'away' in allowed:
        if away:
            b.parts['away'] = [Line(f'{_span(a0, a1)}: away from the gym (lifts need Gym; runs can go)', ids)
                               for a0, a1, ids in away]
        else:
            b.parts['away'] = [Line('none')]
        b.data['away'] = [{'start': a0, 'end': a1, 'ids': ids} for a0, a1, ids in away]
    if 'free' in allowed:
        lines = []
        for d, blocks, away_label in free:
            label = f"{_day(d)}{f' ({away_label})' if away_label else ''}"
            txt = ' · '.join(_span(x, y).split(' ', 3)[3] for x, y in blocks) if blocks else 'none'
            lines.append(Line(f'{label}: {txt}'))
        b.parts['free'] = lines
        b.data['free'] = free

    # --- running
    if 'running' in allowed:
        r = _running(ld, keys, now, window_start, window_end, tz)
        if r:
            b.parts['running'] = [Line(t, ids) for t, ids in r['lines']]
            b.data['running'] = r
            note('running')

    # --- calories, foods, shop
    cal = _calories(ld, keys, now, tz) if (allowed & {'calories', 'foods', 'shop'}) else None
    if cal:
        if 'calories' in allowed:
            b.parts['calories'] = [Line(cal['text'], cal['ids'])]
            b.data['calories'] = cal
            note('calories')
        if 'foods' in allowed and cal.get('foods_text'):
            b.parts['foods'] = [Line(cal['foods_text'], cal['foods_ids'])]
            b.data['foods'] = cal['foods']
            note('calories')
        if 'shop' in allowed:
            shop = _shop(ld, keys, now, tz, cal)
            if shop is not None:
                b.parts['shop'] = [Line(shop['text'], shop['ids'])]
                b.data['shop'] = shop
                note('calories')

    # --- cycle
    if 'cycle' in allowed:
        cy = _cycle(ld, keys, tz)
        if cy:
            b.parts['cycle'] = [Line(cy['text'], cy['ids'])]
            b.data['cycle'] = cy
            note('cycle')

    # --- recovery
    if 'recovery' in allowed:
        rec = _recovery(ld, keys, now, tz)
        if rec:
            b.parts['recovery'] = [Line(rec['text'], rec['ids'])]
            b.data['recovery'] = rec
            note('meditation')

    # --- any other app (generic): its face, citing its latest records
    if 'other' in allowed:
        from ..logic import formula
        others, other_apps = [], []
        for a in readable:
            if a['key'] in STARTER_KEYS:
                continue
            try:
                f = formula.face(a, ld.ctx)
            except Exception:  # a face that can't be read still leaves the app's calendar rows in the brief
                f = None
            refs = {f"{a['key']}/{c['key']}" for c in a.get('collections', [])}
            recs = sorted((r for r in ld.records if r.get('collection') in refs),
                          key=lambda r: r.get('position') or '', reverse=True)[:OTHER_CITES]
            face_txt = f"{f['text']} {f['label']}".strip() if f and f.get('text') not in (None, '', '—') else 'no figure yet'
            others.append(Line(f"{a.get('name', a['key'])}: {face_txt}", [r['id'] for r in recs]))
            other_apps.append(a['key'])
            note(a['key'])
        if others:
            b.parts['other'] = others
            b.data['other_apps'] = other_apps

    if 'shop' in b.parts:
        note('groceries')
    b.apps = sorted(read_order, key=lambda k: APP_ORDER.index(k) if k in APP_ORDER else len(APP_ORDER))
    return b


def _away(booked: list[dict]) -> list[tuple[datetime, datetime, list[str]]]:
    spans: list[tuple[datetime, datetime, list[str]]] = []
    for bk in booked:
        if bk['all_day'] and bk['app'] == 'calendar':
            spans.append((bk['start'], bk['end'], [bk['id']]))
    trips = sorted((bk for bk in booked if not bk['all_day'] and bk['app'] == 'calendar'), key=lambda x: x['start'])
    for i, t in enumerate(trips):
        if _TRIP_BACK.search(t['title']):
            spans.append((t['start'], t['end'], [t['id']]))
            continue
        if not _TRIP_OUT.search(t['title']):
            continue
        back = next((u for u in trips[i + 1:] if _TRIP_BACK.search(u['title'])
                     and u['start'] - t['end'] <= timedelta(days=14)), None)
        if back:
            spans.append((t['start'], back['end'], [t['id'], back['id']]))
        else:
            spans.append((t['start'], t['end'], [t['id']]))
    spans.sort(key=lambda s: s[0])
    merged: list[tuple[datetime, datetime, list[str]]] = []
    for s0, s1, ids in spans:
        if merged and s0 - merged[-1][1] < timedelta(days=1):
            m0, m1, mids = merged[-1]
            merged[-1] = (m0, max(m1, s1), mids + [i for i in ids if i not in mids])
        else:
            merged.append((s0, s1, list(ids)))
    return merged


def _free(lo: date, hi: date, tz: str, booked: list[dict], kept: list[dict], away) -> list:
    busy = [(bk['start'] - BUFFER, bk['end'] + BUFFER) for bk in booked if not bk['all_day']]
    busy += [(s['start'] - BUFFER, s['end'] + BUFFER) for s in kept]
    out = []
    d = lo
    while d <= hi:
        day0 = localize(datetime.combine(d, FREE_FROM), tz)
        day1 = localize(datetime.combine(d, FREE_TO), tz)
        cuts = sorted((max(a, day0), min(z, day1)) for a, z in busy if a < day1 and z > day0)
        blocks, cur = [], day0
        for a, z in cuts:
            if a - cur >= FREE_MIN:
                blocks.append((cur, a))
            cur = max(cur, z)
        if day1 - cur >= FREE_MIN:
            blocks.append((cur, day1))
        label = None
        for a0, a1, _ in away:
            if a0 < day1 and a1 > day0:
                if a0 > day0:
                    label = f'away from {_hm(a0)}'
                elif a1 < day1:
                    label = f'away until {_hm(a1)}'
                else:
                    label = 'away'
        out.append((d, blocks, label))
        d += timedelta(days=1)
    return out


def _running(ld, keys, now, lo: date, hi: date, tz: str):
    if 'running' not in keys:
        return None
    runs = [r for r in _rows(ld, 'running/runs') if (r.get('properties') or {}).get('at')]
    races = [r for r in _rows(ld, 'running/races') if (r.get('properties') or {}).get('at')]
    if not runs and not races:
        return None
    lines = []
    w0 = localize(datetime.combine(lo, time()), tz)
    race = None
    future = sorted((r for r in races if instant(r['properties']['at'], tz) >= now),
                    key=lambda r: instant(r['properties']['at'], tz))
    if future:
        race = future[0]
        rat = _local(race['properties']['at'], tz)
        rday = rat.date() if isinstance(rat, datetime) else rat
        weeks = (rday - lo).days
        within = 'within' if weeks <= RACE_WEEKS * 7 else 'more than'
        lines.append((f"race \"{race['properties'].get('name', 'Race')}\" {_day(rday)}, {(rday - lo).days} days after "
                      f"the window starts ({within} {RACE_WEEKS} weeks)", [race['id']]))
    done = sorted((r for r in runs if r['properties'].get('done')), key=lambda r: instant(r['properties']['at'], tz))
    longs = [r for r in done if str(r['properties'].get('kind', '')).lower() == 'long']
    last3 = longs[-3:]
    if last3:
        lines.append((f"last {len(last3)} long runs {', '.join(_n(r['properties']['distance']) for r in last3)} mi "
                      f"({', '.join(_day(_local(r['properties']['at'], tz).date()) for r in last3)})",
                      [r['id'] for r in last3]))
    ws = week_start(now.date())
    this_week = [r for r in done if ws <= _local(r['properties']['at'], tz).date() <= now.date()]
    if this_week:
        ds = [r['properties'].get('distance') or 0 for r in this_week]
        lines.append((f"this week {' + '.join(_n(x) for x in ds)} = {_n(sum(ds))} mi", [r['id'] for r in this_week]))
    else:
        lines.append(('this week none', []))
    two = [r for r in done if instant(r['properties']['at'], tz) >= now - timedelta(days=14)]
    easy = long_ = None
    if two:
        easy = min(r['properties'].get('distance') or 0 for r in two)
        lines.append((f'easy run distance {_n(easy)} mi (the shortest run in the last 2 weeks)',
                      [r['id'] for r in two if (r['properties'].get('distance') or 0) == easy]))
    if longs:
        last = longs[-1]
        long_ = float(last['properties']['distance']) + LONG_STEP
        lines.append((f"long run distance {_n(long_)} mi (last long run {_n(last['properties']['distance'])} mi "
                      f"+ {_n(LONG_STEP)})", [last['id']]))
    planned = [r for r in runs if not r['properties'].get('done')
               and lo <= _local(r['properties']['at'], tz).date() <= hi]
    if planned:
        lines.append((f"planned runs in the window: "
                      f"{', '.join(_span(_local(r['properties']['at'], tz), None) for r in planned)}",
                      [r['id'] for r in planned]))
    else:
        lines.append(('planned runs in the window: none', []))
    return {'lines': lines, 'race': race['id'] if race else None, 'long_runs': [r['id'] for r in last3],
            'easy': easy, 'long': long_, 'distances': {x for x in (easy, long_) if x is not None},
            'race_within': bool(race) and lines[0][0].endswith(f'(within {RACE_WEEKS} weeks)')}


def _calories(ld, keys, now, tz: str):
    if 'calories' not in keys:
        return None
    app = _app(ld, 'calories')
    meals = [r for r in _rows(ld, 'calories/meals') if (r.get('properties') or {}).get('at')]
    if not meals:
        return None
    today = now.date()
    ws = week_start(today)
    week = sorted((r for r in meals if ws <= _local(r['properties']['at'], tz).date() <= today
                   and instant(r['properties']['at'], tz) <= now),
                  key=lambda r: instant(r['properties']['at'], tz))
    if not week:
        return None
    target = (app.get('settings') or {}).get('target')
    by_day: dict[date, list[dict]] = {}
    for r in week:
        by_day.setdefault(_local(r['properties']['at'], tz).date(), []).append(r)
    parts, protein, full = [], [], []
    for d in sorted(by_day):
        cals = sum(r['properties'].get('calories') or 0 for r in by_day[d])
        if d == today:
            parts.append(f"{d.strftime('%a')} so far {_n(cals)}")
        else:
            parts.append(f"{d.strftime('%a')} {_n(cals)}")
            protein.append(_n(sum(r['properties'].get('protein') or 0 for r in by_day[d])))
            full.append((d, cals))
    txt = f"target {_n(target) if target else 'none set'}; logged per day {' · '.join(parts)}"
    if protein:
        txt += f"; protein {' · '.join(protein)} g"
    if len(full) >= 2:
        lo_c, hi_c = min(c for _, c in full), max(c for _, c in full)
        txt += (f"; {full[0][0].strftime('%a')} to {full[-1][0].strftime('%a')} "
                f"{_n(lo_c)} to {_n(hi_c)} a day")
    out = {'text': txt, 'ids': [r['id'] for r in week], 'target': target,
           'per_day': {d.isoformat(): sum(r['properties'].get('calories') or 0 for r in by_day[d]) for d in by_day},
           'week': week}

    # foods: saved foods, and the breakfast Sam had most this week
    saved = _rows(ld, 'calories/foods')
    saved_by_name = {(r['properties'].get('name') or '').strip().lower(): r for r in saved}
    mornings: dict[date, dict] = {}
    for r in week:
        p = r['properties']
        at = _local(p['at'], tz)
        if p.get('meal') == 'breakfast' or (not p.get('meal') and at.hour < 11):
            mornings.setdefault(at.date(), r)
    counts: dict[str, list[dict]] = {}
    for r in mornings.values():
        counts.setdefault(r['properties'].get('name') or '', []).append(r)
    foods_txt, foods_ids, foods = None, [], {}
    if saved or counts:
        bits = []
        if saved:
            bits.append(f"saved {', '.join(r['properties'].get('name', '') for r in saved)}")
            foods_ids += [r['id'] for r in saved]
        top = max(counts.items(), key=lambda kv: (len(kv[1]), -min(instant(x['properties']['at'], tz) for x in kv[1]).timestamp()),
                  default=None)
        if top and len(top[1]) >= 2:
            bits.append(f"breakfasts this week: \"{top[0]}\" on {len(top[1])} of {len(mornings)} mornings")
            foods_ids = [r['id'] for r in top[1]] + foods_ids
            foods = {'breakfast': top[0], 'count': len(top[1]), 'mornings': len(mornings),
                     'ids': [r['id'] for r in top[1]]}
        foods_txt = '; '.join(bits) if bits else None
    out.update(foods_text=foods_txt, foods_ids=foods_ids, foods=foods, saved_by_name=saved_by_name)
    return out


def _ingredients(name: str) -> list[str]:
    out = []
    for part in re.split(r'\s+(?:and|with)\s+|,\s*', name.strip().lower()):
        part = part.strip()
        if not part:
            continue
        if part in INGREDIENTS:
            out.append(INGREDIENTS[part])
            continue
        for w in part.split():
            if w in INGREDIENTS:
                out.append(INGREDIENTS[w])
    return list(dict.fromkeys(out))


def _shop(ld, keys, now, tz: str, cal: dict):
    if 'groceries' not in keys:
        return None
    items = _rows(ld, 'groceries/items')
    if not items:
        return None
    saved = cal.get('saved_by_name') or {}
    eaten: dict[str, list[dict]] = {}
    for r in cal['week']:
        nm = (r['properties'].get('name') or '').strip().lower()
        if nm in saved:
            eaten.setdefault(nm, []).append(r)
    since = now.date() - timedelta(days=SHOP_DAYS)
    covered = set()
    for it in items:
        p = it.get('properties') or {}
        if p.get('status') == 'to_buy':
            covered.add(_norm(p.get('name', '')))
        elif p.get('trip') and p.get('bought_on') and date.fromisoformat(str(p['bought_on'])[:10]) >= since:
            covered.add(_norm(p.get('name', '')))
    found: dict[str, list[str]] = {}
    sources: dict[str, str] = {}
    for nm, rows in eaten.items():
        for ing in _ingredients(nm):
            if _norm(ing) in covered or ing in found:
                continue
            found[ing] = [r['id'] for r in rows] + [saved[nm]['id']]
            sources[ing] = saved[nm]['properties'].get('name', nm)
    if not found:
        return {'text': 'none (every ingredient of the saved foods logged this week is on a list or was bought '
                        f'in the last {SHOP_DAYS} days)', 'ids': [], 'items': []}
    txt = (f'ingredients of saved foods logged this week that are on no list and in no trip in {SHOP_DAYS} days: '
           + ', '.join(f'{ing} (from "{sources[ing]}")' for ing in found))
    default_list = _default_list(ld)
    if default_list:
        txt += f"; default list {default_list['label']} = {default_list['id']}"
    ids = list(dict.fromkeys(i for v in found.values() for i in v))
    return {'text': txt, 'ids': ids, 'items': list(found), 'from': sources,
            'list': default_list['id'] if default_list else None}


def _default_list(ld) -> dict | None:
    app = _app(ld, 'groceries')
    for c in (app or {}).get('collections') or []:
        if c.get('key') != 'items':
            continue
        for f in c.get('fields') or []:
            if f.get('key') == 'list':
                opts = [o for o in f.get('options') or [] if isinstance(o, dict)]
                return opts[0] if opts else None
    return None


def _cycle(ld, keys, tz: str):
    if 'cycle' not in keys:
        return None
    cycles = sorted((r for r in _rows(ld, 'cycle/cycles') if (r.get('properties') or {}).get('start')),
                    key=lambda r: str(r['properties']['start']))
    if not cycles:
        return None
    starts = [date.fromisoformat(str(r['properties']['start'])[:10]) for r in cycles]
    lengths = []
    for i, r in enumerate(cycles):
        ln = r['properties'].get('length')
        if not ln and i + 1 < len(cycles):
            ln = (starts[i + 1] - starts[i]).days
        if ln:
            lengths.append(int(ln))
    txt = f"starts {', '.join(_day(s) for s in starts)}"
    ids = [r['id'] for r in cycles]
    exp = None
    if lengths:
        txt += f" ({lengths[0]} days each)" if len(set(lengths)) == 1 else f" ({', '.join(map(str, lengths))} days)"
        mean = round(sum(lengths) / len(lengths))
        nxt = starts[-1] + timedelta(days=mean)
        exp = (nxt - timedelta(days=1), nxt + timedelta(days=1))
        txt += f"; expected next {_range(exp[0], exp[1])}"
    days = [r for r in _rows(ld, 'cycle/days') if (r.get('properties') or {}).get('date')]
    low: dict[int, list[dict]] = {}
    energies = set()
    for r in days:
        p = r['properties']
        e = p.get('energy')
        if e is None or e > LOW_ENERGY:
            continue
        d = date.fromisoformat(str(p['date'])[:10])
        st = max((s for s in starts if s <= d), default=None)
        if st is None:
            continue
        low.setdefault((d - st).days + 1, []).append(r)
        energies.add(e)
    if low:
        n = len(starts)
        groups: dict[int, list[int]] = {}
        for dn, rows in low.items():
            groups.setdefault(len({_cycle_of(r, starts) for r in rows}), []).append(dn)
        bits = []
        for cnt in sorted(groups, reverse=True):
            dns = sorted(groups[cnt])
            word = 'day' if len(dns) == 1 else 'days'
            of = f'all {n}' if cnt == n else f'{cnt} of {n}'
            bits.append(f"{word} {_and([str(x) for x in dns])} of {of}")
        e_txt = _n(max(energies)) if len(energies) == 1 else f'{_n(max(energies))} or lower'
        txt += f"; energy {e_txt} logged on {'; '.join(bits)}"
        ids += [r['id'] for dn in sorted(low) for r in sorted(low[dn], key=lambda x: x['properties']['date'])]
    return {'text': txt, 'ids': ids, 'expected': exp, 'low_days': sorted(low)}


def _cycle_of(row: dict, starts: list[date]) -> date | None:
    d = date.fromisoformat(str(row['properties']['date'])[:10])
    return max((s for s in starts if s <= d), default=None)


def _recovery(ld, keys, now, tz: str):
    if 'meditation' not in keys:
        return None
    ws = week_start(now.date())
    rows = sorted((r for r in _rows(ld, 'meditation/sessions') if (r.get('properties') or {}).get('at')
                   and ws <= _local(r['properties']['at'], tz).date() <= now.date()
                   and instant(r['properties']['at'], tz) <= now),
                  key=lambda r: instant(r['properties']['at'], tz))
    if not rows:
        return None
    mins = sum(r['properties'].get('minutes') or 0 for r in rows)
    whens = ', '.join(f"{_local(r['properties']['at'], tz).strftime('%a')} {_hm(_local(r['properties']['at'], tz))}"
                      for r in rows)
    n = len(rows)
    return {'text': f"Meditation this week: {n} session{'s' if n != 1 else ''}, {_n(mins)} min ({whens})",
            'ids': [r['id'] for r in rows], 'sessions': n, 'minutes': mins}


# ---------------------------------------------------------------- server validation (§12.9 step 4)

def _get(o, k, default=None):
    if isinstance(o, dict):
        return o.get(k, default)
    return getattr(o, k, default)


def _norm_op(o) -> dict:
    kind = 'keep' if _get(o, 'keep') else _get(o, 'op')
    app, coll = _get(o, 'app'), _get(o, 'collection')
    ref = _get(o, 'ref')
    if ref is not None and not app:
        if isinstance(ref, str) and '/' in ref:
            app, coll = ref.split('/', 1)
        else:
            app, coll = _get(ref, 'app'), _get(ref, 'collection')
    values: dict[str, Any] = {}
    for f in _get(o, 'fields') or []:
        values[_get(f, 'key')] = _get(f, 'value')
    values.update(_get(o, 'values') or {})
    occ = _get(o, 'occurrence')
    return {'op': kind, 'app': app, 'collection': coll, 'record_id': _get(o, 'record_id') or _get(o, 'rowId'),
            'occurrence': str(occ) if occ is not None else None, 'values': values,
            'reason_source': _get(o, 'reason_source'), 'also_source': _get(o, 'also_source')}


def _as_dt(v, tz: str) -> datetime | None:
    if v in (None, ''):
        return None
    try:
        p = parse_value(str(v), tz)
    except ValueError:
        return None
    return to_local(p, tz) if isinstance(p, datetime) else None


def _num(v) -> float | None:
    try:
        return float(str(v).replace('mi', '').strip())
    except (TypeError, ValueError):
        return None


def check_plan(ops, brief: Brief, ld) -> list[str]:
    """Problems with a planning run's ops, each a sentence the model can act on; [] when fine."""
    tz = brief.tz
    problems: list[str] = []
    seen = brief.seen
    by_id = {r['id']: r for r in ld.records}
    idx = index_apps(ld.apps)
    writable = brief.writable_apps()
    sessions = {(s['record_id'], s['occurrence']): s for s in brief.sessions_all}
    clashing = {(c['record_id'], c['occurrence']) for c in brief.data.get('clashes', [])}
    timed = [bk for bk in brief.booked_spans if not bk['all_day']]
    distances = (brief.data.get('running') or {}).get('distances') or set()

    def away_at(s: datetime, e: datetime):
        return next(((a0, a1) for a0, a1, _ in brief.away_spans if s < a1 and e > a0), None)

    def free_of_booked(i: int, what: str, s: datetime, e: datetime):
        for bk in timed:
            if _gap(s, e, bk['start'], bk['end']) < BUFFER:
                problems.append(f"op {i}: {what} at {_span(s, e)} is within 30 min of \"{bk['title']}\" "
                                f"{_span(bk['start'], bk['end'] if bk['end'] != bk['start'] else None)} ({bk['id']}); "
                                f"use a free block from the brief")

    def no_lift_away(i: int, what: str, s: datetime, e: datetime):
        a = away_at(s, e)
        if a:
            problems.append(f"op {i}: {what} at {_span(s, None)} is while Sam is away ({_span(a[0], a[1])}); "
                            f"lifts need the gym, so move it to the first free block after the return")

    for i, raw in enumerate(ops):
        o = _norm_op(raw)
        for k in ('reason_source', 'also_source'):
            v = o[k]
            if v and v not in seen:
                problems.append(f'op {i}: {k} {v} is not a record in the brief')
        rid = o['record_id']
        if o['op'] != 'insert' and rid:
            rec = by_id.get(rid)
            if rec and (rec.get('properties') or {}).get('source'):
                src = rec['properties']['source']
                problems.append(f'op {i}: {rid} comes from {"Google Calendar" if src == "google" else src} '
                                f'and cannot be changed; plan around it')
                continue
            if rec and not o['app']:
                o['app'], o['collection'] = rec['collection'].split('/', 1)
        app = o['app']
        if app and app not in writable:
            problems.append(f'op {i}: the brief has no part that plans {app}; leave it out')
            continue

        if o['op'] in ('keep', 'move_occurrence'):
            key = (rid, o['occurrence'])
            s = sessions.get(key)
            if s is None:
                problems.append(f"op {i}: {rid} has no session on {o['occurrence']} in the brief's sessions")
                continue
            if o['op'] == 'keep':
                if key in clashing:
                    problems.append(f"op {i}: {s['name']} on {o['occurrence']} is in clashes; move it")
                if s.get('needs'):
                    no_lift_away(i, s['name'], s['start'], s['end'])
                continue
            new = None
            for k in ('at', 'time', 'due'):
                new = new or _as_dt(o['values'].get(k), tz)
            if new is None:
                problems.append(f"op {i}: move_occurrence needs a new time (fields at = YYYY-MM-DDTHH:MM)")
                continue
            end = new + timedelta(minutes=s['minutes'])
            free_of_booked(i, s['name'], new, end)
            if s.get('needs'):
                no_lift_away(i, s['name'], new, end)
            continue

        if o['op'] == 'insert':
            ref = f"{app}/{o['collection']}"
            c = (idx.get(ref) or (None, {}))[1]
            df = c.get('dateField') if c else None
            at = _as_dt(o['values'].get(df), tz) if df else None
            if ref == 'running/runs':
                d = _num(o['values'].get('distance'))
                if d is None or not any(abs(d - x) < 1e-9 for x in distances):
                    want = ' or '.join(f'{_n(x)} mi' for x in sorted(distances)) or 'none'
                    problems.append(f"op {i}: a run of {o['values'].get('distance')} mi; the brief's distances are {want}")
                if at:
                    mins = _num(o['values'].get('minutes')) or RUN_DEFAULT_MIN
                    free_of_booked(i, o['values'].get('name') or 'Run', at, at + timedelta(minutes=mins))
            elif ref == 'workout/sessions' and at:
                mins = _num(o['values'].get('minutes')) or SESSION_DEFAULT_MIN
                free_of_booked(i, o['values'].get('name') or 'Session', at, at + timedelta(minutes=mins))
                no_lift_away(i, o['values'].get('name') or 'Session', at, at + timedelta(minutes=mins))
            elif at:
                free_of_booked(i, o['values'].get('title') or o['values'].get('name') or 'New row', at, at)
    return problems
