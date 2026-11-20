// Links (Nov 20): relations you can see and set, and links between any two records, Obsidian style (design/DESIGN.md "Links").
// Generic: driven by the spec's relation fields and the reserved `_links` / `_backlinks` keys, never by an app. The client never
// counts or derives a link: backlinks and counts arrive from the server (the mock does it in getApp).
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorText, request } from '../api/client';
import type { AppSpec, Collection, CommandResult, Field, LinkRef, Rec, SearchHit } from '../api/types';
import { relIds, singular, title as titleOf } from '../lib/format';
import { EASE, RM, T } from '../lib/motion';
import { afterCommand, getState, linkRecord, loadApp, searchRecords, toast, unlinkRecord, useStore } from '../lib/store';
import { Icon } from './Icon';
import { Sheet } from './Sheet';

// ---------------------------------------------------------------- shapes and helpers
/** Keys a person never sees as fields (a stitch's bookkeeping): never relation chips or pickers either. (`trip` left this list on Nov 20: an item's trip is shown and can be set.) */
export const SYSTEM_KEYS = new Set(['source', 'ext_id', 'bought_on', 'usual']);
export const GONE = '(deleted)';
export const isGone = (l: { title: string }) => l.title === GONE;
const links = (v: unknown): LinkRef[] => (Array.isArray(v) ? v.filter((x): x is LinkRef => !!x && typeof x === 'object' && 'id' in x) : []);
/** Links made from this record (stored). */
export const linksOf = (r?: Rec) => links(r?.properties._links);
/** Records and relation rows that point here (derived by the server). */
export const backlinksOf = (r?: Rec) => links(r?.properties._backlinks);
export const appOf = (ref: string) => ref.split('/')[0];
export const relFields = (c: Collection) => c.fields.filter((f) => f.type === 'relation' && !!f.target && !SYSTEM_KEYS.has(f.key));
export const hasRel = (r: Rec, field: string, id: string) => relIds(r.properties[field]).includes(id);
export const goRow = (app: string, id: string) => `/a/${app}?row=${encodeURIComponent(id)}`;
export const goFilter = (app: string, field: string, id: string, tab?: string) => `/a/${app}?${tab ? `tab=${tab}&` : ''}filter=${field}:${encodeURIComponent(id)}`;

/** `?filter=<relationField>:<id>` */
export type RelFilter = { field: string; id: string };
export function parseFilter(s: string | null): RelFilter | null {
  const i = s ? s.indexOf(':') : -1;
  return s && i > 0 && i < s.length - 1 ? { field: s.slice(0, i), id: s.slice(i + 1) } : null;
}
const rowBlock = (b: { kind: string }): b is { kind: string; source: string } => b.kind === 'list' || b.kind === 'checklist';
const withField = (spec: AppSpec, field: string) => spec.collections.filter((c) => c.fields.some((f) => f.key === field && f.type === 'relation')).map((c) => `${spec.key}/${c.key}`);
/** The filter, if this app has a relation field of that name. */
export const validFilter = (spec: AppSpec, f: RelFilter | null) => (f && withField(spec, f.field).length ? f : null);
/** The first tab that lists this collection. */
export const tabFor = (spec: AppSpec, ref: string) => spec.tabs.find((t) => t.children.some((b) => rowBlock(b) && b.source === ref))?.id;
/** The first tab that lists a collection with this relation field: where a filtered list is drawn. */
export const filterTab = (spec: AppSpec, field: string) => { const refs = withField(spec, field); return spec.tabs.find((t) => t.children.some((b) => rowBlock(b) && refs.includes(b.source)))?.id; };
export const tabHasField = (spec: AppSpec, tab: string, field: string) => { const refs = withField(spec, field); return !!spec.tabs.find((t) => t.id === tab)?.children.some((b) => rowBlock(b) && refs.includes(b.source)); };

