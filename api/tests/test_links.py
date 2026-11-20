"""Search and links (spec/backend.md sections 2, 5, 10): the pure logic, the op and spec rules, and the routes against
throwaway workspaces.

The first half needs no database. The second half (marker `integration`) builds two workspaces named 'test-<uuid>' from the
canonical seed, drives the real app through a TestClient signed in as a stand-in member of the first, and cascades both away at
the end. It never touches the demo workspace.
"""
import copy
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from api import models as m  # noqa: E402
from api.commands.ops import CoerceError, CommandError, coerce_value, parse_ops  # noqa: E402
from api.logic import links as L  # noqa: E402
from api.seed import data  # noqa: E402
from api.seed.load import build_blocks  # noqa: E402

TZ = 'America/Denver'
WS0 = uuid.UUID('00000000-0000-4000-8000-000000000001')
TODAY = datetime.fromisoformat(data.DEMO_NOW).date()


# ---------------------------------------------------------------- the canonical seed, as logic sees it

def seeded(ws=WS0):
    blocks = build_blocks(ws)
    pages = [b for b in blocks if b['block_type'] == 'page']
    colls = [b for b in blocks if b['block_type'] == 'collection']
    key_of = {p['id']: p['properties']['key'] for p in pages}
    ref_of = {c['id']: f"{key_of[c['parent_id']]}/{c['properties']['key']}" for c in colls}
    apps = []
    for p in pages:
        spec = dict(p['properties'], id=str(p['id']))
        spec['collections'] = [dict(c['properties'], id=str(c['id'])) for c in colls if c['parent_id'] == p['id']]
        apps.append(spec)
    records = [{'id': str(b['id']), 'collection': ref_of[b['collection_id']], 'properties': b['properties'],
                'position': b['position']} for b in blocks if b['block_type'] == 'record']
    return apps, records


def rid(ref, key, ws=WS0):
    from api.seed.load import block_id
    return str(block_id(ws, f'{ref}/{key}'))


def coll_of(apps, ref):
    app, _, ckey = ref.partition('/')
    return next(c for a in apps if a['key'] == app for c in a['collections'] if c['key'] == ckey)


# ---------------------------------------------------------------- text, queries, ranking

def test_wiki_titles():
    assert L.wiki_titles('see [[Chain rule recap]] and [[  chain RULE recap ]] and [[Other]]') == ['Chain rule recap', 'Other']
    assert L.wiki_titles('no links, a [single] bracket, an [[ ]] empty one and [[unclosed') == []
    assert L.wiki_titles('[[a\nb]] is not a title but [[b]] is') == ['b']
    assert L.wiki_titles(None) == [] and L.wiki_titles(5) == []
    many = ' '.join(f'[[t{i}]]' for i in range(200))
    assert len(L.wiki_titles(many)) == L.MAX_WIKI
    assert len(L.wiki_titles('[[' + 'x' * 300 + ']]')) == 0, 'a title is at most 200 characters'


def test_like_pattern_escapes_wildcards():
    assert L.like_pattern('50%_off') == '%50\\%\\_off%'
    assert L.like_pattern('a\\b') == '%a\\\\b%'
    assert L.like_pattern('plain') == '%plain%'


def test_clean_query():
    assert L.clean_query('  cafe rio  ') == 'cafe rio'
    assert L.clean_query('a\x00b') == 'ab', 'Postgres refuses NUL in text'
    assert len(L.clean_query('x' * 1000)) == L.MAX_QUERY
    assert L.clean_query(None) == ''


def test_rank():
    assert L.rank('Chain rule recap', 'chain') == 0
    assert L.rank('Chain rule recap', 'RULE') == 1
    assert L.rank('Price elasticity', 'last') == 2 and L.rank('Price elasticity', 'zzz') is None
    assert L.rank('Anything', '') == 0
    assert L.rank('Café', 'cafe') is None and L.rank('Café', 'café') == 0
    assert L.rank('Re-roof', 'roof') == 1, 'a word after a hyphen starts a word'


def test_interleave_takes_turns_across_apps():
    rows = [{'id': f'{a}{i}', 'app': a} for a, n in (('x', 5), ('y', 2), ('z', 1)) for i in range(n)]
    rows.sort(key=lambda r: (r['id'][1], r['id'][0]))     # recency order: round-robin input, apps tied
    out = [r['id'] for r in L.interleave(rows, 5)]
    assert out == ['x0', 'y0', 'z0', 'x1', 'y1']
    assert len({r['app'] for r in L.interleave(rows, 3)}) == 3
    assert L.interleave(rows, 0) == []


# ---------------------------------------------------------------- snippets tell rows with the same title apart

def test_snippets_disambiguate_the_cafe_rio_rows():
    apps, records = seeded()
    spend = coll_of(apps, 'budget/spend')
    cafe = [r for r in records if r['collection'] == 'budget/spend' and r['properties'].get('note') == 'Cafe Rio']
    assert len(cafe) >= 3, 'the seed has several Cafe Rio spends'
    snips = [L.snippet(spend, r['properties'], TZ, TODAY) for r in cafe]
    assert len(set(snips)) == len(snips), snips
    assert all(s.startswith('$') and ' · ' in s for s in snips)
    first = next(r for r in records if r['id'] == rid('budget/spend', 'sp_02'))
    assert L.snippet(spend, first['properties'], TZ, TODAY) == '$11.48 · Sun 1 Nov'


