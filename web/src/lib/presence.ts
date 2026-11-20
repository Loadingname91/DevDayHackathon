import { useEffect, useRef, useState } from 'react';
import { EASE, RM, T } from './motion';

/**
 * Keeps an element mounted through its exit. Returns a ref for the element and
 * whether to render it. Enter is CSS (`.tag-in`); exit fades in T.stateOut (140).
 */
export function usePresence<E extends HTMLElement>(show: boolean) {
  const [mounted, setMounted] = useState(show);
  const ref = useRef<E>(null);
  useEffect(() => {
    if (show) { setMounted(true); return; }
    const el = ref.current;
    if (!el) { setMounted(false); return; }
    const a = el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: RM() ? T.fb : T.stateOut, easing: EASE, fill: 'forwards' });
    a.finished.then(() => setMounted(false), () => setMounted(false));
    return () => a.cancel();
  }, [show]);
  return { ref, mounted: show || mounted };
}
