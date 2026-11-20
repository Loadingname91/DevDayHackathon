// One module store read through useSyncExternalStore (spec/ui-tech-plan.md §1).
// The server holds the truth: the store keeps the last answers, paints from the
// IndexedDB cache first in live mode, then catches up.
import { dyedApp, dyedHome } from './dye';
import { useSyncExternalStore } from 'react';
import { isLive, request } from '../api/client';
import type { AppResponse, ChangeSet, CommandResult, Face, Home, Me, Offer, SearchHit, SearchResponse, SyncResponse } from '../api/types';
import { authConfigured, supabase } from './auth';
import { cacheGet, cachePut } from './cache';

/** One receipt capsule docked above the bar (components/Toast.tsx). `ms` is its life, and with an `action` also the length of the
 *  thread that unthreads around it; `error` shows at once even behind a sheet; `dyes` are the apps it concerns (up to 3 dots). */
export type Toast = { id: number; text: string; action?: { label: string; run: () => void }; ms?: number; error?: boolean; dyes: string[]; at: number };
type State = {
  me: Me | null;
  home: Home | null;
  apps: Record<string, AppResponse>;
  toast: Toast | null;
  clairOpen: boolean;
  /** A confirm animation is running: catch-up results wait until it ends. */
  busy: boolean;
  offer: Offer | null;
  offline: boolean;
  error: string | null;
  /** a build proposal on its way to the Build preview */
  buildDraft: { cs: ChangeSet; sentence: string } | null;
  /** apps whose patch should sew onto Home next time it paints */
  sewing: string[];
  /** apps that changed but can't be seen: their tiles creep up above the bar */
  peek: Peek | null;
  /** laptop: the row shown in the detail pane (Laptop board) */
  detail: Detail | null;
  /** laptop: how many lists and checklists the screen shows that have rows you can pick; the pane is there only when it is above 0 */
  pickable: number;
};
export type Detail = { app: string; ref: string; id: string; occurrence?: string };
export type Peek = { id: number; reverse: boolean; items: { app: string; from: string; to: string }[] };

let state: State = { me: null, home: null, apps: {}, toast: null, clairOpen: false, busy: false, offer: null, offline: false, error: null, buildDraft: null, sewing: [], peek: null, detail: null, pickable: 0 };
const subs = new Set<() => void>();
const set = (p: Partial<State>) => { state = { ...state, ...p }; subs.forEach((f) => f()); };
export const getState = () => state;
export function useStore<T>(pick: (s: State) => T): T {
  return useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f); }, () => pick(state));
}

let lastSeq = 0;
let pendingCatchUp = false;

async function cached<T>(path: string, apply: (v: T) => void): Promise<T> {
  if (isLive) { const hit = await cacheGet<T>(path); if (hit) apply(hit); }
  const fresh = await request<T>('GET', path);
  apply(fresh);
  if (isLive) void cachePut(path, fresh);
  return fresh;
}

export async function loadMe() {
  try { await cached<Me>('/me', (me) => set({ me })); } catch (e) { fail(e); }
}
export async function loadHome() {
  try {
    const h = await cached<Home>('/home', (home) => set({ home: dyedHome(home) }));
    lastSeq = Math.max(lastSeq, h.seq);
    set({ offline: false, error: null });
  } catch (e) { fail(e); }
}
export async function loadApp(key: string) {
  try {
    const a = await cached<AppResponse>(`/apps/${key}`, (app) => set({ apps: { ...state.apps, [key]: dyedApp(app) } }));
    lastSeq = Math.max(lastSeq, a.seq);
  } catch (e) { fail(e); }
}
function fail(e: unknown) {
  const offline = typeof navigator !== 'undefined' && navigator.onLine === false;
  set({ offline, error: offline ? "You're offline. Showing what was last loaded." : e instanceof Error ? e.message : 'Could not load.' });
}
export function markOpened(key: string) {
  void request('POST', `/apps/${key}/opened`).catch(() => {});
  if (state.home) set({ home: { ...state.home, apps: state.home.apps.map((p) => (p.key === key ? { ...p, changed: false } : p)) } });
}

