import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../lib/store';
import { useHoldToTalk } from '../lib/voice';
import { CG } from './clair/Glyph';
import { byRecent } from '../lib/recent';
import { Icon } from './Icon';
import { LogoMark } from './Logo';
import { useFresh } from '../lib/fresh';
import type { Patch } from '../api/types';
import { Tag } from './Tag';

/**
 * The laptop's apps sidebar (Laptop board): the mark, Tell Clair anything, Search (⌘K finds
 * an app by name; it does not search rows), every app (pins first, then most used), New app, and you. The app tiles are
 * thread targets, like the bar's pins on a phone.
 */
export function Sidebar() {
  const home = useStore((s) => s.home);
  const me = useStore((s) => s.me);
  const { pathname } = useLocation();
  const [q, setQ] = useState('');
  const find = useRef<HTMLInputElement>(null);
  const hold = useHoldToTalk(); // the same hold as the phone's Clair cell
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); find.current?.focus(); } };
    addEventListener('keydown', key);
    return () => removeEventListener('keydown', key);
  }, []);
  const order = me?.workspace.settings.pins ?? [];
  const apps = home?.apps ?? [];
  const pins = apps.filter((p) => p.pinned).sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key));
  const rest = apps.filter((p) => !p.pinned).sort(byRecent);
  const needle = q.trim().toLowerCase();
  const list = [...pins, ...rest].filter((a) => a.name.toLowerCase().includes(needle));
  const current = /^\/a\/([^/]+)/.exec(pathname)?.[1];

  return (
    <aside className="side" aria-label="Apps">
      <Link to="/" className="side-logo" aria-label="Home" aria-current={pathname === '/' ? 'page' : undefined}><LogoMark />quilt</Link>
      <button type="button" className="side-clair" {...hold}><Icon name="spool" size={20} sw={1.8} />Tell Clair anything</button>
      <Link to="/chat" className="side-chat" aria-current={pathname === '/chat' ? 'page' : undefined}><CG name="chat" size={16} />Chat</Link>
      <label className="side-find">
        <Icon name="search" size={16} sw={1.8} />
        <input ref={find} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find an app" aria-label="Find an app" autoComplete="off"
          onKeyDown={(e) => { if (e.key === 'Escape') { setQ(''); e.currentTarget.blur(); } }} />
        <kbd>⌘K</kbd>
      </label>
      <span className="side-sec">Apps</span>
      <nav className="side-apps" aria-label="Your apps">
        {list.map((p) => <SideApp key={p.key} p={p} on={current === p.key} />)}
        {!list.length && <span className="side-none">No app called “{q.trim()}”.</span>}
      </nav>
      <Link to="/build" className="side-new"><Icon name="plus" size={16} sw={1.8} />New app</Link>
      <Link to="/you" className="side-you">
        <span className="avatar" data-dye="blush" aria-hidden="true"><Icon name="user" size={15} sw={1.8} /></span>
        {me ? `${me.user.display_name} · ${me.credits.left} credits` : 'You'}
      </Link>
    </aside>
  );
}

function SideApp({ p, on }: { p: Patch; on: boolean }) {
  const live = useFresh(`patch:${p.key}`, !!p.changed && !p.isNew); // same clock as Home's patch and the bar's pin
  return (
    <Link to={`/a/${p.key}`} className="side-app" data-dye={p.dye} aria-current={on ? 'page' : undefined}
      aria-label={`${p.name}, ${p.face.text} ${p.face.label}${p.isNew ? ', new' : live ? ', just changed' : ''}`}>
      <span className="tile" data-thread-target={p.key} aria-hidden="true"><Icon name={p.icon} size={15} sw={1.8} /></span>
      <span className="nm">{p.name}</span>
      <Tag show={!!p.changed || !!p.isNew} text={p.isNew ? 'new' : 'just changed'} id={p.isNew ? undefined : `patch:${p.key}`} />
    </Link>
  );
}