// ---------------------------------------------------------------- what the store knows about other apps
const asked = new Set<string>();
/** A target in another app (a notebook's class) is not in this app's response: load that app once, so a chip can say its name. */
export function useEnsureApps(keys: string[]) {
  const k = keys.join('|');
  useEffect(() => {
    for (const key of keys) {
      if (!key || getState().apps[key] || asked.has(key)) continue;
      asked.add(key);
      void loadApp(key).then(() => { if (!getState().apps[key]) asked.delete(key); });
    }
  }, [k]); // eslint-disable-line react-hooks/exhaustive-deps
}
export function useAppMeta(key: string): { name: string; dye?: string } {
  const patch = useStore((s) => s.home?.apps.find((a) => a.key === key));
  const spec = useStore((s) => s.apps[key]?.spec);
  return { name: patch?.name ?? spec?.name ?? key, dye: patch?.dye ?? spec?.dye };
}
export type Resolved = { title?: string; gone?: boolean };
/** What a relation id points at: its title; `gone` when that app is loaded and has no such row; neither while the app is not loaded yet. */
export function useResolve() {
  const apps = useStore((s) => s.apps);
  return useCallback((ref: string, id: string): Resolved => {
    const a = apps[appOf(ref)];
    const rows = a?.data[ref] as Rec[] | undefined;
    const c = a?.spec.collections.find((x) => `${a.spec.key}/${x.key}` === ref);
    if (!a || !rows || !c) return {};
    const r = rows.find((x) => x.id === id);
    return r ? { title: titleOf(c, r) } : { gone: true };
  }, [apps]);
}

// ---------------------------------------------------------------- motion: a chip rises in, fades out
/** A chip that arrives after the list was drawn rises 8 px as it fades in (220); on first paint nothing moves. Reduced motion: a 120 ms fade. */
function useArrive(host: RefObject<HTMLElement | null>, keys: string[]) {
  const was = useRef<Set<string> | null>(null);
  const k = keys.join('\n');
  useLayoutEffect(() => {
    const prev = was.current;
    was.current = new Set(keys);
    if (!prev || !host.current) return;
    for (const key of keys) {
      if (prev.has(key)) continue;
      const el = [...host.current.querySelectorAll<HTMLElement>('[data-lc]')].find((e) => e.dataset.lc === key);
      el?.animate(RM() ? [{ opacity: 0 }, { opacity: 1 }] : [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: RM() ? T.fb : T.state, easing: EASE });
    }
  }, [k]); // eslint-disable-line react-hooks/exhaustive-deps
}
const fadeOut = (el: Element | null) => el?.animate([{ opacity: 1 }, { opacity: 0 }], { duration: RM() ? T.fb : T.stateOut, easing: EASE, fill: 'forwards' });

export const LinkGlyph = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: 'none' }}>
    <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />
  </svg>
);

// ---------------------------------------------------------------- the chip
type ChipProps = {
  id: string; app: string; text: string; gone?: boolean;
  /** the target app's dye dot */ dot?: boolean;
  /** "· Classes": the app's name after the title, for a target in another app */ showApp?: boolean;
  /** the accessible name of the open button, given the app's name */ name: (appName: string) => string;
  onOpen?: () => void;
  onRemove?: () => Promise<boolean | void> | void; removeName?: string;
  /** a count that opens a list: "4 notes ›" */ count?: boolean; glyph?: boolean;
};
/**
 * A small pill: the title, the target app's dye dot, and a button that opens it. The button is 44 high though the pill is 28 (the
 * reach is the button, like `.tick`); a deleted target is struck through and not a button. With `onRemove` a × follows (44 wide).
 */