/** Faces from a command result are final: patch them into Home at once (no refetch needed to roll). */
export function applyFaces(faces: Record<string, Face>) {
  if (!state.home) return;
  set({ home: { ...state.home, apps: state.home.apps.map((p) => (faces[p.key] ? { ...p, face: { ...p.face, ...faces[p.key] } } : p)) } });
}
/** A thread landed: show the card's delta on that app's face (and in the status line if it leads with it). */
export function applyDelta(app: string, before?: string, after?: string, changed = true) {
  if (!state.home) return;
  const status = before && after && state.home.status.startsWith(before) ? after + state.home.status.slice(before.length) : state.home.status;
  set({ home: { ...state.home, status, apps: state.home.apps.map((p) => (p.key === app || p.id === app ? { ...p, face: after ? { ...p.face, text: after } : p.face, changed } : p)) } });
}
/** Undo: the tags fade and the numbers go back. */
export function clearChanged(apps: string[]) {
  if (!state.home) return;
  set({ home: { ...state.home, apps: state.home.apps.map((p) => (apps.includes(p.key) ? { ...p, changed: false } : p)) } });
}
/** After any write: remember the seq (echo dedupe), then reload what is on screen. */
export async function afterCommand(result: CommandResult | null) {
  if (result) lastSeq = Math.max(lastSeq, result.server_seq);
  await refresh();
}
export async function refresh() {
  searched.clear(); // a write can change a title or add a record: a search answered before it is stale
  await Promise.all([loadHome(), loadMe(), ...Object.keys(state.apps).map(loadApp)]);
}

// ---- links (Nov 20): link two records, by hand or by `[[Title]]`; both are writes with an Undo like any other
/** Link a record to any record in any app. Idempotent on the server; undoable. The caller says it in a toast and calls `afterCommand`. */
export const linkRecord = (id: string, to: { ref: string; id: string }) => request<CommandResult>('POST', `/records/${id}/links`, { to });
export const unlinkRecord = (id: string, targetId: string) => request<CommandResult>('DELETE', `/records/${id}/links/${targetId}`);
const searched = new Map<string, Promise<SearchHit[]>>();
/** The link picker and the `[[` suggestions: titles across all apps (or one), never `exclude` (the record itself). One answer per question until the next write. */
export function searchRecords(q: string, o: { app?: string; exclude?: string } = {}): Promise<SearchHit[]> {
  const path = `/search?q=${encodeURIComponent(q)}${o.app ? `&app=${encodeURIComponent(o.app)}` : ''}${o.exclude ? `&exclude=${encodeURIComponent(o.exclude)}` : ''}`;
  let hit = searched.get(path);
  if (!hit) {
    hit = request<SearchResponse>('GET', path).then((r) => r.hits ?? []);
    searched.set(path, hit);
    hit.catch(() => searched.delete(path)); // a failure is not remembered
  }
  return hit;
}

export function setBusy(busy: boolean) {
  set({ busy });
  if (!busy && pendingCatchUp) { pendingCatchUp = false; void catchUp(); }
}
export const openClair = (open = true) => set({ clairOpen: open });
export const setDetail = (detail: Detail | null) => set({ detail });
export const setPickable = (pickable: number) => { if (pickable !== state.pickable) set({ pickable }); };
export const setOffer = (offer: Offer | null) => set({ offer });
export const setBuildDraft = (buildDraft: State['buildDraft']) => set({ buildDraft });
export const sew = (app: string) => set({ sewing: [...state.sewing, app] });
export const sewn = (app: string) => set({ sewing: state.sewing.filter((a) => a !== app) });
let peekId = 0;
const peekWaiters = new Map<number, () => void>();
/**
 * Raise the tiles of hidden apps. `from`/`to` are the face before and after (the
 * card's deltas). Resolves as they begin to sink (peekSinking), so the receipt capsule rises out of
 * the bar as they fold into it: the capsule and the tiles share the space above the bar.
 */
