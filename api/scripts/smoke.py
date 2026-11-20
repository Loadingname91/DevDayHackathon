"""End-to-end check of a deployed API (the base cut line, backend.md §13).

  uv run --project api python -m api.scripts.smoke [BASE_URL]   (default: the Railway URL)

Signs in as the demo user, checks faces and Home, sends "spent $12 on lunch" through Clair,
checks nothing counts before Add, confirms ($412 -> $400), confirms again (409), undoes ($412),
then resets the demo workspace. Prints timings; never prints a key or password.
"""
import json
import os
import sys
import time

import httpx

from api.settings import settings

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'https://api-production-a4c7e6bd.up.railway.app').rstrip('/') + '/api'
FACES = {'budget': '$412', 'groceries': '12', 'calendar': '3', 'classes': '2', 'notes': '3', 'todos': '2', 'workout': '3',
         'subscriptions': '$38.46', 'calories': '1,140', 'running': '7', 'meditation': '25', 'cycle': 'Tue 27 Oct'}
ok = True


def check(name, cond, extra=''):
    global ok
    ok &= bool(cond)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + extra) if extra else ''}")


def timed(fn, *a, **k):
    t = time.time()
    r = fn(*a, **k)
    return r, (time.time() - t) * 1000


def main():
    s = settings()
    pw = open(os.path.expanduser('~/.config/quilt/demo-password')).read().strip()
    tok = httpx.post(f'{s.supabase_url}/auth/v1/token?grant_type=password', headers={'apikey': s.supabase_anon_key},
                     json={'email': 'sam@quilt.demo', 'password': pw}, timeout=20).json()['access_token']
    h = {'Authorization': f'Bearer {tok}'}
    c = httpx.Client(base_url=BASE, headers=h, timeout=60)
    print(f'API {BASE}')

    r, ms = timed(c.get, '/health')
    check('health', r.json().get('db') is True, f'{ms:.0f} ms')
    r, ms = timed(c.get, '/me')
    check('/me credits', r.status_code == 200, f"{r.json().get('credits')} {ms:.0f} ms")
    r, ms = timed(c.get, '/apps')
    faces = {p['key']: p['face']['text'] for p in r.json()}
    check('/apps 12 faces canonical', faces == FACES, f'{ms:.0f} ms' if faces == FACES else str(faces))
    r, ms = timed(c.get, '/home')
    hm = r.json()
    check('/home', hm.get('greeting') and len(hm.get('nextUp', [])) == 3, f"{hm.get('greeting')} | {hm.get('status')} {ms:.0f} ms")
    r, ms = timed(c.get, '/apps/budget')
    check('/apps/budget', r.status_code == 200 and r.json()['faces']['budget']['text'] == '$412', f'{ms:.0f} ms')

    # Clair: one real turn
    t0, events, cs = time.time(), [], None
    with c.stream('POST', '/clair/turns', json={'text': 'spent $12 on lunch'}) as resp:
        check('clair stream opens', resp.status_code == 200, resp.headers.get('content-type', ''))
        ev = None
        for line in resp.iter_lines():
            if line.startswith('event:'):
                ev = line[6:].strip()
            elif line.startswith('data:') and ev:
                events.append((ev, round((time.time() - t0) * 1000)))
                if ev == 'proposal':
                    cs = json.loads(line[5:])['change_set']
    print('    events:', ', '.join(f'{e} {ms} ms' for e, ms in events))
    check('clair proposal', cs is not None)
    if not cs:
        return
    deltas = {d['app']: (d['from'], d['to']) for d in cs.get('deltas', [])} if cs.get('deltas') and 'from' in cs['deltas'][0] else cs.get('deltas')
    check('card delta $412 -> $400', '$400' in json.dumps(cs.get('deltas')), json.dumps(deltas))
    check('nothing counts before Add', c.get('/apps/budget').json()['faces']['budget']['text'] == '$412')

    r, ms = timed(c.post, f"/change-sets/{cs['id']}/confirm")
    check('confirm -> $400', r.status_code == 200 and r.json()['faces'].get('budget', {}).get('text') == '$400', f'{ms:.0f} ms')
    r = c.post(f"/change-sets/{cs['id']}/confirm")
    check('second confirm 409', r.status_code == 409, r.text[:80])
    r = c.get('/sync', params={'since': hm['seq']})
    check('/sync sees the change', r.status_code == 200 and 'budget' in r.json().get('touched_apps', []))
    r, ms = timed(c.post, f"/change-sets/{cs['id']}/undo")
    check('undo -> $412', r.status_code == 200 and r.json()['faces'].get('budget', {}).get('text') == '$412', f'{ms:.0f} ms')
    c.post(f"/change-sets/{cs['id']}/dismiss")

    key = [l.split('=', 1)[1].strip() for l in open(os.path.join(os.path.dirname(__file__), '..', '.env')) if l.startswith('DEMO_KEY=')][0]
    r = httpx.post(f'{BASE}/dev/reset', headers={'X-Demo-Key': key}, timeout=60)
    check('reset', r.status_code == 204)

    if '--full' in sys.argv:
        planner(c)
        httpx.post(f'{BASE}/dev/reset', headers={'X-Demo-Key': key}, timeout=60)
        rec = sign_in('sam.record@quilt.demo', pw)
        build(httpx.Client(base_url=BASE, headers={'Authorization': f'Bearer {rec}'}, timeout=90))
        r = httpx.post(f'{BASE}/dev/reset', params={'state': 'before'}, headers={'X-Demo-Key': key}, timeout=60)
        check('reset before', r.status_code == 204)
    print('ALL PASS' if ok else 'SOME FAILED')