def test_snippets_by_kind_of_record():
    apps, records = seeded()
    by = {r['id']: r for r in records}
    note = by[rid('notes/notes', 'n_di')]
    assert L.snippet(coll_of(apps, 'notes/notes'), note['properties'], TZ, TODAY).startswith('Hand a class its dependencies')
    todo = by[rid('todos/todos', 't_library')]
    assert L.snippet(coll_of(apps, 'todos/todos'), todo['properties'], TZ, TODAY) == 'Fri 20 Nov · 9:00 pm · Marriott Library'
    item = by[rid('groceries/items', 'i_eggs')]
    assert L.snippet(coll_of(apps, 'groceries/items'), item['properties'], TZ, TODAY) == 'Weekly shop · To buy'
    notebook = by[rid('notes/notebooks', 'nb_personal')]
    assert L.snippet(coll_of(apps, 'notes/notebooks'), notebook['properties'], TZ, TODAY) == 'Notebooks'
    long = {'fields': [{'key': 't', 'type': 'text'}, {'key': 'b', 'type': 'text', 'multiline': True}], 'titleField': 't'}
    assert len(L.snippet(long, {'t': 'x', 'b': 'word ' * 100}, TZ, TODAY)) <= L.SNIPPET_MAX
    assert L.excerpt('a ' * 60 + 'needle in a haystack ' + 'b ' * 60, 'needle').count('needle') == 1


def test_titles_never_come_from_relations():
    apps, records = seeded()
    sets = coll_of(apps, 'workout/sets')
    assert not L.titled(sets), 'a set is titled by its exercise: not a title to search or to match a [[Title]]'
    assert L.titled(coll_of(apps, 'notes/notes'))
    index = L.LinkIndex(apps, records)
    s = next(r for r in records if r['collection'] == 'workout/sets')
    assert index.title(s['id']) not in ('', None) and index.title(s['id']) != L.UNTITLED, 'a set shows its exercise'


# ---------------------------------------------------------------- stored links

def test_stored_links_are_cleaned():
    props = {'_links': [{'id': 'a', 'source': 'text', 'field_key': 'body'}, {'id': 'a'}, 'junk', {'id': 'b', 'source': 'nope'},
                        {'id': 'c', 'source': 'text'}]}
    assert L.stored_links(props) == [{'id': 'a', 'source': 'text', 'field_key': 'body'}, {'id': 'b', 'source': 'manual'},
                                     {'id': 'c', 'source': 'text'}]
    assert L.stored_links({}) == [] and L.stored_links(None) == []


def test_link_add_remove_and_one_link_per_pair():
    a = L.add_manual([], 'x')
    assert a == [{'id': 'x', 'source': 'manual'}]
    assert L.add_manual(a, 'x') == a, 'a repeat is a no-op'
    t = [{'id': 'x', 'source': 'text', 'field_key': 'body'}]
    assert L.add_manual(t, 'x') == t, 'already linked by a [[Title]]: stays as it was'
    assert L.remove_link(a + [{'id': 'y', 'source': 'manual'}], 'x') == [{'id': 'y', 'source': 'manual'}]
    assert L.remove_link(a, 'zzz') == a


def test_text_links_replace_only_their_own_field():
    old = [{'id': 'm', 'source': 'manual'}, {'id': 't1', 'source': 'text', 'field_key': 'body'},
           {'id': 't2', 'source': 'text', 'field_key': 'summary'}]
    new = L.text_links(old, ['body'], {'body': ['t3', 'm']})
    assert new == [{'id': 'm', 'source': 'manual'}, {'id': 't2', 'source': 'text', 'field_key': 'summary'},
                   {'id': 't3', 'source': 'text', 'field_key': 'body'}], 'hand-made and other fields stay; m is not doubled'
    assert L.text_links(old, ['body'], {}) == [old[0], old[2]], 'a [[Title]] removed from the text removes its link'
    assert L.text_links(old, ['title'], {'title': ['q']})[-1] == {'id': 'q', 'source': 'text', 'field_key': 'title'}


def test_resolve_wiki_prefers_the_same_collection_then_app_order():
    cands = [
        {'id': 'n1', 'ref': 'notes/notes', 'title': 'Chain rule recap', 'app_idx': 0, 'coll_idx': 1, 'position': 'a1'},
        {'id': 'n2', 'ref': 'notes/notes', 'title': 'chain  RULE recap', 'app_idx': 0, 'coll_idx': 1, 'position': 'a2'},
        {'id': 't1', 'ref': 'todos/todos', 'title': 'Chain rule recap', 'app_idx': 5, 'coll_idx': 0, 'position': 'a0'},
        {'id': 'b1', 'ref': 'budget/spend', 'title': 'Chain rule recap', 'app_idx': 1, 'coll_idx': 0, 'position': 'a0'},
    ]
    assert L.resolve_wiki('Chain rule recap', 'notes/notes', 'zz', cands) == 'n1', 'same collection, first by position'
    assert L.resolve_wiki('chain rule recap', 'todos/todos', 'zz', cands) == 't1', "the record's own collection first"
    assert L.resolve_wiki('chain rule recap', 'classes/due', 'zz', cands) == 'n1', 'then app order'
    assert L.resolve_wiki('Chain rule recap', 'notes/notes', 'n1', cands) == 'n2', 'never itself'
    assert L.resolve_wiki('nothing like it', 'notes/notes', 'zz', cands) is None


# ---------------------------------------------------------------- the seed's links

