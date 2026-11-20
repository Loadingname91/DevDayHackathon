// Clair's face, ported from spool() in design/prototypes/quilt-home.html (fixspec §A).
// One per screen; sizes 30, 44 or 96. Hop and shake play once, only when the
// expression is newly entered. Reduced motion shows the face only (motion.css).
import { memo, useEffect, useRef } from 'react';

export type Expr = 'hello' | 'working' | 'thinking' | 'waiting' | 'stitched' | 'proud' | 'oops' | 'sleepy';

function svg(expr: Expr, size: 30 | 44 | 96, play: boolean): string {
  const W = '#FFFFFF', INKC = '#2A2119', sm = size <= 44;
  const o = sm ? 2.6 : 1.6, fw = sm ? 2.6 : 1.8, er = sm ? 3.2 : 2.3; // outline, face stroke, eye radius
  const eyes = (dx = 0, dy = 0) => `<g class="eyes"><circle cx="${23 + dx}" cy="${26 + dy}" r="${er}" fill="${W}"/><circle cx="${33 + dx}" cy="${26 + dy}" r="${er}" fill="${W}"/></g>`;
  const P = (d: string) => `<path d="${d}" fill="none" stroke="${W}" stroke-width="${fw}" stroke-linecap="round" stroke-linejoin="round"/>`;
  const happyEyes = P('M20.5 27 q2.5 -3.5 5 0 M30.5 27 q2.5 -3.5 5 0');
  let face = '', extra = '', tail = 'M14 38 C8 40 5 43 0 45', over = '', cls = '';
  switch (expr) {
    case 'hello': face = eyes() + P('M24 31 q4 3 8 0'); cls = play ? 'sp-hop' : ''; break;
    case 'working': face = eyes(1.5, 1.5) + `<ellipse cx="29.5" cy="33" rx="1.8" ry="1.5" fill="${W}"/>`; cls = 'sp-bob'; break;
    case 'thinking': face = eyes(1.5, -2) + P('M26 33 h5'); extra = `<g class="dots"><circle cx="50" cy="8" r="1.8" fill="currentColor"/><circle cx="55" cy="2" r="2.2" fill="currentColor"/><circle cx="61" cy="-5" r="2.6" fill="currentColor"/></g>`; cls = 'sp-think'; break;
    case 'waiting': face = eyes() + P('M20.5 21 q2.5 -2 5 0 M30.5 21 q2.5 -2 5 0') + P('M25 31.5 q3 2 6 0'); extra = `<path d="M41 9 L55 -5 L57 -7 L55 -3 Z" fill="#C9CCD1" stroke="${INKC}" stroke-width="1.2" stroke-linejoin="round"/>`; break;
    case 'stitched': face = happyEyes + P('M23.5 30.5 q4.5 4.5 9 0'); cls = play ? 'sp-hop' : ''; if (sm) extra = `<path d="M46 2l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`; break;
    case 'proud': face = happyEyes + `<circle cx="18.5" cy="31" r="2.1" fill="#F8DCC2"/><circle cx="37.5" cy="31" r="2.1" fill="#F8DCC2"/><path d="M23 30 q5 6.5 10 0 z" fill="${W}"/>`; cls = play ? 'sp-hop' : ''; break;
    case 'oops': face = eyes(0, 1) + P('M20.5 22.5 L25.5 20.5 M30.5 20.5 L35.5 22.5') + P('M23.5 33.5 q1.5 -1.6 3 0 t3 0 t3 0'); tail = ''; over = `<path d="M14 40 l-4 1.5 l2 3 l-4.5 1 l2 3 l-5 1" fill="none" stroke="${INKC}" stroke-width="${o}" stroke-linecap="round" stroke-linejoin="round"/>`; cls = play ? 'sp-shake' : ''; break;
    case 'sleepy': face = P('M20.5 26 q2.5 2 5 0 M30.5 26 q2.5 2 5 0') + P('M26 32.5 q2 1.2 4 0'); extra = `<path d="M47 1h5l-5 6h5M55 -7h4l-4 5h4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`; cls = 'sp-breathe'; break;
  }
  return `<svg class="sp ${cls}" width="${size}" height="${Math.round((size * 70) / 68)}" viewBox="-6 -10 68 70" aria-hidden="true"><g class="body">
    ${tail ? `<path d="${tail}" fill="none" stroke="${INKC}" stroke-width="${o}" stroke-linecap="round" stroke-linejoin="round"/>` : ''}
    <rect x="10" y="6" width="36" height="8" rx="3" fill="#D9B98F" stroke="${INKC}" stroke-width="${o}"/>
    <rect x="14" y="14" width="28" height="28" fill="#3557A6" stroke="${INKC}" stroke-width="${o}"/>
    ${sm ? '' : '<path d="M14 18.5h28M14 38h28" stroke="#FFFFFF" stroke-opacity=".28" stroke-width="1.4"/>'}
    <rect x="10" y="42" width="36" height="8" rx="3" fill="#D9B98F" stroke="${INKC}" stroke-width="${o}"/>
    ${over}${face}</g>${extra}</svg>`;
}

/** The screen's one spool. `key` it per screen so "newly entered" is per screen. Memoised: a parent that re-renders while the hop plays
 *  (a stepper tapped, a tick of the timer) does not swap the svg and cut the hop short. */
export const Spool = memo(function Spool({ expr, size = 44 }: { expr: Expr; size?: 30 | 44 | 96 }) {
  const last = useRef<Expr | null>(null);
  const play = last.current !== expr; // read during render, committed after, so StrictMode's double render agrees
  useEffect(() => { last.current = expr; }, [expr]);
  // re-keying on expr restarts the one-shot animation when the face changes
  return <span key={expr} style={{ display: 'inline-flex', color: 'var(--ink)' }} dangerouslySetInnerHTML={{ __html: svg(expr, size, play) }} />;
});
