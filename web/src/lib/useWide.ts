import { useSyncExternalStore } from 'react';

/** The laptop shell (Laptop board, 1280×800): an apps sidebar, the screen, a detail pane. */
export const WIDE_QUERY = '(min-width: 1024px)';
const mq = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(WIDE_QUERY) : null;
export const isWide = () => !!mq?.matches;
export function useWide(): boolean {
  return useSyncExternalStore((f) => { mq?.addEventListener('change', f); return () => mq?.removeEventListener('change', f); }, isWide, () => false);
}
