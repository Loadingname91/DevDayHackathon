import { useLayoutEffect, useRef } from 'react';
import { EASE, T } from '../lib/motion';
import { openClair } from '../lib/store';
import { Icon } from './Icon';
import { Spool } from './Spool';

/**
 * An empty list or block is never a dead end: the sleepy spool (96, as on the empty-app board), one line, and the two ways
 * to fill it, "Tell Clair" and "Type one in". `onAdd` is there only when the collection can be written to; a build preview
 * passes `actions={false}` and shows the line alone. `compact` drops the spool for a screen that already has a block with one
 * (the spool is one per screen). `card` draws it as its own card; inside a list's card it stays bare.
 */
export function EmptyState({ line = 'Nothing here yet', hint, onAdd, actions = true, compact = false, card = false }: {
  line?: string; hint?: string; onAdd?: () => void; actions?: boolean; compact?: boolean; card?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  // The first row arrives (lib/enter.ts marks it `data-enter`): the card leaves with a 120 ms fade, spool and all, as a copy that
  // is left behind in its place. Any other way out (a tab, a screen) is not this moment, and the copy is dropped.
  useLayoutEffect(() => {
    const el = ref.current;
    return () => {
      const host = el?.parentElement;
      if (!el || !host) return;
      const ghost = el.cloneNode(true) as HTMLElement;
      const at = { left: el.offsetLeft, top: el.offsetTop, width: el.offsetWidth };
      queueMicrotask(() => { // after the commit: the row is in the page and marked, the card is out of it
        if (el.isConnected || !host.isConnected || !host.querySelector('[data-enter]')) return;
        ghost.inert = true; ghost.setAttribute('aria-hidden', 'true');
        ghost.style.cssText = `position:absolute;margin:0;pointer-events:none;left:${at.left}px;top:${at.top}px;width:${at.width}px`;
        host.append(ghost);
        ghost.animate([{ opacity: 1 }, { opacity: 0 }], { duration: T.fb, easing: EASE, fill: 'forwards' }).finished.then(() => ghost.remove(), () => ghost.remove());
      });
    };
  }, []);
  return (
    <div ref={ref} className={`landed empty-state${compact ? ' compact' : ''}${card ? ' card' : ''}`}>
      {!compact && <Spool expr="sleepy" size={96} />}
      <b>{line}</b>
      {hint && <p>{hint}</p>}
      {actions && (
        <div className="acts">
          <button type="button" className="ghost" onClick={() => openClair(true)}><Icon name="spool" size={18} />Tell Clair</button>
          {onAdd && <button type="button" className="ghost" onClick={onAdd}><Icon name="plus" size={18} />Type one in</button>}
        </div>
      )}
    </div>
  );
}

/**
 * A figure block the server sent nothing for. A missing entry reads "No data yet" under the block's own label; an entry that
 * is there without its figure (`failed`) keeps the dash, so the two never look alike. The dash is for a figure that is
 * on its way or could not be worked out, never for a block that has no data.
 */
export function NoData({ label, failed = false, className = '' }: { label?: string; failed?: boolean; className?: string }) {
  return (
    <section className={`card nodata ${failed ? 'failed' : ''} ${className}`} aria-label={label}>
      {label && <span className="c-title">{label}</span>}
      <span className="nd-t">{failed ? '–' : 'No data yet'}</span>
      {failed && <span className="nd-s">Could not be worked out.</span>}
    </section>
  );
}
