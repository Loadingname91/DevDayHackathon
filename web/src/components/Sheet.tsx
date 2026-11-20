import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from 'react';
import { createPortal } from 'react-dom';
import { project, RM, rubberband, spring, T, tracker } from '../lib/motion';
import { Icon } from './Icon';

/** One open sheet: its scrim and its panel. The last entry is the top sheet. */
type Entry = { id: string; scrim: RefObject<HTMLDivElement | null>; sheet: RefObject<HTMLDivElement | null> };
const stack: Entry[] = [];
/** Stays live behind and above a sheet: the toast (its Undo), Peek and the threads. */
const LIVE = '.toast, .peek, .threads';
const inerted = new Set<Element>();

/** Everything in the frame except the top sheet (and its scrim) is `inert`: no focus, no taps, hidden from readers. */
function syncInert() {
  const frame = document.querySelector('.frame');
  if (!frame) return;
  const top = stack[stack.length - 1];
  const keep = top ? [top.scrim.current, top.sheet.current] : [];
  for (const el of Array.from(frame.children)) {
    if (top && !keep.includes(el as HTMLDivElement) && !el.matches(LIVE)) {
      if (!el.hasAttribute('inert')) { el.setAttribute('inert', ''); inerted.add(el); }
    } else if (inerted.has(el)) { el.removeAttribute('inert'); inerted.delete(el); }
  }
}

/** What opened a sheet, for the rise origin: the focused control, or the last thing pressed (iOS never focuses a tapped button). */
let lastPress: Element | null = null;
if (typeof document !== 'undefined') document.addEventListener('pointerdown', (e) => { lastPress = e.target instanceof Element ? e.target : null; }, true);

/** The grabber and the header carry `touch-action: none` (interaction.css), so a drag there is ours and the browser does not scroll. */
const HEAD = '.grab, .sheet-head, .cs-head, .clair-head';

type Props = {
  open: boolean; onClose: () => void; onExited?: () => void; label: string; children: ReactNode; footer?: ReactNode;
  /** called as the sheet starts rising: focus the field here, so the first keystroke is never lost */
  onOpened?: () => void;
  /** the sheet has its own way out (Clair's ×): no built-in close button */
  noClose?: boolean;
  /** the pinned bar stays above the scrim, lit, because the sheet's cards stitch onto its pins (Clair) */
  keepBar?: boolean;
};

/**
 * Bottom sheet above the bar. Rises from its trigger (translateY 16 + scale .96, 350 in, 220 out; origin on the Clair
 * cell, else under the button that opened it). Drag down from the grabber, the top 48 px, or the body when it
 * is scrolled to the top: 1:1 with the finger, rubber-band upward, close if
 * y + project(v) > .35h (or a flick over 400 px/s past 24 px), critically damped spring .35. A press mid-spring grabs the
 * sheet where it is. Port of bindSheetDrag() in design/prototypes/quilt-flows.html.
 * Modal: the page behind is inert, focus moves in and returns to the trigger, Escape closes only the top sheet,
 * every sheet has a 44 px close button unless it brings its own.
 */
