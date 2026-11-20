// The Notes workspace (Nov 20): notebooks and the pages in them, like Notion or Obsidian.
//   laptop  a tree (notebooks → pages, search, "+") beside one page: a big title and a writing area, with a live preview beside it.
//   phone   a notebook switcher (a sheet) over the page list; a page opens full screen with a Write | Preview switch.
// A page is a row of `block.pages`; its notebooks are the relation `block.link` (a page can sit in several); its text is `block.body`.
// Everything is written through the ordinary record gestures (POST, PATCH, DELETE /records): no new route. Design: design/DESIGN.md §14.
import { useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { errorText, request } from '../../api/client';
import type { Collection, CommandResult, NotebookBlock, Rec } from '../../api/types';
import { day, relIds } from '../../lib/format';
import { plain } from '../../lib/plain';
import { getState, afterCommand, toast } from '../../lib/store';
import { useWide } from '../../lib/useWide';
import { AddSheet } from '../AddSheet';
import { Icon } from '../Icon';
import { BodyField, goRow, LinkedSection, RelationPicker } from '../Links';
import { Sheet } from '../Sheet';
import { Tree, type TreeGroup } from '../Tree';
import type { Ctx } from './index';

const NONE = '__none';
const ALL = 'all';
const str = (v: unknown) => (typeof v === 'string' ? v : '');
const norm = (t: string) => t.trim() || 'Untitled';
type Mode = 'split' | 'write' | 'preview';
const MODE_KEY = 'quilt.notes.mode';
const readMode = (): Mode => { try { const v = localStorage.getItem(MODE_KEY); if (v === 'split' || v === 'write' || v === 'preview') return v; } catch { /* private window: the default */ } return 'split'; };
const saveMode = (m: Mode) => { try { localStorage.setItem(MODE_KEY, m); } catch { /* not remembered */ } };

/** The newest version of a record the store holds (a write bumps it; the next write must name it). */
const versionOf = (app: string, ref: string, id: string, fallback: number) => (getState().apps[app]?.data[ref] as Rec[] | undefined)?.find((r) => r.id === id)?.version ?? fallback;

// ---------------------------------------------------------------- one name, typed in place ("New notebook")
function NewName({ label, onDone, onCancel }: { label: string; onDone: (name: string) => void; onCancel: () => void }) {
  const [v, setV] = useState('');
  return (
    <form className="nb-new" onSubmit={(e) => { e.preventDefault(); if (v.trim()) onDone(v.trim()); }}>
      <input className="fld" autoFocus value={v} onChange={(e) => setV(e.target.value)} placeholder={label} aria-label={label} autoComplete="off" enterKeyHint="done"
        onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onCancel(); } }} onBlur={() => { if (!v.trim()) onCancel(); }} />
    </form>
  );
}

// ---------------------------------------------------------------- the preview (markdown, loaded when first needed)
type MD = typeof import('../../lib/markdown');
function Preview({ text, lookup, onLink }: { text: string; lookup: (title: string) => { app: string; id: string } | undefined; onLink: (app: string, id: string) => void }) {
  const [md, setMd] = useState<MD | null>(null);
  useEffect(() => { let on = true; void import('../../lib/markdown').then((m) => { if (on) setMd(m); }); return () => { on = false; }; }, []);
  const deferred = useDeferredValue(text);
  const html = useMemo(() => (md && deferred.trim() ? md.renderMarkdown(deferred, lookup) : ''), [md, deferred, lookup]);
  if (!deferred.trim()) return <p className="np-empty">Nothing to preview yet. Write something and it shows here.</p>;
  return (
    <div className="md" onClick={(e) => {
      const a = (e.target as HTMLElement).closest<HTMLAnchorElement>('a.wl[data-id]');
      if (!a) return;
      e.preventDefault();
      onLink(a.dataset.app ?? '', a.dataset.id ?? '');
    }} dangerouslySetInnerHTML={{ __html: html }} />
  );
}