export function peek(items: Peek['items'], reverse = false): Promise<void> {
  if (!items.length) return Promise.resolve();
  for (const done of peekWaiters.values()) done(); // a newer peek replaces the old one
  peekWaiters.clear();
  const id = ++peekId;
  set({ peek: { id, reverse, items } });
  return new Promise((ok) => peekWaiters.set(id, ok));
}
/** The tiles are sinking: whoever waited for the space above the bar may start now (the capsule overlaps the last 80 ms). */
export const peekSinking = (id: number) => { peekWaiters.get(id)?.(); peekWaiters.delete(id); };
export const clearPeek = (id: number) => {
  if (state.peek?.id === id) set({ peek: null });
  peekWaiters.get(id)?.(); peekWaiters.delete(id);
};
/** Resolves when nothing is rising above the bar. */
export const peekSettled = () => (state.peek ? new Promise<void>((ok) => peekWaiters.set(state.peek!.id, ((prev) => () => { prev?.(); ok(); })(peekWaiters.get(state.peek!.id)))) : Promise.resolve());

let toastId = 0;
/** The dye of the app whose screen is open: a toast raised there carries that app's dot. */
const screenDye = () => (typeof document === 'undefined' ? undefined : document.querySelector('.screen[data-dye]')?.getAttribute('data-dye') ?? undefined);
export type ToastOpts = { error?: boolean; dyes?: (string | undefined)[] };
/**
 * Say what just happened, in one docked capsule (Toast.tsx owns the clock, the pause and the queue behind sheets). A new toast
 * replaces the old one. With an `action` ("Undo") a thread unthreads around the capsule over `ms`. An error is a toast with no
 * action and 4 s or less unless `opts.error` says otherwise: it shows at once, a frayed edge, and never waits behind a sheet.
 */
export function toast(text: string, action?: Toast['action'], ms = 8000, opts: ToastOpts = {}) {
  const dyes = [...new Set((opts.dyes ?? [screenDye()]).filter((d): d is string => !!d))].slice(0, 3);
  set({ toast: { id: ++toastId, text, action, ms, error: opts.error ?? (!action && ms <= 4000), dyes, at: Date.now() } });
}
/** `id`: only that toast (an Undo that failed has already put its error up in its place). */
export const dismissToast = (id?: number) => { if (id === undefined || state.toast?.id === id) set({ toast: null }); };

// ---- catch-up: Realtime nudge → GET /sync?since= (backend.md §7)
let debounce: ReturnType<typeof setTimeout> | undefined;
export function nudge(seq?: number) {
  if (seq !== undefined && seq <= lastSeq) return; // our own echo
  clearTimeout(debounce);
  debounce = setTimeout(() => void catchUp(), 150);
}
async function catchUp() {
  if (state.busy) { pendingCatchUp = true; return; }
  try {
    const s = await request<SyncResponse>('GET', `/sync?since=${lastSeq}`);
    if (state.me && s.epoch !== state.me.workspace.epoch) { location.reload(); return; } // the demo was reseeded
    if (s.seq <= lastSeq) return;
    lastSeq = s.seq;
    await refresh();
    // other devices get the tag, never the thread pull
    if (state.home && s.touched_apps.length) {
      set({ home: { ...state.home, apps: state.home.apps.map((p) => (s.touched_apps.includes(p.id) || s.touched_apps.includes(p.key) ? { ...p, changed: true } : p)) } });
    }
  } catch { /* the next nudge or resume tries again */ }
}

let started = false;
export async function startSync() {
  if (started || !isLive) return;
  started = true;
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') nudge(); });
  addEventListener('online', () => nudge());
  if (!authConfigured || !state.me) return;
  const sb = await supabase();
  sb.channel('events')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'events', filter: `workspace_id=eq.${state.me.workspace.id}` },
      (p) => nudge(Number((p.new as { server_seq?: number }).server_seq)))
    .subscribe((status) => { if (status === 'SUBSCRIBED') nudge(); });
}

/** Demo menu: forget everything loaded and load again. */
export async function resetStore() {
  set({ me: null, home: null, apps: {}, toast: null, clairOpen: false, busy: false, offer: null, error: null, buildDraft: null, sewing: [], peek: null });
  lastSeq = 0;
  await Promise.all([loadMe(), loadHome()]);
}
