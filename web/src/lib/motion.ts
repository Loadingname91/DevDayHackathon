// Ported from design/prototypes/quilt-flows.html and quilt-home.html with the
// signatures of spec/ui-tech-plan.md §7. The prototype code is the reference.
export const EASE = 'cubic-bezier(.16,1,.3,1)';
export const EASE_THREAD = 'cubic-bezier(.45,0,.15,1)';
export const T = {
  fb: 120, state: 220, layout: 350, focal: 600, stateOut: 140, layoutOut: 220, focalOut: 360,
  /** a landed change stays on screen this long before it clears (Peek hold, Clair closing after the last landing) */
  land: 500, hold: 700,
  /** how long Clair may stay silent before "Use sample" is offered */
  slow: 12000,
};
/** Arrival stagger (catalogue N3): 40 ms apart, capped at the third. Use STAGGER[Math.min(i, 2)]. */
export const STAGGER = [0, 40, 90] as const;

const mq = typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : null;
let rm = !!mq?.matches;
mq?.addEventListener('change', (e) => { rm = e.matches; });
/** Live reduced-motion flag. */
export const RM = () => rm;

export const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** Gesture release: critically damped spring (no overshoot), carries finger speed. Returns a cancel function. */
export function spring(from: number, to: number, v0: number, response: number, onUpdate: (x: number, v: number) => void, onDone?: () => void): () => void {
  if (rm) { onUpdate(to, 0); onDone?.(); return () => {}; }
  const w = (2 * Math.PI) / response, x0 = from - to, t0 = performance.now();
  let id = 0;
  const step = (n: number) => {
    const t = (n - t0) / 1000, e = Math.exp(-w * t);
    const x = (x0 + (v0 + w * x0) * t) * e, v = (v0 - w * (v0 + w * x0) * t) * e;
    if (Math.abs(x) < 0.5 && Math.abs(v) < 5) { onUpdate(to, 0); onDone?.(); } else { onUpdate(to + x, v); id = requestAnimationFrame(step); }
  };
  id = requestAnimationFrame(step);
  return () => cancelAnimationFrame(id);
}
export const project = (v: number, d = 0.995) => ((v / 1000) * d) / (1 - d);
export const rubberband = (o: number, d: number, c = 0.55) => (o * d * c) / (d + c * Math.abs(o));
/** Velocity (px/s) from the last 3 move samples. */
export const tracker = () => {
  let a: [number, number][] = [];
  return {
    add(x: number) { a.push([x, performance.now()]); if (a.length > 3) a.shift(); },
    v() {
      if (a.length < 2) return 0;
      const [x0, t0] = a[0], [x1, t1] = a[a.length - 1];
      if (performance.now() - t1 > 80) return 0; // finger paused before lifting
      return t1 > t0 ? ((x1 - x0) / (t1 - t0)) * 1000 : 0;
    },
    reset() { a = []; },
  };
};

/** `color`: the thread takes the target app's deep dye (Soft Quilt has no mustard; ADR-009). */
type Pair = { from: Element; to: Element; top?: boolean; color?: string };
type PullOpts = { frame: HTMLElement; pairs: Pair[]; onLand: (i: number) => void; alive: () => boolean };
const NS = 'http://www.w3.org/2000/svg';

function drawPaths(frame: HTMLElement, pairs: Pair[]) {
  const fr = frame.getBoundingClientRect(), ox = fr.left + frame.clientLeft, oy = fr.top + frame.clientTop;
  const pt = (el: Element, top?: boolean) => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2 - ox, y: (top ? r.top : r.top + r.height / 2) - oy }; };
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 'threads');
  svg.setAttribute('aria-hidden', 'true');
  frame.appendChild(svg);
  const paths = pairs.map(({ from, to, top, color }) => {
    const a = pt(from), b = pt(to, top), dy = Math.max(40, (b.y - a.y) * 0.55);
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', `M${a.x},${a.y} C${a.x},${a.y + dy} ${b.x},${b.y - dy} ${b.x},${b.y}`);
    path.style.stroke = color || getComputedStyle(frame).color;
    svg.appendChild(path);
    return path;
  });
  return { svg, paths };
}

