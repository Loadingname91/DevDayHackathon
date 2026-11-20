// Chats are saved (owner, Nov 20). Every turn is stored on the server already, but the API has one read route
// (`GET /clair/threads/latest`, the last thread within 24 h), no list and no get-by-id. Until it has, this device keeps its own
// archive: after each completed turn the thread is written to IndexedDB, text only (what was said, the answer, one line per card,
// the apps it came from), the last 30 chats and 90 days. It works without IndexedDB (private mode): the list then lives in memory.
// A separate database from the read cache, so a cache schema change or a sign-out wipe never takes the chats with it.

/** What a card said it did, kept as one line: the card's own body is never stored. */
export type SavedCard = { title: string; status: 'basted' | 'stitched' | 'undone' | 'dismissed'; apps: string[] };
export type SavedMsg = {
  role: 'user' | 'clair';
  text: string;
  at: string;
  sources?: string[];
  cards?: SavedCard[];
  /** a message read from the server: it names its change set but not what was in it */
  csId?: string;
};
export type SavedThread = {
  id: string;
  user: string;
  /** the server's thread id once known: "Continue" needs it, and it must still be the latest thread */
  server?: string;
  started: string;
  last: string;
  title: string;
  custom?: boolean;
  apps: string[];
  msgs: SavedMsg[];
  /** a sample chat seeded in a mock build; never written to IndexedDB */
  demo?: boolean;
  /** a deleted server thread: remembered so it is not brought back from `/clair/threads/latest` */
  tomb?: boolean;
};

const DB = 'quilt-chats';
const STORE = 'threads';
export const KEEP = 30;
export const DAYS = 90;
const DAY = 864e5;

let db: Promise<IDBDatabase | null> | null = null;
function open(): Promise<IDBDatabase | null> {
  db ??= new Promise((resolve) => {
    try {
      const req = indexedDB.open(DB, 1);
      req.onupgradeneeded = () => { req.result.createObjectStore(STORE); };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      req.onblocked = () => resolve(null);
    } catch { resolve(null); }
  });
  return db;
}
const key = (user: string, id: string) => `${user}:${id}`;

/** This user's saved chats, newest first, within the limits. Older and surplus ones are dropped from the store as they are found. */
export async function dbLoad(user: string): Promise<SavedThread[]> {
  const d = await open();
  if (!d) return [];
  const all = await new Promise<SavedThread[]>((resolve) => {
    try {
      const req = d.transaction(STORE).objectStore(STORE).getAll();
      req.onsuccess = () => resolve((req.result as SavedThread[]) ?? []);
      req.onerror = () => resolve([]);
    } catch { resolve([]); }
  });
  const mine = all.filter((t) => t && t.user === user && (t.tomb || Array.isArray(t.msgs))).sort((a, b) => Date.parse(b.last) - Date.parse(a.last));
  const fresh = mine.filter((t) => Date.now() - Date.parse(t.last) <= DAYS * DAY);
  const keep = [...fresh.filter((t) => !t.tomb).slice(0, KEEP), ...fresh.filter((t) => t.tomb)];
  for (const t of mine) if (!keep.includes(t)) void dbDelete(user, t.id);
  return keep;
}
export async function dbPut(t: SavedThread): Promise<void> {
  if (t.demo) return;
  const d = await open();
  if (!d) return;
  try { d.transaction(STORE, 'readwrite').objectStore(STORE).put(t, key(t.user, t.id)); } catch { /* quota or private mode: the list stays in memory */ }
}
export async function dbDelete(user: string, id: string): Promise<void> {
  const d = await open();
  if (!d) return;
  try { d.transaction(STORE, 'readwrite').objectStore(STORE).delete(key(user, id)); } catch { /* nothing to delete */ }
}

// ------------------------------------------------------------------------------------------------ the list's words
const startOfDay = (ts: number) => { const d = new Date(ts); d.setHours(0, 0, 0, 0); return d.getTime(); };
export type Group = 'Today' | 'Yesterday' | 'Previous 7 days' | 'Older';
export const GROUPS: Group[] = ['Today', 'Yesterday', 'Previous 7 days', 'Older'];
export function groupOf(ts: number, now = Date.now()): Group {
  const t0 = startOfDay(now);
  if (ts >= t0) return 'Today';
  if (ts >= t0 - DAY) return 'Yesterday';
  if (ts >= t0 - 7 * DAY) return 'Previous 7 days';
  return 'Older';
}
/** "just now", "12 min ago", "3 h ago", "Tue 17 Nov". Time of day in sentence case, as the rest of the app words it. */
export function ago(ts: number, now = Date.now()): string {
  const m = Math.round((now - ts) / 6e4);
  if (m < 1) return 'just now';
  if (m < 60) return `${m} min ago`;
  if (m < 60 * 12 && startOfDay(ts) === startOfDay(now)) return `${Math.round(m / 60)} h ago`;
  return new Date(ts).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' });
}
/** A chat's title: its first line, one line, no model call. */
export const clip = (s: string, n = 80) => s.replace(/\s+/g, ' ').trim().slice(0, n);

// ------------------------------------------------------------------------------------------------ sample chats (mock builds only)
/** Eight sample chats spread over today, yesterday, last week and older, so the history list can be seen full. Marked "sample"; never saved. */
export function seedThreads(now = Date.now()): SavedThread[] {
  const at = (ms: number) => new Date(now - ms).toISOString();
  const M = 6e4, H = 36e5;
  const mk = (n: number, ago_: number, said: string, reply: { text?: string; sources?: string[]; cards?: SavedCard[] }): SavedThread => ({
    id: `sample-${n}`, user: '', started: at(ago_ + 2 * M), last: at(ago_), title: said, demo: true,
    apps: [...new Set([...(reply.sources ?? []), ...(reply.cards ?? []).flatMap((c) => c.apps)])],
    msgs: [
      { role: 'user', text: said, at: at(ago_ + 2 * M) },
      { role: 'clair', text: reply.text ?? '', at: at(ago_), sources: reply.sources, cards: reply.cards },
    ],
  });
  return [
    mk(1, 40 * M, 'Plan my training for next week', { cards: [{ title: "Next week's training", status: 'stitched', apps: ['workout', 'running', 'todos', 'groceries', 'calendar'] }] }),
    mk(2, 3 * H, 'How much did I spend on food this week?', { text: '**$35.83** on groceries so far this week, all at Corner Market.', sources: ['budget', 'groceries'] }),
    mk(3, 26 * H, 'Can I afford $60 concert tickets?', { text: 'Budget has **$412** left of $1,200 this month. A $60 ticket leaves **$352**.', sources: ['budget'] }),
    mk(4, 29 * H, 'add oat milk to groceries', { cards: [{ title: 'Oat milk', status: 'stitched', apps: ['groceries'] }] }),
    mk(5, 3 * 24 * H, "What's due this week?", { text: '**2** things are due this week in Classes.', sources: ['classes', 'todos'] }),
    mk(6, 5 * 24 * H, 'Am I due for any appointments?', { text: 'Nothing yet. Your haircut comes due around **Sat 21 Nov**.', sources: ['calendar'] }),
    mk(7, 12 * 24 * H, 'Build a calories app', { cards: [{ title: 'Calories', status: 'stitched', apps: ['calories'] }] }),
    mk(8, 30 * 24 * H, 'Spent $12 on lunch', { cards: [{ title: 'Lunch', status: 'stitched', apps: ['budget'] }] }),
  ];
}
