// Answers the paths of spec/backend.md §10 from fixtures. One device, state in
// memory, reset on reload. It is a tape player, not a second server: it never
// evaluates a formula, expands a stitch or works out a date. Confirmed change sets
// lay their recorded effect (rows, faces, values) over the base fixtures.
import { ApiError } from '../api/client';
import type { Answer, AppResponse, ChangeSet, ClairEvent, DatedRow, Home, Me, Patch, Rec, TurnRequest, Workflow } from '../api/types';
import { BASES, SCENARIOS, params, pickFixture, pickRuleRun, type MockState, type ScriptedEvent } from './scenarios';

const files = import.meta.glob('./fixtures/*.json', { import: 'default' }) as Record<string, () => Promise<unknown>>;
async function fixture<T>(name: string): Promise<T> {
  const load = files[`./fixtures/${name}.json`];
  if (!load) throw new ApiError(404, { error: 'no_fixture', name }, `No fixture "${name}"`);
  return structuredClone(await load()) as T;
}

type Effect = {
  credits?: number;
  home?: { status?: string; faces?: Record<string, { text: string }>; changed?: string[]; addApps?: Patch[] };
  apps?: Record<string, { add?: Record<string, unknown[]>; remove?: Record<string, string[]>; values?: AppResponse['values']; face?: { text: string; label: string }; status?: string }>;
  rules?: Record<string, Workflow[]>;
  fixtures?: Record<string, string>;
};

const initial = params();
let fault = initial.fault;
const { base, rung } = initial;
const S: MockState & {
  sets: Map<string, { effect?: string; cs: ChangeSet }>;
  rules: Record<string, Workflow[]>;
  credits: number;
  seq: number;
  google: 'on' | 'off';
  added: Record<string, Rec[]>;
  done: Record<string, true>;
  edits: Record<string, Record<string, unknown>>;
  deleted: Set<string>;
} = {
  base, rung, applied: [], rulesOn: {}, sets: new Map(), rules: {}, credits: 0, seq: 4100,
  google: fault === 'google-off' || fault === 'google-deny' ? 'off' : 'on',
  added: {},
  done: {},
  edits: {},
  deleted: new Set(),
};
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** The demo menu: start over in another state without reloading the page. */
export function resetMock(o: { base: MockState['base']; rung: MockState['rung']; fault: string }) {
  fault = o.fault;
  asked.clear();
  Object.assign(S, {
    base: o.base, rung: o.rung, applied: [], rulesOn: {}, sets: new Map(), rules: {}, credits: 0, seq: 4100, added: {}, done: {}, edits: {}, deleted: new Set(),
    google: o.fault === 'google-off' || o.fault === 'google-deny' ? 'off' : 'on',
  });
  try { sessionStorage.setItem('quilt:mock', JSON.stringify({ scenario: o.base, mock: o.fault, rung: String(o.rung) })); } catch { /* private mode */ }
}
export const mockState = () => ({ base: S.base, rung: S.rung, fault });
const effects = () => Promise.all(S.applied.map((e) => fixture<Effect>(`effect.${e}`)));
const syncRulesOn = () => { S.rulesOn = Object.fromEntries(Object.entries(S.rules).map(([k, v]) => [k, v.some((w) => w.on)])); };
const datedKey = (r: DatedRow) => `${r.record_id}@${r.occurrence ?? r.at}`;
const rowKey = (row: unknown) => ('record_id' in (row as object) ? datedKey(row as DatedRow) : (row as Rec).id);

