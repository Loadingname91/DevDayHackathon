import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../lib/store';
import { useHoldToTalk } from '../lib/voice';
import { useWide } from '../lib/useWide';
import { Icon } from './Icon';

/** The pinned bar: 4 pins and the Clair button. It never moves on scroll. Pins are thread targets. */
export function Bar() {
  const home = useStore((s) => s.home);
  const me = useStore((s) => s.me);
  const { pathname } = useLocation();
  const wide = useWide();
  const hold = useHoldToTalk(); // tap opens the sheet; hold 450 ms talks, release sends, slide up cancels (lib/voice.ts)
  // the bar hides for focused tasks, which carry their own Back (app.md, "Bar behaviour")
  if (wide || pathname.startsWith('/build') || pathname.includes('/do/')) return null;
  const order = me?.workspace.settings.pins ?? [];
  const pins = (home?.apps ?? []).filter((p) => p.pinned).sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key)).slice(0, 4);
  return (
    <nav className="bar" aria-label="Pinned apps and Clair">
      {pins.map((p) => (
        <Link key={p.key} to={`/a/${p.key}`} className={`cell ${pathname === `/a/${p.key}` ? 'on' : ''}`} data-dye={p.dye} aria-label={`${p.name}, ${p.face.text} ${p.face.label}${p.changed ? ', just changed' : ''}`}>
          <span className="ico" data-thread-target={p.key} aria-hidden="true"><Icon name={p.icon} size={19} sw={1.8} /></span>
          <span className="lbl">{p.name}</span>
          {p.changed && <span className="notch" aria-hidden="true" />}
        </Link>
      ))}
      <button className="cell clair" {...hold} aria-label="Clair: tell Clair anything. Hold to talk">
        <span className="ico" aria-hidden="true"><Icon name="spool" size={19} sw={1.8} /></span>
        <span className="lbl">Clair</span>
      </button>
    </nav>
  );
}
