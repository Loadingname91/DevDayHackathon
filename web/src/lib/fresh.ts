import { useEffect, useReducer } from 'react';

/** How long a "just changed" marker stays before it lets go on its own (ms). Opening the app clears it sooner (the server resets `changed`). */
export const FRESH_MS = 8000;

// first time each marker was seen active; module-level so Home remounts and navigation don't restart the clock
const seen = new Map<string, number>();

/**
 * Time-limits a "just changed" marker. Returns true while `active` and within `ttl` of the first time this id was active;
 * false after, so the chip/notch exits through usePresence. The clock restarts only after the marker has gone inactive
 * (a new change). Without an id (a "new" tag) it never expires.
 */
export function useFresh(id: string | undefined, active: boolean, ttl = FRESH_MS): boolean {
  const [, tick] = useReducer((n: number) => n + 1, 0);
  if (id) {
    if (!active) seen.delete(id);
    else if (!seen.has(id)) seen.set(id, Date.now());
  }
  const left = id && active ? ttl - (Date.now() - (seen.get(id) ?? Date.now())) : Infinity;
  useEffect(() => {
    if (!isFinite(left) || left <= 0) return;
    const t = setTimeout(tick, left + 20);
    return () => clearTimeout(t);
  }, [left > 0, id, active]); // eslint-disable-line react-hooks/exhaustive-deps
  return !id || !active || left > 0;
}