/** Signature thread pull: draw with the thread curve, land at 70% of each draw (120 ms stagger), fade 400 ms after the last landing. */
export async function threadPull({ frame, pairs, onLand, alive }: PullOpts): Promise<boolean> {
  if (rm || !pairs.length) { pairs.forEach((_, i) => onLand(i)); return alive(); }
  const { svg, paths } = drawPaths(frame, pairs);
  const lands = paths.map((path, i) => {
    const L = path.getTotalLength();
    path.style.strokeDasharray = String(L);
    path.style.strokeDashoffset = String(L);
    path.animate([{ strokeDashoffset: L }, { strokeDashoffset: 0 }], { duration: T.focal, delay: i * 120, easing: EASE_THREAD, fill: 'forwards' });
    return sleep(i * 120 + T.focal * 0.7).then(() => { if (alive()) onLand(i); });
  });
  await Promise.all(lands);
  await sleep(400);
  if (alive()) await svg.animate([{ opacity: 1 }, { opacity: 0 }], { duration: T.layoutOut, easing: EASE, fill: 'forwards' }).finished;
  svg.remove();
  return alive();
}

/** Undo, or a failed confirm: the threads pull back toward the source. */
export async function retractThreads({ frame, pairs, alive }: Omit<PullOpts, 'onLand'>): Promise<void> {
  if (rm || !pairs.length) return;
  const { svg, paths } = drawPaths(frame, pairs);
  await Promise.all(paths.map((path) => {
    const L = path.getTotalLength();
    path.style.strokeDasharray = String(L);
    return path.animate([{ strokeDashoffset: 0 }, { strokeDashoffset: L }], { duration: T.focalOut, easing: EASE_THREAD, fill: 'forwards' }).finished;
  }));
  svg.remove();
}

