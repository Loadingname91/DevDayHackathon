// One module store read through useSyncExternalStore (spec/ui-tech-plan.md §1).
// The server holds the truth: the store keeps the last answers, paints from the
// IndexedDB cache first in live mode, then catches up.
import { dyedApp, dyedHome, normDye } from './dye';
import { upgradeApp } from './upgrade';
import { useSyncExternalStore } from 'react';
import { ApiError, errorText, isLive, request } from '../api/client';
import type { AppResponse, ChangeSet, CommandResult, Dependent, Dependents, Face, Home, Me, Offer, RemovedApp, SearchHit, SearchResponse, SyncResponse } from '../api/types';
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
  /** the trash: removed apps and when each is deleted for good (null until You asks) */
  removed: RemovedApp[] | null;
  /** apps that changed but can't be seen: their tiles creep up above the bar */
  peek: Peek | null;
  /** laptop: the row shown in the detail pane (Laptop board) */
  detail: Detail | null;
  /** laptop: how many lists and checklists the screen shows that have rows you can pick; the pane is there only when it is above 0 */
  pickable: number;
};
export type Detail = { app: string; ref: string; id: string; occurrence?: string };
export type Peek = { id: number; reverse: boolean; items: { app: string; from: string; to: string }[] };

let state: State = { me: null, home: null, apps: {}, toast: null, clairOpen: false, busy: false, offer: null, offline: false, error: null, buildDraft: null, sewing: [], removed: null, peek: null, detail: null, pickable: 0 };
const subs = new Set<() => void>();
const set = (p: Partial<State>) => { state = { ...state, ...p }; subs.forEach((f) => f()); };
export const getState = () => state;
export function useStore<T>(pick: (s: State) => T): T {
  return useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f); }, () => pick(state));
}

let lastSeq = 0;
let pendingCatchUp = false;

/** Per path: how many GETs have started. Only the newest one's answer is applied, so a slow answer that left before a write
 *  and arrives after it can never put the old numbers back (live finding: a Home reload racing a confirm rolled $400 back to $412). */
const started_ = new Map<string, number>();
/**
 * `paintCache`: show the IndexedDB answer first (a reopen paints at once, ADR-008). Only for the first load of a path: a refresh
 * after a write or a sync already has newer data on screen, and painting the cached (older) answer would roll it back for as long
 * as the live request takes, about a second on the demo API.
 */
async function cached<T>(path: string, apply: (v: T) => void, paintCache = true): Promise<T> {
  const n = (started_.get(path) ?? 0) + 1;
  started_.set(path, n);
  if (isLive && paintCache) { const hit = await cacheGet<T>(path); if (hit && started_.get(path) === n) apply(hit); }
  const fresh = await request<T>('GET', path);
  if (started_.get(path) === n) { apply(fresh); if (isLive) void cachePut(path, fresh); }
  return fresh;
}

