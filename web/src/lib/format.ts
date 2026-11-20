// Formatting only. The client never works out "today" from the device clock:
// every date is read from the wall time written in the string, and "today" comes
// from the server's `server_now` (spec/ui-tech-plan.md §1, demo clock).
import type { Collection, Field, Rec } from '../api/types';

const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export type Wall = { y: number; m: number; d: number; hh?: number; mm?: number };
/** Reads "2026-11-20" or "2026-11-20T18:00:00-07:00" as the wall time it states. */
export function wall(iso: string): Wall | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/.exec(iso);
  if (!m) return null;
  return { y: +m[1], m: +m[2], d: +m[3], ...(m[4] !== undefined ? { hh: +m[4], mm: +m[5] } : {}) };
}
export const dayKey = (iso: string) => iso.slice(0, 10);
const utc = (w: Wall) => Date.UTC(w.y, w.m - 1, w.d);
export const dow = (iso: string) => { const w = wall(iso); return w ? new Date(utc(w)).getUTCDay() : 0; };
/** Adds days to a "YYYY-MM-DD" key (calendar arithmetic only, for laying out a week). */
export function addDays(key: string, n: number): string {
  const w = wall(key)!;
  return new Date(utc(w) + n * 86400000).toISOString().slice(0, 10);
}
/** Monday of the week holding this day. */
export const weekStart = (key: string) => addDays(key, -((dow(key) + 6) % 7));

export function time(iso: string): string {
  const w = wall(iso);
  if (!w || w.hh === undefined) return '';
  const h = w.hh % 12 || 12;
  return `${h}:${String(w.mm).padStart(2, '0')} ${w.hh < 12 ? 'am' : 'pm'}`;
}
export function day(iso: string): string {
  const w = wall(iso);
  return w ? `${DOW[dow(iso)]} ${w.d} ${MON[w.m - 1]}` : iso;
}
/** "Fri 20 Nov, 6:00 pm", or "Today, 6:00 pm" when `now` says so. */
export function when(iso: string, now?: string): string {
  const t = time(iso);
  const d = now && dayKey(iso) === dayKey(now) ? 'Today' : day(iso);
  return t ? `${d}, ${t}` : d;
}
export const dowShort = (key: string) => DOW[dow(key)];
export const dayNum = (key: string) => wall(key)!.d;
export const monthName = (key: string) => MON[wall(key)!.m - 1];

/** "a note", "an event": the article for a row's name, for "Add a note". */
export const aNoun = (word: string) => `${/^[aeiou]/i.test(word) ? 'an' : 'a'} ${word}`;

/** Integer cents to "$35.83". Faces arrive already rounded from the server. */
export const money = (cents: number) => `$${(cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const isDone = (r: Rec) => r.properties.done === true || r.properties.status === 'bought';

export type Lookup = (ref: string, id: string) => string | undefined;

/** One field value as the text a row shows. */
export function fieldText(field: Field, value: unknown, now?: string, lookup?: Lookup): string {
  if (value === undefined || value === null || value === '') return '';
  switch (field.type) {
    case 'money': return money(Number(value));
    case 'date':
    case 'datetime': return when(String(value), now);
    case 'bool': return value ? field.label : '';
    case 'select': return field.options?.find((o) => o.id === value)?.label ?? String(value);
    case 'relation': {
      const ids = Array.isArray(value) ? value : [value];
      return ids.map((id) => (field.target && lookup?.(field.target, String(id))) || '').filter(Boolean).join(', ');
    }
    case 'number': {
      const n = Number(value).toLocaleString('en-US');
      if (!field.unit) return n;
      return field.unitFirst ? `${field.unit} ${n}` : `${n} ${field.unit}`;
    }
    case 'repeat': return '';
    default: return String(value);
  }
}

export function title(c: Collection, r: Rec, now?: string, lookup?: Lookup): string {
  const f = c.fields.find((x) => x.key === c.titleField);
  const v = r.properties[c.titleField];
  return (f ? fieldText(f, v, undefined, lookup) : String(v ?? '')) || 'Untitled';
}

/** "Budget, Groceries and Calendar" */
export function listNames(names: string[]): string {
  if (names.length <= 1) return names[0] ?? '';
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}

/** Whole days from one date key to another (calendar days, not 24 h). */
export function daysBetween(from: string, to: string): number {
  const a = wall(from), b = wall(to);
  if (!a || !b) return 0;
  return Math.round((Date.UTC(b.y, b.m - 1, b.d) - Date.UTC(a.y, a.m - 1, a.d)) / 86400000);
}
/** "Overdue · 2 days", "Today", "Tomorrow", "in 3 days", "Sun 22 Nov": a due date against server_now. */
export function relDue(iso: string, now: string): { text: string; overdue: boolean } {
  const n = daysBetween(dayKey(now), dayKey(iso));
  if (n < 0) return { text: `Overdue · ${-n} day${n === -1 ? '' : 's'}`, overdue: true };
  if (n === 0) return { text: 'Today', overdue: false };
  if (n === 1) return { text: 'Tomorrow', overdue: false };
  if (n < 7) return { text: `in ${n} days`, overdue: false };
  return { text: day(iso), overdue: false };
}
/** Clock for timers: 18:42, 1:02:03. */
export function clock(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds)), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}` : `${m}:${String(r).padStart(2, '0')}`;
}