export function Chip({ id, app, text, gone, dot, showApp, name, onOpen, onRemove, removeName, count, glyph }: ChipProps) {
  const meta = useAppMeta(app);
  const host = useRef<HTMLSpanElement>(null);
  const body = (
    <>
      {glyph && <LinkGlyph size={14} />}
      {dot && <i className="lc-dot" data-dye={meta.dye} aria-hidden="true" />}
      <span className="lc-t">{text}</span>
      {showApp && <span className="lc-app">· {meta.name}</span>}
      {count && <Icon name="chev" size={14} sw={2.2} />}
    </>
  );
  const remove = async () => {
    const a = fadeOut(host.current);
    const ok = await onRemove?.();
    if (ok === false) a?.cancel(); // it did not go: the chip comes back
  };
  return (
    <span ref={host} className={`lc${gone ? ' gone' : ''}${onRemove ? ' has-x' : ''}${count ? ' count' : ''}`} data-lc={id}>
      {onOpen && !gone
        ? <button type="button" className="lc-main" aria-label={name(meta.name)} onClick={onOpen}>{body}</button>
        : <span className="lc-main">{body}</span>}
      {onRemove && <button type="button" className="lc-x" aria-label={removeName} onClick={remove}><Icon name="close" size={12} sw={2.4} /></button>}
    </span>
  );
}

/** One relation value as a chip: a target in this app filters the list to it; a target in another app opens that record there. */
function RelChip({ f, c, id, app, onGo }: { f: Field; c: Collection; id: string; app: string; onGo?: () => void }) {
  const go = useNavigate();
  const resolve = useResolve();
  const tApp = appOf(f.target!);
  const r = resolve(f.target!, id);
  if (!r.title && !r.gone) return null; // still loading: nothing until it can say its name
  const cross = tApp !== app;
  const text = r.gone ? GONE : r.title!;
  return (
    <Chip id={`${f.key}:${id}`} app={tApp} text={text} gone={r.gone} dot={cross} showApp={cross}
      name={(a) => (cross ? `${f.label}: ${text} in ${a}. Open` : `In ${f.label.toLowerCase()} ${text}. Show all ${c.name.toLowerCase()} in it`)}
      onOpen={() => { onGo?.(); go(cross ? goRow(tApp, id) : goFilter(app, f.key, id)); }} />
  );
}
/** A relation field's value as chips (the laptop pane). */
export function RelValue({ f, c, rec, app }: { f: Field; c: Collection; rec: Rec; app: string }) {
  const ids = relIds(rec.properties[f.key]);
  const host = useRef<HTMLSpanElement>(null);
  useEnsureApps(appOf(f.target!) === app ? [] : [appOf(f.target!)]);
  useArrive(host, ids.map((id) => `${f.key}:${id}`));
  return <span ref={host} className="lc-chips end">{ids.map((id) => <RelChip key={id} f={f} c={c} id={id} app={app} />)}</span>;
}

/** The server's reverse counts for a row that rows point at through a relation field ("4 notes"). */
function reverseGroups(rec: Rec) {
  const m = new Map<string, { app: string; ref: string; via: string; n: number }>();
  for (const b of backlinksOf(rec)) {
    if (!b.via || isGone(b)) continue;
    const k = `${b.ref}|${b.via}`;
    m.set(k, { app: b.app, ref: b.ref, via: b.via, n: (m.get(k)?.n ?? 0) + 1 });
  }
  return [...m.values()];
}
function CountChip({ g, rec, app }: { g: { app: string; ref: string; via: string; n: number }; rec: Rec; app: string }) {
  const go = useNavigate();
  const other = useStore((s) => s.apps[g.app]?.spec);
  const meta = useAppMeta(g.app);
  const c = other?.collections.find((x) => `${g.app}/${x.key}` === g.ref);
  const noun = c ? (g.n === 1 ? singular(c) : c.name.toLowerCase()) : null;
  const text = noun ? `${g.n} ${noun}` : g.app === app ? `${g.n} linked` : `${g.n} in ${meta.name}`;
  const tab = other ? filterTab(other, g.via) : undefined;
  return (
    <Chip id={`n:${g.ref}|${g.via}`} app={g.app} text={text} count dot={g.app !== app}
      name={() => `${text}${g.app === app ? '' : ` in ${meta.name}`}. Show them`}
      onOpen={() => go(goFilter(g.app, g.via, rec.id, tab))} />
  );
}