def test_seed_text_links_agree_with_what_the_server_would_store():
    apps, records = seeded()
    cands = []
    for ai, a in enumerate(apps):
        for ci, c in enumerate(a['collections']):
            if not L.titled(c):
                continue
            for r in records:
                if r['collection'] == f"{a['key']}/{c['key']}" and L.title_text(c, r['properties']):
                    cands.append({'id': r['id'], 'ref': r['collection'], 'title': L.title_text(c, r['properties']),
                                  'app_idx': ai, 'coll_idx': ci, 'position': r['position']})
    found = 0
    for r in records:
        coll = coll_of(apps, r['collection'])
        stored = [e for e in L.stored_links(r['properties']) if e['source'] == 'text']
        recomputed = []
        for f in coll['fields']:
            if f['type'] != 'text':
                continue
            for t in L.wiki_titles(r['properties'].get(f['key'])):
                tid = L.resolve_wiki(t, r['collection'], r['id'], cands)
                if tid:
                    recomputed.append({'id': tid, 'source': 'text', 'field_key': f['key']})
        assert stored == recomputed, r['properties'].get('title')
        found += len(stored)
    assert found == 3, 'three [[wikilinks]] in the seeded bodies (backend.md section 2.3)'


def test_seed_links_match_the_spec_list():
    apps, records = seeded()
    index = L.LinkIndex(apps, records)
    title = index.title
    out = {title(r['id']): [(x['title'], x['app']) for x in index.links(r['id'])] for r in records if index.links(r['id'])}
    assert out == {
        'Related rates examples': [('Chain rule recap', 'notes')],
        'Finals study plan': [('Homework 11', 'classes'), ('Related rates examples', 'notes')],   # by hand first, then text
        'Gift ideas for mom': [('Thrift shop', 'budget')],
        'Dependency injection': [('Unit testing with mocks', 'notes')],
        'Return library books': [('ECON 1010', 'classes')],
        'Call home': [('Gift ideas for mom', 'notes')],
        'Chicken thighs': [('Chicken and rice', 'notes')],
    }


def test_seed_backlinks_and_relation_backlinks():
    apps, records = seeded()
    index = L.LinkIndex(apps, records)
    nb = {n: [(x['title'], x.get('via')) for x in index.backlinks(rid('notes/notebooks', k))]
          for n, k in (('math', 'nb_math'), ('econ', 'nb_econ'), ('cs', 'nb_cs3500'), ('personal', 'nb_personal'))}
    assert [len(nb[k]) for k in ('math', 'econ', 'cs', 'personal')] == [3, 2, 2, 2], 'notes per notebook (n_finals is in two)'
    assert all(via == 'notebook' for rows in nb.values() for _, via in rows)
    assert nb['math'] == [('Related rates examples', 'notebook'), ('Chain rule recap', 'notebook'), ('Finals study plan', 'notebook')]
    econ = {(x['title'], x.get('via')) for x in index.backlinks(rid('classes/classes', 'c01'))}
    assert econ == {('ECON 1010', 'class'), ('Return library books', None)}, 'the notebook by relation, the to-do by link'
    hw = index.backlinks(rid('classes/due', 'd02'))
    assert [(x['title'], x['app'], x.get('via')) for x in hw] == [('Finals study plan', 'notes', None)]
    gift = [x['title'] for x in index.backlinks(rid('notes/notes', 'n_gift_ideas'))]
    assert gift == ['Call home'], 'the to-do links to the note'
    assert index.backlinks(rid('budget/spend', 'sp_01')) == []


def test_a_deleted_target_stays_in_links_as_deleted():
    apps, records = seeded()
    gone = rid('notes/notes', 'n_chain_rule')
    live = [r for r in records if r['id'] != gone]
    index = L.LinkIndex(apps, live, tomb={gone: {'app': 'notes', 'ref': 'notes/notes'}})
    assert index.links(rid('notes/notes', 'n_related_rates')) == [
        {'app': 'notes', 'ref': 'notes/notes', 'id': gone, 'title': '(deleted)'}]
    assert L.dangling_targets(live) == {gone}
    assert L.dangling_targets(records) == set()
    unknown = L.LinkIndex(apps, live)           # no tombstone known: the link is left out, not invented
    assert unknown.links(rid('notes/notes', 'n_related_rates')) == []


def test_link_refs_match_the_contract_model():
    apps, records = seeded()
    index = L.LinkIndex(apps, records)
    for r in records:
        for x in index.links(r['id']) + index.backlinks(r['id']):
            m.LinkRef.model_validate(x)
    props = L.wire_record(index, rid('notes/notes', 'n_finals'), next(r for r in records if r['id'] == rid('notes/notes', 'n_finals'))['properties'])
    assert set(props) >= {'_links', '_backlinks', 'title', 'body', 'notebook'} and isinstance(props['_links'][0], dict)
    assert 'source' not in props['_links'][0], 'the stored form (source, field_key) never goes on the wire'


# ---------------------------------------------------------------- ops, coercion and spec rules

def test_link_ops_parse_and_reject_bad_shapes():
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    ops = parse_ops([{'op': 'link', 'record_id': a, 'target_id': b}, {'op': 'unlink', 'record_id': a, 'target_id': b}])
    assert [o.op for o in ops] == ['link', 'unlink']
    for bad in ({'op': 'link', 'record_id': a}, {'op': 'link', 'target_id': b}, {'op': 'link', 'record_id': a, 'target_id': 'x'},
                {'op': 'link', 'record_id': a, 'target_id': b, 'fields': {'x': 1}},
                {'op': 'update', 'record_id': a, 'target_id': b, 'fields': {'x': 1}}):
        with pytest.raises(CommandError):
            parse_ops([bad])


@pytest.mark.parametrize('key', ['_links', '_backlinks', '_via'])
def test_reserved_keys_are_never_written(key):
    with pytest.raises(CommandError) as e:
        parse_ops([{'op': 'update', 'record_id': str(uuid.uuid4()), 'fields': {key: []}}])
    assert e.value.status == 422
    with pytest.raises(CommandError):
        parse_ops([{'op': 'insert', 'collection_id': str(uuid.uuid4()), 'fields': {'title': 'x', key: []}}])


