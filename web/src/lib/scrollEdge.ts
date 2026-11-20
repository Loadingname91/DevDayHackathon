// A scrolling row says so: it gets data-edge="start", "end" or "start end" while there is more to scroll to, and the
// stylesheet (styles/blocks.css) fades that edge. Rows that fit get no attribute and no fade. One watcher for the whole
// app, so any row Clair's apps draw with .tabs, .chips.scroll or .side-apps gets it without knowing about it.
const SEL = '.tabs, .chips.scroll, .side-apps';
const seen = new WeakSet<Element>();

function mark(el: HTMLElement) {
  const y = el.matches('.side-apps'); // the sidebar scrolls down, the others sideways
  const view = y ? el.clientHeight : el.clientWidth, total = y ? el.scrollHeight : el.scrollWidth, at = y ? el.scrollTop : el.scrollLeft;
  const edge = [at > 2 && 'start', total - view - at > 2 && 'end'].filter(Boolean).join(' ');
  if (edge) { if (el.dataset.edge !== edge) el.dataset.edge = edge; } else if (el.dataset.edge !== undefined) delete el.dataset.edge;
}

/** Starts the watcher; returns its stop function. */
export function watchScrollEdges(): () => void {
  if (typeof ResizeObserver === 'undefined' || typeof MutationObserver === 'undefined') return () => {};
  const ro = new ResizeObserver((entries) => entries.forEach((e) => mark(e.target as HTMLElement)));
  let queued = false;
  const scan = () => {
    queued = false;
    document.querySelectorAll<HTMLElement>(SEL).forEach((el) => {
      if (!seen.has(el)) { seen.add(el); ro.observe(el); }
      mark(el);
    });
  };
  const soon = () => { if (!queued) { queued = true; requestAnimationFrame(scan); } };
  const onScroll = (e: Event) => { if (e.target instanceof HTMLElement && e.target.matches(SEL)) mark(e.target); };
  const mo = new MutationObserver(soon);
  mo.observe(document.body, { childList: true, subtree: true });
  document.addEventListener('scroll', onScroll, { capture: true, passive: true }); // scroll doesn't bubble; capture sees every row
  addEventListener('resize', soon);
  void document.fonts?.ready.then(soon);
  soon();
  return () => { ro.disconnect(); mo.disconnect(); document.removeEventListener('scroll', onScroll, true); removeEventListener('resize', soon); };
}
