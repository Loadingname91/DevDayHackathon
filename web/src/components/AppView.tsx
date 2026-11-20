import { useLayoutEffect, type KeyboardEvent } from 'react';
import type { AppResponse, LeafBlock, Patch } from '../api/types';
import { loadApp, setPickable } from '../lib/store';
import { useWide } from '../lib/useWide';
import { Block, type Ctx } from './blocks';

/** Draws one tab of any app from its spec. Blocks read from `data`; nothing here fetches (ADR-001).
 *  `tabbed` says the app's tablist (AppScreen) is on the page: the panel is then that tab's tabpanel. */
export function AppView({ app, tab, apps, now, tabbed = false, filter }: { app: AppResponse; tab: string; apps: Patch[]; now: string; tabbed?: boolean; filter?: { field: string; id: string } | null }) {
  const wide = useWide();
  const page = app.spec.tabs.find((t) => t.id === tab) ?? app.spec.tabs[0];
  const preview = app.seq === 0; // a build preview (no server sequence yet)
  // rows you can pick on a laptop: the detail pane is there only while the screen has some (App.tsx reads the count)
  const rowBlocks = (page?.children ?? []).filter((b) => b.kind === 'list' || b.kind === 'checklist');
  const pickable = preview ? 0 : rowBlocks.filter((b) => 'source' in b && b.source.startsWith(app.spec.key + '/')).length;
  useLayoutEffect(() => { setPickable(pickable); return () => setPickable(0); }, [pickable]);
  if (!page) return null;
  const values = app.values ?? {};
  const ctx: Ctx = { spec: app.spec, data: app.data, values, now, apps, preview, many: rowBlocks.length > 1, filter: filter ?? undefined, reload: () => void loadApp(app.spec.key) };
  // neighbouring metrics sit side by side
  const groups: LeafBlock[][] = [];
  for (const b of page.children) {
    const last = groups[groups.length - 1];
    if (b.kind === 'metric' && last && last[0].kind === 'metric' && last.length < 2 && page.children.filter((x) => x.kind === 'metric').length > 1) last.push(b);
    else groups.push([b]);
  }
  const node = (g: LeafBlock[]) => g.length > 1
    ? <div className="metrics-row" key={g[0].id}>{g.map((b) => <Block key={b.id} block={b} ctx={ctx} />)}</div>
    : <Block key={g[0].id} block={g[0]} ctx={ctx} />;
  // Small instruments (a gauge, bars, a ring, a strip) pair up two to a row; on a phone the pair is just a stack.
  // Rows, calendars, timers and logs always take the full width. A lone small block takes it too.
  // ...but only when they are about as tall, so a short card never sits beside a long one with a hole under it
  const tall = (g: LeafBlock[]) => g.length > 1 ? 90 : HEIGHT(g[0], values[g[0].id]?.rows?.length ?? 0);
  const near = (a: LeafBlock[], b: LeafBlock[]) => Math.max(tall(a), tall(b)) / Math.min(tall(a), tall(b)) <= 1.8;
  const rows: LeafBlock[][][] = [];
  for (const g of groups) {
    const last = rows[rows.length - 1];
    if (NARROW.has(g[0].kind) && last && last.length === 1 && NARROW.has(last[0][0].kind) && near(last[0], g)) last.push(g); else rows.push([g]);
  }
  // Laptop: ArrowUp and ArrowDown on the picked row move the pick; Enter edits it (the pane's Edit). The rows are Checklist's and List's.
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const el = e.target as HTMLElement;
    if (!wide || el.getAttribute('aria-pressed') !== 'true' || !el.matches('button.row-btn, .row-in .main')) return;
    if (e.key === 'Enter') { e.preventDefault(); document.querySelector<HTMLButtonElement>('.detail .d-actions .ghost')?.click(); return; }
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const all = [...(el.closest('ul')?.querySelectorAll<HTMLElement>('button.row-btn, .row-in .main:not(:disabled)') ?? [])];
    const next = all[all.indexOf(el) + (e.key === 'ArrowDown' ? 1 : -1)];
    if (!next) return;
    e.preventDefault(); next.click(); next.focus();
  };
  return (
    // the panel of the selected tab, named by that tab; with no tablist (one tab, or a Build preview) it is a plain div
    <div className="blocks" onKeyDown={onKey} {...(tabbed ? { role: 'tabpanel', id: `panel-${page.id}`, 'aria-labelledby': `tab-${page.id}` } : {})}>
      {rows.map((r) => r.length > 1
        ? <div className="pair" key={r[0][0].id}>{r.map((g) => <div className="pair-item" key={g[0].id}>{node(g)}</div>)}</div>
        : node(r[0]))}
    </div>
  );
}

/** The kinds that are small enough to sit beside another (Laptop board: the gauge beside its bars). */
const NARROW = new Set<LeafBlock['kind']>(['gauge', 'bars', 'ring', 'countdown', 'strip', 'metric', 'progress', 'picks', 'next']);
/** About how tall a small block is in px, for pairing only (a bars card grows with its rows). Never a measure of anything shown. */
const HEIGHT = (b: LeafBlock, rows: number) => (b.kind === 'bars' ? 60 + 62 * rows : { gauge: 130, ring: 164, countdown: 110, metric: 80, progress: 96, picks: 100, strip: 110, next: 150 }[b.kind as string] ?? 100);
