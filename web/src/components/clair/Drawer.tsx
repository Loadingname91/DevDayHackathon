import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { RM, T } from '../../lib/motion';

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),textarea,select,[tabindex]:not([tabindex="-1"])';

/**
 * A panel that slides in from the left over the screen (the phone's chat history). It slides in 350 ms on the ease, the backdrop fades
 * in 220; tap outside, Escape or a swipe left closes it (the panel follows the finger, then goes or springs back). Focus moves in,
 * stays in (Tab wraps) and returns to what opened it; the page behind is `inert` through `onInert`. Transform and opacity only.
 * Reduced motion: a 120 ms fade, no travel.
 */
export function Drawer({ open, onClose, label, children, onInert }: { open: boolean; onClose: () => void; label: string; children: ReactNode; onInert?: (on: boolean) => void }) {
  const [mounted, setMounted] = useState(open);
  const [on, setOn] = useState(false);
  const panel = useRef<HTMLDivElement>(null);
  const from = useRef<HTMLElement | null>(null);
  const cb = useRef({ onClose, onInert });
  useLayoutEffect(() => { cb.current = { onClose, onInert }; });

  // open: mount, then start the slide in the same frame
  useLayoutEffect(() => {
    if (!open) return;
    from.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setMounted(true);
  }, [open]);
  useLayoutEffect(() => {
    if (!open || !mounted) return;
    panel.current?.getBoundingClientRect(); // commit the closed state, so the next class change is a transition
    setOn(true);
  }, [open, mounted]);
  useEffect(() => { if (on) { cb.current.onInert?.(true); panel.current?.focus({ preventScroll: true }); } }, [on]);

  // close: slide out, then unmount and give the focus back
  useEffect(() => {
    if (open || !mounted) return;
    setOn(false);
    cb.current.onInert?.(false);
    const t = setTimeout(() => { setMounted(false); const f = from.current; from.current = null; if (f?.isConnected) f.focus({ preventScroll: true }); }, RM() ? T.fb : T.layoutOut);
    return () => clearTimeout(t);
  }, [open, mounted]);
  useEffect(() => () => cb.current.onInert?.(false), []);

  // Escape closes; Tab wraps inside
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // a row's menu, rename field or search that has something to cancel takes the first Escape
        const t = e.target as HTMLElement;
        if (t.closest?.('.editing') || (t instanceof HTMLInputElement && t.type === 'search' && t.value)) return;
        e.stopImmediatePropagation(); cb.current.onClose(); return;
      }
      if (e.key !== 'Tab' || !panel.current) return;
      const f = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((x) => x.offsetParent !== null);
      if (!f.length) { e.preventDefault(); return; }
      const a = document.activeElement;
      if (e.shiftKey && (a === f[0] || a === panel.current)) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && a === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    };
    addEventListener('keydown', key, true);
    return () => removeEventListener('keydown', key, true);
  }, [open]);

  // swipe left to close: the panel follows the finger 1:1, goes past a third of its width (or on a quick flick), else comes back
  useEffect(() => {
    const el = panel.current;
    if (!el || !mounted) return;
    let x0 = 0, y0 = 0, t0 = 0, dx = 0, state: 'idle' | 'pending' | 'drag' = 'idle', id = -1;
    const down = (e: PointerEvent) => { if (e.pointerType === 'mouse') return; state = 'pending'; x0 = e.clientX; y0 = e.clientY; t0 = e.timeStamp; dx = 0; id = e.pointerId; };
    const move = (e: PointerEvent) => {
      if (state === 'idle' || e.pointerId !== id) return;
      const mx = e.clientX - x0, my = e.clientY - y0;
      if (state === 'pending') {
        if (Math.abs(mx) < 8 && Math.abs(my) < 8) return;
        if (Math.abs(my) > Math.abs(mx) || mx > 0) { state = 'idle'; return; } // a scroll, or a swipe the wrong way
        state = 'drag'; el.classList.add('dragging');
        try { el.setPointerCapture(id); } catch { /* the window listeners below carry it */ }
      }
      dx = Math.min(0, mx);
      el.style.transform = `translateX(${dx}px)`;
    };
    const up = (e: PointerEvent) => {
      if (state !== 'drag' || e.pointerId !== id) { state = 'idle'; return; }
      state = 'idle';
      const v = dx / Math.max(1, e.timeStamp - t0); // px per ms, negative leftwards
      el.classList.remove('dragging');
      const shut = dx < -el.offsetWidth / 3 || (v < -0.5 && dx < -24);
      el.style.transform = '';
      if (shut) cb.current.onClose();
      const f = (ev: Event) => { ev.stopPropagation(); ev.preventDefault(); };
      el.addEventListener('click', f, true); setTimeout(() => el.removeEventListener('click', f, true), 0); // the release is not a tap on a row
    };
    el.addEventListener('pointerdown', down); el.addEventListener('pointermove', move); el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
    return () => { el.removeEventListener('pointerdown', down); el.removeEventListener('pointermove', move); el.removeEventListener('pointerup', up); el.removeEventListener('pointercancel', up); };
  }, [mounted]);

  if (!mounted) return null;
  return (
    <>
      <div className={`dr-scrim${on ? ' on' : ''}`} onPointerDown={() => cb.current.onClose()} aria-hidden="true" />
      <div ref={panel} className={`dr${on ? ' on' : ''}`} role="dialog" aria-modal="true" aria-label={label} tabIndex={-1}>{children}</div>
    </>
  );
}