// ---------------------------------------------------------------- one page: title, writing area, preview, its links
function Page({ rec, block, ctx, pc, nbs, wide, mode, setMode, backLabel, onBack, onGone, onLink, focusTitle }: {
  rec: Rec; block: NotebookBlock; ctx: Ctx; pc: Collection; nbs: Rec[]; wide: boolean; mode: Mode; setMode: (m: Mode) => void;
  backLabel: string; onBack: () => void; onGone: () => void; onLink: (app: string, id: string) => void; focusTitle: boolean;
}) {
  const app = ctx.spec.key;
  const ro = !!ctx.preview;
  const titleKey = pc.titleField;
  const serverTitle = str(rec.properties[titleKey]), serverBody = str(rec.properties[block.body]);
  const [title, setTitle] = useState(serverTitle);
  const [body, setBody] = useState(serverBody);
  const [status, setStatus] = useState<'ok' | 'saving' | 'failed'>('ok');
  const [err, setErr] = useState('');
  const [picking, setPicking] = useState(false);
  const base = useRef({ title: serverTitle, body: serverBody }); // what the server holds, as far as we know
  const cur = useRef({ title, body, version: rec.version });
  cur.current = { title, body, version: rec.version };
  const chain = useRef<Promise<unknown>>(Promise.resolve()); // one write at a time, so each names the version the last one made
  const gone = useRef(false);
  const titleRef = useRef<HTMLTextAreaElement>(null);
  const dirty = norm(title) !== norm(base.current.title) || body !== base.current.body;

  // a change from elsewhere (another device) is adopted only while nothing here is unsaved
  useEffect(() => {
    if (norm(cur.current.title) !== norm(base.current.title) || cur.current.body !== base.current.body) return; // something here is unsaved: it wins
    if (norm(serverTitle) !== norm(cur.current.title)) setTitle(serverTitle);
    if (serverBody !== cur.current.body) setBody(serverBody);
    base.current = { title: serverTitle, body: serverBody };
  }, [serverTitle, serverBody]);

  const enqueue = <T,>(fn: () => Promise<T>) => { const run = chain.current.then(fn, fn); chain.current = run.catch(() => {}); return run; };
  const flush = () => enqueue(async () => {
    if (ro || gone.current) return;
    try {
      for (;;) {
        const { title: t, body: b } = cur.current;
        const f: Record<string, unknown> = {};
        if (norm(t) !== norm(base.current.title)) f[titleKey] = norm(t);
        if (b !== base.current.body) f[block.body] = b;
        if (!Object.keys(f).length) break;
        setStatus('saving');
        const r = await request<CommandResult>('PATCH', `/records/${rec.id}`, { fields: f, base_version: versionOf(app, block.pages, rec.id, cur.current.version) });
        base.current = { title: (f[titleKey] as string | undefined) ?? base.current.title, body: (f[block.body] as string | undefined) ?? base.current.body };
        await afterCommand(r);
      }
      setStatus('ok'); setErr('');
    } catch (x) { setStatus('failed'); setErr(errorText(x)); }
  });
  useEffect(() => { // autosave: a pause in typing, not every key
    if (!dirty || ro) return;
    const t = setTimeout(() => void flush(), 900);
    return () => clearTimeout(t);
  }, [title, body]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { // leaving the page, hiding the tab or closing it saves what is typed
    const out = () => { if (document.visibilityState === 'hidden') void flush(); };
    document.addEventListener('visibilitychange', out); window.addEventListener('pagehide', out as () => void);
    return () => { document.removeEventListener('visibilitychange', out); window.removeEventListener('pagehide', out as () => void); void flush(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useLayoutEffect(() => { // the title is a one-line field that wraps: it grows with its words
    const el = titleRef.current; if (!el) return;
    const y = window.scrollY;
    el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px`;
    if (window.scrollY !== y) window.scrollTo(window.scrollX, y);
  }, [title]);
  useEffect(() => { if (focusTitle && !ro) { titleRef.current?.focus(); titleRef.current?.select(); } }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const nbIds = relIds(rec.properties[block.link]).filter((id) => nbs.some((n) => n.id === id));
  const nbName = (id: string) => str(nbs.find((n) => n.id === id)?.properties[ctx.spec.collections.find((c) => `${app}/${c.key}` === block.source)?.titleField ?? 'name']);
  const setNotebooks = (ids: string[]) => enqueue(async () => {
    try {
      const r = await request<CommandResult>('PATCH', `/records/${rec.id}`, { fields: { [block.link]: ids }, base_version: versionOf(app, block.pages, rec.id, cur.current.version) });
      await afterCommand(r);
    } catch (x) { toast(errorText(x), undefined, 4000); }
  });
  const remove = async () => {
    await flush(); // an unsaved edit goes first, so Undo brings back the last text
    gone.current = true;
    try {
      const r = await request<CommandResult>('DELETE', `/records/${rec.id}`);
      await afterCommand(r);
      onGone();
      toast('Page deleted.', { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } });
    } catch (x) { gone.current = false; toast(errorText(x), undefined, 4000); }
  };

  // what a `[[Title]]` opens: the record's own links (the server resolved them), else a page of this app with that title (typed just now)
  const lookup = useMemo(() => {
    const m = new Map<string, { app: string; id: string }>();
    for (const r of (ctx.data[block.pages] ?? []) as Rec[]) { const t = str(r.properties[titleKey]).trim().toLowerCase(); if (t && r.id !== rec.id && !m.has(t)) m.set(t, { app, id: r.id }); }
    const ls = rec.properties._links;
    if (Array.isArray(ls)) for (const l of ls as { app: string; id: string; title: string }[]) if (l.title && l.title !== '(deleted)') m.set(l.title.trim().toLowerCase(), { app: l.app, id: l.id });
    return (t: string) => m.get(t.trim().toLowerCase());
  }, [ctx.data, block.pages, titleKey, rec.id, rec.properties._links, app]); // eslint-disable-line react-hooks/exhaustive-deps

  const shown: Mode = !wide && mode === 'split' ? 'write' : mode;
  const field = pc.fields.find((f) => f.key === block.link);
  const bodyId = `np-body-${rec.id}`;
  const modes: [Mode, string][] = wide ? [['write', 'Write'], ['split', 'Split'], ['preview', 'Preview']] : [['write', 'Write'], ['preview', 'Preview']];
  return (
    <section className="np" aria-label={`Page: ${norm(title)}`}>
      <div className="np-bar">
        {!wide && <button type="button" className="np-back" onClick={onBack} aria-label={`Back to ${backLabel}`}><Icon name="back" /><span>{backLabel}</span></button>}
        <span className="np-status" role="status" aria-live="polite">
          {status === 'failed'
            ? <>Not saved. <button type="button" className="link" onClick={() => void flush()} title={err}>Try again</button></>
            : ro ? 'Example' : status === 'saving' || dirty ? 'Saving…' : 'Saved'}
        </span>
        <span className="seg np-modes" role="group" aria-label="View">
          {modes.map(([m, t]) => <button key={m} type="button" aria-pressed={shown === m} onClick={() => { setMode(m); if (wide) saveMode(m); }}>{t}</button>)}
        </span>
        {!ro && <button type="button" className="round np-del" aria-label="Delete this page" onClick={() => void remove()}><Icon name="trash" size={18} sw={1.8} /></button>}
      </div>

      <textarea ref={titleRef} className="np-title" rows={1} value={title} placeholder="Untitled" aria-label="Page title" readOnly={ro} spellCheck
        onChange={(e) => setTitle(e.target.value.replace(/\n/g, ' '))}
        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); document.getElementById(bodyId)?.focus(); } }} onBlur={() => void flush()} />

      <div className="np-meta">
        <button type="button" className="np-in" aria-expanded={picking} onClick={() => setPicking((v) => !v)} disabled={ro}>
          <Icon name="book" size={16} sw={1.8} /><span>{nbIds.length ? `In ${nbIds.map(nbName).join(', ')}` : 'In no notebook'}</span>
        </button>
      </div>
      {picking && field && <div className="np-pick card"><RelationPicker field={field} app={app} value={nbIds} onChange={(ids) => void setNotebooks(ids)} labelId={`np-nb-${rec.id}`} /></div>}

      <div className={`np-body ${shown}`}>
        {shown !== 'preview' && (
          <div className="np-pane np-write">
            <BodyField id={bodyId} value={body} onChange={ro ? () => {} : setBody} placeholder={'Start writing. Markdown works: # a heading, - a list, **bold**.\nType [[ to link another page.'} app={app} recId={rec.id} max={Infinity} className="note" />
          </div>
        )}
        {shown !== 'write' && (
          <div className="np-pane np-read" aria-label="Preview"><Preview text={body} lookup={lookup} onLink={onLink} /></div>
        )}
      </div>

      {!ro && <div className="np-links"><LinkedSection app={app} collection={pc} record={rec} /></div>}
    </section>
  );
}

// ---------------------------------------------------------------- the block
export function Notebook({ block, ctx }: { block: NotebookBlock; ctx: Ctx }) {
  const wide = useWide();
  const nav = useNavigate();
  const [q, setQ] = useSearchParams();
  const app = ctx.spec.key;
  const ro = !!ctx.preview;
  const nbc = ctx.spec.collections.find((c) => `${app}/${c.key}` === block.source);
  const pc = ctx.spec.collections.find((c) => `${app}/${c.key}` === block.pages);
  const nbs = useMemo(() => (ctx.data[block.source] ?? []) as Rec[], [ctx.data, block.source]);
  const all = (ctx.data[block.pages] ?? []) as Rec[];
  const [scope, setScope] = useState<string>(ctx.filter?.field === block.link ? ctx.filter.id : ALL); // the notebook you are in; where "New page" goes
  const [shut, setShut] = useState<Set<string>>(() => new Set()); // closed notebooks: all start open
  const [find, setFind] = useState('');
  const [naming, setNaming] = useState(false);
  const [picker, setPicker] = useState(false);
  const [editNb, setEditNb] = useState<Rec | null>(null);
  const [mode, setMode] = useState<Mode>(() => (wide ? readMode() : 'write')); // the laptop remembers its view; a phone opens to Write
  const fresh = useRef<string | null>(null); // a page just made: its title takes the cursor
  const [busy, setBusy] = useState(false);
  const want = q.get('page');
  useEffect(() => { if (!wide && want) window.scrollTo(0, 0); }, [want, wide]); // a page opens at its top
  if (!nbc || !pc) return null;
  const titleKey = pc.titleField, nameKey = nbc.titleField, at = pc.dateField;
  const tt = (r: Rec) => norm(str(r.properties[titleKey]));
  const whenOf = (r: Rec) => str(at ? r.properties[at] : '');
  const pages = [...all].sort((a, b) => (whenOf(a) < whenOf(b) ? 1 : whenOf(a) > whenOf(b) ? -1 : 0)); // newest first; typing never moves a page
  const inNb = (r: Rec) => relIds(r.properties[block.link]).filter((id) => nbs.some((n) => n.id === id));
  const members = (id: string) => (id === NONE ? pages.filter((r) => inNb(r).length === 0) : pages.filter((r) => inNb(r).includes(id)));
  const nameOf = (id: string) => (id === ALL ? 'All pages' : id === NONE ? 'Unfiled' : str(nbs.find((n) => n.id === id)?.properties[nameKey]) || 'Notebook');

  const inScope = scope === ALL ? pages : members(scope);
  const rec = pages.find((r) => r.id === want) ?? (wide && !want ? (inScope[0] ?? pages[0]) : undefined);
  const openPage = (id: string | null, replace = !wide) => {
    const n = new URLSearchParams(q);
    if (id) n.set('page', id); else n.delete('page');
    setQ(n, { replace });
  };
  const toLink = (to: string, id: string) => { if (to === app) openPage(id); else nav(goRow(to, id)); };

  const create = async (ref: string, fields: Record<string, unknown>, onId?: (id: string) => void): Promise<string | undefined> => {
    setBusy(true);
    try {
      const r = await request<CommandResult>('POST', '/records', { collection_id: ref, fields });
      const id = r.blocks?.[0]?.id;
      if (id) onId?.(id); // before the rows reload: the new page can show at once (it is the newest), and must already know it is new
      await afterCommand(r);
      return id;
    } catch (x) { toast(errorText(x), undefined, 4000); return undefined; } finally { setBusy(false); }
  };
  const newPage = async (into?: string) => {
    const nb = into ?? (scope !== ALL && scope !== NONE ? scope : undefined);
    const fields: Record<string, unknown> = { [titleKey]: 'Untitled' };
    if (at) fields[at] = ctx.now.slice(0, 16);
    if (nb) fields[block.link] = [nb];
    const id = await create(block.pages, fields, (n) => { fresh.current = n; });
    if (!id) return;
    if (nb) { setShut((s) => { const n = new Set(s); n.delete(nb); return n; }); setScope(nb); }
    setFind('');
    openPage(id, false);
  };
  const newNotebook = async (name: string) => {
    setNaming(false);
    const id = await create(block.source, { [nameKey]: name });
    if (id) setScope(id);
  };

  const needle = find.trim().toLowerCase();
  const hit = (r: Rec) => !needle || tt(r).toLowerCase().includes(needle) || str(r.properties[block.body]).toLowerCase().includes(needle);
  const snippet = (r: Rec) => plain(str(r.properties[block.body]), 80);
  const groups: TreeGroup[] = [
    ...nbs.map((n) => {
      const ms = members(n.id), items = ms.filter(hit).map((r) => ({ id: r.id, label: tt(r), meta: needle ? snippet(r) : undefined }));
      return { id: n.id, label: nameOf(n.id), count: needle ? items.length : ms.length, items, empty: 'No pages yet' } satisfies TreeGroup;
    }),
    ...(members(NONE).length ? [{ id: NONE, label: 'Unfiled', count: members(NONE).filter(hit).length, fixed: true, items: members(NONE).filter(hit).map((r) => ({ id: r.id, label: tt(r), meta: needle ? snippet(r) : undefined })) } satisfies TreeGroup] : []),
  ].filter((g) => !needle || g.items.length > 0);
  const open = new Set(groups.filter((g) => needle || !shut.has(g.id)).map((g) => g.id));
  const toggle = (id: string) => setShut((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });

  const editSheet = !ro && (
    <AddSheet app={app} appName={ctx.spec.name} collection={nbc} now={ctx.now} apps={ctx.apps} record={editNb ?? undefined}
      open={!!editNb} onClose={() => setEditNb(null)} onAdded={() => ctx.reload?.()} />
  );

  // a page, in the same component for both sizes (keyed, so each page has its own draft)
  const page = rec && pc && (
    <Page key={rec.id} rec={rec} block={block} ctx={ctx} pc={pc} nbs={nbs} wide={wide} mode={mode} setMode={setMode} focusTitle={fresh.current === rec.id}
      backLabel={nameOf(scope)} onBack={() => openPage(null)} onGone={() => { const next = pages.find((r) => r.id !== rec.id && inScope.includes(r)); openPage(wide ? next?.id ?? null : null, true); }} onLink={toLink} />
  );

  // ---------------------------------------------------------------- phone
  if (!wide) {
    if (rec) return <div className="nb nb-open" data-dye={ctx.spec.dye}>{page}{editSheet}</div>;
    const list = needle ? pages.filter(hit) : inScope;
    return (
      <div className="nb nb-phone" data-dye={ctx.spec.dye}>
        <div className="nb-top">
          <button type="button" className="nb-switch" onClick={() => setPicker(true)} aria-haspopup="dialog">
            <Icon name="book" size={18} sw={1.8} /><span className="nb-sw-t">{nameOf(scope)}</span><span className="nb-sw-n">{scope === ALL ? pages.length : members(scope).length}</span><Icon name="chev" size={14} sw={2.2} />
          </button>
          {!ro && <button type="button" className="round nb-plus" aria-label={scope !== ALL && scope !== NONE ? `New page in ${nameOf(scope)}` : 'New page'} disabled={busy} onClick={() => void newPage()}><Icon name="plus" size={20} sw={2} /></button>}
        </div>
        <label className="nb-find"><Icon name="search" size={16} sw={1.8} /><input type="search" value={find} onChange={(e) => setFind(e.target.value)} placeholder="Search pages" aria-label="Search pages" autoComplete="off" /></label>
        <ul className="card list nb-list">
          {list.length === 0 && (
            <li className="empty-li"><p className="nb-none">{needle ? `Nothing matches "${find.trim()}".` : nbs.length || pages.length ? 'No pages here yet.' : 'No notebooks yet. Make one, then add pages to it.'}</p></li>
          )}
          {list.map((r) => (
            <li className="row" key={r.id} data-row={r.id}>
              <button type="button" className="row-btn" onClick={() => openPage(r.id)}>
                <span className="main"><span className="t">{tt(r)}</span>
                  <span className="s">{[whenOf(r) ? day(whenOf(r)) : '', scope === ALL || needle ? inNb(r).map(nameOf).join(', ') : '', snippet(r)].filter(Boolean).join(' · ')}</span></span>
                <Icon name="chev" size={18} />
              </button>
            </li>
          ))}
          {!ro && !needle && <li className="add-row-li"><button type="button" className="add-row" disabled={busy} onClick={() => void newPage()}><Icon name="plus" size={16} />Add a page</button></li>}
        </ul>
        <Sheet open={picker} onClose={() => { setPicker(false); setNaming(false); }} label="Notebooks">
          <div className="sheet-head"><span className="txt"><h2>Notebooks</h2><span className="sub">{pages.length} page{pages.length === 1 ? '' : 's'}</span></span></div>
          <ul className="card list nb-books">
            {[ALL, ...nbs.map((n) => n.id), ...(members(NONE).length ? [NONE] : [])].map((id) => (
              <li className="row nb-book" key={id}>
                <button type="button" className="row-btn" aria-pressed={scope === id} onClick={() => { setScope(id); setPicker(false); setNaming(false); }}>
                  <span className="main"><span className="t">{nameOf(id)}</span></span><span className="amt">{id === ALL ? pages.length : members(id).length}</span>
                </button>
                {!ro && id !== ALL && id !== NONE && <button type="button" className="round nb-more" aria-label={`${nameOf(id)} options`} onClick={() => { setPicker(false); setEditNb(nbs.find((n) => n.id === id) ?? null); }}><Icon name="more" size={18} sw={2} /></button>}
              </li>
            ))}
            {!ro && (naming
              ? <li className="add-row-li"><NewName label="Notebook name" onDone={(n) => { void newNotebook(n); setPicker(false); }} onCancel={() => setNaming(false)} /></li>
              : <li className="add-row-li"><button type="button" className="add-row" onClick={() => setNaming(true)}><Icon name="plus" size={16} />New notebook</button></li>)}
          </ul>
        </Sheet>
        {editSheet}
      </div>
    );
  }

  // ---------------------------------------------------------------- laptop
  return (
    <div className="nb nb-wide" data-dye={ctx.spec.dye}>
      <aside className="nb-tree" aria-label="Notebooks">
        <label className="nb-find"><Icon name="search" size={16} sw={1.8} /><input type="search" value={find} onChange={(e) => setFind(e.target.value)} placeholder="Search pages" aria-label="Search pages" autoComplete="off" /></label>
        {!ro && <button type="button" className="nb-newpage" disabled={busy} onClick={() => void newPage()}><Icon name="plus" size={16} sw={2} />New page{scope !== ALL && scope !== NONE ? ` in ${nameOf(scope)}` : ''}</button>}
        <Tree label="Notebooks and pages" groups={groups} open={open} onToggle={toggle} picked={rec?.id ?? null} pickedGroup={scope}
          onPick={(i, g) => { setScope(g.id); openPage(i.id); }}
          onPickGroup={(g) => { setScope(g.id); if (!needle) toggle(g.id); }}
          onAdd={ro ? undefined : (g) => void newPage(g.id === NONE ? undefined : g.id)} addLabel={(g) => `New page in ${g.label}`}
          onMore={ro ? undefined : (g) => setEditNb(nbs.find((n) => n.id === g.id) ?? null)} moreLabel={(g) => `${g.label} options: rename or delete`}
          empty={needle ? `Nothing matches "${find.trim()}".` : 'No notebooks yet.'} />
        {!ro && (naming
          ? <NewName label="Notebook name" onDone={(n) => void newNotebook(n)} onCancel={() => setNaming(false)} />
          : <button type="button" className="nb-newbook" onClick={() => setNaming(true)}><Icon name="plus" size={16} sw={2} />New notebook</button>)}
      </aside>
      <div className="nb-main">
        {page ?? (
          <div className="np-none">
            <p>{pages.length ? 'Pick a page to read or write.' : 'No pages yet.'}</p>
            {!ro && <button type="button" className="cta" disabled={busy} onClick={() => void newPage()}>New page</button>}
          </div>
        )}
      </div>
      {editSheet}
    </div>
  );
}
