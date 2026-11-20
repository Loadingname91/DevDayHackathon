import { useState } from 'react';

type Look = 'workbench' | 'cloth' | 'default';
const LOOKS: [Look, string][] = [['workbench', 'Workbench'], ['cloth', 'Cloth'], ['default', 'Mint']];
const root = typeof document !== 'undefined' ? document.documentElement : null;

/** Three buttons to change the look before you are signed in (the demo menu only exists on mock data). Remembered like `?look=`. */
export function LookSwitch() {
  const [look, setLook] = useState<Look>((root?.dataset.look as Look | undefined) ?? 'default');
  const pick = (v: Look) => {
    setLook(v);
    if (!root) return;
    if (v === 'default') delete root.dataset.look; else root.dataset.look = v;
    try { localStorage.setItem('quilt-look', v); } catch { /* fine without it */ }
  };
  return (
    <div role="group" aria-label="Look" style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
      {LOOKS.map(([v, n]) => (
        <button key={v} type="button" className="chip" aria-pressed={look === v} onClick={() => pick(v)}>{n}</button>
      ))}
    </div>
  );
}
