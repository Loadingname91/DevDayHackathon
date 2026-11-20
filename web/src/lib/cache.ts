// IndexedDB read cache: the last answer to each GET, so a reopen paints at once
// and then catches up (ADR-008). Live mode only; the mock resets on reload.
const DB = 'quilt-cache';
const STORE = 'get';
const SCHEMA = 1;

let db: Promise<IDBDatabase | null> | null = null;
function open(): Promise<IDBDatabase | null> {
  db ??= new Promise((resolve) => {
    try {
      const req = indexedDB.open(DB, SCHEMA);
      req.onupgradeneeded = () => {
        // a schema change wipes the cache (backend.md §7, cache invalidation)
        for (const name of [...req.result.objectStoreNames]) req.result.deleteObjectStore(name);
        req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    } catch { resolve(null); }
  });
  return db;
}

export async function cacheGet<T>(key: string): Promise<T | null> {
  const d = await open();
  if (!d) return null;
  return new Promise((resolve) => {
    const req = d.transaction(STORE).objectStore(STORE).get(key);
    req.onsuccess = () => resolve((req.result as T) ?? null);
    req.onerror = () => resolve(null);
  });
}
export async function cachePut(key: string, value: unknown): Promise<void> {
  const d = await open();
  if (!d) return;
  try { d.transaction(STORE, 'readwrite').objectStore(STORE).put(value, key); } catch { /* quota or private mode */ }
}
export async function cacheClear(): Promise<void> {
  const d = await open();
  if (!d) return;
  try { d.transaction(STORE, 'readwrite').objectStore(STORE).clear(); } catch { /* nothing to clear */ }
}