async function getHome(): Promise<Home> {
  const home = await fixture<Home>(BASES[S.base]['/home']);
  for (const e of await effects()) {
    const h = e.home;
    if (!h) continue;
    if (h.status) home.status = h.status;
    if (h.addApps) home.apps.push(...h.addApps);
    home.apps = home.apps.map((p) => ({
      ...p,
      face: h.faces?.[p.key] ? { ...p.face, ...h.faces[p.key] } : p.face,
      changed: p.changed || !!h.changed?.includes(p.key),
    }));
  }
  // basted cards from rule runs wait in Needs your OK
  home.needsOk = [...S.sets.values()].filter((x) => x.cs.status === 'basted' && x.cs.source.kind === 'workflow').map((x) => ({ kind: 'change_set' as const, change_set: x.cs }));
  home.seq = S.seq;
  return home;
}

async function getApp(key: string): Promise<AppResponse> {
  const effs = await effects();
  let name = `app.${key}`;
  if (key === 'calendar' && S.google === 'off') name = 'app.calendar.nogoogle';
  for (const e of effs) if (e.fixtures?.[`/apps/${key}`]) name = e.fixtures[`/apps/${key}`];
  const app = await fixture<AppResponse>(name);
  for (const e of effs) {
    const a = e.apps?.[key];
    if (!a) continue;
    for (const [ref, ids] of Object.entries(a.remove ?? {})) app.data[ref] = (app.data[ref] ?? []).filter((row) => !ids.includes(rowKey(row)));
    for (const [ref, rows] of Object.entries(a.add ?? {})) app.data[ref] = [...(app.data[ref] ?? []), ...(rows as (Rec | DatedRow)[])];
    if (a.values) app.values = { ...app.values, ...a.values };
    if (a.face) app.faces = { ...app.faces, [key]: a.face };
    if (a.status) app.status = a.status;
  }
  // rows added by hand this session (faces don't move on mocks: they're computed on the server)
  for (const [ref, rows] of Object.entries(S.added)) if (ref.startsWith(key + '/')) app.data[ref] = [...(app.data[ref] ?? []), ...rows];
  // edits and deletes made by hand this session
  for (const [ref, rows] of Object.entries(app.data)) {
    app.data[ref] = (rows as Rec[]).filter((r) => !('id' in r) || !S.deleted.has(r.id))
      .map((r) => ('properties' in r && S.edits[r.id] ? { ...r, version: r.version + 1, properties: { ...r.properties, ...S.edits[r.id] } } : r));
  }
  // ticked rows: a grocery item is bought (and stamped bought_on, so it shows under "Bought in the last week"), anything else is done (a repeating to-do would move to its next date on the server)
  for (const rows of Object.values(app.data)) for (const r of rows as Rec[]) {
    if (!('properties' in r) || !S.done[r.id]) continue;
    if (typeof r.properties.status === 'string') { r.properties.status = 'bought'; r.properties.bought_on = '2026-11-20'; } else r.properties.done = true;
  }
  // the server adds a last tab named Workflows to an app with rules (workflows.md, Engine v1)
  const rules = S.rules[key];
  if (rules?.length) {
    app.spec.workflows = rules;
    app.spec.tabs = [...app.spec.tabs, { kind: 'page', id: 't_workflows', title: 'Workflows', children: [{ kind: 'workflows', id: 'b_workflows' }] }];
  }
  app.seq = S.seq;
  return app;
}

async function getMe(): Promise<Me> {
  const me = await fixture<Me>('me');
  const spent = S.credits;
  me.credits = { ...me.credits, left: me.credits.left - spent, spent: me.credits.spent + spent };
  return me;
}

const ok = (id: string) => ({ change_set_id: id, server_seq: ++S.seq, blocks: [], faces: {}, warnings: [] });

