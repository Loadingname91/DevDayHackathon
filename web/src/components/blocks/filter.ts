import type { Filter, Rec } from '../../api/types';
import { addDays, dayKey, weekStart } from '../../lib/format';

/**
 * Does a row pass a filter? Dates compare against the server's now (never the device clock).
 * `within`: "today", "week", "past" (before today), "future" (after today), "7d" (the next 7 days), "-7d" (the last 7 days).
 */
export function passes(r: Rec, f: Filter, now: string): boolean {
  const raw = r.properties[f.field];
  if (f.op === 'empty') return raw === undefined || raw === null || raw === '';
  const v = raw === undefined && typeof f.value === 'boolean' ? false : raw;
  if (f.op === 'within') {
    if (typeof v !== 'string' || !now) return false;
    const d = dayKey(v), today = dayKey(now);
    switch (f.value) {
      case 'today': return d === today;
      case 'week': return weekStart(d) === weekStart(today);
      case 'past': return d < today;
      case 'future': return d > today;
    }
    const n = /^(-?)(\d+)d$/.exec(String(f.value));
    if (!n) return true;
    return n[1] ? d <= today && d > addDays(today, -+n[2]) : d >= today && d < addDays(today, +n[2]);
  }
  const eq = Array.isArray(v) ? v.includes(f.value) : v === f.value;
  if (f.op === 'eq') return eq;
  if (f.op === 'ne') return !eq;
  if (f.op === 'lt') return (v as number) < (f.value as number);
  return (v as number) > (f.value as number);
}
export const passesAll = (r: Rec, where: Filter[] | undefined, now: string) => (where ?? []).every((f) => passes(r, f, now));
