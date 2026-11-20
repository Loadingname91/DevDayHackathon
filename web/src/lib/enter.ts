// A row that arrives in a list that is already on screen grows in. Nothing animates on the first paint, on a tab or a
// list switch, or for a row that was already there: only an id that is new since the list was last drawn (design/DESIGN.md
// §6, "Lists"; frequency decides: adding a row is occasional, ticking and switching are not).
import { useLayoutEffect, useRef } from 'react';
import { EASE, RM, T } from './motion';

/**
 * One row arrives. It grows from nothing to its own height (the one allowed layout animation: small, once, 220 ms) while it
 * fades in, so the rows below move with it. `lift` is for the first row of a list that showed an empty card: it rises 8 px
 * instead of growing, as the card fades out (EmptyState). Reduced motion: opacity only, 120 ms.
 * The row carries `data-enter` while it runs (EmptyState reads it to know a row is arriving).
 */
export function enterRow(li: HTMLElement | null, lift = false) {
  if (!li) return;
  li.dataset.enter = '';
  const clear = () => { delete li.dataset.enter; li.style.overflow = ''; };
  let a: Animation;
  if (RM()) a = li.animate([{ opacity: 0 }, { opacity: 1 }], { duration: T.fb, easing: EASE });
  else if (lift) a = li.animate([{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: T.state, easing: EASE });
  else {
    const h = li.offsetHeight; // the natural height, measured before the first frame
    li.style.overflow = 'hidden'; // a swipe row already clips; a plain row needs it while it grows
    a = li.animate([{ height: '0px', opacity: 0 }, { height: `${h}px`, opacity: 1 }], { duration: T.state, easing: EASE });
  }
  a.finished.then(clear, clear);
}

/**
 * Plays `enterRow` for each id that is new since the last commit, on the row element `[data-row="<id>"]`.
 * `ids`: every row the list holds (drawn or not, so a row that moves between sections, or appears when a section opens or
 * "Show all" is pressed, is not new); `null` while the data is not there yet. `scope` names which list this is (a picked
 * chip, say): a change of scope re-baselines without animating. `lift`: the first row of an empty list rises instead.
 */
export function useRowEnter(ids: readonly string[] | null, o: { scope?: string; lift?: boolean } = {}) {
  const prev = useRef<{ scope: string; ids: Set<string> } | null>(null);
  useLayoutEffect(() => {
    if (!ids) return;
    const scope = o.scope ?? '', was = prev.current;
    prev.current = { scope, ids: new Set(ids) };
    if (!was || was.scope !== scope) return; // first paint, or another list
    for (const id of ids) if (!was.ids.has(id)) enterRow(document.querySelector<HTMLElement>(`[data-row="${CSS.escape(id)}"]`), !!o.lift && was.ids.size === 0);
  });
}