export async function mockRequest<T>(method: string, fullPath: string, body?: unknown): Promise<T> {
  const path = fullPath.split('?')[0];
  await sleep(60 + Math.random() * 80);
  const b = (body ?? {}) as Record<string, unknown>;

  if (method === 'GET') {
    if (path === '/health') return { ok: true, db: true, version: 'mock' } as T;
    if (path === '/me') return (await getMe()) as T;
    if (path === '/home') return (await getHome()) as T;
    if (path === '/apps') return (await getHome()).apps as T;
    if (path === '/change-sets') return [...S.sets.values()].map((s) => s.cs).filter((c) => c.status === 'basted') as T;
    if (path === '/connect') {
      if (S.google === 'off') return [] as T;
      const c = await fixture<{ needs_reconnect: boolean }[]>('connect');
      if (fault === 'google-stale') c[0].needs_reconnect = true;
      return c as T;
    }
    if (path === '/sync') return { seq: S.seq, epoch: 1, server_now: '2026-11-20T17:45:00-07:00', blocks: [], change_sets: [], faces: {}, touched_apps: [] } as T;
    const app = path.match(/^\/apps\/([a-z_]+)$/);
    if (app) return (await getApp(app[1])) as T;
  }

  if (method === 'POST') {
    if (/^\/apps\/[a-z_]+\/opened$/.test(path)) return undefined as T;

    // ---- change sets
    const act = path.match(/^\/change-sets\/([^/]+)\/(confirm|undo|dismiss)$/);
    if (act) {
      const [, id, verb] = act;
      if (id.startsWith('cs_del_') && verb === 'undo') { S.deleted.delete(id.slice(7)); return ok(id) as T; }
      if (id.startsWith('cs_edit_') && verb === 'undo') { delete S.edits[id.slice(8)]; return ok(id) as T; }
      if (id.startsWith('cs_done_') && verb === 'undo') { delete S.done[id.slice(8)]; return ok(id) as T; }
      if (id.startsWith('cs_add_') && verb === 'undo') {
        const rid = id.slice(7);
        for (const k of Object.keys(S.added)) S.added[k] = S.added[k].filter((r) => r.id !== rid);
        return ok(id) as T;
      }
      const entry = S.sets.get(id);
      if (!entry) throw new ApiError(404, { error: 'not_found' });
      const { cs, effect } = entry;
      if (verb === 'confirm') {
        if (fault === 'slow') await sleep(2500);
        if (fault === 'fail-confirm') throw new ApiError(500, { error: 'mock_failure' });
        if (cs.status !== 'basted') throw new ApiError(409, { status: cs.status });
        cs.status = 'stitched';
        if (effect) {
          S.applied.push(effect);
          const e = await fixture<Effect>(`effect.${effect}`);
          for (const [app, ws] of Object.entries(e.rules ?? {})) S.rules[app] = [...(S.rules[app] ?? []), ...ws];
          syncRulesOn();
          const r = await fixture<{ faces: object }>(`confirm.${effect}`);
          return { ...r, server_seq: ++S.seq } as T;
        }
        return ok(id) as T;
      }
      if (verb === 'undo') {
        if (cs.status !== 'stitched') throw new ApiError(409, { status: cs.status });
        cs.status = 'basted';
        if (effect) {
          S.applied = S.applied.filter((x) => x !== effect);
          const e = await fixture<Effect>(`effect.${effect}`);
          for (const [app, ws] of Object.entries(e.rules ?? {})) S.rules[app] = (S.rules[app] ?? []).filter((w) => !ws.some((x) => x.id === w.id));
          syncRulesOn();
          const r = await fixture<{ faces: object }>(`undo.${effect}`);
          return { ...r, server_seq: ++S.seq } as T;
        }
        return ok(id) as T;
      }
      if (cs.status !== 'basted') throw new ApiError(409, { status: cs.status });
      cs.status = 'dismissed';
      return undefined as T;
    }

    // ---- rules (workflows.md, Engine v1)
    const wf = path.match(/^\/apps\/([a-z_]+)\/workflows$/);
    if (wf) {
      const rule = { id: `w_${wf[1]}_${Date.now()}`, on: true, ...(b as Omit<Workflow, 'id' | 'on'>) };
      S.rules[wf[1]] = [...(S.rules[wf[1]] ?? []), rule];
      syncRulesOn();
      return ok(`cs_${rule.id}`) as T;
    }

    // ---- Google (backend.md §8a): the mock "redirect" comes straight back
    if (path === '/connect/google/start') {
      if (fault !== 'google-deny') S.google = 'on';
      return { url: fault === 'google-deny' ? '/app/calendar?connected=failed&mock=google-off' : '/app/calendar?connected=google&mock=' } as T;
    }
    if (path === '/connect/google/sync') { await sleep(500); return fixture<T>('connect.sync'); }

    // ---- gestures: the mock stores nothing it would have to compute from, so it only accepts them
    if (path === '/records') {
      // (typed values are parsed by parseFields below)
      // gestures carry what was typed; the server parses it (backend.md §3). The mock stores it so the row shows.
      const ref = String(b.collection_id);
      const app = await fixture<AppResponse>(`app.${ref.split('/')[0]}`).catch(() => null);
      const fields = app?.spec.collections.find((c) => `${ref.split('/')[0]}/${c.key}` === ref)?.fields ?? [];
      const props = parseFields(fields, (b.fields ?? {}) as Record<string, unknown>);
      const row: Rec = { id: `r_${Date.now()}`, position: 'z', version: 1, properties: props };
      S.added[ref] = [...(S.added[ref] ?? []), row];
      return { ...ok(`cs_add_${row.id}`), blocks: [row] } as T;
    }
    const done = path.match(/^\/records\/([^/]+)\/complete$/);
    if (done) { S.done[done[1]] = true; return ok(`cs_done_${done[1]}`) as T; }
    if (/^\/records\/[^/]+\/(skip|move)$/.test(path)) return ok(`cs_gesture_${Date.now()}`) as T;
    if (path === '/join-codes') return { code: 'K7QX2', expires_at: '2026-11-20T17:50:00-07:00' } as T;
  }

  if (method === 'PATCH' || method === 'DELETE') {
    const recm = path.match(/^\/records\/([^/]+)$/);
    if (recm) {
      const id = recm[1];
      if (method === 'DELETE') { S.deleted.add(id); return ok(`cs_del_${id}`) as T; }
      // the mock doesn't know the record's app here, so it stores what was typed; numbers and money parse by shape
      S.edits[id] = { ...(S.edits[id] ?? {}), ...parseFields(null, (b.fields ?? {}) as Record<string, unknown>) };
      return ok(`cs_edit_${id}`) as T;
    }
  }
  if (method === 'PATCH') {
    const wf = path.match(/^\/apps\/([a-z_]+)\/workflows\/([^/]+)$/);
    if (wf) {
      S.rules[wf[1]] = (S.rules[wf[1]] ?? []).map((w) => (w.id === wf[2] ? { ...w, on: !!b.on } : w));
      syncRulesOn();
      return ok(`cs_${wf[2]}`) as T;
    }
  }
  throw new ApiError(404, { error: 'not_mocked', path }, `The mock has no answer for ${method} ${path}`);
}

