// One turn engine for the Clair sheet and the Chat screen. The conversation lives here, outside React, so a turn started in the
// sheet carries on (stream, cards, Undo) when the chat opens, and the other way round. The sheet shows the last turn of the current
// chat (and, grown, the turns since it opened); the chat shows all of it, with the saved messages before them.
//
// Chats are saved: after each completed turn the thread goes to this device's archive (lib/chats.ts), and the server's latest thread
// (`GET /clair/threads/latest`, last 24 h) is read when the sheet or the chat opens, so a reload or another device offers "Continue".
import { useSyncExternalStore } from 'react';
import { clairTurn, isMocked, request } from '../api/client';
import { ATTACH_ONLY_TEXT, type Thumb } from './attachments';
import type { ChangeSet, ClairEvent, LatestThread, Offer, TurnRequest } from '../api/types';
import * as db from './chats';
import { T } from './motion';
import { getState, loadMe } from './store';
import { speak } from './voice';

// ------------------------------------------------------------------------------------------------ types
export type Turn = {
  id: number;
  at: number;
  said: string;
  status: string | null; // the status line is the only loading UI
  understood: string | null;
  /** what Clair says the input is (`understood.kind`: receipt, syllabus, calendar…), for the understanding line's glyph */
  kind: string | null;
  /** sent with the turn: names and thumbnails only (never the bytes), and the Storage paths, so Try again sends the same files */
  attach: Thumb[];
  paths: { images: string[]; files: string[] } | null;
  /** Clair's thinking, streamed (`thinking_delta`); shown open while it streams, then folded to "Thought for Ns" */
  thinking: string;
  /** when the first thinking arrived, and how long it ran (ms; null while it still streams) */
  thinkAt: number | null;
  thinkMs: number | null;
  cards: ChangeSet[];
  offer: Offer | null;
  answer: string;
  sources: string[];
  done: boolean;
  error: string | null;
  slow: boolean; // no card after 12 s: "Use sample"
  stitched: boolean;
  /** spoken to Clair: its answer is read aloud (clair-agent.md §4) */
  voice: boolean;
  /** sent again before it finished: the line says "Stopped." */
  cancelled: boolean;
};
export type Conv = {
  /** local id; the archive key */
  id: string;
  /** the server's thread id, once known: a turn then sends `thread_id` and carries on the same thread */
  server?: string;
  started: number;
  last: number;
  title: string;
  custom: boolean;
  /** saved messages shown before the live turns (read from the archive or the server) */
  past: db.SavedMsg[];
  turns: Turn[];
  /** opened from the list: shown, not sent into, until "Continue" */
  readOnly: boolean;
  demo: boolean;
  apps: string[];
  /** the person has done something in it: a pristine chat may still be replaced by the server's latest */
  touched: boolean;
};
type Latest = { at: number; data: LatestThread | null } | null;
export type St = {
  convs: Record<string, Conv>;
  current: string;
  /** the sheet shows the current chat's turns from here; at the end of the list is its start state */
  sheetFrom: number;
  archive: db.SavedThread[];
  /** server threads deleted on this device: not brought back from `/clair/threads/latest` */
  tombs: string[];
  loaded: boolean;
  latest: Latest;
};

/** Board ClairSheet, "Try this evening": the three sentences the demo answers (also the chat's suggestion chips). */
export const TRY = [
  { text: 'Spent $12 on lunch', meta: 'Log it · Budget', icon: 'receipt' },
  { text: 'Plan my training for next week', meta: 'Plan · Workout and Calendar', icon: 'dumbbell' },
  { text: 'Am I due for any appointments?', meta: 'Check · Calendar', icon: 'calendar' },
];

