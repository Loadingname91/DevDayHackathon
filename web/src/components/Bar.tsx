import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../lib/store';
import { useHoldToTalk } from '../lib/voice';
import { useWide } from '../lib/useWide';
import { useFresh } from '../lib/fresh';
import type { Patch } from '../api/types';
import { Icon } from './Icon';
import { Notch } from './Tag';

/** The pinned bar: 4 pins and the Clair button. It never moves on scroll. Pins are thread targets. */
export function Bar() {
  const home = useStore((s) => s.home);
  const me = useStore((s) => s.me);
  const { pathname, search } = useLocation();
  const wide = useWide();
  const hold = useHoldToTalk(); // tap opens the sheet; hold 450 ms talks, release sends, slide up cancels (lib/voice.ts)
  // the bar hides for focused tasks, which carry their own Back (app.md, "Bar behaviour")
  if (wide || pathname.startsWith('/build') || pathname.startsWith('/chat') || pathname.includes('/do/')
    || (/^\/(a|app)\/[^/]+\/?$/.test(pathname) && /[?&]page=/.test(search))) return null; // the chat has its own field at the bottom; a notebook page open for writing is a focused task too
  const order = me?.workspace.settings.pins ?? [];
  const pins = (home?.apps ?? []).filter((p) => p.pinned).sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key)).slice(0, 4);
  return (
    <nav className="bar" aria-label="Pinned apps and Clair">
      {pins.map((p) => <Pin key={p.key} p={p} on={pathname === `/a/${p.key}`} />)}
      <button className="cell clair" {...hold} aria-label="Clair: tell Clair anything. Hold to talk">
        <span className="ico" aria-hidden="true"><Icon name="spool" size={19} sw={1.8} /></span>
        <span className="lbl">Clair</span>
      </button>
    </nav>
  );
}

function Pin({ p, on }: { p: Patch; on: boolean }) {
  const live = useFresh(`patch:${p.key}`, p.changed);
  return (
    <Link to={`/a/${p.key}`} className={`cell ${on ? 'on' : ''}`} data-dye={p.dye} aria-label={`${p.name}, ${p.face.text} ${p.face.label}${live ? ', just changed' : ''}`}>
      <span className="ico" data-thread-target={p.key} aria-hidden="true"><Icon name={p.icon} size={19} sw={1.8} /></span>
      <span className="lbl">{p.name}</span>
      <Notch show={p.changed} id={`patch:${p.key}`} className="notch" />
    </Link>
  );
}