def test_relation_values_one_many_and_clear():
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    one, many = {'type': 'relation', 'target': 'x/y'}, {'type': 'relation', 'target': 'x/y', 'many': True}
    assert coerce_value(one, a, TZ) == [a] and coerce_value(one, [a], TZ) == [a]
    assert coerce_value(many, [a, b, a], TZ) == [a, b], 'one link per target'
    with pytest.raises(CoerceError):
        coerce_value(one, [a, b], TZ)
    assert coerce_value(many, [], TZ) is None and coerce_value(one, [], TZ) is None, 'clearing the last one clears it'
    assert coerce_value(many, None, TZ) is None


def test_app_specs_accept_many_and_multiline():
    from api.commands.apps import validate_app
    from api.commands.service import Model
    from api.seed.load import load_template
    model = Model(ws=uuid.uuid4(), tz=TZ)
    spec = load_template('notes')
    spec['collections'][0]['fields'][1]['target'] = 'notes/notebooks'
    out = validate_app(model, spec, new=True)['spec']
    fields = {f['key']: f for f in out['collections'][1]['fields']}
    assert fields['notebook']['many'] is True and fields['body']['multiline'] is True
    assert out['tabs'][0]['children'][0]['kind'] == 'notebook'
    bad = copy.deepcopy(spec)
    bad['collections'][1]['fields'][0]['many'] = True
    bad['collections'][1]['fields'][2]['multiline'] = True
    with pytest.raises(CommandError) as e:
        validate_app(model, bad, new=True)
    assert len(e.value.body['issues']) == 2


def test_the_notes_template_is_the_workspace():
    from api.seed.load import load_template
    spec = load_template('notes')
    notes = next(c for c in spec['collections'] if c['key'] == 'notes')
    f = {x['key']: x for x in notes['fields']}
    assert f['notebook'].get('many') is True and f['body'].get('multiline') is True
    assert [t['id'] for t in spec['tabs']] == ['t_notes']
    assert spec['tabs'][0]['children'] == [{'kind': 'notebook', 'id': 'b_notebook', 'source': 'notes/notebooks',
                                            'pages': 'notes/notes', 'link': 'notebook', 'body': 'body'}]


def test_search_models_are_the_clients_shape():
    now = datetime.now(timezone.utc)
    hit = m.SearchHit(app='budget', ref='budget/spend', collection='spend', id='x', title='Cafe Rio', snippet='$11.48 · Sun 1 Nov', updated=now)
    assert m.SearchResponse(hits=[hit]).model_dump(mode='json')['hits'][0]['ref'] == 'budget/spend'
    assert m.LinkCreate(to=m.LinkTarget(ref='a/b', id='x')).to.id == 'x' and m.LinkCreate(target_id='x').target_id == 'x'


# ================================================================ integration: throwaway workspaces

def _db_ok() -> bool:
    try:
        from api.settings import settings
        return bool(settings().database_url)
    except Exception:
        return False


def integ(fn):
    return pytest.mark.integration(pytest.mark.skipif(not _db_ok(), reason='no DATABASE_URL')(fn))


@pytest.fixture(scope='module')
def env():
    from psycopg.types.json import Jsonb

    from api.db import connect
    from api.index import app
    from api.auth import Member, User, current_member
    from fastapi.testclient import TestClient

    made = []
    with connect() as conn:
        stand_in = conn.execute('select user_id from workspace_members limit 1').fetchone()   # a real user id, for the FK
        for _ in range(2):
            ws = conn.execute('insert into workspaces (name, tz, settings) values (%s, %s, %s) returning id',
                              (f'test-{uuid.uuid4()}', TZ, Jsonb({}))).fetchone()['id']
            made.append(ws)
        conn.commit()
    try:
        with connect() as conn:
            for ws in made:
                blocks = build_blocks(ws)
                with conn.cursor() as cur:
                    cur.executemany(
                        'insert into blocks (id, workspace_id, parent_id, position, block_type, collection_id, properties) '
                        'values (%s, %s, %s, %s, %s, %s, %s)',
                        [(b['id'], ws, b['parent_id'], b['position'], b['block_type'], b['collection_id'], Jsonb(b['properties']))
                         for b in blocks])
            conn.commit()
        ws0, ws1 = made
        app.dependency_overrides[current_member] = lambda: Member(user=User(id=stand_in['user_id'], is_anonymous=False, email=None),
                                                                  workspace_id=ws0, tz=TZ)
        with TestClient(app) as client:
            yield {'ws': ws0, 'other': ws1, 'client': client}
    finally:
        app.dependency_overrides.pop(current_member, None)
        with connect() as conn:
            conn.execute('delete from workspaces where id = any(%s) and name like %s', (made, 'test-%'))
            conn.commit()


def R(env, ref, key, ws=None):
    return rid(ref, key, ws or env['ws'])


def get_app(env, key):
    r = env['client'].get(f'/api/apps/{key}')
    assert r.status_code == 200, r.text
    return r.json()


def rec(env, app, ref, key):
    want = R(env, ref, key)
    return next(r for r in get_app(env, app)['data'][ref] if r['id'] == want)


def search(env, **params):
    r = env['client'].get('/api/search', params=params)
    assert r.status_code == 200, r.text
    return r.json()['hits']


def events(env, block_id):
    from api.db import connect
    with connect() as conn:
        return conn.execute('select field_path, old, new, change_set_id from events where block_id = %s order by server_seq',
                            (uuid.UUID(block_id),)).fetchall()


# ---------------------------------------------------------------- search

@integ
def test_search_suggested_is_interleaved_across_apps(env):
    hits = search(env)
    assert len(hits) == 20
    apps = [h['app'] for h in hits]
    assert len(set(apps)) >= 10, f'one app must not fill the list: {apps}'
    assert apps[:11] == list(dict.fromkeys(apps))[:11], 'the first round is one hit from each app'
    assert 'cycle' not in apps, 'Cycle is private: never suggested'
    for h in hits:
        m.SearchHit.model_validate(h)
        assert h['title'] and h['snippet'] is not None and h['ref'].startswith(h['app'] + '/')
    assert len({h['id'] for h in hits}) == 20