/**
 * Under a row's title (List and Checklist): its relations as chips ("Calculus", "Math 201 · Classes"), the rows that point at it
 * as a count that opens them ("4 notes ›"), and how many records are linked to it by hand ("2 linked", which opens the record).
 * Outside the row's own button: a chip is a button, and a button can't hold one. `only`: the relation fields the block lists (all when it lists none).
 */
export function RowRel({ rec, c, app, only }: { rec: Rec; c: Collection; app: string; only?: string[] }) {
  const go = useNavigate();
  const resolve = useResolve();
  const host = useRef<HTMLDivElement>(null);
  const fields = relFields(c).filter((f) => !only || only.includes(f.key));
  useEnsureApps([...new Set(fields.map((f) => appOf(f.target!)).filter((a) => a !== app))]);
  const fwd = fields.flatMap((f) => relIds(rec.properties[f.key]).map((id) => ({ f, id })));
  const keys = fwd.filter(({ f, id }) => { const r = resolve(f.target!, id); return r.title || r.gone; }).map(({ f, id }) => `${f.key}:${id}`);
  const back = reverseGroups(rec);
  const linked = linksOf(rec).length + backlinksOf(rec).filter((b) => !b.via).length;
  useArrive(host, keys);
  if (!keys.length && !back.length && !linked) return null;
  return (
    <div ref={host} className="lc-rel">
      {fwd.map(({ f, id }) => <RelChip key={`${f.key}:${id}`} f={f} c={c} id={id} app={app} />)}
      {back.map((g) => <CountChip key={`${g.ref}|${g.via}`} g={g} rec={rec} app={app} />)}
      {linked > 0 && <Chip id="linked" app={app} text={`${linked} linked`} glyph name={() => `${linked} linked. Open to see them`} onOpen={() => go(goRow(app, rec.id))} />}
    </div>
  );
}

/** The dismissible chip under the tab strip: "In notebook · Calculus ×". */
export function FilterChip({ spec, filter, onClear }: { spec: AppSpec; filter: RelFilter; onClear: () => void }) {
  const resolve = useResolve();
  const f = spec.collections.flatMap((c) => c.fields).find((x) => x.key === filter.field && x.type === 'relation');
  useEnsureApps(f?.target && appOf(f.target) !== spec.key ? [appOf(f.target)] : []);
  const r = f?.target ? resolve(f.target, filter.id) : {};
  const text = `In ${(f?.label ?? filter.field).toLowerCase()}${r.gone ? ` · ${GONE}` : r.title ? ` · ${r.title}` : ''}`;
  return (
    <button type="button" className="lc-filter" onClick={onClear} aria-label={`Clear filter: ${text}`}>
      <span className="lc-fpill"><span>{text}</span><Icon name="close" size={14} sw={2.2} /></span>
    </button>
  );
}

