"""A scripted stand-in for the model (`CLAIR_MODEL=mock`, or no ANTHROPIC_API_KEY).

It reads the conversation the way the real model would and answers with the tool calls Claude makes for
the demo sentences, so the deployed server runs the whole pipeline (tools, propose_changes →
create_change_set, card, events, credits) with no model:

- "spent $12 on lunch" (and "spent $N on <thing>"): report_understanding + propose_changes, one insert
  into budget/spend.
- "Plan my training for next week": with the run's planning brief (brief.py, handed over by the runner
  through `use_brief`), proposes the rung-1 plan at once from the brief's facts: its understanding line, its
  sessions, clashes, away spans and free blocks, so the mock and the real model act on the same facts.
  Without a brief it falls back to reading Workout sessions, Calendar events and Classes and proposes the
  rung-1 plan (clair-agent.md §12.9: lifts kept or moved with move_occurrence, a reason per row sourced
  from a record it read). The plan is worked out here from the rows the reads returned, by the rules of
  the planning prompt; nothing is hard-coded to ids.
- "I want to track my calories" (a Calories build, §7 rule 7 / §11): ask_user with a card of two questions
  (target, logging; plan_after true), then on the answer propose_app with a plan built from the answers
  when api/clair/build.py offers propose_app, otherwise a short text reply saying what it would build.
  "Sam changed the answers: {...}" re-proposes from the new answers.
- Anything else: one short text answer.

Runs are marked "mock" in agent_runs.model. Proposals are `mode: live` (a live run with a scripted model).
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from pathlib import Path

from .runner import CHANGED_ANSWERS, ModelReply, is_planning

SPENT_RE = re.compile(r'\bspent\s+\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:dollars\s+)?(?:on|for|at)\s+(.+?)[.!?]*$', re.I)
CATEGORY = [
    (r'lunch|dinner|breakfast|brunch|coffee|food|pizza|tacos?|sushi|burger|snack|cafe|restaurant|takeout|boba|drinks?',
     'Eating out'),
    (r'groceries|grocery|supermarket|market', 'Groceries'),
    (r'gas|uber|lyft|bus|train|scooter|parking|taxi|fuel', 'Transport'),
    (r'rent', 'Rent'),
    (r'netflix|spotify|hulu|subscription', 'Subscriptions'),
]
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
LIFT_MINUTES = 45
BUFFER = timedelta(minutes=30)
SAME_DAY_SLOTS = [time(7), time(17), time(16), time(18), time(19), time(8)]
RETURN_SLOTS = [time(16), time(17), time(18), time(19)]
BUILD_RE = re.compile(r'\b(track|log|count|build|make|want|app)\b.*\bcalories?\b|\bcalories?\s+(app|tracker)\b', re.I)
CALORIES_SPEC = Path(__file__).resolve().parent.parent / 'templates' / 'calories.json'   # §12.11 Calories
CALORIES_ASK = {'plan_after': True, 'questions': [
    {'id': 'target', 'header': 'Daily target', 'question': 'Do you want a daily calorie target?', 'multi_select': False,
     'options': [{'label': 'Set a number', 'description': 'You choose it; the Today ring fills toward it',
                  'input': {'placeholder': 'Calories a day', 'numeric': True}},
                 {'label': 'No target', 'description': 'Just totals for the day'}]},
    {'id': 'logging', 'header': 'Logging', 'question': 'How do you log meals?', 'multi_select': True,
     'options': [{'label': 'Type them', 'description': 'Name, calories and protein each time'},
                 {'label': 'Pick from foods you save', 'description': 'Save a food once, then tap it to log it again'}]},
]}
CANT = ('I can\'t do that one yet. Try "spent $12 on lunch" or "Plan my training for next week".')


def _turn(messages: list[dict]) -> tuple[str, str, list[dict], dict[str, dict]]:
    """(Sam's text, snapshot text, assistant messages since, tool results by tool name)."""
    start = 0
    for i, m in enumerate(messages):
        if m['role'] == 'user' and any(b.get('type') == 'text' for b in m['content']):
            start = i
    texts = [b['text'] for b in messages[start]['content'] if b.get('type') == 'text']
    snap = next((t for t in texts if t.startswith('<snapshot>')), '')
    said = next((t for t in reversed(texts) if not t.startswith('<snapshot>')), '')
    later = messages[start + 1:]
    names = {}
    for m in later:
        if m['role'] == 'assistant':
            for b in m['content']:
                if b.get('type') == 'tool_use':
                    names[b['id']] = (b['name'], b.get('input') or {})
    results: dict[str, dict] = {}
    for m in later:
        if m['role'] == 'user':
            for b in m['content']:
                if b.get('type') == 'tool_result' and b['tool_use_id'] in names:
                    name, inp = names[b['tool_use_id']]
                    key = name if name != 'query_records' else f"{inp.get('app')}/{inp.get('collection')}"
                    try:
                        results[key] = {'error': bool(b.get('is_error')), 'data': json.loads(b['content'])}
                    except (TypeError, ValueError):
                        results[key] = {'error': True, 'data': b.get('content')}
    return said, snap, [m for m in later if m['role'] == 'assistant'], results


def _use(i: int, step: int, name: str, inp: dict) -> dict:
    return {'type': 'tool_use', 'id': f'mock_{step}_{i}', 'name': name, 'input': inp}


def _reply(content: list[dict], stop: str = 'end_turn') -> ModelReply:
    return ModelReply(content=content, stop_reason=stop, model='mock', usage={'input_tokens': 0, 'output_tokens': 0})


class MockClient:
    name = 'mock'
    brief = None

    def use_brief(self, brief) -> None:
        self.brief = brief

    def create(self, *, system, tools, messages, effort, timeout, on_text) -> ModelReply:
        said, snap, done, results = _turn(messages)
        step = len(done)
        m = re.search(r'^now: (\S+)', snap, re.M)
        now = datetime.fromisoformat(m.group(1)) if m else datetime.now().astimezone()
        tz = re.search(r'time zone: (\S+)', snap)
        tz = tz.group(1) if tz else 'America/Denver'
        if said.startswith(CHANGED_ANSWERS):
            try:
                answers = json.loads(said[len(CHANGED_ANSWERS):])
            except ValueError:
                answers = {'skipped': True}
            return self._build_propose(step, tools, on_text, answers) if step == 0 else _reply([])
        if BUILD_RE.search(said):
            return self._build(step, tools, on_text, results)
        spent = SPENT_RE.search(said.strip())
        if spent:
            return self._spend(step, spent, now, results)
        if is_planning(said):
            if self.brief is not None:
                return self._plan_from_brief(step, self.brief) if step == 0 else _reply([])
            return self._plan(step, now, tz, results)
        return self._text(on_text, CANT) if step == 0 else _reply([])

    @staticmethod
    def _text(on_text, text: str) -> ModelReply:
        on_text(text)
        return _reply([{'type': 'text', 'text': text}])

    # ---- "I want to track my calories" (ask first, then propose_app with a plan)
    def _build(self, step: int, tools: list[dict], on_text, results: dict) -> ModelReply:
        if step == 0:
            on_text("A few questions first, then I'll show you the plan.")
            return _reply([{'type': 'text', 'text': "A few questions first, then I'll show you the plan."},
                           _use(0, step, 'ask_user', CALORIES_ASK)], 'tool_use')
        if step == 1:
            ans = (results.get('ask_user') or {}).get('data')
            return self._build_propose(step, tools, on_text, ans if isinstance(ans, dict) else {'skipped': True})
        return _reply([])

    def _build_propose(self, step: int, tools: list[dict], on_text, ans: dict) -> ModelReply:
        a = ans.get('answers') or {}
        target = None
        t = a.get('target') or {}
        if 'Set a number' in (t.get('choices') or []) and t.get('other'):
            try:
                target = int(float(str(t['other']).replace(',', '')))
            except ValueError:
                target = None
        logging = (a.get('logging') or {}).get('choices') or ['Type them']
        lines = [{'app': 'calories', 'text': f'Today: a ring for calories against {target:,}' if target
                  else 'Today: calories and protein so far, no target'}]
        if 'Type them' in logging or ans.get('skipped'):
            lines.append({'app': 'calories', 'text': 'Log: meals with calories and protein'})
        if 'Pick from foods you save' in logging:
            lines.append({'app': 'calories', 'text': 'Foods: save a food once, tap it to log it again'})
        if len(lines) < 2:
            lines.append({'app': 'calories', 'text': 'Log: meals with calories and protein'})
        if not any(t.get('name') == 'propose_app' for t in tools):
            text = 'I would build Calories: ' + '; '.join(ln['text'] for ln in lines) + '.'
            return self._text(on_text, text)
        spec = json.loads(CALORIES_SPEC.read_text())
        if target:
            spec['settings'] = {**(spec.get('settings') or {}), 'target': target}
        else:
            spec.get('settings', {}).pop('target', None)
        foods = 'Pick from foods you save' in logging
        return _reply([_use(0, step, 'propose_app', {
            'name': 'Calories', 'purpose': 'Meals with calories and protein' + (', and foods Sam saves' if foods else ''),
            'summary': 'Meals with calories and protein' + (', and foods you save.' if foods else '.'),
            'spec': json.dumps(spec), 'rows': [], 'stitches_into': [], 'plan': lines})], 'tool_use')

    # ---- "spent $12 on lunch"
    def _spend(self, step: int, m: re.Match, now: datetime, results: dict) -> ModelReply:
        if step > 0:
            return _reply([])
        amount = float(m.group(1))
        thing = m.group(2).strip()
        cat = next((c for pat, c in CATEGORY if re.search(rf'\b({pat})\b', thing, re.I)), 'Fun')
        title = thing[:1].upper() + thing[1:]
        dollars = f'{amount:.2f}'
        return _reply([
            _use(0, step, 'report_understanding', {'kind': 'request', 'confidence': 1.0,
                                                    'summary': f'A ${m.group(1)} {thing}. That goes in Budget.'}),
            _use(1, step, 'propose_changes', {'title': title, 'summary': f'${dollars} in {cat}.', 'ops': [{
                'op': 'insert', 'app': 'budget', 'collection': 'spend', 'fields': [
                    {'key': 'note', 'value': title}, {'key': 'amount', 'value': dollars},
                    {'key': 'category', 'value': cat}, {'key': 'at', 'value': now.isoformat()}]}]}),
        ], 'tool_use')

    # ---- "Plan my training for next week" (rung 1) from the planning brief
    def _plan_from_brief(self, step: int, b) -> ModelReply:
        z = ZoneInfo(b.tz)
        booked = {bk['id']: bk for bk in b.booked_spans}
        clashes = {(c['record_id'], c['occurrence']): booked.get(c['booked']) for c in b.data.get('clashes', [])}
        free = {d: blocks for d, blocks, _ in b.data.get('free', [])}
        away = [(a0, a1, ids) for a0, a1, ids in b.away_spans]

        def label(d: datetime) -> str:
            return f"{d.strftime('%a')} {d.hour % 12 or 12}:{d.minute:02d} {'am' if d.hour < 12 else 'pm'}"

        def fits(s: datetime, minutes: int) -> bool:
            e = s + timedelta(minutes=minutes)
            return any(x <= s and e <= y for x, y in free.get(s.date(), [])) and \
                not any(s < a1 and e > a0 for a0, a1, _ in away)

        def short(title: str) -> str:
            return re.split(r'\s+for\s+', title)[0]

        ops, kept, moved = [], 0, 0
        for s in sorted(b.sessions_all, key=lambda x: x['start']):
            base = {'app': 'workout', 'collection': 'sessions', 'record_id': s['record_id'], 'occurrence': s['occurrence']}
            start, mins, d = s['start'], s['minutes'], s['start'].date()
            hit = clashes.get((s['record_id'], s['occurrence']))
            gone = next(((a0, a1, ids) for a0, a1, ids in away
                         if start < a1 and start + timedelta(minutes=mins) > a0), None) if s.get('needs') else None
            if hit is None and gone is None:
                classes = [bk for bk in b.booked_spans if bk['app'] == 'classes' and not bk['all_day']
                           and bk['start'].date() == d and bk['end'] <= start]
                if classes:
                    c = max(classes, key=lambda bk: bk['end'])
                    reason, src = f"Free after {c['title']}", c['id']
                else:
                    reason, src = 'Nothing booked nearby', s['record_id']
                ops.append({**base, 'op': 'keep', 'keep': True, 'reason': reason, 'reason_source': src})
                kept += 1
                continue
            # the nearest free slot that day (a lift before the trip out still counts), else the first day back
            why = hit or next((booked.get(i) for i in (gone or ((), (), []))[2] if i in booked), None)
            new = next((c for t in SAME_DAY_SLOTS for c in [datetime.combine(d, t, z)] if fits(c, mins)), None)
            if new is not None and why is not None and not why['all_day']:
                ops.append({**base, 'op': 'move_occurrence', 'fields': [{'key': 'at', 'value': new.isoformat()}],
                            'reason': f"{short(why['title'])} at {label(why['start']).split(' ', 1)[1]}",
                            'reason_source': why['id']})
                moved += 1
                continue
            span = gone or next(((a0, a1, ids) for a0, a1, ids in away if a0 <= start + timedelta(days=1) and a1 > start - timedelta(days=1)), None)
            if span is None:
                continue
            a1 = span[1]
            back = max((bk for bk in b.booked_spans if bk['id'] in span[2] and not bk['all_day']),
                       key=lambda bk: bk['end'], default=None)
            new = next((c for t in RETURN_SLOTS for c in [datetime.combine(a1.date(), t, z)]
                        if c >= a1 + BUFFER and fits(c, mins)), None)
            if new is None or back is None:
                continue
            ops.append({**base, 'op': 'move_occurrence', 'fields': [{'key': 'at', 'value': new.isoformat()}],
                        'reason': f"{back['title']} {label(back['start'])}", 'reason_source': back['id']})
            moved += 1
        if not ops:
            return _reply([{'type': 'text', 'text': 'No lifts planned next week, so nothing to move.'}])
        return _reply([
            _use(0, step, 'report_understanding', {'kind': 'request', 'confidence': 1.0, 'summary': b.understanding()}),
            _use(1, step, 'propose_changes', {'title': "Next week's training",
                                               'summary': f'{kept + moved} lifts ({kept} kept, {moved} moved).', 'ops': ops}),
        ], 'tool_use')

    # ---- "Plan my training for next week" (rung 1), reading the apps (no brief)
    def _plan(self, step: int, now: datetime, tz: str, results: dict) -> ModelReply:
        if step == 0:
            return _reply([
                _use(0, step, 'query_records', {'app': 'workout', 'collection': 'sessions', 'limit': 50}),
                _use(1, step, 'query_records', {'app': 'calendar', 'collection': 'events', 'limit': 50}),
                _use(2, step, 'query_records', {'app': 'classes', 'collection': 'classes', 'limit': 50}),
            ], 'tool_use')
        if step == 1:
            return self._propose_plan(step, now, tz, results)
        return _reply([])

    def _propose_plan(self, step, now: datetime, tz: str, results: dict) -> ModelReply:
        z = ZoneInfo(tz)
        rows = lambda k: (results.get(k) or {}).get('data', {}).get('rows', []) if not (results.get(k) or {}).get('error') else []
        sessions, events, classes = rows('workout/sessions'), rows('calendar/events'), rows('classes/classes')
        monday = now.date() + timedelta(days=(7 - now.weekday()) or 7)
        week = [monday + timedelta(days=i) for i in range(7)]

        def parse(v) -> tuple[datetime, bool]:
            if isinstance(v, str) and 'T' in v:
                d = datetime.fromisoformat(v)
                return (d if d.tzinfo else d.replace(tzinfo=z)).astimezone(z), False
            return datetime.combine(date.fromisoformat(str(v)), time(0), z), True

        def series(row) -> list[tuple[date, datetime]]:
            rep = (row.get('fields') or {}).get('repeat') or {}
            rule = rep.get('rule') or ''
            by = re.search(r'BYDAY=([A-Z,]+)', rule)
            if not by or not rep.get('start'):
                return []
            at = datetime.fromisoformat(rep['start']).time()
            off = set(rep.get('skip') or []) | set(rep.get('log') or [])
            return [(d, datetime.combine(d, at, z)) for d in week
                    if DAYS[d.weekday()] in by.group(1).split(',') and d.isoformat() not in off]

        busy = []   # (start, end, row)
        for e in events:
            f = e.get('fields') or {}
            if not f.get('at'):
                continue
            s, all_day = parse(f['at'])
            if f.get('ends'):
                en, end_all_day = parse(f['ends'])
                if end_all_day:
                    en = en + timedelta(days=1)
            else:
                en = s + (timedelta(days=1) if all_day else timedelta(hours=1))
            busy.append((s, en, e))
        for c in classes:
            for _, s in series(c):
                busy.append((s, s + timedelta(minutes=75), c))

        drive = next((b for b in busy if re.search(r'\b(drive|flight|fly)\b', str(b[2]['fields'].get('title', '')), re.I)), None)
        back = next((b for b in busy if re.search(r'\bback to\b|\breturn', str(b[2]['fields'].get('title', '')), re.I)), None)
        away = (drive[0], back[1]) if drive and back and back[1] > drive[0] else None

        def clash(s: datetime):
            e = s + timedelta(minutes=LIFT_MINUTES)
            for b in busy:
                if b[0] < e + BUFFER and s - BUFFER < b[1] and b[2] in events:
                    return b
            for b in busy:
                if b[0] < e and s < b[1]:
                    return b
            return None

        def is_away(s: datetime) -> bool:
            return bool(away and away[0] <= s < away[1])

        def label(d: datetime) -> str:
            return f"{d.strftime('%a')} {d.hour % 12 or 12}:{d.minute:02d} {'am' if d.hour < 12 else 'pm'}"

        def short(title: str) -> str:
            return re.split(r'\s+for\s+', title)[0]

        ops, kept, moved = [], 0, 0
        occs = sorted((s, d, row) for row in sessions for d, s in series(row))
        for s, d, row in occs:
            name = row['fields'].get('name', 'Session')
            base = {'app': 'workout', 'collection': 'sessions', 'record_id': row['id'], 'occurrence': d.isoformat()}
            hit = clash(s)
            if hit is not None and hit[2] in events:
                new = next((datetime.combine(d, t, z) for t in SAME_DAY_SLOTS
                            if not clash(datetime.combine(d, t, z)) and not is_away(datetime.combine(d, t, z))), None)
                if new is not None:
                    ev = hit[2]
                    ops.append({**base, 'op': 'move_occurrence', 'fields': [{'key': 'at', 'value': new.isoformat()}],
                                'reason': f"{short(ev['fields']['title'])} at {label(hit[0]).split(' ', 1)[1]}",
                                'reason_source': ev['id']})
                    moved += 1
                    continue
            if is_away(s) or hit is not None:
                if not away:
                    continue
                day = away[1].date()
                new = next((datetime.combine(day, t, z) for t in RETURN_SLOTS
                            if datetime.combine(day, t, z) >= away[1] + BUFFER and not clash(datetime.combine(day, t, z))), None)
                if new is None:
                    continue
                ev = back[2]
                ops.append({**base, 'op': 'move_occurrence', 'fields': [{'key': 'at', 'value': new.isoformat()}],
                            'reason': f"{ev['fields']['title']} {label(back[0])}", 'reason_source': ev['id']})
                moved += 1
                continue
            before = [b for b in busy if b[2] in classes and b[0].date() == d and b[1] <= s]
            if before:
                c = max(before, key=lambda b: b[1])[2]
                reason, src = f"Free after {c['fields'].get('name', 'class')}", c['id']
            else:
                reason, src = 'Nothing booked nearby', row['id']
            ops.append({**base, 'op': 'keep', 'keep': True, 'reason': reason, 'reason_source': src})
            kept += 1
        if not ops:
            return _reply([{'type': 'text', 'text': 'No lifts planned next week, so nothing to move.'}])
        n = kept + moved
        apps = sorted({'Workout'} | ({'Calendar'} if events else set()) | ({'Classes'} if classes else set()))
        read = f"Read {len(apps)} apps: {', '.join(apps[:-1])} and {apps[-1]}." if len(apps) > 1 else f'Read {apps[0]}.'
        return _reply([
            _use(0, step, 'report_understanding', {'kind': 'request', 'confidence': 1.0, 'summary': read}),
            _use(1, step, 'propose_changes', {'title': "Next week's training",
                                               'summary': f'{n} lifts ({kept} kept, {moved} moved).', 'ops': ops}),
        ], 'tool_use')