export async function loadMe() {
  try { await cached<Me>('/me', (me) => set({ me }), !state.me); } catch (e) { fail(e); }
}
export async function loadHome() {
  try {
    const h = await cached<Home>('/home', (home) => set({ home: dyedHome(home) }), !state.home);
    lastSeq = Math.max(lastSeq, h.seq);
    set({ offline: false, error: null });
  } catch (e) { fail(e); }
}
export async function loadApp(key: string) {
  try {
    const a = await cached<AppResponse>(`/apps/${key}`, (app) => set({ apps: { ...state.apps, [key]: upgradeApp(dyedApp(app)) } }), !state.apps[key]);
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
  // the server marks the leading figure bold ("**$412** left this month"): swap it inside the marks, or bare
  const lead = (before && state.home.status.startsWith(`**${before}**`)) ? 2 : 0;
  const status = before && after && state.home.status.startsWith(before, lead) ? state.home.status.slice(0, lead) + after + state.home.status.slice(lead + before.length) : state.home.status;
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

// ---- remove an app (spec/backend.md §11 row 21, FR-S8): a preview first, then one change set with an Undo like any other write
/** What else reads the app, from `DELETE /apps/{id}` without `confirm` (a 409 with `dependents`). [] means nothing does. Never removes anything. */
export async function previewRemoveApp(key: string): Promise<Dependent[]> {
  try {
    await request<CommandResult>('DELETE', `/apps/${encodeURIComponent(key)}`);
    return []; // not expected: the server previews first. Treat a 2xx as "nothing depends on it"; the caller's confirm is then a no-op the server answers
  } catch (e) {
    if (e instanceof ApiError && e.status === 409 && (e.body as Partial<Dependents> | null)?.error === 'dependents') return (e.body as Dependents).dependents ?? [];
    throw e;
  }
}
/**
 * Remove an app: `DELETE /apps/{id}?confirm=true` tombstones its blocks in ONE change set (stitches from it are skipped, records already
 * copied stay), and the capsule says so with Undo (`POST /change-sets/{id}/undo` brings every block back). The patch and its pin leave Home
 * and the sidebar at once; `leave` is the caller's way out of the app's screen (close the sheet, go Home) and resolves when it is done,
 * after which the app's own answer is dropped from the store and the IndexedDB cache (a reopen must not paint it) and Home and `me` reload.
 */
export async function removeApp(key: string, o: { name: string; dye?: string; leave?: () => Promise<void> | void }): Promise<CommandResult> {
  const r = await request<CommandResult>('DELETE', `/apps/${encodeURIComponent(key)}?confirm=true`);
  lastSeq = Math.max(lastSeq, r.server_seq);
  set({
    home: state.home && { ...state.home, apps: state.home.apps.filter((p) => p.key !== key) },
    me: state.me && { ...state.me, workspace: { ...state.me.workspace, settings: { ...state.me.workspace.settings, pins: state.me.workspace.settings.pins.filter((k) => k !== key) } } },
  });
  toast(`Removed ${o.name}.`, {
    label: 'Undo',
    run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); } catch (x) { toast(errorText(x), undefined, 4000); } },
  }, 8000, { dyes: [o.dye] });
  void (async () => {
    try { await o.leave?.(); } catch { /* the screen stays; the store still catches up */ }
    const { [key]: _gone, ...apps } = state.apps; // eslint-disable-line @typescript-eslint/no-unused-vars
    set({ apps, removed: null }); // the trash has one more: You asks again when it opens
    void cachePut(`/apps/${key}`, null); // a null answer paints nothing (cacheGet treats it as a miss)
    await refresh();
  })();
  return r;
}

// ---- the trash (spec/backend.md §10 `/apps/removed`, §11 row 21): a removed app is kept 3 days, then the server deletes it for good
/** `GET /apps/removed`, newest first. The server owns `purge_at`; a failed read leaves the last list (or null) and says nothing. */
export async function loadRemoved(): Promise<void> {
  try { set({ removed: (await request<RemovedApp[]>('GET', '/apps/removed')).map((a) => ({ ...a, dye: normDye(a.dye) })) }); } catch (e) { fail(e); }
}
/** Restore: the app's blocks, rules, stitches and pin come back; its patch sews onto Home and reads "just changed". Not an Undo-able write: Remove is the way back out. */
export async function restoreApp(key: string, name: string, dye?: string): Promise<void> {
  const r = await request<CommandResult>('POST', `/apps/${encodeURIComponent(key)}/restore`);
  lastSeq = Math.max(lastSeq, r.server_seq);
  set({ removed: state.removed?.filter((a) => a.key !== key) ?? null, sewing: [...state.sewing, key] });
  toast(`Restored ${name}.`, undefined, 5000, { dyes: [dye] });
  await refresh();
}
/** Delete now: gone for good, no Undo (the confirm step said so). */
export async function purgeApp(key: string, name: string, dye?: string): Promise<void> {
  const r = await request<CommandResult>('DELETE', `/apps/${encodeURIComponent(key)}/purge`);
  lastSeq = Math.max(lastSeq, r.server_seq);
  set({ removed: state.removed?.filter((a) => a.key !== key) ?? null });
  toast(`Deleted ${name} for good.`, undefined, 5000, { dyes: [dye] });
}
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
  set({ me: null, home: null, apps: {}, toast: null, clairOpen: false, busy: false, offer: null, error: null, buildDraft: null, sewing: [], removed: null, peek: null });
  lastSeq = 0;
  await Promise.all([loadMe(), loadHome()]);
}
