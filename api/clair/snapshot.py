"""The per-turn snapshot (clair-agent.md §8): plain text with light tags, read by the model.

Built from `workspace.load()` on every turn. It names apps, faces, collections with their fields and
select options, the open items of to-do-like collections and Clair notes. Every record id it shows
joins the run's seen set (§10), so Clair may update those records without a read call first.

Read levels (§8): `full` as above; `field_names` drops faces, open items and notes; `none` never
reaches here (the route answers 403 before any model call).

A planning run passes the planning brief (§12.9, `brief.py`); its block goes in before `</snapshot>`
and every id it names joins the seen set. Whether Clair reads an app is `settings.clair_read`
(`brief.clair_can_read`): Cycle is private and, in the demo account, readable.
"""
from __future__ import annotations

import re
from datetime import datetime

from ..logic import fmt
from ..workspace import Loaded, faces
from .brief import Brief, clair_can_read

OPEN_LIMIT = 50


def _field_line(f: dict) -> str:
    t = f.get('type', 'text')
    if t == 'select':
        opts = []
        for o in f.get('options') or []:
            if isinstance(o, dict):
                opts.append(f"{o.get('label', o.get('id'))}={o.get('id')}")
            else:
                opts.append(str(o))
        return f"{f['key']} select[{', '.join(opts)}]"
    if t == 'relation':
        return f"{f['key']} relation({f.get('target', '')})"
    return f"{f['key']} {t}"


def _title(c: dict, props: dict) -> str:
    v = props.get(c.get('titleField') or 'name') or props.get('title') or props.get('name')
    return str(v) if v is not None else '(untitled)'


def _is_open(c: dict, props: dict) -> bool | None:
    """True/False for collections with an open/closed notion; None when the collection has none."""
    keys = {f.get('key'): f for f in c.get('fields') or []}
    if 'status' in keys and any(isinstance(o, dict) and o.get('id') in ('to_buy',) for o in keys['status'].get('options') or []):
        return props.get('status') == 'to_buy'
    if 'done' in keys and keys['done'].get('type') == 'bool' and not keys.get('repeat'):
        return not props.get('done')
    return None


_BRIEF_IDS = re.compile(r'\[([^\[\]]+)\]\s*$', re.M)


def brief_ids(text: str) -> set[str]:
    """The record ids a rendered brief names (each line ends with `[id, id]`)."""
    out: set[str] = set()
    for m in _BRIEF_IDS.finditer(text or ''):
        out |= {x.strip() for x in m.group(1).split(',') if x.strip()}
    return out


def build(ld: Loaded, read_level: str, *, typed: str | None, spoken: bool, context: dict | None = None,
          clair_notes: list[dict] | None = None, brief: Brief | str | None = None) -> tuple[str, set[str]]:
    """(snapshot text, record ids shown). `brief`: a Brief or its rendered text, for a planning run."""
    seen: set[str] = set()
    now: datetime = ld.now
    out = ['<snapshot>',
           f"now: {now.isoformat()} ({now.strftime('%a')}) · time zone: {ld.tz}",
           f'read level: {read_level}',
           f"input: typed: {'yes' if typed and not spoken else 'none'}, spoken: {'yes' if spoken else 'no'}"]
    if context:
        out.append(f"opened from: {context}")
    full = read_level == 'full'
    fc = faces(ld) if full else {}
    out.append('')
    out.append('apps:')
    for a in ld.apps:
        settings = a.get('settings') or {}
        private = not clair_can_read(a)
        face = fc.get(a['key'])
        face_s = ''
        if face:
            face_s = f" · face \"{(face['text'] + ' ' + face.get('label', '')).strip()}\""
        out.append(f"- {a['key']} \"{a.get('name', a['key'])}\"{face_s}" + (' · private: not read' if private else ''))
        if private:
            continue
        lim = settings.get('limit')
        if full and lim is not None and isinstance(lim, int):
            out.append(f'  limit {fmt.money_face(lim)} (setting)')
        for c in a.get('collections') or []:
            flags = ' (calendar)' if c.get('calendar') else ''
            fields = ', '.join(_field_line(f) for f in c.get('fields') or [] if f.get('key'))
            out.append(f"  {c['key']}{flags}: {fields}")
    if full:
        open_lines = []
        for a in ld.apps:
            if not clair_can_read(a):
                continue
            for c in a.get('collections') or []:
                ref = f"{a['key']}/{c['key']}"
                rows = [r for r in ld.records if r['collection'] == ref and _is_open(c, r['properties'])]
                if not rows:
                    continue
                rows = rows[:OPEN_LIMIT]
                for r in rows:
                    seen.add(r['id'])
                open_lines.append(f'{ref} ({len(rows)}): ' + ' · '.join(f"{r['id']} {_title(c, r['properties'])}" for r in rows))
        if open_lines:
            out.append('')
            out.append('open items:')
            out.extend(open_lines)
        if clair_notes:
            out.append('')
            out.append('clair notes:')
            for n in clair_notes:
                out.append(f"- ({n['kind']}) {n['text']}")
    if brief is not None and read_level != 'none':
        if isinstance(brief, Brief):
            b_text, b_seen = brief.text(), brief.seen
        else:
            b_text, b_seen = brief, brief_ids(brief)
        if b_text:
            out.append('')
            out.append(b_text)
            seen |= b_seen
    if spoken:
        out.append('')
        out.append('This turn was spoken. End with one line "Spoken: <15 words or fewer>".')
    out.append('</snapshot>')
    return '\n'.join(out), seen