@integ
def test_search_ranks_prefix_then_word_start_then_the_rest(env):
    hits = search(env, q='chain')
    assert hits and hits[0]['title'] == 'Chain rule recap' and hits[0]['app'] == 'notes'
    titles = [h['title'] for h in hits]
    assert 'chain' in titles[0].lower()
    low = search(env, q='CHAIN RULE')
    assert [h['id'] for h in low][:1] == [hits[0]['id']], 'case-insensitive'
    ranks = [L.rank(h['title'], 'e') if L.rank(h['title'], 'e') is not None else 3 for h in search(env, q='e', limit=50)]
    assert ranks == sorted(ranks), 'prefix matches, then word starts, then the rest'


@integ
def test_search_snippets_tell_the_cafe_rio_rows_apart(env):
    hits = [h for h in search(env, q='cafe rio') if h['title'] == 'Cafe Rio']
    assert len(hits) >= 3 and len({h['snippet'] for h in hits}) == len(hits), hits
    assert all(h['app'] == 'budget' and h['snippet'].startswith('$') for h in hits)


@integ
def test_search_also_finds_text_in_a_body_and_shows_where(env):
    hits = search(env, q='thrift shop')
    by = {h['title']: h for h in hits}
    assert 'Thrift shop' in by and by['Thrift shop']['app'] == 'budget', 'the title match'
    assert 'Gift ideas for mom' in by, 'its body says "found one at the thrift shop"'
    assert 'thrift shop' in by['Gift ideas for mom']['snippet'].lower()
    assert hits.index(by['Thrift shop']) < hits.index(by['Gift ideas for mom']), 'a title match outranks a body match'


@integ
def test_search_wildcards_are_literal_and_odd_queries_are_safe(env):
    assert search(env, q='%') == [] and search(env, q='_') == [] and search(env, q='\\') == []
    assert search(env, q="x'; drop table blocks; --") == []
    assert search(env, q='Cafe_Rio') == [], '_ is not "any character"'
    assert len(search(env, q='a' * 5000)) == 0
    assert env['client'].get('/api/search', params={'q': 'a\x00b'}).status_code == 200
    assert len(search(env, q='   ')) == 20, 'blank is Suggested'
    assert env['client'].get('/api/search', params={'q': 'a', 'limit': 51}).status_code == 422
    assert env['client'].get('/api/search', params={'q': 'a', 'limit': 0}).status_code == 422
    assert len(search(env, q='a', limit=3)) == 3


@integ
def test_search_exclude_app_and_private(env):
    me = R(env, 'notes/notes', 'n_chain_rule')
    assert me not in [h['id'] for h in search(env, q='chain', exclude=me)]
    two = [R(env, 'notes/notes', 'n_chain_rule'), R(env, 'notes/notes', 'n_finals')]
    got = {h['id'] for h in env['client'].get('/api/search', params=[('q', 'e'), ('exclude', two[0]), ('exclude', two[1]),
                                                                 ('exclude', 'not-a-uuid'), ('limit', 50)]).json()['hits']}
    assert not got & set(two)
    only = search(env, q='e', app='budget', limit=50)
    assert only and {h['app'] for h in only} == {'budget'}
    assert search(env, app='no_such_app') == []
    # Cycle is private: not suggested, not found by its dates, not even when named
    cycle_day = R(env, 'cycle/days', next(k for k, _ in data.records()['cycle']['days']))
    assert cycle_day not in [h['id'] for h in search(env, limit=50)]
    assert search(env, q='2026', app='cycle', limit=50) == []
    assert all(h['app'] != 'cycle' for h in search(env, q='2026', limit=50))


@integ
def test_search_never_crosses_workspaces_or_returns_deleted_rows(env):
    other_ids = {rid(r['collection'], k, env['other']) for k in ('n_chain_rule',) for r in [{'collection': 'notes/notes'}]}
    mine = search(env, q='chain rule', limit=50)
    assert mine and not {h['id'] for h in mine} & other_ids, "another workspace's rows are never returned"
    assert mine[0]['id'] == rid('notes/notes', 'n_chain_rule', env['ws']), 'the title match first; notes that mention it follow'
    victim = R(env, 'notes/notes', 'n_gift_ideas')
    assert victim in [h['id'] for h in search(env, q='gift ideas')]
    d = env['client'].delete(f'/api/records/{victim}')
    assert d.status_code == 200
    assert victim not in [h['id'] for h in search(env, q='gift ideas')], 'a deleted row is not searched'
    assert victim not in [h['id'] for h in search(env, limit=50)], 'nor suggested'
    assert env['client'].post(f"/api/change-sets/{d.json()['change_set_id']}/undo").status_code == 200   # back for the later tests
    assert victim in [h['id'] for h in search(env, q='gift ideas')]


# ---------------------------------------------------------------- links on every record