// ---------------------------------------------------------------- linking and unlinking (writes, with Undo like any other)
const undoer = (id: string) => async () => {
  try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${id}/undo`)); } catch (x) { toast(errorText(x)); }
};
function useLinkOps(from: { id: string; app: string; title: string }) {
  const meta = useAppMeta(from.app);
  const link = async (to: { ref: string; id: string; title: string; app: string }, toDye?: string) => {
    try {
      const r = await linkRecord(from.id, { ref: to.ref, id: to.id });
      await afterCommand(r);
      toast(`Linked to ${to.title}.`, { label: 'Undo', run: undoer(r.change_set_id) }, 8000, { dyes: [meta.dye, toDye] });
      return true;
    } catch (x) { toast(errorText(x), undefined, 4000); return false; }
  };
  const unlink = async (l: LinkRef) => {
    try {
      const r = await unlinkRecord(from.id, l.id);
      await afterCommand(r);
      toast(`Unlinked ${l.title}.`, { label: 'Undo', run: undoer(r.change_set_id) }, 8000, { dyes: [meta.dye] });
      return true;
    } catch (x) { toast(errorText(x), undefined, 4000); return false; }
  };
  return { link, unlink };
}

/** The record as the store has it now: the sheet's copy is from when it opened, and a link changes the record under it. */
export function useLive(app: string, c: Collection, record: Rec): Rec {
  return useStore((s) => (s.apps[app]?.data[`${app}/${c.key}`] as Rec[] | undefined)?.find((r) => r.id === record.id)) ?? record;
}

/**
 * "Linked" (what this record links to, with a × on each) and "Linked from" (what links here: read-only), and the Link to… button.
 * In the edit sheet and in the laptop pane. A chip opens the record in its app (`?row=`); `onNavigate` lets a sheet close first.
 */
export function LinkedSection({ app, collection, record, onNavigate }: { app: string; collection: Collection; record: Rec; onNavigate?: () => void }) {
  const go = useNavigate();
  const live = useLive(app, collection, record);
  const out = linksOf(live), inn = backlinksOf(live);
  const [picking, setPicking] = useState(false);
  const [all, setAll] = useState(false);
  const outHost = useRef<HTMLDivElement>(null), inHost = useRef<HTMLDivElement>(null);
  const from = { id: live.id, app, title: titleOf(collection, live) };
  const ops = useLinkOps(from);
  useArrive(outHost, out.map((l) => l.id));
  useArrive(inHost, inn.map((l) => l.id));
  const open = (l: LinkRef) => { onNavigate?.(); go(goRow(l.app, l.id)); };
  const CAP = 8;
  const chip = (l: LinkRef, verb: string, removable: boolean) => (
    <Chip key={`${l.ref}:${l.id}:${l.via ?? ''}`} id={l.id} app={l.app} text={l.title} gone={isGone(l)} dot showApp={l.app !== app}
      name={(a) => `${verb} ${l.title} in ${a}. Open`} onOpen={() => open(l)}
      onRemove={removable ? () => ops.unlink(l) : undefined} removeName={`Unlink ${l.title}`} />
  );
  return (
    <section className="lc-sec" aria-label="Links">
      <div className="sec"><span>Linked</span>{out.length > 0 && <span className="meta">{out.length}</span>}</div>
      {out.length > 0 && <div ref={outHost} className="lc-chips">{out.map((l) => chip(l, 'Linked to', true))}</div>}
      <button type="button" className="ghost lc-add" onClick={() => setPicking(true)}><LinkGlyph />Link to…</button>
      {out.length === 0 && inn.length === 0 && <p className="lc-empty">Nothing linked yet. Link a note, a class, anything.</p>}
      {inn.length > 0 && (
        <>
          <div className="sec"><span>Linked from</span><span className="meta">{inn.length}</span></div>
          <div ref={inHost} className="lc-chips">{(all ? inn : inn.slice(0, CAP)).map((l) => chip(l, 'Linked from', false))}</div>
          {inn.length > CAP && <button type="button" className="link" onClick={() => setAll(!all)}>{all ? 'Show fewer' : `Show all ${inn.length}`}</button>}
        </>
      )}
      <LinkPicker open={picking} onClose={() => setPicking(false)} from={from} linked={out.map((l) => l.id)} onLink={ops.link} />
    </section>
  );
}

// ---------------------------------------------------------------- Link to…: search every app, one tap = one link
function Result({ h, done, onPick }: { h: SearchHit; done: boolean; onPick: () => void }) {
  return (
    <li className="row" data-row={h.id}>
      <button type="button" className="row-btn lc-res" disabled={done} onClick={onPick}>
        <span className="main"><span className="t">{h.title}</span>{h.snippet && <span className="s">{h.snippet}</span>}</span>
        {done && <span className="lc-done"><Icon name="check" size={16} sw={2.4} />Linked</span>}
      </button>
    </li>
  );
}
function Group({ app, hits, linked, onPick }: { app: string; hits: SearchHit[]; linked: string[]; onPick: (h: SearchHit, dye?: string) => void }) {
  const meta = useAppMeta(app);
  return (
    <section aria-label={meta.name} className="lc-group">
      <div className="sec"><span className="lc-gh"><i className="lc-dot" data-dye={meta.dye} aria-hidden="true" />{meta.name}</span></div>
      <ul className="card list">{hits.map((h) => <Result key={`${h.ref}:${h.id}`} h={h} done={linked.includes(h.id)} onPick={() => onPick(h, meta.dye)} />)}</ul>
    </section>
  );
}
/** A sheet: a search field (autofocus on a fine pointer), results grouped by app with their dye dots, suggestions while it is empty. */
export function LinkPicker({ open, onClose, from, linked, onLink }: {
  open: boolean; onClose: () => void; from: { id: string; app: string; title: string }; linked: string[];
  onLink: (to: { ref: string; id: string; title: string; app: string }, dye?: string) => Promise<boolean>;
}) {
  const [q, setQ] = useState('');
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [failed, setFailed] = useState(false);
  const field = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!open) { setQ(''); setHits(null); setFailed(false); return; }
    let live = true;
    const t = setTimeout(() => {
      searchRecords(q.trim(), { exclude: from.id }).then((h) => { if (live) { setHits(h.filter((x) => x.id !== from.id)); setFailed(false); } }, () => { if (live) { setHits([]); setFailed(true); } });
    }, q ? 150 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [open, q, from.id]);
  const groups: [string, SearchHit[]][] = [];
  for (const h of hits ?? []) { const g = groups.find((x) => x[0] === h.app); if (g) g[1].push(h); else groups.push([h.app, [h]]); }
  const pick = async (h: SearchHit, dye?: string) => { if (await onLink({ ref: h.ref, id: h.id, title: h.title, app: h.app }, dye)) onClose(); };
  return (
    <Sheet open={open} onClose={onClose} label="Link to…" onOpened={() => { if (matchMedia('(pointer: fine)').matches) field.current?.focus({ preventScroll: true }); }}>
      <div className="lc-picker">
        <div className="sheet-head"><span className="txt"><h2>Link to…</h2><span className="sub">{from.title}</span></span></div>
        <input ref={field} className="fld" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search all your apps" aria-label="Search all your apps" autoComplete="off" enterKeyHint="search"
          onKeyDown={(e) => { if (e.key === 'ArrowDown') { e.preventDefault(); document.querySelector<HTMLElement>('.lc-res:not(:disabled)')?.focus(); } }} />
        <p className="lc-hint" role="status">{hits === null ? 'Searching…' : failed ? "Search isn't available right now." : q.trim() ? (hits.length ? '' : `Nothing matches "${q.trim()}".`) : 'Suggested'}</p>
        {groups.map(([app, hs]) => <Group key={app} app={app} hits={hs} linked={linked} onPick={pick} />)}
      </div>
    </Sheet>
  );
}

// ---------------------------------------------------------------- a relation field in the form: chips of the target's rows
/** Chips for the rows of the target collection (this app's, or another app's): the picked ones first with a ×, the rest to add, a search past six. */
export function RelationPicker({ field, app, value, onChange, labelId }: { field: Field; app: string; value: string[]; onChange: (v: string[]) => void; labelId: string }) {
  const tApp = appOf(field.target!);
  useEnsureApps(tApp === app ? [] : [tApp]);
  const target = useStore((s) => s.apps[tApp]);
  const meta = useAppMeta(tApp);
  const c = target?.spec.collections.find((x) => `${tApp}/${x.key}` === field.target);
  const rows = target?.data[field.target!] as Rec[] | undefined;
  const [q, setQ] = useState('');
  const host = useRef<HTMLDivElement>(null);
  useArrive(host, value);
  if (!target || !c || !rows) return <p className="lc-hint" role="status">Loading {field.label.toLowerCase()}s…</p>;
  const all = rows.map((r) => ({ id: r.id, text: titleOf(c, r) }));
  const known = new Map(all.map((o) => [o.id, o.text]));
  const cross = tApp !== app;
  const word = singular(c);
  const picked = value.map((id) => ({ id, text: known.get(id) ?? GONE }));
  const needle = q.trim().toLowerCase();
  const rest = all.filter((o) => !value.includes(o.id) && (!needle || o.text.toLowerCase().includes(needle)));
  const shown = needle ? rest : rest.slice(0, 30);
  const set = (id: string) => onChange(field.many ? [...value, id] : [id]);
  const dot = cross && <i className="lc-dot" data-dye={meta.dye} aria-hidden="true" />;
  return (
    <div className="lc-pick" role="group" aria-labelledby={labelId} ref={host}>
      {picked.length > 0 && (
        <span className="chips">
          {picked.map((p) => (
            <button key={p.id} type="button" className="chip pick sel" data-lc={p.id} aria-label={`Remove ${p.text}`} onClick={() => onChange(value.filter((x) => x !== p.id))}>
              {dot}<span className="lc-t">{p.text}</span><Icon name="close" size={14} sw={2.4} />
            </button>
          ))}
        </span>
      )}
      {all.length > 6 && <input className="fld" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Search ${c.name.toLowerCase()}`} aria-label={`Search ${c.name.toLowerCase()}`} autoComplete="off" />}
      {all.length === 0 && <p className="lc-hint">No {c.name.toLowerCase()} yet{cross ? ` in ${meta.name}` : ''}.</p>}
      {shown.length > 0 && (
        <span className="chips">
          {shown.map((o) => <button key={o.id} type="button" className="chip pick" aria-label={`${field.many && picked.length ? 'Also in' : 'Set'} ${word} ${o.text}`} onClick={() => set(o.id)}>{dot}<span className="lc-t">{o.text}</span></button>)}
        </span>
      )}
      {!needle && rest.length > shown.length && <p className="lc-hint">Search to see {rest.length - shown.length} more.</p>}
      {needle && rest.length === 0 && <p className="lc-hint">Nothing matches "{q.trim()}".</p>}
    </div>
  );
}

