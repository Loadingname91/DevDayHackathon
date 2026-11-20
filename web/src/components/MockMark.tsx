import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { anyMock } from '../api/client';
import { MOTION, setMotion } from '../lib/motion';
import { resetStore } from '../lib/store';
import { Sheet } from './Sheet';

const root = typeof document !== 'undefined' ? document.documentElement : null;
const hostTheme = root?.dataset.theme; // the page host may set its own light or dark; "Auto" goes back to it
const FAULTS: [string, string][] = [['', 'None'], ['fail-confirm', 'Confirm fails'], ['no-card', 'No card (Use sample)'], ['slow', 'Slow run'], ['google-off', 'Google not connected']];

/**
 * Any screen showing mock data carries a visible mark (spec/split.md §3). On mocks the
 * mark also opens the demo menu: motion, the 12- or 8-app state, the planner rung and
 * an error case. It starts the mock over in place; nothing here exists on the live API.
 */
export function MockMark() {
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const [motion, setM] = useState(MOTION);
  const [base, setBase] = useState<'seed' | 'before'>('seed');
  const [rung, setRung] = useState<1 | 4>(4);
  const [fault, setFault] = useState('');
  const [look, setLookS] = useState<'default' | 'cloth'>(root?.dataset.look === 'cloth' ? 'cloth' : 'default');
  const [scheme, setSchemeS] = useState<'auto' | 'light' | 'dark'>(root?.dataset.theme && root.dataset.theme !== hostTheme ? (root.dataset.theme as 'light' | 'dark') : 'auto');
  if (!anyMock) return null;
  // Look (the Cloth theme layer) and Colours apply at once; they are a viewing choice, not part of the mock data
  const pickLook = (v: 'default' | 'cloth') => {
    setLookS(v);
    if (!root) return;
    if (v === 'cloth') root.dataset.look = 'cloth'; else delete root.dataset.look;
    try { localStorage.setItem('quilt-look', v); } catch { /* fine without it */ }
  };
  const pickScheme = (v: 'auto' | 'light' | 'dark') => {
    setSchemeS(v);
    if (!root) return;
    const next = v === 'auto' ? hostTheme : v;
    if (next) root.dataset.theme = next; else delete root.dataset.theme;
  };
  const apply = async () => {
    const { resetMock } = await import('../mocks/handler');
    setMotion(motion);
    resetMock({ base, rung, fault });
    setOpen(false);
    nav('/');
    await resetStore();
  };
  const seg = <T extends string | number>(value: T, set: (v: T) => void, opts: [T, string][], label: string) => (
    <div className="demo-row" role="radiogroup" aria-label={label}>
      <span className="demo-l">{label}</span>
      <span className="demo-seg">{opts.map(([v, t]) => <button key={String(v)} role="radio" aria-checked={value === v} onClick={() => set(v)}>{t}</button>)}</span>
    </div>
  );
  return (
    <>
      <button className="mock-mark" onClick={() => setOpen(true)} aria-label="Mock data. Open the demo menu">mock data · demo</button>
      <button className="look-pill" onClick={() => setOpen(true)} aria-label={`Look: ${look === 'cloth' ? 'Cloth' : 'Current'}. Open the demo menu to change the look`}>{look === 'cloth' ? 'Cloth' : 'Current'} look</button>
      <Sheet open={open} onClose={() => setOpen(false)} label="Demo menu">
        <div className="clair-head"><h2>Demo menu</h2><button className="ghost" onClick={() => setOpen(false)}>Close</button></div>
        {seg(look, pickLook, [['default', 'Current'], ['cloth', 'Cloth']], 'Look')}
        {seg(scheme, pickScheme, [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']], 'Colours')}
        <p className="muted small">Look and Colours change at once. Below, Start over resets the mock data; nothing here is on the live API.</p>
        {seg(motion, setM, [['stitch', 'Stitch + peek'], ['threads', 'Threads']], 'Confirm motion')}
        {seg(base, setBase, [['seed', '12 apps'], ['before', '8 apps (builds)']], 'Account')}
        {seg(rung, setRung, [[4, 'Rung 4'], [1, 'Rung 1']], 'Planner')}
        <label className="add-field" htmlFor="demo-fault"><span>Error case</span>
          <select id="demo-fault" className="input" value={fault} onChange={(e) => setFault(e.target.value)}>{FAULTS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
        </label>
        <button className="cta" onClick={apply}>Start over</button>
        <div className="demo-try">
          <span className="h2">Try</span>
          <ul className="muted small">
            <li>Clair → "Spent $12 on lunch" → Add to Budget → Undo on the toast</li>
            <li>Clair → "Plan my training for next week" → Add to 5 apps → Turn on</li>
            <li>Workout → Workflows → Run now (after Undo, the card lands on Home)</li>
            <li>8 apps → Describe an app → a sentence → Make it</li>
            <li>Calendar → Week → next week</li>
          </ul>
        </div>
      </Sheet>
    </>
  );
}