@integ
def test_every_record_carries_links_and_backlinks(env):
    notes = get_app(env, 'notes')
    for ref, rows in notes['data'].items():
        for r in rows:
            assert isinstance(r['properties']['_links'], list) and isinstance(r['properties']['_backlinks'], list), ref
            for x in r['properties']['_links'] + r['properties']['_backlinks']:
                m.LinkRef.model_validate(x)
    finals = rec(env, 'notes', 'notes/notes', 'n_finals')['properties']
    assert [(x['title'], x['app']) for x in finals['_links']] == [('Homework 11', 'classes'), ('Related rates examples', 'notes')]
    assert 'source' not in finals['_links'][0]
    assert finals['notebook'] == [R(env, 'notes/notebooks', 'nb_math'), R(env, 'notes/notebooks', 'nb_econ')], 'a relation stays ids'
    math = rec(env, 'notes', 'notes/notebooks', 'nb_math')['properties']['_backlinks']
    assert [(x['title'], x['via']) for x in math] == [('Related rates examples', 'notebook'), ('Chain rule recap', 'notebook'),
                                                       ('Finals study plan', 'notebook')]
    # the Class field points into another app: those rows ride along
    assert 'classes/classes' in notes['data'] and len(notes['data']['classes/classes']) == 3
    assert 'cycle/days' not in get_app(env, 'todos')['data']
    # the other end of a link made in another app
    classes = get_app(env, 'classes')
    hw = next(r for r in classes['data']['classes/due'] if r['id'] == R(env, 'classes/due', 'd02'))
    assert [(x['title'], x['app']) for x in hw['properties']['_backlinks']] == [('Finals study plan', 'notes')]
    # old sample rows aside, nothing else about the response moved
    assert notes['faces']['notes']['text'] == '3'


# ---------------------------------------------------------------- hand-made links

def link(env, a, b, **kw):
    return env['client'].post(f'/api/records/{a}/links', **({'json': {'to': {'ref': kw.get('ref'), 'id': b}}} if kw.get('ref') else {'json': {'target_id': b}}))