// ---------------------------------------------------------------- [[ in a long text field
function Option({ h, id, active, onPick, onHover }: { h: SearchHit; id: string; active: boolean; onPick: () => void; onHover: () => void }) {
  const meta = useAppMeta(h.app);
  return (
    <li id={id} role="option" aria-selected={active} className="lc-opt" onClick={onPick} onMouseMove={onHover}>
      <span className="lc-ot"><i className="lc-dot" data-dye={meta.dye} aria-hidden="true" />{h.title}</span>
      <span className="lc-os">{[meta.name, h.snippet].filter(Boolean).join(' · ')}</span>
    </li>
  );
}
/**
 * A textarea that grows with its text. Typing `[[` opens a listbox of records (this app's first, then every app): arrows and Enter
 * on a keyboard, a tap on touch; the choice goes in as `[[Title]]`; Escape closes it. The text stays as typed: the server turns each
 * `[[Title]]` into a link when it saves.
 */
export function BodyField({ id, value, onChange, placeholder, app, recId, max = 360, className = '', autoFocus }: { id: string; value: string; onChange: (v: string) => void; placeholder?: string; app: string; recId?: string; max?: number; className?: string; autoFocus?: boolean }) {
  const ta = useRef<HTMLTextAreaElement>(null);
  const [trig, setTrig] = useState<{ start: number; end: number; q: string } | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState(0);
  const list = useId();
  const open = !!trig;
  useLayoutEffect(() => { // `max` caps the growth (a sheet's field); a page writes without a cap, so the page scroll is kept while the height resets
    const el = ta.current; if (!el) return;
    const y = window.scrollY;
    el.style.height = 'auto'; el.style.height = `${Math.min(el.scrollHeight, max)}px`;
    if (window.scrollY !== y) window.scrollTo(window.scrollX, y);
  }, [value, max]);
  const detect = (el: HTMLTextAreaElement) => {
    const caret = el.selectionStart ?? 0;
    const m = /\[\[([^[\]\n]{0,60})$/.exec(el.value.slice(0, caret));
    setTrig((t) => (m ? (t && t.start === caret - m[0].length && t.q === m[1] && t.end === caret ? t : { start: caret - m[0].length, end: caret, q: m[1] }) : null));
  };
  const q = trig?.q;
  useEffect(() => {
    if (q === undefined) { setHits([]); return; }
    let live = true;
    setBusy(true);
    const t = setTimeout(() => {
      searchRecords(q, { exclude: recId }).then((h) => { if (!live) return; setHits([...h.filter((x) => x.app === app), ...h.filter((x) => x.app !== app)].slice(0, 8)); setActive(0); setBusy(false); }, () => { if (live) { setHits([]); setBusy(false); } });
    }, q ? 120 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [q, recId, app]);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => { if (open && hits.length && max <= 360) box.current?.scrollIntoView({ block: 'nearest' }); }, [open, hits.length, max]); // a page's list is pinned to the screen's bottom (notes.css), so it needs no scrolling to
  const pick = (h: SearchHit) => {
    if (!trig) return;
    const next = value.slice(0, trig.start) + `[[${h.title}]]` + value.slice(trig.end).replace(/^\]\]/, '');
    const caret = trig.start + h.title.length + 4;
    onChange(next); setTrig(null);
    requestAnimationFrame(() => { ta.current?.focus({ preventScroll: true }); ta.current?.setSelectionRange(caret, caret); });
  };
  const key = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); setTrig(null); return; } // the sheet behind keeps its Escape for the next press
    if (!hits.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => (a + 1) % hits.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => (a - 1 + hits.length) % hits.length); }
    else if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); pick(hits[active]); }
  };
  return (
    <div className={`lc-body${className ? ` ${className}` : ''}`}>
      <textarea ref={ta} id={id} className={`fld fld-multi${className ? ` ${className}-ta` : ''}`} rows={4} autoFocus={autoFocus} value={value} placeholder={placeholder}
        aria-autocomplete="list" aria-haspopup="listbox" aria-controls={open && hits.length ? list : undefined} aria-activedescendant={open && hits.length ? `${list}-${active}` : undefined}
        onChange={(e) => { onChange(e.target.value); detect(e.target); }} onKeyDown={key}
        onKeyUp={(e) => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) detect(e.currentTarget); }}
        onClick={(e) => detect(e.currentTarget)} onBlur={() => setTrig(null)} />
      {open && (
        <div ref={box} className="lc-sug" onMouseDown={(e) => e.preventDefault()} onPointerDown={(e) => e.preventDefault()}>
          {hits.length > 0
            ? <ul id={list} role="listbox" aria-label="Link to">{hits.map((h, i) => <Option key={`${h.ref}:${h.id}`} h={h} id={`${list}-${i}`} active={i === active} onPick={() => pick(h)} onHover={() => setActive(i)} />)}</ul>
            : <p className="lc-hint" role="status">{busy ? 'Searching…' : 'No match yet.'}</p>}
        </div>
      )}
    </div>
  );
}

/** A long text as it reads: each `[[Title]]` that resolves in the record's links is a chip that opens it; one that doesn't stays text. */
export function BodyText({ text, links: ls, app, onNavigate }: { text: string; links: LinkRef[]; app: string; onNavigate?: () => void }) {
  const go = useNavigate();
  const parts: ReactNode[] = [];
  let last = 0, n = 0;
  for (const m of text.matchAll(/\[\[([^[\]\n]+)\]\]/g)) {
    const at = m.index ?? 0;
    if (at > last) parts.push(text.slice(last, at));
    const hit = ls.find((l) => l.title.toLowerCase() === m[1].trim().toLowerCase());
    parts.push(hit
      ? <Chip key={`w${n++}`} id={`w:${hit.id}`} app={hit.app} text={hit.title} gone={isGone(hit)} dot showApp={hit.app !== app} name={(a) => `Linked to ${hit.title} in ${a}. Open`} onOpen={() => { onNavigate?.(); go(goRow(hit.app, hit.id)); }} />
      : m[0]);
    last = at + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}
