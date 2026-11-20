"""Links in the command service (spec/backend.md section 5: `link`, `unlink`, and `[[Title]]` in a text field).

Storage (a difference from backend.md section 2.1, which has a `links` table: no schema change was asked for, and none is
needed). A record's links live on the record itself, in its reserved property `_links`, as a list of
`{id, source, field_key?}` in the order made (`source` is `manual` for Link to... and `text` for a `[[Title]]` in the
text field `field_key`). That gives, with no new table and no new undo code:

- `link` and `unlink` are an `update` of the source record's `_links`, so the change set has one event with
  `field_path = '_links'` (`old` and `new` the stored lists), Undo is the plain inverse, and `/sync` carries the change as
  an event on the source record (so a second device refreshes both ends);
- a text save carries the text and the recomputed `_links` in one change set, so one Undo reverts both;
- `_backlinks` are derived on every read, never stored (api/logic/links.py `LinkIndex`);
- a deleted target keeps its entry, and reads as "(deleted)".

The cost: the source record's `version` moves when it is linked (the spec's table would not move it). A client's
`base_version` is only ever compared field by field (`superseded`), so a link never makes a text save conflict.

Clair never sees `_links`: `query_records` drops every `_` key, and her ops cannot name a link (`ClairOp` has no `link`).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from ..logic import links as L


def _q(conn: psycopg.Connection, sql: str, params: Any = None):
    cur = conn.cursor(row_factory=dict_row)
    cur.execute(sql, params)
    return cur


def check_target(model, rows: dict[UUID, dict], source: dict, target_id: str, i: int, issues) -> dict | None:
    """The record a `link` points at, or None after adding the problem to `issues`: it must be a live record of this
    workspace (`rows` was read with the workspace id, so another workspace's id is simply missing: 404), not the source
    itself (422 `self_link`), and not in a private app (422 `private_target`)."""
    t = rows.get(UUID(target_id))
    if t is None or t['block_type'] != 'record' or t['deleted_at'] is not None or t['collection_id'] not in model.colls:
        issues.add(i, f'no record {target_id}', code='not_found', field='target_id')
        return None
    if t['id'] == source['id']:
        issues.add(i, 'a record cannot link to itself', code='self_link', field='target_id')
        return None
    page = model.pages[model.colls[t['collection_id']]['parent_id']]['properties']
    if L.is_private(page):
        issues.add(i, f'{page.get("name") or page.get("key")} is private: its records cannot be linked to',
                   code='private_target', field='target_id')
        return None
    return t


def wiki_candidates(conn: psycopg.Connection, ws: UUID, model) -> list[dict]:
    """Every live, titled record a `[[Title]]` could name: `{id, ref, title, app_idx, coll_idx, position}`. Private apps and
    collections whose title is another record's (Workout's sets) are left out."""
    meta: dict[UUID, tuple[str, int, int, dict]] = {}
    for ai, page in enumerate(sorted(model.pages.values(), key=lambda p: p['position'])):
        if L.is_private(page['properties']):
            continue
        colls = sorted((c for c in model.colls.values() if c['parent_id'] == page['id']), key=lambda c: c['position'])
        for ci, c in enumerate(colls):
            if L.titled(c['properties']):
                meta[c['id']] = (model.ref(c['id']), ai, ci, c['properties'])
    if not meta:
        return []
    out = []
    for r in _q(conn, "select id, collection_id, position, properties from blocks where workspace_id = %s "
                      "and block_type = 'record' and deleted_at is null and collection_id = any(%s)",
                (ws, list(meta))).fetchall():
        ref, ai, ci, coll = meta[r['collection_id']]
        title = L.title_text(coll, r['properties'])
        if title:
            out.append({'id': str(r['id']), 'ref': ref, 'title': title, 'app_idx': ai, 'coll_idx': ci,
                        'position': r['position']})
    return out


def apply_text_links(conn: psycopg.Connection, ws: UUID, model, cmds: list, rows: dict[UUID, dict]) -> None:
    """On every insert and update that writes a text field: resolve each `[[Title]]` (same collection first, then the other
    collections in app order, first match wins; unresolved stays text) and put the recomputed `_links` into the same command.
    The `[[Title]]` links of the saved fields are replaced; hand-made links and the other fields' links stay."""
    candidates: list[dict] | None = None
    for c in cmds:
        if c.kind not in ('insert', 'update') or c.hop:
            continue
        defs = model.fields(c.collection_id)
        changed = [k for k, v in c.fields.items() if defs.get(k, {}).get('type') == 'text' and (v is None or isinstance(v, str))]
        if not changed:
            continue
        old = rows.get(c.record_id)
        existing = L.stored_links(old['properties']) if c.kind == 'update' and old else []
        titles = {k: L.wiki_titles(c.fields.get(k)) for k in changed}
        drops = any(e['source'] == 'text' and e.get('field_key') in changed for e in existing)
        if not drops and not any(titles.values()):
            continue
        found: dict[str, list[str]] = {}
        if any(titles.values()):
            if candidates is None:
                candidates = wiki_candidates(conn, ws, model)
            ref = model.ref(c.collection_id)
            for k, ts in titles.items():
                ids: list[str] = []
                for t in ts:
                    rid = L.resolve_wiki(t, ref, str(c.record_id), candidates)
                    if rid and rid not in ids:
                        ids.append(rid)
                found[k] = ids
        new = L.text_links(existing, changed, found)
        if new != existing:
            c.fields['_links'] = new or None
