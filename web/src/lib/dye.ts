import type { AppResponse, Dye, Home } from '../api/types';

/** The nine cloth dyes (tokens.css). The API stores the name; the CSS turns it into a colour. */
export const DYES: readonly Dye[] = ['butter', 'pear', 'sage', 'sea glass', 'chambray', 'lavender', 'blush', 'apricot', 'linen'];

/**
 * Any dye name becomes one of the nine. A name Clair or the server invents (a tenth dye, a typo) would
 * otherwise reach CSS as an unknown value; it gets a stable pick from the nine by hash instead, so
 * the same app is always the same colour. Linen, the neutral, is never picked by hash.
 */
export function normDye(d: unknown): Dye {
  if (typeof d === 'string' && (DYES as readonly string[]).includes(d)) return d as Dye;
  let h = 0;
  for (const ch of String(d ?? '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return DYES[h % (DYES.length - 1)];
}

export const dyedHome = (h: Home): Home => ({ ...h, apps: h.apps.map((a) => ({ ...a, dye: normDye(a.dye) })) });
export const dyedApp = (a: AppResponse): AppResponse => ({ ...a, spec: { ...a.spec, dye: normDye(a.spec.dye) } });