@integ
def test_link_then_undo_then_unlink(env):
    c = env['client']
    a, b = R(env, 'todos/todos', 't_maya'), R(env, 'budget/spend', 'sp_01')
    r = link(env, a, b, ref='budget/spend')                # the client's shape: {to: {ref, id}}
    assert r.status_code == 200, r.text
    res = m.CommandResult.model_validate(r.json())
    assert res.blocks and res.blocks[0].id == a
    assert [x['id'] for x in res.blocks[0].properties['_links']] == [b], 'the result block sends LinkRefs'
    assert 'source' not in res.blocks[0].properties['_links'][0]
    got = rec(env, 'todos', 'todos/todos', 't_maya')['properties']
    assert [(x['title'], x['app']) for x in got['_links']] == [('November rent', 'budget')]
    back = rec(env, 'budget', 'budget/spend', 'sp_01')['properties']['_backlinks']
    assert [(x['title'], x['app'], x.get('via')) for x in back] == [('Pay Maya back for pizza ($14)', 'todos', None)]
    ev = [e for e in events(env, a) if e['field_path'] == '_links']
    assert len(ev) == 1 and ev[0]['old'] is None and ev[0]['new'][0]['id'] == b, 'one event on the source record, field _links'
    # a second device sees it on its next sync, on the source record
    sync = c.get('/api/sync?since=0').json()
    blk = next(x for x in sync['blocks'] if x['id'] == a)
    assert blk['properties']['_links'][0]['title'] == 'November rent' and 'source' not in blk['properties']['_links'][0]
    # it is a change set like any other edit: listed with a title, by You, stitched at once (not a basted card)
    listed = c.get('/api/change-sets')
    assert listed.status_code == 200, listed.text
    mine = next(x for x in listed.json() if x['id'] == res.change_set_id)
    assert mine['status'] == 'stitched' and mine['title'] == 'Linked Pay Maya back for pizza ($14) to November rent'
    assert mine['source']['kind'] == 'gesture'
    # Undo reverses it (the toast's Undo is POST /change-sets/{id}/undo)
    assert c.post(f"/api/change-sets/{res.change_set_id}/undo").status_code == 200
    assert rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links'] == []
    assert rec(env, 'budget', 'budget/spend', 'sp_01')['properties']['_backlinks'] == []
    # link again, then unlink, then undo the unlink
    link(env, a, b)
    un = c.delete(f'/api/records/{a}/links/{b}')
    assert un.status_code == 200 and rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links'] == []
    assert c.post(f"/api/change-sets/{un.json()['change_set_id']}/undo").status_code == 200
    assert [x['id'] for x in rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links']] == [b]
    assert c.delete(f'/api/records/{a}/links/{b}').status_code == 200


@integ
def test_a_repeat_is_a_no_op_that_undo_does_nothing_for(env):
    c = env['client']
    a, b = R(env, 'todos/todos', 't_flu'), R(env, 'budget/spend', 'sp_02')
    first = link(env, a, b)
    n = len(events(env, a))
    again = link(env, a, b)
    assert again.status_code == 200 and again.json()['blocks'] == [], 'nothing written'
    assert len(events(env, a)) == n, 'no new event'
    assert [x['id'] for x in rec(env, 'todos', 'todos/todos', 't_flu')['properties']['_links']] == [b]
    assert c.post(f"/api/change-sets/{again.json()['change_set_id']}/undo").status_code == 200, 'Undo of a no-op is fine'
    assert [x['id'] for x in rec(env, 'todos', 'todos/todos', 't_flu')['properties']['_links']] == [b], 'and does nothing'
    assert first.status_code == 200
    # unlinking what is not linked is also a no-op
    assert c.delete(f'/api/records/{a}/links/{R(env, "budget/spend", "sp_03")}').status_code == 200
    assert c.delete(f'/api/records/{a}/links/{b}').status_code == 200


@integ
def test_links_the_service_refuses(env):
    c = env['client']
    a, b = R(env, 'todos/todos', 't_maya'), R(env, 'budget/spend', 'sp_01')
    self_ = link(env, a, a)
    assert self_.status_code == 422 and self_.json()['error'] == 'self_link'
    cycle = R(env, 'cycle/days', data.records()['cycle']['days'][0][0])
    priv = link(env, a, cycle)
    assert priv.status_code == 422 and priv.json()['error'] == 'private_target' and 'private' in priv.json()['issues'][0]['msg']
    assert link(env, a, str(uuid.uuid4())).status_code == 404, 'a missing record'
    assert link(env, str(uuid.uuid4()), b).status_code == 404
    assert link(env, a, 'not-an-id').status_code == 404
    foreign = rid('budget/spend', 'sp_01', env['other'])
    assert link(env, a, foreign).status_code == 404, "another workspace's record is not found (no leak)"
    assert link(env, foreign, b).status_code == 404
    assert c.delete(f'/api/records/{foreign}/links/{b}').status_code == 404
    wrong = c.post(f'/api/records/{a}/links', json={'to': {'ref': 'budget/spend', 'id': R(env, 'notes/notes', 'n_di')}})
    assert wrong.status_code == 422, 'the ref names another collection than the record is in'
    assert c.post(f'/api/records/{a}/links', json={}).status_code == 422
    assert c.post(f'/api/records/{a}/links', json={'to': {'id': a}, 'target_id': b}).status_code == 422
    # a deleted record is missing; a link to a deleted record stays as "(deleted)" and can be unlinked
    gone = R(env, 'groceries/items', 'i_limes')
    link(env, a, gone)
    assert c.delete(f'/api/records/{gone}').status_code == 200
    shown = rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links']
    assert shown == [{'app': 'groceries', 'ref': 'groceries/items', 'id': gone, 'title': '(deleted)'}]
    assert link(env, gone, b).status_code == 404, 'a deleted source is missing'
    assert link(env, a, gone).status_code == 404, 'and so is a deleted target'
    assert c.delete(f'/api/records/{a}/links/{gone}').status_code == 200
    assert rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links'] == []


@integ
def test_a_google_event_cannot_be_linked_from(env):
    from psycopg.types.json import Jsonb

    from api.db import connect
    events_coll = next(b for b in build_blocks(env['ws']) if b['block_type'] == 'collection' and b['properties']['key'] == 'events')
    gid = uuid.uuid4()
    with connect() as conn:
        conn.execute("insert into blocks (id, workspace_id, parent_id, position, block_type, collection_id, properties) "
                     "values (%s, %s, %s, 'zz', 'record', %s, %s)",
                     (gid, env['ws'], events_coll['id'], events_coll['id'],
                      Jsonb({'title': 'Dentist', 'at': '2026-11-24T07:30:00-07:00', 'source': 'google', 'ext_id': 'g1'})))
        conn.commit()
    b = R(env, 'budget/spend', 'sp_01')
    r = link(env, str(gid), b)
    assert r.status_code == 422 and r.json()['error'] == 'from_google'
    assert link(env, R(env, 'todos/todos', 't_maya'), str(gid)).status_code == 200, 'linking TO an imported event is fine'
    env['client'].delete(f"/api/records/{R(env, 'todos/todos', 't_maya')}/links/{gid}")


# ---------------------------------------------------------------- [[Title]] and relations on write

def note(env, title, body, notebook=None, **kw):
    fields = {'title': title, 'body': body, 'at': '2026-11-20T17:00:00-07:00'}
    if notebook is not None:
        fields['notebook'] = notebook
    r = env['client'].post('/api/records', json={'collection_id': 'notes/notes', 'fields': fields, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def note_props(env, bid):
    return next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == bid)['properties']


@integ
def test_wiki_titles_are_resolved_on_create_and_edit(env):
    c = env['client']
    created = note(env, 'Exam plan', 'Review [[Chain rule recap]], the [[Cafe Rio]] receipt, [[No such note]] and [[exam plan]].',
                   [R(env, 'notes/notebooks', 'nb_math')])
    nid = created['blocks'][0]['id']
    p = note_props(env, nid)
    assert [(x['title'], x['app']) for x in p['_links']] == [('Chain rule recap', 'notes'), ('Cafe Rio', 'budget')], \
        'same collection first, then other apps; unresolved and itself stay text'
    assert p['body'].startswith('Review [[Chain rule recap]]'), 'the text is saved as typed'
    assert [x['id'] for x in rec(env, 'notes', 'notes/notes', 'n_chain_rule')['properties']['_backlinks'] if x['id'] == nid], 'the other end'
    # hand-made link, then edit the body: [[Title]] links are recomputed, hand-made ones stay
    todo = R(env, 'todos/todos', 't_library')
    assert link(env, nid, todo).status_code == 200
    v = note_props(env, nid) and next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    e = c.patch(f'/api/records/{nid}', json={'fields': {'body': 'Now only [[Price elasticity]].'}, 'base_version': v})
    assert e.status_code == 200, e.text
    p = note_props(env, nid)
    assert [(x['title'], x['app']) for x in p['_links']] == [('Return library books', 'todos'), ('Price elasticity', 'notes')]
    # a PATCH of only the title keeps notebook and every link as they were
    v = next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    assert c.patch(f'/api/records/{nid}', json={'fields': {'title': 'Exam plan v2'}, 'base_version': v}).status_code == 200
    p2 = note_props(env, nid)
    assert p2['_links'] == p['_links'] and p2['notebook'] == [R(env, 'notes/notebooks', 'nb_math')]
    # unlink a [[Title]] link: it stays unlinked until that text is saved again with the [[Title]] in it
    assert c.delete(f"/api/records/{nid}/links/{R(env, 'notes/notes', 'n_elasticity')}").status_code == 200
    assert [x['title'] for x in note_props(env, nid)['_links']] == ['Return library books']
    v = next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    c.patch(f'/api/records/{nid}', json={'fields': {'title': 'Exam plan v3'}, 'base_version': v})
    assert [x['title'] for x in note_props(env, nid)['_links']] == ['Return library books'], 'a title save does not relink the body'
    v = next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    c.patch(f'/api/records/{nid}', json={'fields': {'body': 'Still [[Price elasticity]].'}, 'base_version': v})
    assert [x['title'] for x in note_props(env, nid)['_links']] == ['Return library books', 'Price elasticity']
    # one Undo reverts both the text and its links
    v = next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    ed = c.patch(f'/api/records/{nid}', json={'fields': {'body': 'Plain now.'}, 'base_version': v}).json()
    assert [x['title'] for x in note_props(env, nid)['_links']] == ['Return library books']
    assert c.post(f"/api/change-sets/{ed['change_set_id']}/undo").status_code == 200
    back = note_props(env, nid)
    assert back['body'] == 'Still [[Price elasticity]].' and [x['title'] for x in back['_links']] == ['Return library books', 'Price elasticity']
    # create-and-undo removes the record, and the other end loses its backlink
    assert c.post(f"/api/change-sets/{created['change_set_id']}/undo").status_code == 200
    assert nid not in [x['id'] for x in rec(env, 'notes', 'notes/notes', 'n_chain_rule')['properties']['_backlinks']]


@integ
def test_an_ambiguous_title_goes_to_the_same_collection_first(env):
    # "Cafe Rio" is also a Budget spend; a note titled the same wins from inside Notes
    twin = note(env, 'Cafe Rio', 'the note')['blocks'][0]['id']
    ref = note(env, 'Where I ate', 'See [[cafe  rio]].')['blocks'][0]['id']
    assert [(x['id'], x['app']) for x in note_props(env, ref)['_links']] == [(twin, 'notes')]
    # from To-dos there is no to-do of that name: the first app in order that has one, and Notes comes before Budget
    todo = R(env, 'todos/todos', 't_call_home')
    t = env['client'].patch(f'/api/records/{todo}', json={'fields': {'place': 'ask about [[Cafe Rio]]'}, 'base_version': 1})
    assert t.status_code == 200, t.text
    got = rec(env, 'todos', 'todos/todos', 't_call_home')['properties']['_links']
    assert got[-1]['id'] == twin and got[-1]['app'] == 'notes', 'the hand-made link to Gift ideas first, then the [[Cafe Rio]] one'
    assert [x['title'] for x in got] == ['Gift ideas for mom', 'Cafe Rio']


@integ
def test_reserved_keys_and_relation_values_on_write(env):
    c = env['client']
    nid = R(env, 'notes/notes', 'n_gift_ideas')
    v = next(r for r in get_app(env, 'notes')['data']['notes/notes'] if r['id'] == nid)['version']
    for key in ('_links', '_backlinks'):
        r = c.patch(f'/api/records/{nid}', json={'fields': {key: [{'id': R(env, 'budget/spend', 'sp_01')}]}, 'base_version': v})
        assert r.status_code == 422, (key, r.text)
        r = c.post('/api/records', json={'collection_id': 'notes/notes', 'fields': {'title': 'x', key: []}})
        assert r.status_code == 422, (key, r.text)
    # a `many` relation takes several ids, one id, or a one-element array; [] clears it
    nbs = [R(env, 'notes/notebooks', k) for k in ('nb_math', 'nb_econ')]
    for value, want in ((nbs, nbs), (nbs[0], nbs[:1]), ([nbs[1]], nbs[1:])):
        r = c.patch(f'/api/records/{nid}', json={'fields': {'notebook': value}, 'base_version': v})
        assert r.status_code == 200, r.text
        assert note_props(env, nid)['notebook'] == want
        v += 1
    assert c.patch(f'/api/records/{nid}', json={'fields': {'notebook': []}, 'base_version': v}).status_code == 200
    assert 'notebook' not in note_props(env, nid) or note_props(env, nid)['notebook'] in ([], None)
    # a single relation takes one record, not two
    due = R(env, 'classes/due', 'd01')
    bad = c.patch(f'/api/records/{due}', json={'fields': {'class': [R(env, 'classes/classes', 'c01'), R(env, 'classes/classes', 'c02')]},
                                              'base_version': 1})
    assert bad.status_code == 422 and bad.json()['issues'][0]['loc'] == ['class']
    ok = c.patch(f'/api/records/{due}', json={'fields': {'class': R(env, 'classes/classes', 'c01')}, 'base_version': 1})
    assert ok.status_code == 200
    # a relation to a record that is not in the target collection is refused
    assert c.patch(f'/api/records/{nid}', json={'fields': {'notebook': [R(env, 'budget/spend', 'sp_01')]},
                                                'base_version': v + 1}).status_code == 422


@integ
def test_a_deleted_app_takes_its_rows_out_of_search_and_leaves_links_as_deleted(env):
    """Last in the module: it removes the Groceries app from the throwaway workspace."""
    c = env['client']
    todo, item = R(env, 'todos/todos', 't_maya'), R(env, 'groceries/items', 'i_oat_milk')
    assert link(env, todo, item).status_code == 200
    assert item in [h['id'] for h in search(env, q='oat milk')]
    gone = c.delete('/api/apps/groceries?confirm=true')
    assert gone.status_code == 200, gone.text
    assert item not in [h['id'] for h in search(env, q='oat milk')], 'a deleted app is not searched'
    assert all(h['app'] != 'groceries' for h in search(env, limit=50))
    shown = rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links']
    assert shown == [{'app': 'groceries', 'ref': 'groceries/items', 'id': item, 'title': '(deleted)'}]
    assert c.post(f"/api/change-sets/{gone.json()['change_set_id']}/undo").status_code == 200
    assert [x['title'] for x in rec(env, 'todos', 'todos/todos', 't_maya')['properties']['_links']] == ['Oat milk']
    assert item in [h['id'] for h in search(env, q='oat milk')]
