import { useRef, type ReactNode } from 'react';
import { project, RM, rubberband, spring, tracker } from '../lib/motion';
import { Icon } from './Icon';

/** What a swipe action answers: `false` means it did not happen, so the row springs back. Anything else is a success. */
type Act = () => void | boolean | Promise<void | boolean>;

/**
 * A row that follows the finger sideways (catalogue: "Swipe row"). Right completes,
 * left deletes. 1:1 to ±130 then rubber-band; arms at 90 px with a short buzz; commits
 * past 90 or with a fling (|x + project(v)| > .4w), flying out on a .25 spring; otherwise
 * springs back (.3). A press mid-spring grabs the row where it is. Vertical drags scroll.
 * A swipe may start anywhere on the row, buttons included (put `data-no-swipe` on a control that must not start one);
 * past 10 px the row captures the pointer, so the release does not click what is under the finger.
 * After the fly-out the row waits for the action: it stays gone on success and springs back only if the action answered `false`.
 */
export function SwipeRow({ children, onRight, onLeft, className, ...rest }: {
  children: ReactNode; onRight?: Act; onLeft?: Act; className?: string;
} & React.HTMLAttributes<HTMLLIElement>) {
  const ref = useRef<HTMLLIElement>(null);
  const face = useRef<HTMLDivElement>(null);
  const stop = useRef<(() => void) | null>(null);
  if (!onRight && !onLeft) return <li className={className} {...rest}>{children}</li>;

  const down = (e: React.PointerEvent) => {
    if (e.button || !e.isPrimary || (e.target as Element).closest('input,textarea,select,[data-no-swipe]')) return;
    const el = face.current!, w = ref.current!.offsetWidth, pid = e.pointerId;
    stop.current?.();
    const live = new DOMMatrix(getComputedStyle(el).transform).m41 || 0;
    const x0 = e.clientX - live, y0 = e.clientY, tr = tracker();
    let x = live, state: 'pending' | 'drag' | 'idle' = live ? 'drag' : 'pending', armed = false;
    const set = (v: number) => {
      x = v; el.style.transform = `translateX(${v}px)`;
      ref.current!.dataset.dir = v > 0 ? 'right' : v < 0 ? 'left' : '';
      const a = Math.abs(v) > 90;
      if (a !== armed) { armed = a; ref.current!.dataset.armed = a ? '1' : ''; if (a) try { navigator.vibrate?.(8); } catch { /* no buzz */ } }
    };
    const grab = () => { try { el.setPointerCapture(pid); } catch { /* the pointer is gone */ } };
    if (live) grab();
    const move = (ev: PointerEvent) => {
      if (ev.pointerId !== pid || !ev.isPrimary) return;
      const dx = ev.clientX - x0, dy = ev.clientY - y0;
      if (state === 'pending') {
        if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
        if (Math.abs(dy) > Math.abs(dx)) { state = 'idle'; return end(ev); }
        state = 'drag'; grab();
      }
      if (state !== 'drag') return;
      tr.add(ev.clientX);
      let v = dx;
      if ((v > 0 && !onRight) || (v < 0 && !onLeft)) v = rubberband(v, 40);
      else if (Math.abs(v) > 130) v = Math.sign(v) * (130 + rubberband(Math.abs(v) - 130, w));
      set(v);
    };
    function end(ev: PointerEvent) {
      if (ev.pointerId !== pid) return;
      removeEventListener('pointermove', move); removeEventListener('pointerup', end); removeEventListener('pointercancel', end);
      try { el.releasePointerCapture(pid); } catch { /* already released */ }
      if (state !== 'drag') return;
      const cancelled = ev.type === 'pointercancel';
      const v = cancelled ? 0 : tr.v(), go = !cancelled && (Math.abs(x) > 90 || Math.abs(x + project(v)) > 0.4 * w);
      const dir = x > 0 ? 'right' : 'left';
      const act = dir === 'right' ? onRight : onLeft;
      // eat the click this release would send to the row
      const f = (ev2: Event) => { ev2.stopPropagation(); ev2.preventDefault(); };
      document.addEventListener('click', f, true); setTimeout(() => document.removeEventListener('click', f, true), 0);
      if (go && act) {
        if (RM()) { set(0); void act(); return; }
        stop.current = spring(x, Math.sign(x) * w, v, 0.25, set, () => {
          stop.current = null;
          // the row is gone; the action decides whether it stays gone
          void Promise.resolve(act()).then((ok) => { if (ok === false && ref.current) stop.current = spring(x, 0, 0, 0.3, set); }, () => { if (ref.current) stop.current = spring(x, 0, 0, 0.3, set); });
        });
      } else stop.current = spring(x, 0, v, 0.3, set);
    }
    addEventListener('pointermove', move); addEventListener('pointerup', end); addEventListener('pointercancel', end);
  };

  return (
    <li ref={ref} className={`swrow ${className ?? ''}`} {...rest}>
      {onRight && <span className="sw-bg right" aria-hidden="true"><Icon name="check" size={18} sw={2.4} />Done</span>}
      {onLeft && <span className="sw-bg left" aria-hidden="true">Delete<Icon name="trash" size={18} /></span>}
      <div ref={face} className="sw-face" onPointerDown={down}>{children}</div>
    </li>
  );
}

/** Bring a row back after its action finished but the row is still on screen (a repeating item): unfold it and put its face home. */
export function resetRow(li: Element | null) {
  if (!li || !li.isConnected) return;
  li.getAnimations().forEach((a) => a.cancel());
  const face = li.querySelector<HTMLElement>('.sw-face');
  if (face) face.style.transform = '';
  (li as HTMLElement).dataset.dir = ''; (li as HTMLElement).dataset.armed = '';
}
