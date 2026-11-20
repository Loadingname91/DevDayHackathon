import type { Patch } from '../api/types';

/** Most recently opened first. The API sends `lastOpened: null` for an app nobody has opened yet (a brand-new one): it goes first. */
export const byRecent = (a: Patch, b: Patch): number => (b.lastOpened ?? '￿').localeCompare(a.lastOpened ?? '￿');
