"""Write and change-set routes against the live database, signed in as the recording account
(sam.record@quilt.demo, the 8-app 'before' state; Budget starts at $412). Resets that workspace before and after.

The base cut line: a basted "spent $12 on lunch" shows on GET /change-sets with delta Budget $412 → $400 while the
Budget face stays $412; confirm → $400; a second confirm is 409; undo → $412 and the live blocks equal the seed.
"""
import os
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

PW_FILE = os.path.expanduser('~/.config/quilt/demo-password')


def _ok() -> bool:
    try:
        from api.settings import settings
        s = settings()
        return bool(s.database_url and s.demo_record_workspace_id and os.path.exists(PW_FILE))
    except Exception:
        return False


pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _ok(), reason='no database or demo password')]

import httpx  # noqa: E402
from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api import db, models as m  # noqa: E402
from api.index import contract_errors, validation_errors  # noqa: E402
from api.routes import write  # noqa: E402
from api.settings import settings  # noqa: E402

S = settings()
WS = UUID(S.demo_record_workspace_id)


def _reset():
    from api.seed.load import reset_workspace
    with db.transaction(WS) as c:
        reset_workspace(c, WS, 'before')


def _live_blocks():
    with db.connect() as c:
        rows = c.execute('select id, block_type, position, properties from blocks where workspace_id = %s '
                         'and deleted_at is null order by id', (WS,)).fetchall()
    return [(str(r['id']), r['block_type'], r['position'], r['properties']) for r in rows]


def _faces():
    from api.workspace import faces, load
    with db.connect() as c:
        return faces(load(c, WS))


@pytest.fixture(scope='module')
def client():
    pw = open(PW_FILE).read().strip()
    tok = httpx.post(f'{S.supabase_url}/auth/v1/token?grant_type=password', headers={'apikey': S.supabase_anon_key},
                     json={'email': 'sam.record@quilt.demo', 'password': pw}, timeout=20).json()['access_token']
    app = FastAPI()
    app.add_exception_handler(HTTPException, contract_errors)
    app.add_exception_handler(RequestValidationError, validation_errors)
    api = APIRouter(prefix='/api')
    api.include_router(write.router)
    app.include_router(api)
    _reset()
    with TestClient(app, headers={'Authorization': f'Bearer {tok}'}) as tc:
        yield tc
    _reset()


def _lunch() -> UUID:
    from api.commands import create_change_set
    with db.transaction(WS) as c:
        return create_change_set(c, WS, actor='clair', origin='clair', title='Lunch', summary='$12.00 in Eating out.',
                                 source={'kind': 'text', 'label': 'You typed', 'at': S.demo_now},
                                 ops=[{'op': 'insert', 'app': 'budget', 'collection': 'spend',
                                       'fields': [{'key': 'note', 'value': 'Lunch'}, {'key': 'amount', 'value': 1200},
                                                  {'key': 'category', 'value': 'Eating out'},
                                                  {'key': 'at', 'value': S.demo_now}]}])


def test_lunch_base_cut_line(client):
    seed = _live_blocks()
    assert _faces()['budget']['text'] == '$412'
    cs = _lunch()

    r = client.get('/api/change-sets', params={'status': 'basted'})
    assert r.status_code == 200, r.text
    cards = r.json()
    card = next(c for c in cards if c['id'] == str(cs))
    m.ChangeSet.model_validate(card)
    assert card['deltas'] == [{'app': 'budget', 'before': '$412', 'after': '$400'}]
    assert card['targets'] == ['budget']
    assert card['actions'] == {'primary': 'Add to Budget', 'secondary': 'Review items'}
    assert card['lines'][0] == {'apps': ['budget'], 'what': 'Lunch · Eating out', 'val': '$12.00',
                                'sub': '$412 → $400 left'}
    assert card['ops'][0]['op'] == 'insert' and card['ops'][0]['ref'] == 'budget/spend'
    assert card['ops'][0]['values']['amount'] == 1200 and card['ops'][0]['values']['category'] == 'c_eating_out'
    assert card['review'][0]['title'] == 'Lunch' and card['review'][0]['change'] == 'new'
    assert card['review'][0]['when'] == 'Today, 5:45 pm · $12.00'
    # nothing counted before confirm
    assert _faces()['budget']['text'] == '$412'
    assert _live_blocks() == seed

    r = client.post(f'/api/change-sets/{cs}/confirm')
    assert r.status_code == 200, r.text
    res = r.json()
    assert res['faces']['budget']['text'] == '$400' and res['faces']['budget']['value'] == 40000
    assert res['change_set_id'] == str(cs) and res['server_seq'] > 0
    assert any(b['properties'].get('note') == 'Lunch' for b in res['blocks'])

    r = client.post(f'/api/change-sets/{cs}/confirm')
    assert r.status_code == 409 and r.json() == {'error': 'status', 'status': 'stitched'}

    r = client.post(f'/api/change-sets/{cs}/undo')
    assert r.status_code == 200, r.text
    assert r.json()['faces']['budget']['text'] == '$412'
    assert _live_blocks() == seed
    # a Clair set goes back to basted: the card is offered again with fresh deltas
    cards = client.get('/api/change-sets', params={'status': 'basted'}).json()
    assert next(c for c in cards if c['id'] == str(cs))['deltas'][0]['after'] == '$400'

    # dismiss: 204, then 409 on repeat
    assert client.post(f'/api/change-sets/{cs}/dismiss').status_code == 204
    r = client.post(f'/api/change-sets/{cs}/dismiss')
    assert r.status_code == 409 and r.json()['status'] == 'dismissed'
    assert _live_blocks() == seed