// ------------------------------------------------------------------------------------------------ the store
// ids never use crypto.randomUUID: the voice checks count its calls to prove one request per turn
const uid = () => `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
const fresh = (id = uid()): Conv => ({ id, started: Date.now(), last: Date.now(), title: '', custom: false, past: [], turns: [], readOnly: false, demo: false, apps: [], touched: false });
const first = fresh();
let st: St = { convs: { [first.id]: first }, current: first.id, sheetFrom: 0, archive: [], tombs: [], loaded: false, latest: null };
const subs = new Set<() => void>();
const sub = (f: () => void) => { subs.add(f); return () => { subs.delete(f); }; };
const commit = (p: Partial<St>) => { st = { ...st, ...p }; subs.forEach((f) => f()); };
export const useTurns = () => useSyncExternalStore(sub, () => st);
export const getTurns = () => st;
export const currentChat = () => st.convs[st.current];
const updConv = (id: string, f: (c: Conv) => Conv) => { const c = st.convs[id]; if (c) commit({ convs: { ...st.convs, [id]: f(c) } }); };
const updTurn = (cid: string, tid: number, f: (t: Turn) => Turn) => updConv(cid, (c) => ({ ...c, turns: c.turns.map((t) => (t.id === tid ? f(t) : t)) }));

/** Thinking is over once anything else arrives: remember how long it ran (the fold says "Thought for 4 s"). */
const stopThinking = (t: Turn): Turn => (t.thinkAt && t.thinkMs === null ? { ...t, thinkMs: Date.now() - t.thinkAt } : t);

let nextTurn = 1;
const blank = (said: string, voice: boolean): Turn => ({ id: nextTurn++, at: Date.now(), said, status: 'Reading…', understood: null, kind: null, attach: [], paths: null, thinking: '', thinkAt: null, thinkMs: null, cards: [], offer: null, answer: '', sources: [], done: false, error: null, slow: false, stitched: false, voice, cancelled: false });
/** A finished turn with nothing waiting on the person: the sheet starts fresh next time. One still waiting for OK stays. */
export const clean = (t: Turn) => ((t.done || !!t.error) && !t.cards.some((c) => c.status === 'basted')) || t.stitched;
export const running = (c: Conv | undefined) => { const l = c?.turns[c.turns.length - 1]; return !!l && !l.done && !l.cancelled; };

/** Who shows the chat and who takes a finished hand-off to Build, registered by the always-mounted sheet and the chat screen. */
export const surface = { chat: false };
let handoff: ((said: string) => void) | null = null;
export function registerHandoff(f: (said: string) => void) { handoff = f; return () => { if (handoff === f) handoff = null; }; }
let chatVoice: ((o: import('./voice').Outcome) => void) | null = null;
export function registerChatVoice(f: (o: import('./voice').Outcome) => void) { chatVoice = f; return () => { if (chatVoice === f) chatVoice = null; }; }
export const routeChatVoice = (o: import('./voice').Outcome) => { if (!chatVoice) return false; chatVoice(o); return true; };

// ------------------------------------------------------------------------------------------------ sending
const aborts: Record<string, AbortController> = {};
const slowTimers: Record<string, ReturnType<typeof setTimeout>> = {};

/**
 * Sends a turn into the current chat and streams its events into that turn. One turn at a time (backend.md edge 40, a second turn
 * on a running thread is a 409): while one runs, a send waits, unless it has gone slow ("Use sample" re-runs it in place, `replace`).
 * A chat opened read-only starts a new one. Returns false when nothing was sent.
 */
export function send(body: TurnRequest, said: string, o: { replace?: number; attach?: Thumb[] } = {}): boolean {
  let c = currentChat();
  if (c.readOnly) { newChat(); c = currentChat(); }
  const last = c.turns[c.turns.length - 1];
  if (!o.replace && last && !last.done && !last.cancelled && !last.slow) return false;
  const voice = 'voice' in body && !!body.voice;
  const cid = c.id;
  aborts[cid]?.abort();
  const ac = new AbortController();
  aborts[cid] = ac;
  const turn = blank(said, voice);
  if (o.replace) turn.id = o.replace;
  if ('images' in body || 'files' in body) { turn.paths = { images: body.images ?? [], files: body.files ?? [] }; turn.attach = o.attach ?? []; }
  updConv(cid, (x) => ({
    ...x, touched: true, last: Date.now(), title: x.title || db.clip(o.attach?.length && said === ATTACH_ONLY_TEXT ? o.attach[0].name : said),
    turns: o.replace
      ? x.turns.map((t) => (t.id === o.replace ? turn : t))
      : [...x.turns.map((t) => (t === last && !t.done ? { ...t, done: true, status: null, cancelled: true } : t)), turn],
  }));
  const tid = turn.id;
  clearTimeout(slowTimers[cid]);
  slowTimers[cid] = setTimeout(() => updTurn(cid, tid, (t) => (!t.cards.length && !t.done ? { ...t, slow: true } : t)), T.slow);
  // the same thread carries on once its id is known; a sample, an answer to a question and the first turn have none to send
  const req: TurnRequest = c.server && !('fixture' in body) && !('answer' in body) && !body.thread_id ? { ...body, thread_id: c.server } : body;

  const on = (e: ClairEvent) => {
    if (ac.signal.aborted) return;
    updTurn(cid, tid, (t) => {
      switch (e.event) {
        case 'status': return { ...t, status: e.data.text };
        case 'thinking_delta': return { ...t, thinking: t.thinking + e.data.text, thinkAt: t.thinkAt ?? Date.now() };
        case 'thinking_done': return stopThinking(t);
        case 'understood': return { ...stopThinking(t), understood: e.data.summary, kind: e.data.kind };
        case 'proposal': {
          const i = t.cards.findIndex((x) => x.id === e.data.change_set.id); // the same id replaces the card
          const cards = i < 0 ? [...t.cards, e.data.change_set] : t.cards.map((x, k) => (k === i ? e.data.change_set : x));
          return { ...stopThinking(t), cards, status: null, slow: false };
        }
        case 'offer': return { ...t, offer: e.data }; // held until the card is confirmed
        case 'text_delta': return { ...stopThinking(t), answer: t.answer + e.data.text, status: null };
        case 'done':
          return { ...stopThinking(t), done: true, status: null, sources: e.data.sources ?? [], slow: e.data.status === 'error' ? true : t.slow,
            error: e.data.status === 'error' ? (e.data.message ?? 'Clair could not finish that. Nothing was changed.') : null };
        default: return t;
      }
    });
    if (e.event === 'done') {
      clearTimeout(slowTimers[cid]); void loadMe();
      if (voice && e.data.spoken && (getState().clairOpen || surface.chat)) speak(e.data.spoken); // Clair answers aloud only when Sam talked first
      afterTurn(cid, !('fixture' in body) && !('answer' in body));
    }
    // Clair needs to ask before it builds: the Build screen shows the questions and the plan, so hand the sentence over
    if (e.event === 'question' && 'questions' in e.data) {
      ac.abort(); clearTimeout(slowTimers[cid]);
      updConv(cid, (x) => ({ ...x, turns: x.turns.filter((t) => t.id !== tid) }));
      handoff?.(said);
    }
  };
  void clairTurn({ ...req, run_id: crypto.randomUUID() }, on, ac.signal);
  return true;
}

/** A confirmed card: the turn is stitched and the card says so (the chat saves it as "Added to …"). */
export function markStitched(cid: string, tid: number, done: ChangeSet) {
  updTurn(cid, tid, (t) => ({ ...t, stitched: true, cards: t.cards.map((x) => (x.id === done.id ? { ...x, status: 'stitched' as const } : x)) }));
  persist(cid);
}
export function markUndone(cid: string, tid: number, csId: string) {
  updTurn(cid, tid, (t) => ({ ...t, stitched: false, cards: t.cards.map((x) => (x.id === csId ? { ...x, status: 'basted' as const } : x)) }));
  persist(cid);
}

/** The sheet closed (or opened over a chat that moved on): a finished turn starts fresh next time; one waiting for OK stays. */
export function sheetSettle() {
  const c = currentChat();
  const l = c?.turns[c.turns.length - 1];
  if (l && clean(l) && st.sheetFrom < c.turns.length) commit({ sheetFrom: c.turns.length });
}

// ------------------------------------------------------------------------------------------------ chats: new, open, rename, delete
/** Chats kept in memory: the one shown and any with a turn still running (its cards stay confirmable). The rest live in the archive. */
const keepLive = (convs: Record<string, Conv>, current: string) => Object.fromEntries(Object.entries(convs).filter(([id, c]) => id === current || c.turns.some((t) => !t.done && !t.cancelled)));

export function newChat() {
  const c = fresh();
  c.touched = true;
  commit({ convs: keepLive({ ...st.convs, [c.id]: c }, c.id), current: c.id, sheetFrom: 0 });
}
export function openThread(id: string, o: { resume?: boolean } = {}) {
  const live = st.convs[id];
  if (live) {
    commit({ convs: keepLive({ ...st.convs, [id]: { ...live, readOnly: o.resume ? false : live.readOnly, touched: true } }, id), current: id, sheetFrom: live.turns.length });
    return;
  }
  const r = st.archive.find((x) => x.id === id);
  if (!r) return;
  const c: Conv = { id: r.id, server: r.server, started: Date.parse(r.started), last: Date.parse(r.last), title: r.title, custom: !!r.custom, past: r.msgs, turns: [], readOnly: !o.resume, demo: !!r.demo, apps: r.apps, touched: true };
  commit({ convs: keepLive({ ...st.convs, [id]: c }, id), current: id, sheetFrom: 0 });
}
export function renameChat(id: string, title: string) {
  const t = db.clip(title);
  if (!t) return;
  updConv(id, (c) => ({ ...c, title: t, custom: true }));
  const r = st.archive.find((x) => x.id === id);
  if (r) { commit({ archive: st.archive.map((x) => (x.id === id ? { ...x, title: t, custom: true } : x)) }); if (!r.demo) { const u = getState().me?.user.id; if (u) void db.dbPut({ ...r, user: u, title: t, custom: true }); } }
  persist(id);
}
export function deleteChat(id: string) {
  const r = st.archive.find((x) => x.id === id);
  const c = st.convs[id];
  const server = c?.server ?? r?.server;
  aborts[id]?.abort();
  const convs = { ...st.convs }; delete convs[id];
  const u = getState().me?.user.id;
  if (u && !(r?.demo ?? c?.demo)) {
    void db.dbDelete(u, id);
    if (server) { void db.dbPut({ id: `tomb-${server}`, user: u, tomb: true, started: new Date().toISOString(), last: new Date().toISOString(), title: '', apps: [], msgs: [] }); }
  }
  commit({ convs, archive: st.archive.filter((x) => x.id !== id), tombs: server ? [...st.tombs, server] : st.tombs });
  if (st.current === id) newChat();
}
/** The chat that "Continue" offers: the one in hand if it has anything in it, else the server's latest within 24 h (not deleted here). */
export function resumable(s: St): { id: string; title: string; last: number; turns: number } | null {
  const c = s.convs[s.current];
  if (c && (c.turns.length || c.past.length) && !c.readOnly) return { id: c.id, title: c.title || 'Your last chat', last: c.last, turns: c.turns.length || c.past.filter((m) => m.role === 'user').length };
  const l = s.latest?.data;
  const r = l && !s.tombs.includes(l.thread.id) ? s.archive.find((x) => x.server === l.thread.id) : undefined;
  if (c && !c.touched && r) return { id: r.id, title: r.title, last: Date.parse(r.last), turns: r.msgs.filter((m) => m.role === 'user').length };
  return null;
}
/** Can a chat opened from the list be carried on? Only the server's latest thread, still within 24 h. */
export function canContinue(s: St, c: Conv | undefined) {
  const l = s.latest?.data;
  return !!c && !c.demo && !!c.server && !!l && l.thread.id === c.server && Date.now() - Date.parse(l.thread.last_at) < 864e5;
}

// ------------------------------------------------------------------------------------------------ saving
const iso = (ms: number) => new Date(ms).toISOString();
function turnMsgs(t: Turn): db.SavedMsg[] {
  // a file is saved as its name only: "Spent $12 · Attached: receipt.jpg"; the bytes never leave the device
  const att = t.attach.length ? `Attached: ${t.attach.map((a) => a.name).join(', ')}` : '';
  const out: db.SavedMsg[] = [{ role: 'user', text: att ? (t.said === ATTACH_ONLY_TEXT ? att : `${t.said} · ${att}`) : t.said, at: iso(t.at) }];
  if (t.done || t.cards.length || t.answer) {
    out.push({ role: 'clair', text: t.answer || (t.cards.length ? '' : t.error ?? ''), at: iso(t.at), sources: t.sources.length ? t.sources : undefined,
      cards: t.cards.length ? t.cards.map((c) => ({ title: c.title, status: c.status, apps: c.targets })) : undefined });
  }
  return out;
}
const appsOf = (c: Conv) => [...new Set([...c.apps, ...c.turns.flatMap((t) => [...t.cards.flatMap((x) => x.targets), ...t.sources])])];
function toSaved(c: Conv, user: string): db.SavedThread {
  return { id: c.id, user, server: c.server, started: iso(c.started), last: iso(c.last), title: c.title, custom: c.custom || undefined, apps: appsOf(c), msgs: [...c.past, ...c.turns.flatMap(turnMsgs)] };
}
/** Writes the chat to the archive (and the list). Skips a chat with nothing in it and a sample. */
function persist(cid: string) {
  const c = st.convs[cid];
  const user = getState().me?.user.id;
  if (!c || c.demo || !(c.turns.length || c.past.length)) return;
  const rec = toSaved(c, user ?? '');
  // a copy of this thread adopted from the server before the chat knew its id is the same chat
  const twins = c.server ? st.archive.filter((x) => x.id !== cid && x.server === c.server && !x.demo) : [];
  if (user) for (const x of twins) void db.dbDelete(user, x.id);
  commit({ archive: [rec, ...st.archive.filter((x) => x.id !== cid && !twins.includes(x))] });
  if (user) void db.dbPut(rec);
}
function afterTurn(cid: string, learn: boolean) {
  persist(cid);
  if (learn && !st.convs[cid]?.server) void learnServer(cid);
}
/** The turn's response headers carry the thread id, but the client never reads them: the thread is found by asking for the latest one
 *  (`adopt` links it to the chat that just said the same thing). */
async function learnServer(cid: string) {
  await fetchLatest(true);
  // the server may still be writing the thread: look once more
  if (!st.convs[cid]?.server) { await new Promise((r) => setTimeout(r, 1500)); if (!st.convs[cid]?.server) await fetchLatest(true); }
}
const lastSaid = (c: Conv) => [...c.turns].reverse().find((t) => !t.cancelled)?.said.trim();

// ------------------------------------------------------------------------------------------------ loading: the archive and the server's latest
let loadedFor = '';
export async function loadChats(user: string) {
  if (loadedFor === user) return;
  loadedFor = user;
  const saved = await db.dbLoad(user);
  const mem = st.archive.filter((x) => !saved.some((s) => s.id === x.id));
  const demo = isMocked('/clair/threads/latest') ? db.seedThreads() : [];
  commit({
    archive: [...mem, ...saved.filter((x) => !x.tomb), ...demo.filter((d) => !st.archive.some((x) => x.id === d.id))],
    tombs: saved.filter((x) => x.tomb).map((x) => x.id.replace(/^tomb-/, '')),
    loaded: true,
  });
}
let inflight: Promise<LatestThread | null> | null = null;
/** Asks the server for its latest thread (`GET /clair/threads/latest`; 204 is none) and makes sure the list has it. */
export function fetchLatest(force = false): Promise<LatestThread | null> {
  if (!force && st.latest && Date.now() - st.latest.at < 15000) return Promise.resolve(st.latest.data);
  inflight ??= request<LatestThread | undefined>('GET', '/clair/threads/latest')
    .then((r) => r ?? null, () => null)
    .then((data) => { commit({ latest: { at: Date.now(), data } }); if (data) adopt(data); return data; })
    .finally(() => { inflight = null; });
  return inflight;
}
function adopt(data: LatestThread) {
  const id = data.thread.id;
  if (st.tombs.includes(id) || st.archive.some((x) => x.server === id) || Object.values(st.convs).some((x) => x.server === id)) return;
  // the thread a chat of this session just made: the chat that said the same last line is that thread
  const theirs = [...data.messages].reverse().find((m) => m.role === 'user')?.text.trim();
  const mine = Object.values(st.convs).find((c) => !c.server && c.turns.length && theirs && lastSaid(c) === theirs);
  if (mine) { updConv(mine.id, (c) => ({ ...c, server: id })); persist(mine.id); return; }
  const msgs: db.SavedMsg[] = data.messages.map((m) => ({ role: m.role, text: m.text, at: m.at, csId: m.change_set_id }));
  const title = msgs.find((m) => m.role === 'user')?.text ?? 'Your last chat';
  const user = getState().me?.user.id ?? '';
  const rec: db.SavedThread = { id: `srv-${id}`, user, server: id, started: data.thread.started_at, last: data.thread.last_at, title: db.clip(title), apps: [], msgs };
  commit({ archive: [rec, ...st.archive] });
  if (user) void db.dbPut(rec);
}
/** The Chat screen opened: load the list, ask for the latest thread, and if nothing has been done in this chat yet, open that thread
 *  (read-only, with "Continue"). */
export async function bootChat(user: string) {
  await loadChats(user);
  const data = await fetchLatest();
  const c = currentChat();
  if (!data || !c || c.touched || c.turns.length || c.past.length || st.tombs.includes(data.thread.id)) return;
  const r = st.archive.find((x) => x.server === data.thread.id);
  if (r) openThread(r.id);
}

// ------------------------------------------------------------------------------------------------ the list
export type ChatRow = { id: string; title: string; last: number; apps: string[]; demo: boolean; current: boolean };
/** Saved chats and the ones in hand, newest first. The chat you are in appears the moment it has a turn. */
export function chatRows(s: St): ChatRow[] {
  const rows = new Map<string, ChatRow>();
  for (const r of s.archive) rows.set(r.id, { id: r.id, title: r.title || 'New chat', last: Date.parse(r.last), apps: r.apps, demo: !!r.demo, current: false });
  for (const c of Object.values(s.convs)) {
    if (!c.turns.length && !c.past.length) continue;
    rows.set(c.id, { id: c.id, title: c.title || 'New chat', last: c.last, apps: appsOf(c), demo: c.demo, current: false });
  }
  return [...rows.values()].map((r) => ({ ...r, current: r.id === s.current })).sort((a, b) => b.last - a.last);
}
