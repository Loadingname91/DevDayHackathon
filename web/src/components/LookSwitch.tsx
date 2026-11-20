import { useState } from 'react';

type Look = 'workbench' | 'cloth' | 'default';
const LOOKS: [Look, string][] = [['workbench', 'Workbench'], ['cloth', 'Cloth'], ['default', 'Mint']];
type Scheme = 'auto' | 'light' | 'dark';
const SCHEMES: [Scheme, string][] = [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']];
const root = typeof document !== 'undefined' ? document.documentElement : null;

/** Buttons to change the look and light or dark before you are signed in (the demo menu only exists on mock data). Remembered. */
export function LookSwitch() {
  const [look, setLook] = useState<Look>((root?.dataset.look as Look | undefined) ?? 'default');
  const pick = (v: Look) => {
    setLook(v);
    if (!root) return;
    if (v === 'default') delete root.dataset.look; else root.dataset.look = v;
    try { localStorage.setItem('quilt-look', v); } catch { /* fine without it */ }
  };
  const [scheme, setScheme] = useState<Scheme>((root?.dataset.theme as Scheme | undefined) ?? 'auto');
  const pickScheme = (v: Scheme) => {
    setScheme(v);
    if (!root) return;
    if (v === 'auto') delete root.dataset.theme; else root.dataset.theme = v;
    try { localStorage.setItem('quilt-scheme', v); } catch { /* fine without it */ }
  };
  const row = { display: 'flex', gap: 8, flexWrap: 'wrap' } as const;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div role="group" aria-label="Look" style={row}>
        {LOOKS.map(([v, n]) => (
          <button key={v} type="button" className="chip" aria-pressed={look === v} onClick={() => pick(v)}>{n}</button>
        ))}
      </div>
      <div role="group" aria-label="Light or dark" style={row}>
        {SCHEMES.map(([v, n]) => (
          <button key={v} type="button" className="chip" aria-pressed={scheme === v} onClick={() => pickScheme(v)}>{n}</button>
        ))}
      </div>
    </div>
  );
}
