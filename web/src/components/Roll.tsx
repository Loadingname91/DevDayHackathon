import { useEffect, useLayoutEffect, useRef } from 'react';
import { roll } from '../lib/motion';

const num = (s: string) => { const m = s.replace(/,/g, '').match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : NaN; };

/** A value that rolls when it changes: up for increases, down for decreases. Runs on a ref, never through React state per frame. */
export function Roll({ text, className }: { text: string; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const prev = useRef(text);
  useLayoutEffect(() => {
    const el = ref.current;
    if (el && !el.firstChild) el.append(Object.assign(document.createElement('span'), { textContent: text }));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (prev.current === text) return;
    const a = num(prev.current), b = num(text);
    roll(ref.current, text, !Number.isNaN(a) && !Number.isNaN(b) ? b < a : false);
    prev.current = text;
  }, [text]);
  // The rolling digits are drawn for the eye only (aria-hidden); the value is real text, visually hidden, so a screen reader reads it
  // where it sits (a role-less span cannot carry an aria-label). The .sr span is absolute, so it takes no part in the layout.
  return (
    <>
      <span ref={ref} className={`roll ${className ?? ''}`} aria-hidden="true" />
      <span className="sr">{text}</span>
    </>
  );
}