/** Number roll: up for increases, down for decreases. `el` holds one <span> per value. */
export function roll(el: HTMLElement | null, text: string, down: boolean) {
  if (!el) return;
  const old = el.lastElementChild as HTMLElement | null;
  if (old?.textContent === text) return;
  [...el.children].slice(0, -1).forEach((c) => c.remove());
  if (rm || !old) { el.replaceChildren(Object.assign(document.createElement('span'), { textContent: text })); return; }
  // a roll caught mid-roll: freeze both halves where they are, then leave from there (no jump back to rest)
  old.getAnimations().forEach((a) => { try { a.commitStyles(); } catch { /* not rendered */ } a.cancel(); });
  const nu = document.createElement('span');
  nu.textContent = text;
  el.append(nu);
  const d = down ? 100 : -100;
  old.animate([{ transform: `translateY(${d}%)`, opacity: 0 }], { duration: T.state, easing: EASE, fill: 'forwards' }).finished.then(() => old.remove(), () => {});
  nu.animate([{ transform: `translateY(${-d}%)`, opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: T.state, easing: EASE });
}

/** FLIP: record tops of [data-f] children, run the mutation, translate each back into place. */
export async function flip(container: HTMLElement, mutate: () => void | Promise<void>) {
  const items = () => [...container.querySelectorAll<HTMLElement>('[data-f]')];
  const first = new Map(items().map((e) => [e.dataset.f!, e.getBoundingClientRect().top]));
  await mutate();
  // a card that left with exitUp and came back from the reload must not stay at opacity 0
  container.getAnimations({ subtree: true }).forEach((a) => { if (a.id === 'exit-up') a.cancel(); });
  if (rm) return;
  await Promise.all(items().map((e) => {
    const was = first.get(e.dataset.f!);
    if (was === undefined) return e.animate([{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: T.state, easing: EASE }).finished;
    const dy = was - e.getBoundingClientRect().top;
    if (Math.abs(dy) < 0.5) return null;
    return e.animate([{ transform: `translateY(${dy}px)` }, { transform: 'none' }], { duration: T.layout, easing: EASE }).finished;
  }));
}

/** The deep dye of the app an element belongs to, for its thread. */
export function dyeOf(el: Element): string | undefined {
  const host = el.closest('[data-dye]');
  return host ? getComputedStyle(host).getPropertyValue('--deep').trim() || undefined : undefined;
}

/** Exit: fade (and lift 8px unless reduced motion), T.stateOut. Resolves when done. The hold (fill forwards) is named
 *  'exit-up': flip() cancels it after the mutation, so a card the reload returns is not left invisible. */
export function exitUp(el: Element | null): Promise<unknown> {
  if (!el) return Promise.resolve();
  const a = el.animate(rm ? [{ opacity: 1 }, { opacity: 0 }] : [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-8px)' }],
    { duration: rm ? T.fb : T.stateOut, easing: EASE, fill: 'forwards' });
  a.id = 'exit-up';
  return a.finished.catch(() => {});
}

/** Crossfade + height: run `mutate`, then animate `el` from its old height to the new one (220). */
export async function resize(el: HTMLElement | null, mutate: () => void | Promise<void>) {
  if (!el || rm) { await mutate(); return; }
  const h0 = el.offsetHeight; // the live height, also when an earlier resize is still running
  el.getAnimations().forEach((a) => { if (a.id === 'resize') a.cancel(); });
  await mutate();
  const h1 = el.offsetHeight;
  if (Math.abs(h1 - h0) < 2) return;
  el.animate([{ height: `${h0}px` }, { height: `${h1}px` }], { duration: T.state, easing: EASE }).id = 'resize';
}

// ---------------------------------------------------------------- stitch-in (replaces the thread pull; owner idea, Nov 19 night)
/** `?motion=threads` brings back the thread pull for comparison; the default is the stitch-in. */
export let MOTION: 'stitch' | 'threads' = (() => {
  try {
    const q = new URLSearchParams(location.search).get('motion');
    if (q) sessionStorage.setItem('quilt:motion', q);
    return (q ?? sessionStorage.getItem('quilt:motion')) === 'threads' ? 'threads' : 'stitch';
  } catch { return 'stitch'; }
})();

export function setMotion(m: 'stitch' | 'threads') {
  MOTION = m;
  try { sessionStorage.setItem('quilt:motion', m); } catch { /* private mode */ }
}

let maskSeq = 0;
/**
 * A running stitch sews itself around a tile: a dashed seam in the app's dye, revealed
 * clockwise from the top left by a mask (T.focal, EASE_THREAD), 120 ms between tiles,
 * landing at 70% of the draw. 400 ms after the last landing the seams fade (T.layoutOut).
 * `reverse` is the seam ripper: the seam starts whole and pulls out (T.focalOut, EASE);
 * it lands at once so numbers roll back while the stitch comes out.
 * Reduced motion: no drawing; every onLand fires at once.
 */
export async function stitchIn({ els, onLand, alive, reverse = false }: {
  els: { el: Element; color?: string }[]; onLand: (i: number) => void; alive: () => boolean; reverse?: boolean;
}): Promise<void> {
  if (rm || !els.length) { els.forEach((_, i) => onLand(i)); return; }
  const made = els.map(({ el, color }) => {
    const host = el as HTMLElement;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    const r = host.getBoundingClientRect(), pad = 3, W = r.width + pad * 2, H = r.height + pad * 2;
    const rad = Math.min(parseFloat(getComputedStyle(host).borderTopLeftRadius) || 12, r.height / 2) + pad;
    const id = `stitch-m${++maskSeq}`;
    const sw = 1.2; // half the stroke, so the seam sits inside the svg box
    const w = W - sw * 2, h = H - sw * 2, rr = Math.min(rad, h / 2, w / 2);
    const L = 2 * (w + h) - (8 - 2 * Math.PI) * rr;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'stitch-ov');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('width', String(W)); svg.setAttribute('height', String(H));
    svg.style.cssText = `position:absolute;left:${-pad}px;top:${-pad}px;overflow:visible;pointer-events:none;z-index:2;color:${color ?? 'currentColor'}`;
    svg.innerHTML = `<defs><mask id="${id}" maskUnits="userSpaceOnUse" x="-6" y="-6" width="${W + 12}" height="${H + 12}">
      <rect class="m" x="${sw}" y="${sw}" width="${w}" height="${h}" rx="${rr}" fill="none" stroke="#fff" stroke-width="7" stroke-dasharray="${L} ${L}" stroke-dashoffset="${reverse ? 0 : L}"/></mask></defs>
      <rect x="${sw}" y="${sw}" width="${w}" height="${h}" rx="${rr}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="5 4.5" mask="url(#${id})"/>`;
    host.appendChild(svg);
    return { svg, m: svg.querySelector<SVGRectElement>('.m')!, L };
  });
  const runs = made.map(({ m, L }, i) => {
    if (reverse) {
      const a = m.animate([{ strokeDashoffset: 0 }, { strokeDashoffset: L }], { duration: T.focalOut, delay: i * 60, easing: EASE, fill: 'forwards' });
      if (alive()) onLand(i);
      return a.finished.catch(() => {});
    }
    m.animate([{ strokeDashoffset: L }, { strokeDashoffset: 0 }], { duration: T.focal, delay: i * 120, easing: EASE_THREAD, fill: 'forwards' });
    return sleep(i * 120 + T.focal * 0.7).then(() => { if (alive()) onLand(i); });
  });
  await Promise.all(runs);
  if (!reverse) await sleep(400 + T.focal * 0.3);
  await Promise.all(made.map(({ svg }) => svg.animate([{ opacity: 1 }, { opacity: 0 }], { duration: T.layoutOut, easing: EASE, fill: 'forwards' }).finished.catch(() => {})));
  made.forEach(({ svg }) => svg.remove());
}

/**
 * Can this thread target be seen right now? Not under a sheet or the scrim. Behind an open sheet the page is `inert`
 * and inert nodes are not hit-testable, so there the answer is by geometry: a pinned-bar tile is seen unless the
 * sheet covers it; anything else is under the scrim.
 */
export function seen(e: Element): boolean {
  const r = e.getBoundingClientRect();
  if (!r.width || r.bottom < 0 || r.top > innerHeight) return false;
  if (e.closest('[inert]')) {
    if (!e.closest('.bar')) return false;
    return ![...document.querySelectorAll('.sheet.on')].some((s) => { const q = s.getBoundingClientRect(); return r.left < q.right && r.right > q.left && r.top < q.bottom && r.bottom > q.top; });
  }
  const hit = document.elementFromPoint(r.left + r.width / 2, Math.min(innerHeight - 1, Math.max(1, r.top + 6)));
  return !!hit && (e === hit || e.contains(hit));
}

/** A sheet is open (or rising). The receipt capsule waits behind it, and a card inside it has its own Undo. */
export const sheetOpen = () => typeof document !== 'undefined' && !!document.querySelector('.sheet.on');

/**
 * Where each target app can be seen: its pinned-bar tile first, then its Home patch,
 * and only if nothing (a sheet, the scrim) covers it. The rest are "hidden". Apps in
 * `numbered` (their face changes) count as hidden when only their pin shows.
 */
export function locate(apps: string[], numbered: string[] = []) {
  const visible: { app: string; el: Element }[] = [], hidden: string[] = [];
  for (const app of apps) {
    const all = [...document.querySelectorAll(`[data-thread-target="${app}"]`)];
    const el = [...all.filter((e) => e.closest('.bar')), ...all.filter((e) => !e.closest('.bar'))].find(seen);
    // a pin shows no number: an app whose number changes creeps up instead, so the roll is seen
    if (el && !(numbered.includes(app) && el.closest('.bar'))) visible.push({ app, el }); else hidden.push(app);
  }
  return { visible, hidden };
}
