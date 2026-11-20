"""Load a workspace's stored blocks into the shapes api/logic expects, and compute faces.

Pages hold the AppSpec minus collections; collection blocks hold one collection each; records
point at their collection (backend.md §2). `load()` joins them back: one AppSpec per app (with
`id` = the page block's UUID and `collections` inside), and every live record as
`{id, collection: "<app>/<coll>", properties, position, version}`.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from .logic import formula, instruments
from .logic import links as link_logic
from .logic.clock import now as clock_now
from .settings import settings


@dataclass
class Loaded:
    workspace_id: UUID
    tz: str
    epoch: int
    settings: dict
    now: datetime
    apps: list[dict]                          # AppSpecs, in page order
    records: list[dict]
    page_ids: dict[str, str] = field(default_factory=dict)       # app key -> page id
    collection_ids: dict[str, str] = field(default_factory=dict)  # "app/coll" -> collection block id
    seq: int = 0
    tomb: dict[str, dict] = field(default_factory=dict)          # link targets no longer live: id -> {app, ref}

    _ctx: Any = None

    @property
    def ctx(self) -> formula.Ctx:
        if self._ctx is None:
            self._ctx = formula.Ctx(self.apps, self.records, now=self.now, tz=self.tz)
        return self._ctx

    def app(self, id_or_key: str) -> dict | None:
        for a in self.apps:
            if a['id'] == id_or_key or a['key'] == id_or_key:
                return a
        return None


def load(conn, workspace_id) -> Loaded:
    w = conn.execute('select tz, epoch, settings from workspaces where id = %s', (workspace_id,)).fetchone()
    rows = conn.execute(
        'select id, parent_id, collection_id, block_type, position, version, properties from blocks '
        'where workspace_id = %s and deleted_at is null order by position', (workspace_id,)).fetchall()
    seq = conn.execute('select coalesce(max(server_seq), 0) as s from events where workspace_id = %s',
                       (workspace_id,)).fetchone()['s']
    pages = [r for r in rows if r['block_type'] == 'page']
    colls = [r for r in rows if r['block_type'] == 'collection']
    app_of_page = {r['id']: r['properties']['key'] for r in pages}
    ref_of_coll = {r['id']: f"{app_of_page.get(r['parent_id'])}/{r['properties']['key']}" for r in colls}

    apps = []
    for p in pages:
        spec = dict(p['properties'])
        spec['id'] = str(p['id'])
        spec['version'] = p['version']
        spec['collections'] = [dict(c['properties'], id=str(c['id'])) for c in colls if c['parent_id'] == p['id']]
        apps.append(spec)
    records = [{'id': str(r['id']), 'collection': ref_of_coll[r['collection_id']], 'properties': r['properties'],
                'position': r['position'], 'version': r['version']}
               for r in rows if r['block_type'] == 'record' and r['collection_id'] in ref_of_coll]
    tz = w['tz']
    # a hand-made or `[[Title]]` link to a record that is gone still shows, as "(deleted)" (backend.md edge case 55)
    gone = link_logic.dangling_targets(records)
    tomb = {i: {'app': t['app'], 'ref': t['ref']} for i, t in lookup_records(conn, workspace_id, gone).items()} if gone else {}
    return Loaded(workspace_id=workspace_id, tz=tz, epoch=w['epoch'], settings=w['settings'] or {},
                  now=clock_now(tz, settings().demo_now), apps=apps, records=records,
                  page_ids={a['key']: a['id'] for a in apps},
                  collection_ids={ref: str(cid) for cid, ref in ref_of_coll.items()}, seq=seq, tomb=tomb)


def lookup_records(conn, workspace_id, ids) -> dict[str, dict]:
    """`{id: {app, ref, title, deleted}}` for these records of the workspace, live or not (one query; ids of other workspaces
    and of blocks that are not records are simply absent). `title` is the record's own title text ("" if it has none)."""
    uuids = []
    for i in ids:
        try:
            uuids.append(UUID(str(i)))
        except ValueError:
            continue
    if not uuids:
        return {}
    rows = conn.execute(
        'select b.id, b.properties, b.deleted_at, c.properties as cprops, c.deleted_at as cdel, p.properties as pprops, '
        'p.deleted_at as pdel from blocks b join blocks c on c.id = b.collection_id '
        'join blocks p on p.id = c.parent_id where b.workspace_id = %s and b.block_type = %s and b.id = any(%s)',
        (workspace_id, 'record', uuids)).fetchall()
    out = {}
    for r in rows:
        key = r['pprops'].get('key')
        out[str(r['id'])] = {
            'app': key, 'ref': f"{key}/{r['cprops'].get('key')}", 'title': link_logic.title_text(r['cprops'], r['properties']),
            'deleted': bool(r['deleted_at'] or r['cdel'] or r['pdel']), 'private': link_logic.is_private(r['pprops'])}
    return out


def faces(ld: Loaded, app_keys: list[str] | None = None) -> dict[str, dict]:
    """`{app key: {text, label, value?}}` for the given apps (all if None)."""
    keys = app_keys if app_keys is not None else [a['key'] for a in ld.apps]
    out = {}
    for k in keys:
        a = ld.app(k)
        if a is not None:
            out[k] = formula.face(a, ld.ctx)
    return out


def values(ld: Loaded, app: dict) -> dict:
    return instruments.values(app, ld.ctx)


def status(ld: Loaded, app: dict) -> str | None:
    return instruments.status(app, ld.ctx)


def compute_faces(conn, workspace_id, app_ids) -> dict:
    """The command service's hook: faces of the apps a change touched, keyed by app key."""
    ld = load(conn, workspace_id)
    wanted = []
    for x in app_ids or []:
        a = ld.app(str(x))
        if a is not None:
            wanted.append(a['key'])
    return faces(ld, wanted)


def wire_blocks(conn, workspace_id, blocks: list[dict]) -> list[dict]:
    """Blocks of a command result or of `/sync` with their stored `_links` turned into `LinkRef`s (api/logic/links.py), one
    query for all of them. Blocks with no `_links` pass through; `_backlinks` come only with `GET /apps/{id}`."""
    ids: set[str] = set()
    for b in blocks:
        if b.get('block_type') == 'record' and (b.get('properties') or {}).get('_links'):
            ids |= {e['id'] for e in link_logic.stored_links(b['properties'])}
    if not ids:
        return blocks
    info = lookup_records(conn, workspace_id, ids)
    out = []
    for b in blocks:
        props = b.get('properties') or {}
        if b.get('block_type') != 'record' or not props.get('_links'):
            out.append(b)
            continue
        refs = []
        for e in link_logic.ordered_links(link_logic.stored_links(props)):
            t = info.get(e['id'])
            if t:
                refs.append({'app': t['app'], 'ref': t['ref'], 'id': e['id'],
                             'title': link_logic.DELETED if t['deleted'] else (t['title'] or link_logic.UNTITLED)})
        out.append({**b, 'properties': {**props, '_links': refs}})
    return out
