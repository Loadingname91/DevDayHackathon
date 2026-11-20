import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { GROUPS, groupOf, type Group } from '../../lib/chats';
import { useStore } from '../../lib/store';
import { chatRows, deleteChat, newChat, openThread, renameChat, useTurns, type ChatRow } from '../../lib/turns';
import { Icon } from '../Icon';
import { CG } from './Glyph';

type Mode = { id: string; kind: 'menu' | 'rename' | 'delete' } | null;

/**
 * The history of chats, like the ones you know from ChatGPT or Claude: New chat on top, a search over the titles, the chats grouped by
 * Today, Yesterday, Previous 7 days and Older. A row is the first line you said; the dot is the app it touched; the chat you are in is
 * the heavier row with a tack stitch beside it. Each row has a "…" (Rename, Delete with an inline "Delete this chat? Delete / Keep").
 * Chats are kept on this device. Arrow keys move through the list, Enter opens. The rail on a laptop and the drawer on a phone are this list.
 */
export function ChatList({ onPick, onNew }: { onPick?: () => void; onNew?: () => void }) {
  const ts = useTurns();
  const apps = useStore((s) => s.home?.apps) ?? [];
  const [q, setQ] = useState('');
  const [mode, setMode] = useState<Mode>(null);
  const root = useRef<HTMLElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const newBtn = useRef<HTMLButtonElement>(null);
  const rows = useMemo(() => chatRows(ts), [ts.archive, ts.convs, ts.current]); // eslint-disable-line react-hooks/exhaustive-deps
  const needle = q.trim().toLowerCase();
  const shown = needle ? rows.filter((r) => r.title.toLowerCase().includes(needle)) : rows;
  const now = Date.now();
  const groups = GROUPS.map((g) => [g, shown.filter((r) => groupOf(r.last, now) === g)] as [Group, ChatRow[]]).filter(([, r]) => r.length);

  // a menu left open when the list changes under it (a chat deleted, a search typed) is closed
  useEffect(() => { if (mode && !rows.some((r) => r.id === mode.id)) setMode(null); }, [rows, mode]);

  const key = (e: KeyboardEvent) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp' && e.key !== 'Home' && e.key !== 'End') return;
    const t = e.target as HTMLElement;
    if (t.tagName === 'INPUT' && t !== search.current) return; // the rename field keeps its arrows
    const stops = [search.current, ...(root.current?.querySelectorAll<HTMLElement>('.hx-open') ?? [])].filter(Boolean) as HTMLElement[];
    const i = stops.indexOf(t);
    if (i < 0) return;
    e.preventDefault();
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? stops.length - 1 : Math.max(0, Math.min(stops.length - 1, i + (e.key === 'ArrowDown' ? 1 : -1)));
    stops[j]?.focus();
  };
  const start = () => { newChat(); setQ(''); setMode(null); (onNew ?? onPick)?.(); };

  return (
    <nav ref={root} className="hx" aria-label="Chat history" onKeyDown={key}>
      <button ref={newBtn} type="button" className="hx-new" onClick={start}><Icon name="spool" size={20} sw={1.8} /><span>New chat</span></button>
      <label className="hx-find">
        <CG name="search" size={16} />
        <input ref={search} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search chats" aria-label="Search chats" autoComplete="off"
          onKeyDown={(e) => { if (e.key === 'Escape' && q) { e.stopPropagation(); setQ(''); } }} />
      </label>
      <div className="hx-scroll">
        {!rows.length && (
          <p className="hx-empty">No chats yet.</p>
        )}
        {rows.length > 0 && !shown.length && <p className="hx-none">No chat called “{q.trim()}”.</p>}
        {groups.map(([g, list]) => (
          <section key={g} className="hx-group" aria-label={g}>
            <h3 className="hx-h">{g}</h3>
            <ul>
              {list.map((r) => (
                <Row key={r.id} r={r} mode={mode?.id === r.id ? mode.kind : null} setMode={(k) => setMode(k ? { id: r.id, kind: k } : null)}
                  dyes={r.apps.map((k) => apps.find((a) => a.key === k)?.dye).filter((d): d is NonNullable<typeof d> => !!d).slice(0, 2)}
                  open={() => { if (!r.current) openThread(r.id); onPick?.(); }} after={() => newBtn.current?.focus()} />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </nav>
  );
}

function Row({ r, mode, setMode, dyes, open, after }: {
  r: ChatRow; mode: 'menu' | 'rename' | 'delete' | null; setMode: (k: 'menu' | 'rename' | 'delete' | null) => void; dyes: string[]; open: () => void; after: () => void;
}) {
  const [name, setName] = useState(r.title);
  const openBtn = useRef<HTMLButtonElement>(null);
  const moreBtn = useRef<HTMLButtonElement>(null);
  const field = useRef<HTMLInputElement>(null);
  useEffect(() => { if (mode === 'rename') { setName(r.title); field.current?.focus(); field.current?.select(); } }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps
  const done = (save: boolean) => { if (save && name.trim()) renameChat(r.id, name); setMode(null); setTimeout(() => openBtn.current?.focus(), 0); };
  return (
    <li className={`hx-row${mode ? ' editing' : ''}`} data-current={r.current || undefined}>
      {mode === 'rename' ? (
        <form className="hx-rename" onSubmit={(e) => { e.preventDefault(); done(true); }}>
          <input ref={field} value={name} onChange={(e) => setName(e.target.value)} aria-label={`Rename chat: ${r.title}`} maxLength={80}
            onKeyDown={(e) => { if (e.key === 'Escape') { e.stopPropagation(); done(false); } }} />
          <button type="submit" className="hx-btn" disabled={!name.trim()}>Save</button>
        </form>
      ) : (
        <div className="hx-line">
          <button ref={openBtn} type="button" className="hx-open" aria-current={r.current ? 'true' : undefined} onClick={open}>
            <span className="hx-dots" aria-hidden="true">{dyes.map((d, i) => <i key={i} className="dyedot" data-dye={d} />)}</span>
            <span className="hx-title">{r.title}</span>
            {r.demo && <span className="hx-tag">sample</span>}
          </button>
          <button ref={moreBtn} type="button" className="hx-more" aria-label={`Chat options: ${r.title}`} aria-haspopup="true" aria-expanded={mode === 'menu' || mode === 'delete'}
            onClick={() => setMode(mode ? null : 'menu')}
            onKeyDown={(e) => { if (e.key === 'Escape' && mode) { e.stopPropagation(); setMode(null); } }}><CG name="more" /></button>
        </div>
      )}
      {mode === 'menu' && (
        <div className="hx-menu" role="group" aria-label="Chat options" onKeyDown={(e) => { if (e.key === 'Escape') { e.stopPropagation(); setMode(null); moreBtn.current?.focus(); } }}>
          <button type="button" className="hx-btn" onClick={() => setMode('rename')}><CG name="pencil" size={16} />Rename</button>
          <button type="button" className="hx-btn" onClick={() => setMode('delete')}><CG name="trash" size={16} />Delete</button>
        </div>
      )}
      {mode === 'delete' && (
        <div className="hx-confirm" role="group" aria-label="Delete this chat?" onKeyDown={(e) => { if (e.key === 'Escape') { e.stopPropagation(); setMode('menu'); } }}>
          <span>Delete this chat?</span>
          <button type="button" className="hx-btn strong" autoFocus onClick={() => { deleteChat(r.id); after(); }}>Delete</button>
          <button type="button" className="hx-btn" onClick={() => { setMode(null); moreBtn.current?.focus(); }}>Keep</button>
        </div>
      )}
    </li>
  );
}