export function Sheet({ open, onClose, onExited, onOpened, label, children, footer, noClose, keepBar }: Props) {
  const [mounted, setMounted] = useState(open);
  const [on, setOn] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const scrim = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const id = useId();
  // callers pass fresh callbacks every render: effects read them from here and never depend on them
  const cb = useRef({ onClose, onExited, onOpened });
  useLayoutEffect(() => { cb.current = { onClose, onExited, onOpened }; });
  const wasOpen = useRef(false);
  const trigger = useRef<{ from: Element | null; focus: HTMLElement | null }>({ from: null, focus: null });

  // ---- open: mount, then start the rise in the same frame (no double rAF: the click-to-motion gap was 22 ms)
  useLayoutEffect(() => {
    if (!open) return;
    wasOpen.current = true;
    const a = document.activeElement;
    const focus = a instanceof HTMLElement && a !== document.body && a !== document.documentElement ? a : null;
    trigger.current = { from: focus ?? lastPress, focus };
    setMounted(true);
  }, [open]);

  useLayoutEffect(() => {
    if (!open || !mounted) return;
    const s = ref.current;
    if (!s) return;
    // origin: under the control that opened it; the Clair cell keeps the corner it rises from
    const from = trigger.current.from;
    if (from && from.isConnected && !s.contains(from) && !from.closest('.bar .clair, .side-clair')) {
      const r = from.getBoundingClientRect(), left = s.getBoundingClientRect().right - s.offsetWidth;
      s.style.transformOrigin = `${Math.max(0, Math.min(s.offsetWidth, r.left + r.width / 2 - left))}px 100%`;
    } else s.style.transformOrigin = '';
    s.getBoundingClientRect(); // commit the closed state, so the next class change is a transition
    setOn(true);
  }, [open, mounted]);

  // ---- close: fade out, then unmount
  useEffect(() => {
    if (open) return;
    setOn(false);
    if (!wasOpen.current) return;
    const t = setTimeout(() => { wasOpen.current = false; setMounted(false); cb.current.onExited?.(); }, RM() ? 120 : T.layoutOut);
    return () => clearTimeout(t);
  }, [open]);

  // ---- modal: top of the stack, inert page, Escape, focus in and back out
  useLayoutEffect(() => {
    if (!open) return;
    const entry: Entry = { id, scrim, sheet: ref };
    stack.push(entry);
    syncInert();
    return () => {
      const i = stack.indexOf(entry);
      if (i >= 0) stack.splice(i, 1);
      syncInert();
    };
  }, [open, id]);
  useLayoutEffect(() => { if (open && mounted) syncInert(); }, [open, mounted]);
  useLayoutEffect(() => {
    if (!open) return;
    return () => {
      const t = trigger.current.focus, panel = ref.current;
      // after the commit: React puts focus back on the field it had before the commit, which would undo this
      queueMicrotask(() => {
        const at = document.activeElement;
        if (t && t.isConnected && (!at || at === document.body || panel?.contains(at))) t.focus({ preventScroll: true });
      });
    };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || stack[stack.length - 1]?.id !== id) return;
      e.stopImmediatePropagation();
      cb.current.onClose();
    };
    addEventListener('keydown', key);
    return () => removeEventListener('keydown', key);
  }, [open, id]);
  useEffect(() => {
    if (!on) return;
    const s = ref.current;
    if (s && !s.contains(document.activeElement)) s.focus({ preventScroll: true });
    cb.current.onOpened?.();
  }, [on]);

  // ---- drag to dismiss (listeners live as long as the sheet is mounted; callbacks come from the ref)
  useEffect(() => {
    const s = ref.current;
    if (!s || !mounted) return;
    let y0 = 0, x0 = 0, y = 0, h = 0, inTop = false, state: 'idle' | 'pending' | 'drag' = 'idle';
    let stop: (() => void) | null = null;
    const tr = tracker();
    const set = (v: number) => {
      y = v;
      s.style.transform = `translateY(${v}px)`;
      if (scrim.current) scrim.current.style.opacity = String(Math.max(0, Math.min(1, 1 - v / h)));
    };
    const reset = () => {
      s.classList.remove('dragging');
      s.style.transform = '';
      if (scrim.current) { scrim.current.style.opacity = ''; scrim.current.style.transition = ''; }
    };
    const begin = (cx: number, cy: number, target: EventTarget | null) => {
      const t = target as Element;
      if (t.closest('input,textarea,select,button,a')) { state = 'idle'; return false; }
      stop?.(); stop = null;
      const r = s.getBoundingClientRect();
      h = r.height;
      const live = new DOMMatrix(getComputedStyle(s).transform).m42;
      inTop = !!t.closest('.grab') || cy - r.top < 48;
      x0 = cx; y0 = cy - (live || 0); tr.reset(); tr.add(cy);
      state = live ? 'drag' : 'pending';
      if (live) { s.classList.add('dragging'); if (scrim.current) scrim.current.style.transition = 'none'; }
      return true;
    };
    const move = (cx: number, cy: number) => {
      if (state === 'idle') return false;
      const dy = cy - y0, dx = cx - x0;
      if (state === 'pending') {
        if (Math.abs(dy) < 6 && Math.abs(dx) < 6) return false;
        const atTop = (body.current?.scrollTop ?? 0) <= 0;
        if (Math.abs(dx) > Math.abs(dy) || !(inTop || (dy > 0 && atTop))) { state = 'idle'; return false; }
        state = 'drag'; s.classList.add('dragging'); if (scrim.current) scrim.current.style.transition = 'none';
      }
      tr.add(cy);
      set(dy >= 0 ? dy : -rubberband(-dy, h));
      return true;
    };
    const end = (cancel: boolean) => {
      if (state !== 'drag') { state = 'idle'; return; }
      state = 'idle';
      const v = cancel ? 0 : tr.v();
      // close past a third of the height with the finger's momentum, or on a quick flick down
      const close = !cancel && (y + project(v) > 0.35 * h || (v > 400 && y > 24));
      const done = () => {
        stop = null;
        if (close) { wasOpen.current = false; setOn(false); setMounted(false); cb.current.onClose(); cb.current.onExited?.(); }
        reset();
      };
      if (close && RM()) { done(); return; }
      stop = spring(y, close ? h : 0, v, 0.35, set, done);
      // eat the click the release would send to whatever is under the finger
      const f = (e: Event) => { e.stopPropagation(); e.preventDefault(); };
      document.addEventListener('click', f, true); setTimeout(() => document.removeEventListener('click', f, true), 0);
    };

    // touch: the grabber and the header are `touch-action: none`, so their non-passive touchmove never fights a scroll.
    // The body only listens passively: it drags the sheet when it is scrolled to the top, and scrolls otherwise.
    const handled = new WeakSet<Event>();
    const ts = (e: TouchEvent) => { if (e.touches.length === 1) begin(e.touches[0].clientX, e.touches[0].clientY, e.target); else state = 'idle'; };
    const tm = (e: TouchEvent) => {
      if (handled.has(e) || e.touches.length !== 1) return;
      handled.add(e);
      if (move(e.touches[0].clientX, e.touches[0].clientY) && e.cancelable) e.preventDefault();
    };
    const te = () => end(false), tc = () => end(true);
    const pd = (e: PointerEvent) => {
      if (e.pointerType !== 'mouse' || e.button || !begin(e.clientX, e.clientY, e.target)) return;
      const mv = (ev: PointerEvent) => { if (move(ev.clientX, ev.clientY)) ev.preventDefault(); };
      const up = (ev: PointerEvent) => { removeEventListener('pointermove', mv); removeEventListener('pointerup', up); removeEventListener('pointercancel', up); end(ev.type === 'pointercancel'); };
      addEventListener('pointermove', mv); addEventListener('pointerup', up); addEventListener('pointercancel', up);
    };
    const zones = [...s.querySelectorAll<HTMLElement>(HEAD)];
    zones.forEach((z) => z.addEventListener('touchmove', tm, { passive: false }));
    s.addEventListener('touchstart', ts, { passive: true });
    s.addEventListener('touchmove', tm, { passive: true });
    s.addEventListener('touchend', te);
    s.addEventListener('touchcancel', tc);
    s.addEventListener('pointerdown', pd);
    return () => {
      stop?.();
      zones.forEach((z) => z.removeEventListener('touchmove', tm));
      s.removeEventListener('touchstart', ts); s.removeEventListener('touchmove', tm); s.removeEventListener('touchend', te);
      s.removeEventListener('touchcancel', tc); s.removeEventListener('pointerdown', pd);
    };
  }, [mounted]);

  if (!mounted) return null;
  const cover = keepBar ? '' : ' cover';
  // portalled, so a sheet opened from inside another sheet or a card isn't caught in its transform
  return createPortal(
    <>
      {/* close only on a press that starts on the scrim */}
      <div ref={scrim} className={`scrim${cover}${on ? ' on' : ''}`} onPointerDown={(e) => { if (e.target === e.currentTarget) cb.current.onClose(); }} />
      <div ref={ref} className={`sheet${cover}${noClose ? '' : ' has-x'}${on ? ' on' : ''}`} role="dialog" aria-modal="true" aria-label={label} tabIndex={-1}>
        <div className="grab" aria-hidden="true" />
        {!noClose && <button type="button" className="sheet-x" onClick={() => cb.current.onClose()} aria-label="Close"><Icon name="close" size={20} sw={1.8} /></button>}
        <div ref={body} className="body">{children}</div>
        {footer && <div className="foot">{footer}</div>}
      </div>
    </>,
    document.querySelector('.frame') ?? document.body,
  );
}
