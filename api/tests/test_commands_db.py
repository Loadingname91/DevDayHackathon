"""Integration tests for the command service against the live database (backend.md §5, §11, §13 check.py).

Each test module run creates one throwaway workspace named 'test-<uuid>' with small Groceries, Budget,
Calendar and Workout apps, and deletes it (cascade) at the end. Skipped without DATABASE_URL.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402


def _db_ok() -> bool:
    try:
        from api.settings import settings
        return bool(settings().database_url)
    except Exception:
        return bool(os.environ.get('DATABASE_URL'))


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _db_ok(), reason='no DATABASE_URL')]

from psycopg.types.json import Jsonb  # noqa: E402

TZ = 'America/Denver'
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']


def _page(key, name, stitches=None, tabs=None):
    return {'v': 1, 'key': key, 'name': name, 'icon': 'x', 'dye': 'sage', 'tabs': tabs or [],
            'face': {'value': 0, 'format': 'count', 'label': ''}, 'stitches': stitches or [], 'settings': {}}


SPECS = {
    'groceries': (_page('groceries', 'Groceries'), {
        'items': {'key': 'items', 'name': 'Items', 'titleField': 'name', 'fields': [
            {'key': 'name', 'label': 'Item', 'type': 'text', 'required': True},
            {'key': 'list', 'label': 'List', 'type': 'select', 'options': [
                {'id': 'l_weekly', 'label': 'Weekly shop'}, {'id': 'l_taco', 'label': 'Taco night'}]},
            {'key': 'status', 'label': 'Status', 'type': 'select', 'options': [
                {'id': 'to_buy', 'label': 'To buy'}, {'id': 'bought', 'label': 'Bought'}]},
            {'key': 'price', 'label': 'Price', 'type': 'money'},
            {'key': 'bought_on', 'label': 'Bought', 'type': 'date'},
            {'key': 'trip', 'label': 'Trip', 'type': 'relation', 'target': 'groceries/trips'},
            {'key': 'usual', 'label': 'Usual', 'type': 'select', 'options': [
                {'id': 'auto', 'label': 'Auto'}, {'id': 'yes', 'label': 'Yes'}, {'id': 'no', 'label': 'No'}]}]},
        'trips': {'key': 'trips', 'name': 'Trips', 'titleField': 'store', 'dateField': 'at', 'calendar': True,
                  'label': 'Grocery trip', 'fields': [
                      {'key': 'store', 'label': 'Store', 'type': 'text', 'required': True},
                      {'key': 'total', 'label': 'Total', 'type': 'money', 'required': True},
                      {'key': 'at', 'label': 'When', 'type': 'datetime', 'required': True}]},
    }),
    'budget': (_page('budget', 'Budget', stitches=[{'from': 'groceries/trips', 'to': 'budget/spend', 'map': [
        {'to': 'amount', 'from': 'total'}, {'to': 'at', 'from': 'at'}, {'to': 'note', 'from': 'store'},
        {'to': 'category', 'const': 'c_groceries'}]}]), {
        'spend': {'key': 'spend', 'name': 'Spend', 'titleField': 'note', 'dateField': 'at', 'fields': [
            {'key': 'note', 'label': 'Note', 'type': 'text'},
            {'key': 'amount', 'label': 'Amount', 'type': 'money', 'required': True},
            {'key': 'category', 'label': 'Category', 'type': 'select', 'options': [
                {'id': 'c_groceries', 'label': 'Groceries'}, {'id': 'c_eating_out', 'label': 'Eating out'}]},
            {'key': 'at', 'label': 'When', 'type': 'datetime'}]},
    }),
    'calendar': (_page('calendar', 'Calendar'), {
        'events': {'key': 'events', 'name': 'Events', 'titleField': 'title', 'dateField': 'at', 'calendar': True,
                   'fields': [{'key': 'title', 'label': 'Title', 'type': 'text', 'required': True},
                              {'key': 'at', 'label': 'When', 'type': 'datetime'},
                              {'key': 'source', 'label': 'Source', 'type': 'text'},
                              {'key': 'ext_id', 'label': 'Ext', 'type': 'text'}]},
    }),
    'workout': (_page('workout', 'Workout'), {
        'sessions': {'key': 'sessions', 'name': 'Sessions', 'titleField': 'name', 'dateField': 'at',
                     'calendar': True, 'fields': [
                         {'key': 'name', 'label': 'Name', 'type': 'text', 'required': True},
                         {'key': 'at', 'label': 'When', 'type': 'datetime'},
                         {'key': 'repeat', 'label': 'Repeat', 'type': 'repeat'},
                         {'key': 'done', 'label': 'Done', 'type': 'bool'}]},
    }),
}


@pytest.fixture(scope='module')
def env():
    from api.db import connect
    ws = None
    with connect() as conn:
        ws = conn.execute("insert into workspaces (name, tz) values (%s, %s) returning id",
                          (f'test-{uuid.uuid4()}', TZ)).fetchone()['id']
        conn.commit()
    try:
        ids = {}
        with connect() as conn:
            for i, (key, (page, colls)) in enumerate(SPECS.items()):
                pid = conn.execute("insert into blocks (workspace_id, position, block_type, properties) "
                                   "values (%s, %s, 'page', %s) returning id", (ws, f'a{i}', Jsonb(page))).fetchone()['id']
                ids[key] = pid
                for j, (ck, cp) in enumerate(colls.items()):
                    ids[f'{key}/{ck}'] = conn.execute(
                        "insert into blocks (workspace_id, parent_id, position, block_type, properties) "
                        "values (%s, %s, %s, 'collection', %s) returning id", (ws, pid, f'a{j}', Jsonb(cp))).fetchone()['id']
            conn.commit()
        yield {'ws': ws, 'ids': ids}
    finally:
        with connect() as conn:
            conn.execute('delete from workspaces where id = %s and name like %s', (ws, 'test-%'))
            conn.commit()


def tx(ws):
    from api.db import transaction
    return transaction(ws)


def svc():
    from api.commands import service
    return service


def block(ws, bid):
    from api.db import connect
    with connect() as conn:
        return conn.execute('select * from blocks where workspace_id = %s and id = %s', (ws, bid)).fetchone()


def live(ws, coll_id):
    from api.db import connect
    with connect() as conn:
        return conn.execute('select * from blocks where workspace_id = %s and collection_id = %s and deleted_at is null '
                            'order by position, id', (ws, coll_id)).fetchall()


def gesture(ws, ops, **kw):
    with tx(ws) as conn:
        return svc().run_gesture(conn, ws, None, ops, **kw)


def add_item(env, name, **fields):
    r = gesture(env['ws'], [{'op': 'insert', 'collection_id': env['ids']['groceries/items'],
                             'fields': {'name': name, 'list': 'l_weekly', 'status': 'to_buy', **fields}}])
    return uuid.UUID(r['blocks'][0]['id'])


def err(fn, *a, **kw):
    from api.commands import CommandError
    with pytest.raises(CommandError) as e:
        fn(*a, **kw)
    return e.value


# ---------------------------------------------------------------- gestures

def test_gesture_insert_update_delete_events(env):
    ws, items = env['ws'], env['ids']['groceries/items']
    a = add_item(env, 'Gesture A')
    b = add_item(env, 'Gesture B')
    pa, pb = block(ws, a)['position'], block(ws, b)['position']
    assert pa < pb, 'new rows go at the end'

    r = gesture(ws, [{'op': 'update', 'record_id': str(a), 'fields': {'price': '$1,200.50', 'qty': None}
                      if False else {'price': '$1,200.50'}}])
    assert r['blocks'][0]['properties']['price'] == 120050
    assert r['blocks'][0]['version'] == 2

    r = gesture(ws, [{'op': 'delete', 'record_id': str(b)}])
    assert block(ws, b)['deleted_at'] is not None

    from api.db import connect
    with connect() as conn:
        evs = conn.execute('select server_seq, block_id, field_path, old, new, version from events '
                           'where workspace_id = %s and block_id = any(%s) order by server_seq', (ws, [a, b])).fetchall()
    seqs = [e['server_seq'] for e in evs]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    ins = [e for e in evs if e['block_id'] == a and e['field_path'] is None]
    assert ins and ins[0]['old'] is None and ins[0]['new']['name'] == 'Gesture A'
    upd = [e for e in evs if e['field_path'] == 'price']
    assert upd[0]['old'] is None and upd[0]['new'] == 120050 and upd[0]['version'] == 2
    dele = [e for e in evs if e['block_id'] == b and e['new'] is None]
    assert dele and dele[0]['old']['name'] == 'Gesture B'
    assert r['server_seq'] == max(seqs)

    # Undo of the delete restores; a second undo is 409 undone
    with tx(ws) as conn:
        u = svc().undo(conn, ws, uuid.UUID(r['change_set_id']))
    assert u['status'] == 'undone' and block(ws, b)['deleted_at'] is None
    with tx(ws) as conn:
        e = err(svc().undo, conn, ws, uuid.UUID(r['change_set_id']))
    assert e.status == 409 and e.body['status'] == 'undone'


def test_gesture_validation(env):
    ws, items = env['ws'], env['ids']['groceries/items']
    e = err(gesture, ws, [{'op': 'insert', 'collection_id': str(items), 'fields': {'list': 'l_weekly'}}])
    assert e.status == 422 and any(i['field'] == 'name' for i in e.body['issues'])
    e = err(gesture, ws, [{'op': 'insert', 'collection_id': str(items), 'fields': {'name': 'X', 'price': 'three'}}])
    assert e.status == 422 and e.body['issues'][0]['field'] == 'price'
    e = err(gesture, ws, [{'op': 'insert', 'collection_id': str(items), 'fields': {'name': 'X', 'colour': 'red'}}])
    assert e.status == 422
    e = err(gesture, ws, [{'op': 'update', 'record_id': str(uuid.uuid4()), 'fields': {'name': 'Y'}}])
    assert e.status == 404
    e = err(gesture, ws, [{'op': 'insert', 'collection_id': str(items),
                           'fields': {'name': 'X', 'trip': [str(uuid.uuid4())]}}])
    assert e.status == 422 and e.body['issues'][0]['field'] == 'trip'


def test_move_and_list_change(env):
    ws, items = env['ws'], env['ids']['groceries/items']
    x, y, z = (add_item(env, n) for n in ('Move X', 'Move Y', 'Move Z'))
    gesture(ws, [{'op': 'move', 'record_id': str(z), 'before_id': str(x), 'after_id': str(y)}])
    assert block(ws, x)['position'] < block(ws, z)['position'] < block(ws, y)['position']
    # a neighbour on another list is ignored; with neither usable, the row goes to the end of the parent
    r = gesture(ws, [{'op': 'move', 'record_id': str(x), 'list': 'Taco night', 'before_id': str(y)}])
    bx = block(ws, x)
    assert bx['properties']['list'] == 'l_taco'
    assert bx['position'] == max(b['position'] for b in live(ws, items))
    with tx(ws) as conn:
        svc().undo(conn, ws, uuid.UUID(r['change_set_id']))
    bx2 = block(ws, x)
    assert bx2['properties']['list'] == 'l_weekly' and bx2['position'] < block(ws, z)['position']


def test_usual_mark_is_copied(env):
    a = add_item(env, 'Orange juice', usual='no')
    b = add_item(env, '  orange JUICE ')
    assert block(env['ws'], a)['properties']['usual'] == 'no'
    assert block(env['ws'], b)['properties']['usual'] == 'no'


def test_complete_item_and_concurrent_edit_warning(env):
    ws = env['ws']
    a = add_item(env, 'Tick me')
    r = gesture(ws, [{'op': 'complete', 'record_id': str(a)}])
    p = r['blocks'][0]['properties']
    assert p['status'] == 'bought' and p['bought_on']
    v = r['blocks'][0]['version']
    gesture(ws, [{'op': 'update', 'record_id': str(a), 'fields': {'price': '1.00'}}])
    r = gesture(ws, [{'op': 'update', 'record_id': str(a), 'fields': {'price': '2.00'}, 'base_version': v}])
    assert {'superseded': 'price', 'block_id': str(a)} in r['warnings']


def test_undo_reports_changed_since(env):
    ws = env['ws']
    a = add_item(env, 'Undo warn')
    first = gesture(ws, [{'op': 'update', 'record_id': str(a), 'fields': {'price': '3.00'}}])
    gesture(ws, [{'op': 'update', 'record_id': str(a), 'fields': {'price': '4.00'}}])
    with tx(ws) as conn:
        u = svc().undo(conn, ws, uuid.UUID(first['change_set_id']))
    assert u['warnings'] == [{'changed_since': {'block_id': str(a), 'field': 'price', 'now': 400, 'was': 300}}]
    assert 'price' not in block(ws, a)['properties']  # the plain inverse is applied anyway


# ---------------------------------------------------------------- basted → confirm → undo

def test_basted_confirm_undo_dismiss(env):
    ws, ids = env['ws'], env['ids']
    oat, eggs = add_item(env, 'Oat milk'), add_item(env, 'Eggs')
    before = {k: dict(block(ws, k)['properties']) for k in (oat, eggs)}
    spend_before = len(live(ws, ids['budget/spend']))
    ops = [
        {'op': 'insert', 'app': 'groceries', 'collection': 'trips', 'record_id': 'new:trip',
         'fields': [{'key': 'store', 'value': 'Corner Market'}, {'key': 'total', 'value': '35.83'},
                    {'key': 'at', 'value': '2026-11-20T17:41'}]},
        {'op': 'update', 'app': 'groceries', 'collection': 'items', 'record_id': str(oat),
         'fields': [{'key': 'status', 'value': 'bought'}, {'key': 'price', 'value': '3.49'},
                    {'key': 'trip', 'value': 'new:trip'}], 'reason': 'on the receipt'},
        {'op': 'update', 'app': 'groceries', 'collection': 'items', 'record_id': str(eggs),
         'fields': [{'key': 'status', 'value': 'bought'}, {'key': 'price', 'value': '4.29'},
                    {'key': 'trip', 'value': 'new:trip'}]},
    ]
    with tx(ws) as conn:
        cs = svc().create_change_set(conn, ws, 'clair', 'clair', ops, title='Corner Market',
                                     source={'kind': 'photo', 'mode': 'live'})

    # check.py 2: nothing in a basted set is counted
    assert {k: block(ws, k)['properties'] for k in (oat, eggs)} == before
    assert live(ws, ids['groceries/trips']) == []
    with tx(ws) as conn:
        pv = svc().preview(conn, ws, cs)
    assert pv['issues'] == [] and not pv['flagged']
    assert set(pv['targets']) == {str(ids['groceries']), str(ids['budget']), str(ids['calendar'])}
    assert any(x.get('via') for x in pv['expanded'])

    seen_apps = []

    def faces(conn, ws_, app_ids):
        seen_apps.extend(app_ids)
        return {a: {'text': 'x'} for a in app_ids}

    with tx(ws) as conn:
        r = svc().confirm(conn, ws, cs, compute_faces=faces)
    assert set(seen_apps) == {str(ids['groceries']), str(ids['budget']), str(ids['calendar'])}
    assert set(r['faces']) == set(seen_apps)
    [trip] = live(ws, ids['groceries/trips'])
    assert trip['properties'] == {'store': 'Corner Market', 'total': 3583, 'at': '2026-11-20T17:41:00-07:00'}
    spends = live(ws, ids['budget/spend'])
    assert len(spends) == spend_before + 1
    sp = [s for s in spends if s['properties'].get('_via', {}).get('record_id') == str(trip['id'])][0]
    assert sp['properties'] == {'amount': 3583, 'at': '2026-11-20T17:41:00-07:00', 'note': 'Corner Market',
                                'category': 'c_groceries', '_via': {'app': 'groceries', 'record_id': str(trip['id'])}}
    assert block(ws, eggs)['properties']['trip'] == [str(trip['id'])]
    assert len(r['blocks']) == 4

    from api.db import connect
    with connect() as conn:
        row = conn.execute('select status, stitched_seq from change_sets where id = %s', (cs,)).fetchone()
        last = conn.execute('select max(server_seq) m from events where change_set_id = %s', (cs,)).fetchone()['m']
        st = conn.execute("select old, new from events where change_set_id = %s and block_id is null "
                          "order by server_seq", (cs,)).fetchall()
    assert row['status'] == 'stitched' and row['stitched_seq'] == last == r['server_seq']
    assert [(e['old'], e['new']) for e in st] == [(None, 'basted'), ('basted', 'stitched')]

    # §11 #1: a second confirm is 409 {status: stitched}
    with tx(ws) as conn:
        e = err(svc().confirm, conn, ws, cs)
    assert e.status == 409 and e.body['status'] == 'stitched'

    # Undo restores exactly; a Clair set goes back to basted
    with tx(ws) as conn:
        u = svc().undo(conn, ws, cs)
    assert u['status'] == 'basted' and u['warnings'] == []
    assert {k: block(ws, k)['properties'] for k in (oat, eggs)} == before
    assert live(ws, ids['groceries/trips']) == []
    assert len(live(ws, ids['budget/spend'])) == spend_before
    with tx(ws) as conn:
        e = err(svc().undo, conn, ws, cs)
    assert e.status == 409 and e.body['status'] == 'basted'

    # confirm again works (new trip), then undo, then dismiss the re-basted card
    with tx(ws) as conn:
        svc().confirm(conn, ws, cs)
    assert len(live(ws, ids['groceries/trips'])) == 1
    with tx(ws) as conn:
        svc().undo(conn, ws, cs)
    with tx(ws) as conn:
        svc().dismiss(conn, ws, cs)
    with tx(ws) as conn:
        e = err(svc().confirm, conn, ws, cs)
    assert e.status == 409 and e.body['status'] == 'dismissed'
    with tx(ws) as conn:
        e = err(svc().dismiss, conn, ws, cs)
    assert e.status == 409


def test_confirm_after_target_deleted_is_409(env):
    ws = env['ws']
    a = add_item(env, 'Gone soon')
    with tx(ws) as conn:
        cs = svc().create_change_set(conn, ws, 'clair', 'clair', [
            {'op': 'update', 'app': 'groceries', 'collection': 'items', 'record_id': str(a),
             'fields': [{'key': 'status', 'value': 'bought'}]}])
    gesture(ws, [{'op': 'delete', 'record_id': str(a)}])
    with tx(ws) as conn:
        e = err(svc().confirm, conn, ws, cs)
    assert e.status == 409 and e.body['issues'][0]['code'] == 'deleted'
    from api.db import connect
    with connect() as conn:
        assert conn.execute('select status from change_sets where id = %s', (cs,)).fetchone()['status'] == 'basted'


def test_clair_validation_is_422(env):
    ws = env['ws']
    with tx(ws) as conn:
        e = err(svc().create_change_set, conn, ws, 'clair', 'clair', [
            {'op': 'insert', 'app': 'plants', 'collection': 'plants', 'fields': [{'key': 'name', 'value': 'Fern'}]},
            {'op': 'insert', 'app': 'groceries', 'collection': 'trips',
             'fields': [{'key': 'store', 'value': 'X'}, {'key': 'total', 'value': 'lots'},
                        {'key': 'at', 'value': '2026-11-20T10:00'}]}])
    assert e.status == 422 and {i['op'] for i in e.body['issues']} == {0, 1}


# ---------------------------------------------------------------- Google guard (check.py 4)

def test_google_records_are_read_only(env):
    ws, ids = env['ws'], env['ids']
    with tx(ws) as conn:
        r = svc().run(conn, ws, [{'op': 'insert', 'collection_id': str(ids['calendar/events']),
                                  'fields': {'title': 'Dentist', 'at': '2026-11-24T07:30', 'source': 'google',
                                             'ext_id': 'g1'}}], actor='system', origin='connector')
    ev = r['blocks'][0]['id']
    e = err(gesture, ws, [{'op': 'update', 'record_id': ev, 'fields': {'title': 'Nope'}}])
    assert e.status == 422 and e.body['error'] == 'from_google'
    e = err(gesture, ws, [{'op': 'delete', 'record_id': ev}])
    assert e.status == 422 and e.body['error'] == 'from_google'
    with tx(ws) as conn:
        e = err(svc().create_change_set, conn, ws, 'clair', 'clair',
                [{'op': 'delete', 'app': 'calendar', 'collection': 'events', 'record_id': ev}])
    assert e.status == 422 and e.body['error'] == 'from_google'
    e = err(gesture, ws, [{'op': 'insert', 'collection_id': str(ids['calendar/events']),
                           'fields': {'title': 'Fake', 'source': 'google'}}])
    assert e.status == 422 and e.body['error'] == 'from_google'
    with tx(ws) as conn:  # the connector itself may update
        svc().run(conn, ws, [{'op': 'update', 'record_id': ev, 'fields': {'title': 'Dentist (moved)'}}],
                  actor='system', origin='connector')
        e = err(svc().undo, conn, ws, uuid.UUID(r['change_set_id']))
    assert e.status == 409 and e.body['error'] == 'not_undoable'


# ---------------------------------------------------------------- repeats (check.py 6)

def _series(env, name):
    s = svc()
    today = s._now(TZ).date()
    start = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=7)
    rule = f'FREQ=WEEKLY;BYDAY={DAYS[start.weekday()]}'
    r = gesture(env['ws'], [{'op': 'insert', 'collection_id': str(env['ids']['workout/sessions']),
                             'fields': {'name': name, 'at': start.isoformat(), 'repeat': rule, 'done': False}}])
    return uuid.UUID(r['blocks'][0]['id']), start


def test_move_occurrence_and_undo(env):
    ws, ids = env['ws'], env['ids']
    leg, start = _series(env, 'Leg day')
    before = dict(block(ws, leg)['properties'])
    assert before['repeat']['start'] == start.isoformat(timespec='minutes')
    occ = (start + timedelta(days=7)).date()
    new_at = (start + timedelta(days=7)).replace(hour=17).isoformat()
    ops = [{'op': 'move_occurrence', 'app': 'workout', 'collection': 'sessions', 'record_id': str(leg),
            'occurrence': occ.isoformat(), 'fields': [{'key': 'at', 'value': new_at}],
            'reason': 'Dentist at 7:30 am'},
           {'op': 'update', 'app': 'workout', 'collection': 'sessions', 'record_id': str(leg), 'keep': True}]
    with tx(ws) as conn:
        cs = svc().create_change_set(conn, ws, 'clair', 'clair', ops)
        svc().confirm(conn, ws, cs)
    series = block(ws, leg)['properties']
    assert series['repeat']['skip'] == [occ.isoformat()]
    one = [b for b in live(ws, ids['workout/sessions']) if b['properties'].get('_moved_from')]
    assert len(one) == 1
    p = one[0]['properties']
    assert p['_moved_from'] == {'record_id': str(leg), 'occurrence': occ.isoformat()}
    assert 'repeat' not in p and p['name'] == 'Leg day' and p['at'].startswith(f'{occ.isoformat()}T17:00:00')

    with tx(ws) as conn:  # not an occurrence any more (skipped) → 422 at propose time
        e = err(svc().create_change_set, conn, ws, 'clair', 'clair', ops[:1])
    assert e.status == 422

    with tx(ws) as conn:
        svc().undo(conn, ws, cs)
    assert block(ws, leg)['properties'] == before
    assert not [b for b in live(ws, ids['workout/sessions']) if b['properties'].get('_moved_from')]


def test_complete_and_skip_occurrence(env):
    ws = env['ws']
    sid, start = _series(env, 'Pull day')
    first = start.date()
    r = gesture(ws, [{'op': 'complete', 'record_id': str(sid), 'occurrence': first.isoformat()}])
    p = r['blocks'][0]['properties']
    assert p['repeat']['log'] == [first.isoformat()]
    assert p['at'].startswith((first + timedelta(days=7)).isoformat())
    r2 = gesture(ws, [{'op': 'skip', 'record_id': str(sid), 'occurrence': (first + timedelta(days=7)).isoformat()}])
    assert r2['blocks'][0]['properties']['at'].startswith((first + timedelta(days=14)).isoformat())
    e = err(gesture, ws, [{'op': 'skip', 'record_id': str(sid), 'occurrence': first.isoformat()}])
    assert e.status == 422
    with tx(ws) as conn:
        svc().undo(conn, ws, uuid.UUID(r2['change_set_id']))
        svc().undo(conn, ws, uuid.UUID(r['change_set_id']))
    p = block(ws, sid)['properties']
    assert p['repeat']['log'] == [] and p['repeat']['skip'] == [] and p['at'].startswith(first.isoformat())


def test_rebalance_long_keys(env):
    ws, items = env['ws'], env['ids']['groceries/items']
    a, b = add_item(env, 'Edge A'), add_item(env, 'Edge B')
    from api.commands import position as pos
    from api.db import connect
    with connect() as conn:  # two neighbours 24 characters long: the next key between them is 25
        conn.execute('update blocks set position = %s where id = %s', ('a0' + 'G' * 22, a))
        conn.execute('update blocks set position = %s where id = %s', ('a0' + 'G' * 21 + 'H', b))
        conn.commit()
    n = add_item(env, 'Squeeze')
    gesture(ws, [{'op': 'move', 'record_id': str(n), 'before_id': str(a), 'after_id': str(b)}])
    assert block(ws, a)['position'] < block(ws, n)['position'] < block(ws, b)['position']
    keys = [x['position'] for x in live(ws, items)]
    assert keys == sorted(keys) and max(map(len, keys)) <= pos.REBALANCE_AT
    from api.db import connect
    with connect() as conn:
        n = conn.execute("select count(*) c from change_sets where workspace_id = %s and origin = 'sweep'",
                         (ws,)).fetchone()['c']
    assert n >= 1