def test_patch_change_set(client):
    cs = _lunch()
    card = next(c for c in client.get('/api/change-sets', params={'status': 'basted'}).json() if c['id'] == str(cs))
    op = dict(card['ops'][0])
    op['values'] = dict(op['values'], amount='20.00')
    r = client.patch(f'/api/change-sets/{cs}', json={'ops': [op], 'version': card['version']})
    assert r.status_code == 200, r.text
    new = r.json()
    assert new['version'] == card['version'] + 1
    assert new['deltas'] == [{'app': 'budget', 'before': '$412', 'after': '$392'}]
    r = client.patch(f'/api/change-sets/{cs}', json={'ops': [op], 'version': card['version']})
    assert r.status_code == 409 and r.json()['error'] == 'version'
    assert client.post(f'/api/change-sets/{cs}/dismiss').status_code == 204
    assert _faces()['budget']['text'] == '$412'


def test_gestures(client):
    seed = _live_blocks()
    r = client.post('/api/records', json={'collection_id': 'todos/todos', 'fields': {'title': 'Buy stamps'}})
    assert r.status_code == 201, r.text
    res = m.CommandResult.model_validate(r.json())
    rec = res.blocks[0]
    assert rec.properties['title'] == 'Buy stamps' and 'due' not in rec.properties   # Someday: no stamp
    add_cs = res.change_set_id

    r = client.patch(f'/api/records/{rec.id}', json={'fields': {'place': 'Post office'}, 'base_version': rec.version})
    assert r.status_code == 200, r.text
    assert r.json()['blocks'][0]['properties']['place'] == 'Post office'

    r = client.post(f'/api/records/{rec.id}/complete', json={})
    assert r.status_code == 200, r.text
    assert r.json()['blocks'][0]['properties']['done'] is True

    r = client.delete(f'/api/records/{rec.id}')
    assert r.status_code == 200, r.text
    del_cs = r.json()['change_set_id']
    assert r.json()['blocks'][0]['deleted_at'] is not None

    r = client.post(f'/api/change-sets/{del_cs}/undo')
    assert r.status_code == 200, r.text
    assert r.json()['blocks'][0]['deleted_at'] is None
    assert client.post(f'/api/change-sets/{del_cs}/undo').status_code == 409

    # undo of the add, after later edits: still undone, with changed_since warnings
    r = client.post(f'/api/change-sets/{add_cs}/undo')
    assert r.status_code == 200, r.text
    assert r.json()['warnings'], 'later edits come back as changed_since'
    assert _live_blocks() == seed

    # errors
    assert client.delete('/api/records/not-a-uuid').status_code == 404
    assert client.delete('/api/records/00000000-0000-0000-0000-000000000000').status_code == 404
    r = client.post('/api/records', json={'collection_id': 'todos/todos', 'fields': {'nope': 1}})
    assert r.status_code == 422 and r.json()['error'] == 'invalid'
    assert client.post('/api/records', json={'collection_id': 'nope/nope', 'fields': {}}).status_code == 404


def test_stamp_and_move_and_skip(client):
    seed = _live_blocks()
    # a log row with no time is stamped with now
    r = client.post('/api/records', json={'collection_id': 'budget/spend',
                                          'fields': {'note': 'Coffee', 'amount': '3.00'}})
    assert r.status_code == 201, r.text
    b = r.json()['blocks'][0]
    assert b['properties']['at'].startswith('2026-11-20T17:45')
    assert r.json()['faces']['budget']['text'] == '$409'
    client.post(f"/api/change-sets/{r.json()['change_set_id']}/undo")

    # move: a grocery item to another list
    with db.connect() as c:
        item = c.execute("select b.id from blocks b join blocks col on col.id = b.collection_id "
                         "where b.workspace_id = %s and col.properties->>'key' = 'items' and b.deleted_at is null "
                         "and b.properties->>'list' = 'l_weekly' limit 1", (WS,)).fetchone()
        rep = c.execute("select id, properties from blocks where workspace_id = %s and block_type = 'record' "
                        "and deleted_at is null and properties ? 'repeat' and jsonb_typeof(properties->'repeat') = 'object' "
                        "and properties->>'source' is distinct from 'google' limit 1", (WS,)).fetchone()
    r = client.post(f"/api/records/{item['id']}/move", json={'list': 'Taco night'})
    assert r.status_code == 200, r.text
    assert r.json()['blocks'][0]['properties']['list'] == 'l_taco'
    client.post(f"/api/change-sets/{r.json()['change_set_id']}/undo")

    # skip: an occurrence of a repeating record
    if rep is not None:
        from api.commands.service import _rrule
        occ = next(d.date() for d in _rrule(rep['properties']['repeat']) if d.date().isoformat() >= '2026-11-21'
                   and d.date().isoformat() not in (rep['properties']['repeat'].get('skip') or []))
        r = client.post(f"/api/records/{rep['id']}/skip", json={'occurrence': occ.isoformat()})
        assert r.status_code == 200, r.text
        assert occ.isoformat() in r.json()['blocks'][0]['properties']['repeat']['skip']
        client.post(f"/api/change-sets/{r.json()['change_set_id']}/undo")
    assert _live_blocks() == seed
