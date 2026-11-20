// Arrange: a per-person layout overlay for any app (spec/ui-tech-plan.md §3 "Layout overlay", spec/backend.md §10 `PATCH /settings`).
// The app's spec is never changed: the overlay only says what order the tabs and the blocks of a tab come in, and which are hidden.
// It is keyed by ids the spec already has (`PageBlock.id`, block `id`), so it works for every app, Clair's builds included. An id the overlay
// does not know (a tab Clair added later) is appended in spec order; an id the spec no longer has is ignored.
// Stored on this device first (localStorage), then in the workspace settings (`settings.layout`), which follows the person to other devices.
import { useSyncExternalStore } from 'react';
import { request } from '../api/client';
import type { AppLayout, AppSpec, LeafBlock, PageBlock } from '../api/types';
import { getState, useStore } from './store';

export type { AppLayout };
export type Layouts = Record<string, AppLayout>;

const KEY = (app: string) => `quilt-layout:${app}`;
const local = new Map<string, AppLayout | null>(); // read once per app; `null` = nothing saved here
const subs = new Set<() => void>();
const emit = () => subs.forEach((f) => f());
const subscribe = (f: () => void) => { subs.add(f); return () => { subs.delete(f); }; };

function readLocal(app: string): AppLayout | null {
  if (local.has(app)) return local.get(app)!;
  let v: AppLayout | null = null;
  try { const s = localStorage.getItem(KEY(app)); v = s ? (JSON.parse(s) as AppLayout) : null; } catch { /* storage blocked or garbled: no layout */ }
  local.set(app, v);
  return v;
}

/** An empty overlay says nothing: it is dropped rather than stored. */
export const isEmptyLayout = (l: AppLayout | null | undefined) =>
  !l || (!l.tabs?.length && !l.hiddenTabs?.length && !Object.values(l.blocks ?? {}).some((b) => b.order?.length || b.hidden?.length));

let version = 0; // bumps on every save so the hook re-reads

/** The layout in force for one app: this device's, else the one in the workspace settings. */
export function useLayout(app: string): AppLayout | null {
  const server = useStore((s) => (s.me?.workspace.settings as { layout?: Layouts } | undefined)?.layout?.[app]);
  useSyncExternalStore(subscribe, () => version, () => 0);
  return readLocal(app) ?? server ?? null;
}

let pending: Record<string, AppLayout | null> = {};
let timer: ReturnType<typeof setTimeout> | undefined;

/** Save an app's layout (null or empty = back to the app's own order). Instant here; sent to the workspace a moment later. */
export function saveLayout(app: string, next: AppLayout | null) {
  const layout = isEmptyLayout(next) ? null : next;
  // `{}` is stored (not removed) when a device resets, so a stale server copy does not bring the old layout back
  local.set(app, layout ?? {});
  try { if (layout) localStorage.setItem(KEY(app), JSON.stringify(layout)); else localStorage.setItem(KEY(app), '{}'); } catch { /* the layout still holds for this session */ }
  version++; emit();
  pending[app] = layout;
  clearTimeout(timer);
  timer = setTimeout(flush, 600);
}

async function flush() {
  const sent = pending; pending = {};
  const me = getState().me;
  const layouts: Layouts = { ...((me?.workspace.settings as { layout?: Layouts } | undefined)?.layout ?? {}) };
  for (const [k, v] of Object.entries(sent)) { if (v) layouts[k] = v; else delete layouts[k]; }
  try { await request('PATCH', '/settings', { layout: layouts }); } catch { /* offline or not built yet: the device copy still holds */ }
}

// ---- applying -------------------------------------------------------------------------------------------------------------------

/** `order` first (ids the list still has), then every id it does not name, in the list's own order. */
export function ordered<T extends { id: string }>(items: T[], order?: string[]): T[] {
  if (!order?.length) return items;
  const by = new Map(items.map((i) => [i.id, i]));
  const first = order.map((id) => by.get(id)).filter((i): i is T => !!i);
  const seen = new Set(first.map((i) => i.id));
  return [...first, ...items.filter((i) => !seen.has(i.id))];
}

/** The ids to show: hidden ones go, but never all of them, and never one named in `keep` (a link that points at it). */
function visible<T extends { id: string }>(items: T[], hidden: string[] | undefined, keep: string[] = []): T[] {
  if (!hidden?.length) return items;
  const shown = items.filter((i) => !hidden.includes(i.id) || keep.includes(i.id));
  return shown.length ? shown : items.slice(0, 1);
}

/** One tab's blocks in the person's order, minus the ones they hid. */
export function applyBlocks(page: PageBlock, layout: AppLayout | null): LeafBlock[] {
  const b = layout?.blocks?.[page.id];
  return b ? visible(ordered(page.children, b.order), b.hidden) : page.children;
}

/** The app's tabs in the person's order, minus the ones they hid. `keep`: tabs a link or a filter asked for stay even when hidden. */
export function applyTabs(spec: AppSpec, layout: AppLayout | null, keep: (string | null | undefined)[] = []): PageBlock[] {
  if (!layout) return spec.tabs;
  return visible(ordered(spec.tabs, layout.tabs), layout.hiddenTabs, keep.filter((k): k is string => !!k));
}

/** The spec as the person arranged it (tabs; each tab's blocks). The pure form the plan names. */
export function applyLayout(spec: AppSpec, layout: AppLayout | null, keep: (string | null | undefined)[] = []): AppSpec {
  if (!layout) return spec;
  return { ...spec, tabs: applyTabs(spec, layout, keep).map((t) => ({ ...t, children: applyBlocks(t, layout) })) };
}

// ---- editing helpers (the Arrange sheet) ----------------------------------------------------------------------------------------

/** Move the item at `from` to `to` in `ids`. */
export const move = (ids: string[], from: number, to: number) => {
  const next = ids.slice();
  const [x] = next.splice(from, 1);
  next.splice(Math.max(0, Math.min(next.length, to)), 0, x);
  return next;
};

/** Set the order of one tab's blocks (or the tabs, with `page` null), keeping the rest of the layout. */
export function withOrder(layout: AppLayout | null, page: string | null, order: string[]): AppLayout {
  const l = layout ?? {};
  return page === null ? { ...l, tabs: order } : { ...l, blocks: { ...l.blocks, [page]: { ...l.blocks?.[page], order } } };
}

/** Hide or show one tab (or one block of `page`). */
export function withHidden(layout: AppLayout | null, page: string | null, id: string, hide: boolean): AppLayout {
  const l = layout ?? {};
  const set = (cur: string[] | undefined) => (hide ? [...new Set([...(cur ?? []), id])] : (cur ?? []).filter((x) => x !== id));
  return page === null
    ? { ...l, hiddenTabs: set(l.hiddenTabs) }
    : { ...l, blocks: { ...l.blocks, [page]: { ...l.blocks?.[page], hidden: set(l.blocks?.[page]?.hidden) } } };
}