def sign_in(email, pw):
    s = settings()
    return httpx.post(f'{s.supabase_url}/auth/v1/token?grant_type=password', headers={'apikey': s.supabase_anon_key},
                      json={'email': email, 'password': pw}, timeout=20).json()['access_token']


def turn(c, body):
    """One Clair turn; returns ([(event, ms, data)], thread id)."""
    t0, out, ev = time.time(), [], None
    with c.stream('POST', '/clair/turns', json=body) as resp:
        if resp.status_code != 200:
            resp.read()
            return [('http', 0, {'status': resp.status_code, 'body': resp.text[:200]})], None
        thread = resp.headers.get('x-thread-id')
        for line in resp.iter_lines():
            if line.startswith('event:'):
                ev = line[6:].strip()
            elif line.startswith('data:') and ev:
                out.append((ev, round((time.time() - t0) * 1000), json.loads(line[5:])))
    return out, thread


def summary(evs):
    return ', '.join(f'{e} {ms} ms' for e, ms, _ in evs if e != 'text_delta')


def planner(c):
    print('  planner (real model, demo account):')
    evs, _ = turn(c, {'text': 'Plan my training for next week'})
    print('    events:', summary(evs))
    und = next((d for e, _, d in evs if e == 'understood'), {})
    cs = next((d['change_set'] for e, _, d in evs if e == 'proposal'), None)
    check('planner understood line', 'Read' in und.get('summary', ''), und.get('summary', ''))
    check('planner card', cs is not None and 'workout' in (cs.get('targets') or []),
          f"{cs and cs.get('title')} · targets {cs and cs.get('targets')}")
    if cs:
        for r in (cs.get('review') or [])[:8]:
            print(f"      - {r.get('title')}: {r.get('change') or r.get('when')}")
        c.post(f"/change-sets/{cs['id']}/dismiss")


def build(c):
    print('  build (real model, recording account, 8 apps):')
    evs, thread = turn(c, {'text': 'I want to track my calories'})
    print('    events:', summary(evs))
    q = next((d for e, _, d in evs if e == 'question'), None)
    cs = next((d['change_set'] for e, _, d in evs if e == 'proposal'), None)
    if q and not cs:
        if 'questions' in q:
            answers = {x['id']: {'choices': [x['options'][0]['label']], **({'other': '2200'} if x['options'][0].get('input') else {})}
                       for x in q['questions']}
            ans = {'question_id': q['id'], 'answers': answers}
        else:
            ans = {'question_id': q['id'], 'choices': [q['options'][0]['id']]}
        thread = thread or next((d.get('thread_id') for e, _, d in evs if e == 'done'), None)
        evs2, _ = turn(c, {'thread_id': thread, 'answer': ans})
        print('    after answer:', summary(evs2))
        evs += evs2
        cs = next((d['change_set'] for e, _, d in evs2 if e == 'proposal'), None)
    check('build asked a question', q is not None)
    check('build plan event', any(e == 'plan' for e, _, _ in evs))
    check('build card kind app', cs is not None and cs.get('kind') == 'app', cs and cs.get('title'))
    if not cs:
        return
    n0 = len(c.get('/apps').json())
    r = c.post(f"/change-sets/{cs['id']}/confirm")
    n1 = len(c.get('/apps').json())
    check('Make it adds the app', r.status_code == 200 and n1 == n0 + 1, f'{n0} -> {n1} apps')
    r = c.post(f"/change-sets/{cs['id']}/undo")
    check('Undo removes it', r.status_code == 200 and len(c.get('/apps').json()) == n0)


if __name__ == '__main__':
    main()
    sys.exit(0 if ok else 1)
