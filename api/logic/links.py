"""Links between records, `[[Title]]` references, search ranking and snippets (spec/backend.md sections 2, 5, 10).

Pure: plain dicts in, plain dicts out, no database. The command service and the routes feed it rows.

Storage (backend.md section 2, "Links storage"; see the note in api/commands/links.py): a record's hand-made and
`[[Title]]` links live on the record itself as `properties._links = [{id, source, field_key?}]`, in the order made.
`source` is `manual` (Link to...) or `text` (a `[[Title]]` in the text field `field_key`). On the wire `_links` is a list
of `LinkRef = {app, ref, id, title}`; `_backlinks` is derived on every read and never stored.

Public API:
    wiki_titles(text) -> list[str]                      # the `[[Title]]`s of a text, trimmed, unique, bounded
    norm(s) -> str                                      # title matching: NFKC, case-folded, whitespace collapsed
    stored_links(props) -> list[dict]                   # the cleaned stored `_links` of a record
    add_manual(links, target_id) / remove_link(links, target_id)
    text_links(links, changed, found) -> list[dict]     # the links after a save of some text fields
    resolve_wiki(title, from_ref, from_id, candidates) -> str | None
    title_text(coll, props) -> str                      # a record's title as text ("" when it has none)
    snippet(coll, props, tz, today) -> str
    rank(title, q) -> int | None                        # 0 prefix, 1 word start, 2 anywhere
    interleave(rows, total) -> list                     # round-robin across apps
    LinkIndex(apps, records, tomb)                      # `_links` and `_backlinks` for every record
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any, Iterable

from . import fmt
from .clock import day_of, instant

WIKI_RE = re.compile(r'\[\[([^\[\]\n]{1,200}?)\]\]')
MAX_WIKI = 50              # `[[ ]]` kept per text field
MAX_QUERY = 200            # characters of `q` searched
SEARCH_DEFAULT = 20
SEARCH_MAX = 50
SNIPPET_MAX = 80
DELETED = '(deleted)'
UNTITLED = 'Untitled'
SOURCES = ('manual', 'text')
# text fields that say where a record came from, not what it is (Google events)
PLUMBING = {'source', 'ext_id'}


# ---------------------------------------------------------------- text

def norm(s: Any) -> str:
    """Title matching (edge case 58): NFKC, case-folded, whitespace collapsed."""
    return ' '.join(unicodedata.normalize('NFKC', str(s or '')).casefold().split())


def wiki_titles(text: Any, limit: int = MAX_WIKI) -> list[str]:
    """Each `[[Title]]` of a text, in order, trimmed, one per distinct title, at most `limit`."""
    if not isinstance(text, str) or '[[' not in text:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for m in WIKI_RE.finditer(text):
        t = m.group(1).strip()
        k = norm(t)
        if t and k not in seen:
            seen.add(k)
            out.append(t)
            if len(out) >= limit:
                break
    return out


def clean_query(q: Any) -> str:
    """Trimmed, NUL-free (Postgres refuses them) and capped."""
    return str(q or '').replace('\x00', '').strip()[:MAX_QUERY].strip()


def like_pattern(q: str) -> str:
    """`%q%` with the LIKE wildcards of `q` escaped (use `escape '\\'`)."""
    esc = q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{esc}%'


def _clip(s: str, n: int = SNIPPET_MAX) -> str:
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


# ---------------------------------------------------------------- titles and fields

def _fields(coll: dict) -> list[dict]:
    return [f for f in coll.get('fields') or [] if isinstance(f, dict) and 'key' in f]


def title_field(coll: dict) -> dict | None:
    key = coll.get('titleField')
    return next((f for f in _fields(coll) if f['key'] == key), None)


def titled(coll: dict) -> bool:
    """A collection whose records have a title of their own: a title that is another record (Workout's sets) or a
    formula is not one to search or to match a `[[Title]]` against."""
    f = title_field(coll)
    return f is not None and f.get('type') not in ('relation', 'formula', 'file', 'repeat')


def _label(field: dict, v: Any) -> str:
    for o in field.get('options') or []:
        if isinstance(o, dict) and o.get('id') == v:
            return str(o.get('label', v))
        if o == v:
            return str(o)
    return str(v)


def title_text(coll: dict, props: dict) -> str:
    """The record's title as text; "" when it has none or its title is not text (a relation, a formula)."""
    f = title_field(coll)
    if f is None or not titled(coll):
        return ''
    v = props.get(f['key'])
    if v is None or isinstance(v, (dict, list)):
        return ''
    if f.get('type') == 'select':
        return _label(f, v).strip()
    if isinstance(v, bool):
        return ''
    return str(v).strip()


def is_private(app: dict) -> bool:
    """An app with `private: true`, and Cycle by key (a Clair-built Cycle is private whether or not the spec says so, as in
    commands/apps.py): never searched, suggested, linked to or matched by a `[[Title]]`."""
    return app.get('private') is True or app.get('key') == 'cycle'


# ---------------------------------------------------------------- snippets

def _first_line(text: str) -> str:
    for line in str(text).splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def excerpt(text: str, q: str, width: int = SNIPPET_MAX) -> str:
    """A bit of `text` around the first match of `q`."""
    flat = ' '.join(str(text).split())
    i = flat.casefold().find(q.casefold()) if q else -1
    if i < 0:
        return _clip(flat, width)
    start = max(0, i - 28)
    end = min(len(flat), start + width - 2)
    out = flat[start:end].strip()
    return ('…' if start > 0 else '') + out + ('…' if end < len(flat) else '')


def _amount(f: dict | None, v: Any) -> str:
    if v is None or isinstance(v, bool):
        return ''
    if f and f.get('type') == 'money' and isinstance(v, (int, float)):
        return fmt.money_row(v)
    if isinstance(v, (int, float)):
        return fmt.number(v) + (f' {f["unit"]}' if f and f.get('unit') else '')
    return str(v)


def snippet(coll: dict, props: dict, tz: str, today: date | None = None) -> str:
    """What tells two records with the same title apart: the first line of a body, else the amount and the day (a spend), else
    the time (an event) or the due date (a to-do) and one more value, else up to two values ("Weekly shop · To buy")."""
    fields = _fields(coll)
    tkey = coll.get('titleField')
    for f in fields:
        if f.get('type') == 'text' and f.get('multiline') and f['key'] != tkey:
            v = props.get(f['key'])
            if isinstance(v, str) and v.strip():
                return _clip(_first_line(v))
    by_key = {f['key']: f for f in fields}
    dkey, akey = coll.get('dateField'), coll.get('amountField')
    parts: list[str] = []
    amount = _amount(by_key.get(akey), props.get(akey)) if akey else ''
    if amount:
        parts.append(amount)
    dv = props.get(dkey) if dkey else None
    if dv not in (None, ''):
        try:
            parts.append(fmt.day_label(day_of(dv, tz), today) if amount else fmt.when_label(dv, tz, today))
        except (ValueError, TypeError):
            pass
    used = {tkey, dkey, akey}
    room = max(0, 2 - len(parts))        # a spend already says amount and day; a row with nothing else gets two more values
    extra = 0
    for f in fields:
        if extra >= room:
            break
        k, t, v = f['key'], f.get('type'), props.get(f['key'])
        if k in used or k in PLUMBING or v in (None, '', []) or isinstance(v, (bool, dict, list)):
            continue
        if t == 'select':
            parts.append(_label(f, v))
        elif t == 'text':
            parts.append(_clip(_first_line(str(v)), 40))
        elif t == 'number' and f.get('unit'):
            parts.append(_amount(f, v))
        else:
            continue
        extra += 1
    return _clip(' · '.join(p for p in parts if p)) or _clip(coll.get('label') or coll.get('name') or '')


# ---------------------------------------------------------------- search

def rank(title: str, q: str) -> int | None:
    """0 the title starts with `q`, 1 a word of it does, 2 it contains `q`; None when it doesn't. An empty `q` is 0."""
    if not q:
        return 0
    t, w = norm(title), norm(q)
    i = t.find(w)
    if i < 0:
        return None
    if i == 0:
        return 0
    return 1 if re.match(r'[\s(\-/]', t[i - 1]) else 2


def text_values(coll: dict, props: dict) -> Iterable[tuple[str, str]]:
    """Every text field's value, `(key, text)`: what a search matches besides the title."""
    for f in _fields(coll):
        if f.get('type') == 'text':
            v = props.get(f['key'])
            if isinstance(v, str) and v:
                yield f['key'], v


def _date_rank(row: dict, now: datetime, tz: str) -> tuple[int, float]:
    """Among rows changed at the same moment (a seed): dated up to now first, latest first; then upcoming, nearest first."""
    dkey = row['coll'].get('dateField')
    dv = row['props'].get(dkey) if dkey else None
    if dv in (None, ''):
        return 2, 0.0
    try:
        delta = (instant(dv, tz) - now).total_seconds()
    except (ValueError, TypeError):
        return 2, 0.0
    return (0, -delta) if delta <= 0 else (1, delta)


def recency_key(row: dict, now: datetime, tz: str) -> tuple:
    up = row.get('updated_at')
    ts = up.timestamp() if isinstance(up, datetime) else 0.0
    band, sec = _date_rank(row, now, tz)
    return (-ts, band, sec, row.get('app_idx', 0), row.get('coll_idx', 0), row.get('position', ''), row['id'])


def interleave(rows: list[dict], total: int) -> list[dict]:
    """Round-robin across apps: the most recent row of every app, then the second of every app, until `total`. `rows` is
    already in recency order; an app's turn within a round is the order of its first row."""
    queues: dict[str, list[dict]] = {}
    for r in rows:
        queues.setdefault(r['app'], []).append(r)
    live = list(queues.values())
    out: list[dict] = []
    while live and len(out) < total:
        nxt = []
        for qu in live:
            if len(out) >= total:
                break
            out.append(qu.pop(0))
            if qu:
                nxt.append(qu)
        live = nxt
    return out


# ---------------------------------------------------------------- stored links

def stored_links(props: dict | None) -> list[dict]:
    """The stored `_links` of a record, cleaned: `{id, source, field_key?}`, one per target."""
    raw = (props or {}).get('_links')
    out: list[dict] = []
    seen: set[str] = set()
    for x in raw if isinstance(raw, list) else []:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or x['id'] in seen:
            continue
        seen.add(x['id'])
        src = x.get('source') if x.get('source') in SOURCES else 'manual'
        e: dict[str, Any] = {'id': x['id'], 'source': src}
        if src == 'text' and isinstance(x.get('field_key'), str):
            e['field_key'] = x['field_key']
        out.append(e)
    return out


def add_manual(links: list[dict], target_id: str) -> list[dict]:
    """Link by hand. A target already linked (by hand or by a `[[Title]]`) stays as it was: one link per pair."""
    if any(e['id'] == target_id for e in links):
        return list(links)
    return [*links, {'id': target_id, 'source': 'manual'}]


def remove_link(links: list[dict], target_id: str) -> list[dict]:
    return [e for e in links if e['id'] != target_id]


def text_links(links: list[dict], changed: Iterable[str], found: dict[str, list[str]]) -> list[dict]:
    """The links after the text fields `changed` were saved: their old `[[Title]]` links go, `found` (`{field: [target ids
    in text order]}`) come in, hand-made links and the `[[Title]]` links of other fields stay. One link per target."""
    changed = list(changed)
    kept = [e for e in links if not (e['source'] == 'text' and e.get('field_key') in changed)]
    have = {e['id'] for e in kept}
    for key in changed:
        for tid in found.get(key, []):
            if tid not in have:
                have.add(tid)
                kept.append({'id': tid, 'source': 'text', 'field_key': key})
    return kept


def resolve_wiki(title: str, from_ref: str, from_id: str, candidates: Iterable[dict]) -> str | None:
    """The record a `[[Title]]` names (edge case 63): the same collection first, then every other collection in app order,
    then the first record in position order; the record itself never matches. `candidates`: `{id, ref, title, app_idx,
    coll_idx, position}` of live, titled records."""
    want = norm(title)
    best: tuple | None = None
    for c in candidates:
        if c['id'] == from_id or norm(c['title']) != want:
            continue
        k = (0 if c['ref'] == from_ref else 1, c['app_idx'], c['coll_idx'], c['position'], c['id'])
        if best is None or k < best[0]:
            best = (k, c['id'])
    return best[1] if best else None


# ---------------------------------------------------------------- the index: `_links` and `_backlinks` on read

def ordered_links(links: list[dict]) -> list[dict]:
    """Hand-made first, then the `[[Title]]` ones; each group in the order stored."""
    return [e for e in links if e['source'] == 'manual'] + [e for e in links if e['source'] == 'text']


class LinkIndex:
    """Titles, `_links` and `_backlinks` for every record of a loaded workspace, computed once per request.

    `apps`: the AppSpecs in page order; `records`: `{id, collection, properties, position}` of every live record;
    `tomb`: `{id: {app, ref}}` for link targets that are no longer live (deleted records, records of a deleted app)."""

    def __init__(self, apps: list[dict], records: list[dict], tomb: dict[str, dict] | None = None):
        self.tomb = tomb or {}
        colls: dict[str, tuple[int, int, dict, dict]] = {}
        for ai, a in enumerate(apps):
            for ci, c in enumerate(a.get('collections') or []):
                colls[f"{a['key']}/{c['key']}"] = (ai, ci, a, c)
        self.rows: dict[str, dict] = {}
        for r in records:
            hit = colls.get(r['collection'])
            if hit is None:
                continue
            ai, ci, a, c = hit
            self.rows[r['id']] = {'id': r['id'], 'app': a['key'], 'ref': r['collection'], 'coll': c, 'props': r['properties'],
                                  'order': (ai, ci, r.get('position') or '', r['id']), 'title': title_text(c, r['properties'])}
        # a title that is another record's (Workout's sets): that record's title
        for row in self.rows.values():
            if row['title']:
                continue
            tf = title_field(row['coll'])
            if tf and tf.get('type') == 'relation':
                v = row['props'].get(tf['key'])
                ids = v if isinstance(v, list) else [v]
                target = self.rows.get(str(ids[0])) if ids and ids[0] else None
                row['title'] = (target or {}).get('title') or ''
            row['title'] = row['title'] or UNTITLED
        self._out: dict[str, list[dict]] = {}
        self._in: dict[str, list[dict]] = {}
        ordered = sorted(self.rows.values(), key=lambda r: r['order'])
        for row in ordered:
            out = []
            for e in ordered_links(stored_links(row['props'])):
                ref = self._ref(e['id'])
                if ref is not None and e['id'] != row['id']:
                    out.append(ref)
            self._out[row['id']] = out
        for row in ordered:
            me = {'app': row['app'], 'ref': row['ref'], 'id': row['id'], 'title': row['title']}
            for f in _fields(row['coll']):
                if f.get('type') != 'relation':
                    continue
                v = row['props'].get(f['key'])
                for tid in v if isinstance(v, list) else ([v] if v else []):
                    if str(tid) in self.rows and str(tid) != row['id']:
                        self._in.setdefault(str(tid), []).append({**me, 'via': f['key']})
            for l in self._out[row['id']]:
                if l['id'] in self.rows:
                    self._in.setdefault(l['id'], []).append(dict(me))

    def _ref(self, rid: str) -> dict | None:
        row = self.rows.get(rid)
        if row is not None:
            return {'app': row['app'], 'ref': row['ref'], 'id': rid, 'title': row['title']}
        t = self.tomb.get(rid)
        if t is not None:
            return {'app': t['app'], 'ref': t['ref'], 'id': rid, 'title': DELETED}
        return None

    def title(self, rid: str) -> str | None:
        r = self.rows.get(rid)
        return r['title'] if r else None

    def links(self, rid: str) -> list[dict]:
        return [dict(x) for x in self._out.get(rid, [])]

    def backlinks(self, rid: str) -> list[dict]:
        return [dict(x) for x in self._in.get(rid, [])]

def dangling_targets(records: list[dict]) -> set[str]:
    """Stored link targets of `records` that are not among them (to look up as deleted before building a LinkIndex)."""
    live = {r['id'] for r in records}
    out: set[str] = set()
    for r in records:
        links = (r.get('properties') or {}).get('_links')
        if not links:
            continue
        for e in stored_links(r['properties']):
            if e['id'] not in live:
                out.add(e['id'])
    return out


def wire_record(index: LinkIndex, rid: str, props: dict) -> dict:
    """The record's properties as the wire sends them: stored `_links` replaced by `LinkRef`s, `_backlinks` added."""
    return {**{k: v for k, v in props.items() if k not in ('_links', '_backlinks')},
            '_links': index.links(rid), '_backlinks': index.backlinks(rid)}
