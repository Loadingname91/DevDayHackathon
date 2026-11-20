import type { ReactNode } from 'react';

/**
 * Content that opens and closes in place ("Add how you feel ›", "More details ›"). It opens by growing from nothing
 * (grid rows 0fr → 1fr plus a fade, 220 ms) and closes faster (140 ms); reduced motion fades in 120 ms and does not move
 * what is below. The content stays mounted: closed, it is hidden and inert, so nothing in it can be focused or read out.
 * Starting open (or closed) animates nothing. The rules are `.disc` in styles/interaction.css.
 * A sibling that should leave as this arrives can be a Disclosure too, with the opposite `open`.
 */
export function Disclosure({ open, children, className = '' }: { open: boolean; children: ReactNode; className?: string }) {
  return (
    <div className={`disc${open ? ' open' : ''}${className ? ` ${className}` : ''}`} inert={!open}>
      <div className="disc-in">{children}</div>
    </div>
  );
}
