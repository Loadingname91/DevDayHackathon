import { useEffect, useId, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import type { AppSpec, LeafBlock } from '../api/types';
import { applyTabs, move, ordered, saveLayout, useLayout, withHidden, withOrder, isEmptyLayout } from '../lib/layout';
import { RM, T } from '../lib/motion';
import { Icon } from './Icon';
import { Sheet } from './Sheet';

/**
 * Arrange (app menu → Arrange): put an app's tabs and the sections of each tab in the order you like, and hide the ones you never use.
 * It is a per-person overlay (lib/layout.ts): the app itself is not edited, so Clair's builds work the same and nobody else's app moves.
 * Drag the grip (it follows the finger 1:1 and the other rows make room), or focus the grip and use the arrow keys; the eye hides or shows.
 * The last tab, and the last section of a tab, cannot be hidden. Reset puts the app back to its own order.
 */

const KIND_NAME: Record<string, string> = {
  days: 'Calendar', month: 'Month log', timer: 'Timer', notebook: 'Pages', next: 'Next up', workflows: 'Rules', text: 'Note', countdown: 'Countdown',
  picks: 'Quick picks', strip: 'This week', form: 'Form', chart: 'Chart', calendar: 'Calendar', metric: 'Figure', progress: 'Progress', gauge: 'Gauge', bars: 'Bars', ring: 'Ring',
};

/** What a section is called in the list: its own label, else the collection it shows, else what kind of block it is. */
export function blockName(b: LeafBlock, spec: AppSpec): string {
  const label = (b as { label?: string }).label;
  if (label) return label;
  if (b.kind === 'text') return b.text.replace(/[*_#>`]/g, '').trim().slice(0, 28) || 'Note';
  const ref = ('source' in b && typeof b.source === 'string' ? b.source : 'from' in b && typeof b.from === 'string' ? b.from : 'collection' in b ? b.collection : '') as string;
  const coll = ref && !ref.startsWith('*') ? spec.collections.find((c) => ref === `${spec.key}/${c.key}` || ref.endsWith(`/${c.key}`)) : undefined;
  if (coll && (b.kind === 'list' || b.kind === 'table' || b.kind === 'checklist')) return coll.name;
  return (coll && !KIND_NAME[b.kind] ? coll.name : KIND_NAME[b.kind]) ?? b.kind;
}

type Item = { id: string; title: string; sub?: string; hidden: boolean };

export function ArrangeSheet({ spec, open, onClose, tab }: { spec: AppSpec; open: boolean; onClose: () => void; tab?: string }) {
  const layout = useLayout(spec.key);
  const [secTab, setSecTab] = useState(tab && spec.tabs.some((t) => t.id === tab) ? tab : spec.tabs[0]?.id ?? '');
  useEffect(() => { if (open && tab && spec.tabs.some((t) => t.id === tab)) setSecTab(tab); }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  const live = useRef<HTMLDivElement>(null);
  const say = (t: string) => { if (live.current) live.current.textContent = t; };

  const tabsAll = ordered(spec.tabs, layout?.tabs);
  const hiddenTabs = layout?.hiddenTabs ?? [];
  const tabItems: Item[] = tabsAll.map((t) => ({ id: t.id, title: t.title, hidden: hiddenTabs.includes(t.id) }));
  const page = spec.tabs.find((t) => t.id === secTab) ?? spec.tabs[0];
  const hiddenBlocks = page ? layout?.blocks?.[page.id]?.hidden ?? [] : [];
  const blockItems: Item[] = page ? ordered(page.children, layout?.blocks?.[page.id]?.order).map((b) => ({ id: b.id, title: blockName(b, spec), sub: b.kind, hidden: hiddenBlocks.includes(b.id) })) : [];

  const shownTabs = applyTabs(spec, layout).length;
  const changed = !isEmptyLayout(layout);
  const reorder = (pageId: string | null, items: Item[], ids: string[], name: string, moved: string) => {
    saveLayout(spec.key, withOrder(layout, pageId, ids));
    say(`${name} moved to position ${ids.indexOf(moved) + 1} of ${items.length}`);
  };
  const toggle = (pageId: string | null, id: string, hidden: boolean) => saveLayout(spec.key, withHidden(layout, pageId, id, !hidden));

  return (
    <Sheet open={open} onClose={onClose} label={`Arrange ${spec.name}`}>
      <div className="sheet-head"><span className="txt"><h2>Arrange {spec.name}</h2><span className="sub">Only you see this order. {spec.name} itself does not change.</span></span></div>
      <div className="arr">
        {spec.tabs.length > 1 && (
          <section aria-label="Tabs">
            <span className="sec"><span>Tabs</span><span>{shownTabs} showing</span></span>
            <SortList label="Tabs" items={tabItems} soleVisible={shownTabs <= 1}
              onReorder={(ids, moved) => reorder(null, tabItems, ids, tabItems.find((i) => i.id === moved)?.title ?? 'Tab', moved)}
              onToggle={(id, hidden) => toggle(null, id, hidden)} />
          </section>
        )}
        <section aria-label="Sections">
          <span className="sec"><span>Sections</span></span>
          {spec.tabs.length > 1 && (
            <div className="chips scroll arr-tabs" role="group" aria-label="Which tab">
              {tabsAll.map((t) => (
                <button key={t.id} type="button" className="chip" aria-pressed={t.id === page?.id} onClick={() => setSecTab(t.id)}>{t.title}</button>
              ))}
            </div>
          )}
          {blockItems.length > 0
            ? <SortList label={`Sections in ${page?.title}`} items={blockItems} soleVisible={blockItems.filter((i) => !i.hidden).length <= 1}
                onReorder={(ids, moved) => reorder(page!.id, blockItems, ids, blockItems.find((i) => i.id === moved)?.title ?? 'Section', moved)}
                onToggle={(id, hidden) => toggle(page!.id, id, hidden)} />
            : <p className="card empty">Nothing on this tab to arrange.</p>}
        </section>
        <div className="sheet-actions arr-actions">
          <button type="button" className="outline" disabled={!changed} onClick={() => { saveLayout(spec.key, null); say('Back to the original order'); }}>Reset</button>
          <button type="button" className="cta" onClick={onClose}>Done</button>
        </div>
        <div ref={live} className="sr-only" role="status" aria-live="polite" />
      </div>
    </Sheet>
  );
}

/**
 * A list you can reorder. The grip is a button: press and drag (the row follows the finger 1:1 and the others slide to make room,
 * release settles it into its slot), or focus it and press ↑ / ↓. Escape during a drag puts it back. Rows are `--hit` tall.
 */
function SortList({ label, items, onReorder, onToggle, soleVisible }: {
  label: string; items: Item[]; onReorder: (ids: string[], moved: string) => void; onToggle: (id: string, hidden: boolean) => void; soleVisible: boolean;
}) {
  const ul = useRef<HTMLUListElement>(null);
  const hint = useId();
  type Drag = { id: string; from: number; to: number; dy: number; settling: boolean };
  const [drag, setDrag] = useState<Drag | null>(null);
  const geo = useRef<{ top: number; h: number }[]>([]);
  const start = useRef({ y: 0, pid: 0 });
  const ids = items.map((i) => i.id);

  const down = (e: PointerEvent<HTMLButtonElement>, i: number) => {
    if (e.button > 0 || drag) return;
    const rows = [...(ul.current?.children ?? [])] as HTMLElement[];
    geo.current = rows.map((r) => ({ top: r.offsetTop, h: r.offsetHeight }));
    start.current = { y: e.clientY, pid: e.pointerId };
    e.currentTarget.setPointerCapture(e.pointerId);
    setDrag({ id: items[i].id, from: i, to: i, dy: 0, settling: false });
  };
  const slot = (dy: number, from: number) => {
    const g = geo.current, mid = g[from].top + g[from].h / 2 + dy;
    let to = from;
    g.forEach((r, k) => { if (mid >= r.top) to = k; });
    return to;
  };
  const moveTo = (e: PointerEvent<HTMLButtonElement>) => {
    if (!drag || drag.settling || e.pointerId !== start.current.pid) return;
    const g = geo.current, last = g.length - 1;
    // the row stays inside the list: from the first row's top to the last row's bottom
    const dy = Math.max(g[0].top - g[drag.from].top, Math.min(g[last].top + g[last].h - g[drag.from].h - g[drag.from].top, e.clientY - start.current.y));
    setDrag({ ...drag, dy, to: slot(dy, drag.from) });
  };
  const finish = (e: PointerEvent<HTMLButtonElement>, cancel = false) => {
    if (!drag || drag.settling || e.pointerId !== start.current.pid) return;
    const to = cancel ? drag.from : drag.to, g = geo.current;
    const settle = (g[to].top - g[drag.from].top) + (to > drag.from ? g[to].h - g[drag.from].h : 0);
    const commit = () => { setDrag(null); if (to !== drag.from) onReorder(move(ids, drag.from, to), drag.id); };
    if (RM()) { commit(); return; }
    setDrag({ ...drag, dy: settle, settling: true }); // glide into the slot, then the real order takes over
    setTimeout(commit, T.fb + 40);
  };
  const key = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    if (e.key === 'Escape' && drag) { e.preventDefault(); setDrag(null); return; }
    const to = e.key === 'ArrowUp' ? i - 1 : e.key === 'ArrowDown' ? i + 1 : e.key === 'Home' ? 0 : e.key === 'End' ? items.length - 1 : -1;
    if (to < 0 || to >= items.length || to === i) { if (to >= 0) e.preventDefault(); return; }
    e.preventDefault();
    onReorder(move(ids, i, to), items[i].id);
  };

  // while dragging, the rows between the old and the new slot step aside by the dragged row's height
  const shift = (i: number) => {
    if (!drag || i === drag.from) return 0;
    const h = geo.current[drag.from]?.h ?? 0;
    return drag.from < drag.to && i > drag.from && i <= drag.to ? -h : drag.from > drag.to && i >= drag.to && i < drag.from ? h : 0;
  };

  return (
    <>
      <span id={hint} className="sr-only">Press up or down arrow to move it. Drag the grip with a finger or mouse.</span>
      <ul className={`card list arr-list${drag ? ' dragging' : ''}`} ref={ul} aria-label={label}>
        {items.map((it, i) => {
          const dragged = drag?.id === it.id;
          const lone = !it.hidden && soleVisible; // the last one showing cannot be hidden
          return (
            <li key={it.id} className={`row arr-row${it.hidden ? ' off' : ''}${dragged ? ' lift' : ''}${dragged && drag?.settling ? ' settle' : ''}${i ? ' sep' : ''}`}
              style={dragged ? { transform: `translateY(${drag!.dy}px)` } : drag ? { transform: `translateY(${shift(i)}px)` } : undefined}>
              <button type="button" className="arr-grip" aria-label={`Move ${it.title}`} aria-describedby={hint} aria-roledescription="sortable item"
                onPointerDown={(e) => down(e, i)} onPointerMove={moveTo} onPointerUp={(e) => finish(e)} onPointerCancel={(e) => finish(e, true)} onKeyDown={(e) => key(e, i)}>
                <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M9 6h.01M15 6h.01M9 12h.01M15 12h.01M9 18h.01M15 18h.01" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" /></svg>
              </button>
              <span className="main"><span className="t">{it.title}</span>{it.hidden && <span className="s">Hidden</span>}</span>
              <button type="button" className="arr-eye" role="switch" aria-checked={!it.hidden} aria-label={`Show ${it.title}`} disabled={lone} title={lone ? 'At least one stays showing' : undefined}
                onClick={() => onToggle(it.id, it.hidden)}>
                <Icon name={it.hidden ? 'minus' : 'check'} size={18} sw={2} />
              </button>
            </li>
          );
        })}
      </ul>
    </>
  );
}