// ---- questions before a build (clair-agent.md §11, §12.11): a card waits here for its answer
type Asked = { run: string; effect?: string; csId?: string; charged?: boolean; failedOnce?: boolean };
const asked = new Map<string, Asked>();
/** The tapes hold the recording's answers. Calories with no number of Sam's (No target, Other without a number, or Skip) has its own. */
function pickAnswer(q: Asked, a: Answer) {
  if (q.run === 'run.build-calories' && (a.skip || !/\d/.test(a.answers?.target?.other ?? ''))) return { run: 'run.build-calories.none', effect: 'build-calories-none' };
  return { run: `${q.run}.answer`, effect: q.effect };
}

/** Replays a scripted run: a list of events with delays (clair-agent.md §2). */
export async function mockTurn(path: string, body: TurnRequest, emit: (e: ClairEvent) => void, signal?: AbortSignal): Promise<void> {
  let pick: { run: string; effect?: string } | null;
  let pending: Asked | undefined; // set on an answer: the question card it answers
  const rule = path.match(/^\/apps\/([a-z_]+)\/workflows\/([^/]+)\/run$/);
  if ('answer' in body) {
    // ?mock=answer-expired: the question is past its 24 h (410); ?mock=answer-fail: the first answer fails (500), Try again works
    await sleep(120);
    const q = asked.get(body.answer.question_id);
    if (!q || fault === 'answer-expired') throw new ApiError(410, { error: 'question_expired' });
    if (fault === 'answer-fail' && !q.failedOnce) { q.failedOnce = true; throw new ApiError(500, { error: 'mock_failure' }); }
    const prev = q.csId ? S.sets.get(q.csId) : undefined;
    if (prev && prev.cs.status !== 'basted') throw new ApiError(409, { status: prev.cs.status }); // made or dismissed: too late to change
    pending = q;
    pick = pickAnswer(q, body.answer);
  } else if (rule) {
    const w = S.rules[rule[1]]?.find((x) => x.id === rule[2]);
    if (!w?.on) throw new ApiError(409, { error: 'rule_off' });
    pick = pickRuleRun(w.action.kind === 'ask_clair' ? w.action.text : '', S);
  } else if ('fixture' in body) {
    pick = pickFixture(body.fixture, S);
  } else {
    const text = body.text ?? body.transcript ?? ''; // a spoken turn carries the on-device transcript (clair-agent.md §2, §4)
    const hit = Object.values(SCENARIOS).find((s) => s.match(text));
    pick = hit ? hit.pick(S) ?? { run: 'run.already-built' } : { run: 'run.unknown' };
  }
  if (!pick) pick = { run: 'run.unknown' };
  const script = await fixture<ScriptedEvent[]>(pick.run);
  // credits are spent when the run answers: a card costs what its effect records, a plain answer costs 1
  if (!pick.effect && pick.run !== 'run.unknown') S.credits += 1;
  for (const { delay, ...e } of script) {
    await sleep(delay);
    if (signal?.aborted) return;
    if (fault === 'slow' && e.event === 'understood') {
      await sleep(6200);
      if (signal?.aborted) return;
      emit({ event: 'status', data: { text: 'Still working on it…' } });
    }
    if (e.event === 'question') {
      // the server's 24 h expiry, stamped when the tape plays; the answer plays the follow-up tape
      e.data.expires_at = new Date(Date.now() + (fault === 'answer-expired' ? -60e3 : 864e5)).toISOString();
      asked.set(e.data.id, { run: pick.run, effect: pick.effect });
    }
    if (e.event === 'proposal') {
      if (fault === 'no-card' && !('fixture' in body)) { await sleep(60000); return; }
      if (fault === 'drop' && !('fixture' in body)) return; // the stream closes before `done`
      const cs = e.data.change_set;
      S.sets.set(cs.id, { effect: pick.effect, cs: structuredClone(cs) }); // a changed answer replaces the basted card in place (same id)
      // a build that asked first costs 10 once, however often the answers change (§11)
      if (pick.effect && !pending?.charged) S.credits += Math.abs((await fixture<Effect>(`effect.${pick.effect}`)).credits ?? 1);
      if (pending) { pending.charged = true; pending.csId = cs.id; }
    }
    emit(e as ClairEvent);
  }
}

/** Gestures carry what was typed; the server parses it (backend.md §3). The mock does the same so the row shows. */
function parseFields(fields: { key: string; type: string }[] | null, input: Record<string, unknown>) {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(input)) {
    const t = fields?.find((f) => f.key === k)?.type;
    if (typeof v !== 'string') { out[k] = v; continue; }
    if (t === 'money' || (!t && /^\$\d/.test(v))) out[k] = Math.round(parseFloat(v.replace(/[$,]/g, '')) * 100);
    else if (t === 'number') out[k] = parseFloat(v);
    else out[k] = v;
  }
  return out;
}
