import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { RM, sheetOpen, T } from '../lib/motion';
import type { Toast as TToast } from '../lib/store';
import { dismissToast, useStore } from '../lib/store';

/** A sheet is open. Its class flips are all there is to hear: the sheets are portalled and live in Sheet.tsx. */
function useSheetOpen() {
  return useSyncExternalStore(
    (notify) => {
      const mo = new MutationObserver(notify);
      mo.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
      return () => mo.disconnect();
    },
    sheetOpen,
    () => false,
  );
}
/** A sheet is open, or left less than 220 ms ago: the capsule takes the space the sheet has just given up. */
function useSheetBlocking() {
  const open = useSheetOpen();
  const [blocking, setBlocking] = useState(open);
  useEffect(() => {
    if (open) { setBlocking(true); return; }
    const h = setTimeout(() => setBlocking(false), RM() ? 0 : T.layoutOut);
    return () => clearTimeout(h);
  }, [open]);
  return blocking;
}

/** A queued toast is only worth saying while it is news. */
const STALE = 30000;

/**
 * The receipt: one capsule docked on the bar's top edge (on a laptop, bottom-centred in the main column) for what just happened
 * and for Undo. It rises out of the bar (14 px + scale .97, 220), leaves back into it (220); a new toast replaces the old one,
 * its text fading in again (120). With an Undo, a gold running stitch unthreads around it over the toast's life (linear: it is a
 * timeline, not a transition), so the thread shows how long Undo is there. A press, the pointer or focus on it holds the clock
 * (WCAG 2.2.1). Undo: the stitch snaps whole (120), the action runs, the capsule dissolves (140). Behind a sheet a toast waits
 * and shows when the last sheet closes; an error shows at once. Never at the top. Reduced motion: no travel, a static stitch,
 * a 120 ms fade.
 */
export function Toast() {
  const t = useStore((s) => s.toast);
  const blocked = useSheetBlocking();
  const [last, setLast] = useState<TToast | null>(t);
  const [held, setHeld] = useState(false);
  const [undoing, setUndoing] = useState(0); // id of the toast whose Undo was pressed
  const holds = useRef(new Set<string>());
  const clock = useRef({ id: 0, left: 0, at: 0, begun: false });
  useEffect(() => { if (t) setLast(t); else { holds.current.clear(); setHeld(false); } }, [t]);

  const shown = t ?? last;
  const open = !!t && !(blocked && !t.error);
  const paused = held || (!!t && undoing === t.id);

  // the toast's own life: it starts when the capsule is first on screen and stops while held, behind a sheet or after Undo
  useEffect(() => {
    if (!t) return;
    const c = clock.current;
    if (c.id !== t.id) Object.assign(c, { id: t.id, left: t.ms ?? 8000, at: 0, begun: false });
    if (!open || paused) return;
    if (!c.begun && Date.now() - t.at > STALE) { dismissToast(t.id); return; } // it waited behind a sheet until it was old news
    c.begun = true; c.at = Date.now();
    const h = setTimeout(() => dismissToast(t.id), c.left);
    return () => { clearTimeout(h); c.left = Math.max(0, c.left - (Date.now() - c.at)); };
  }, [t?.id, open, paused]); // eslint-disable-line react-hooks/exhaustive-deps

  const hold = (key: string, on: boolean) => { if (on) holds.current.add(key); else holds.current.delete(key); setHeld(holds.current.size > 0); };
  const act = () => {
    const a = shown?.action;
    if (!a || !shown || undoing === shown.id) return;
    const id = shown.id;
    setUndoing(id); // the stitch snaps whole
    a.run(); // the card's undo: the reverse peek plays above the bar as the capsule dissolves
    setTimeout(() => dismissToast(id), RM() ? 0 : T.fb); // not a newer toast (a failed Undo says why in its place)
  };

  const cls = ['toast', open && 'on', shown?.action && 'thread', shown?.error && 'frayed', paused && 'held', shown && undoing === shown.id && 'undoing'].filter(Boolean).join(' ');
  return (
    <div className={cls} role="status" aria-live="polite" aria-hidden={!open}
      style={shown ? ({ '--ms': `${shown.ms ?? 8000}ms` } as React.CSSProperties) : undefined}
      onPointerEnter={(e) => { if (e.pointerType === 'mouse') hold('hover', true); }}
      onPointerLeave={() => { hold('hover', false); hold('press', false); }}
      onPointerDown={() => hold('press', true)}
      onPointerUp={() => hold('press', false)}
      onPointerCancel={() => hold('press', false)}
      onFocus={() => hold('focus', true)}
      onBlur={() => hold('focus', false)}>
      {shown && (shown.action || shown.error) && ( // the capsule is 48 tall, its edge 2 px in: radius 23 on both axes
        <svg key={`e${shown.id}`} className="edge" aria-hidden="true">
          {shown.action && <defs><mask id={`toast-m${shown.id}`}><rect className="m" x="0" y="0" width="100%" height="100%" rx="23" ry="23" pathLength="100" /></mask></defs>}
          <rect x="0" y="0" width="100%" height="100%" rx="23" ry="23" mask={shown.action ? `url(#toast-m${shown.id})` : undefined} />
        </svg>
      )}
      {shown && shown.dyes.length > 0 && (
        <i className="dyedots" aria-hidden="true">{shown.dyes.map((d) => <i key={d} className="dyedot" data-dye={d} />)}</i>
      )}
      <span key={shown?.id}>{shown?.text}</span>
      {shown?.action && <button tabIndex={open ? 0 : -1} onClick={act}>{shown.action.label}</button>}
    </div>
  );
}
