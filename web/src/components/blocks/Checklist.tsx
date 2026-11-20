import { useState } from 'react';
import { errorText, request } from '../../api/client';
import type { ChecklistBlock, CommandResult, Field, Rec } from '../../api/types';
import { aNoun, day, dayKey, fieldText, isDone, relDue, singular, time, title } from '../../lib/format';
import { useRowEnter } from '../../lib/enter';
import { EASE, RM, sleep, T } from '../../lib/motion';
import { afterCommand, setDetail, toast, useStore } from '../../lib/store';
import { AddSheet } from '../AddSheet';
import { useWide } from '../../lib/useWide';
import { EmptyState } from '../EmptyState';
import { Icon } from '../Icon';
import { backlinksOf, hasRel, linksOf, relFields, RowRel } from '../Links';
import { QuickAdd } from '../QuickAdd';
import { ListActions } from './TripActions';
import { resetRow, SwipeRow } from '../SwipeRow';
import { passesAll } from './filter';
import type { Ctx } from './index';

/**
 * Rows to tick, in sections (boards To-dos and Groceries). Tap the circle or swipe right to
 * complete; swipe left to delete; tap the row to edit it. Done rows fold into their own
 * section. The add field is pinned above the bar (To-dos) or ends the list (Groceries).
 */
/** Rows a section draws before "Show all N": a 200-row list stays a screen or two, not twelve. */
const CAP = 40;

export function Checklist({ block, ctx }: { block: ChecklistBlock; ctx: Ctx }) {
  const [, appKey] = [0, ctx.spec.key];
  const c = ctx.spec.collections.find((x) => `${appKey}/${x.key}` === block.source);
  const sw = block.switch ? c?.fields.find((f) => f.key === block.switch) : undefined;
  const [picked, setPicked] = useState(sw?.options?.[0]?.id);
  const [ticked, setTicked] = useState<Record<string, boolean>>({});
  const [openDone, setOpenDone] = useState<Record<number, boolean>>({});
  const [showAll, setShowAll] = useState<Record<number, boolean>>({}); // a long section shows its first rows, then all on request
  const [editing, setEditing] = useState<Rec | null>(null);
  const wide = useWide();
  const inPane = useStore((s) => s.detail?.id);
  const [adding, setAdding] = useState(false);
  // a row that arrives after the list is on screen grows in (lib/enter.ts); `scope` keeps a switch between lists from counting as arrivals,
  // `lift`: with no inline add field the empty card shows, and the first row rises as that card fades (EmptyState)
  const rel = c && ctx.filter && relFields(c).some((f) => f.key === ctx.filter!.field) ? ctx.filter : undefined; // `?filter=`: only the rows that hold that id
  const inRel = (r: Rec) => !rel || hasRel(r, rel.field, rel.id);
  const held = ctx.data[block.source] as Rec[] | undefined;
  useRowEnter(held ? held.filter((r) => inRel(r) && (!sw || r.properties[sw.key] === picked) && block.groups.some((g) => passesAll(r, g.where, ctx.now))).map((r) => r.id) : null,
    { scope: `${picked ?? ''}${rel ? `|${rel.field}:${rel.id}` : ''}`, lift: !(block.add && !ctx.preview && !block.add.pinned) });
  if (!c) return null;
  const all = ((ctx.data[block.source] ?? []) as Rec[]).filter(inRel);
  const chipKeys = relFields(c).map((f) => f.key); // drawn as chips under the row, so not again in its meta line
  const only = block.fields?.length ? block.fields : undefined;
  const inSwitch = (r: Rec) => !sw || r.properties[sw.key] === picked;
  const option = sw?.options?.find((o) => o.id === picked)?.label ?? '';
  const fill = (s: string, n: number) => s.replace('{n}', String(n)).replace('{option}', option).replace('{today}', ctx.now ? day(ctx.now) : '');
  const shown = (block.fields ?? []).map((k) => c.fields.find((f) => f.key === k)).filter((f): f is Field => !!f && !(f.type === 'relation' && chipKeys.includes(f.key)));
  const lookup = (ref: string, id: string) => {
    const col = ctx.spec.collections.find((x) => `${appKey}/${x.key}` === ref);
    const r = (ctx.data[ref] as Rec[] | undefined)?.find((x) => x.id === id);
    return r && col ? title(col, r) : undefined;
  };

  const rowEl = (id: string) => document.querySelector<HTMLElement>(`[data-row="${id}"]`);
  /** The one fold every leaving row uses (220 ms, height and opacity), so the rows below close the gap together. */
  const fold = async (li: HTMLElement | null) => {
    if (li && !RM()) await li.animate([{ height: `${li.offsetHeight}px`, opacity: 1 }, { height: '0px', opacity: 0 }], { duration: T.state, easing: EASE, fill: 'forwards' }).finished.catch(() => {});
  };
  /** Resolves true once the row has left, false if it did not (the swipe then springs the row back). */
  const complete = async (r: Rec, li: HTMLElement | null, fromSwipe = false): Promise<boolean> => {
    if (ticked[r.id] || isDone(r)) return false;
    setTicked((t) => ({ ...t, [r.id]: true }));
    const occ = r.properties.repeat && c.dateField ? dayKey(String(r.properties[c.dateField] ?? '')) : undefined;
    try {
      const res = await request<CommandResult>('POST', `/records/${r.id}/complete`, occ ? { occurrence: occ } : {});
      toast(`Done: ${title(c, r)}.`, { label: 'Undo', run: async () => {
        try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${res.change_set_id}/undo`)); setTicked((t) => ({ ...t, [r.id]: false })); resetRow(rowEl(r.id)); ctx.reload?.(); }
        catch (x) { toast(errorText(x)); }
      } }, 5000);
      await sleep(RM() || fromSwipe ? 0 : 200); // the check lands before the row leaves; after a swipe the row is already gone
      await fold(li);
      await afterCommand(res);
      ctx.reload?.();
      setTicked((t) => { const n = { ...t }; delete n[r.id]; return n; });
      setTimeout(() => resetRow(li), 1500); // a repeating item stays in its list: unfold it (a removed row is gone by then)
      return true;
    } catch (x) { setTicked((t) => ({ ...t, [r.id]: false })); toast(errorText(x), undefined, 4000); return false; }
  };
  const remove = async (r: Rec, li: HTMLElement | null): Promise<boolean> => {
    try {
      const res = await request<CommandResult>('DELETE', `/records/${r.id}`);
      toast(`Deleted ${title(c, r)}.`, { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${res.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } }, 5000);
      await fold(li); // same fold as a completed row, so the rows below do not jump
      await afterCommand(res); ctx.reload?.();
      return true;
    } catch (x) { toast(errorText(x), undefined, 4000); return false; }
  };

  const row = (r: Rec, groupLabel: string) => {
    const done = isDone(r) || !!ticked[r.id];
    const via = r.properties._via as { app?: string; workflow?: string } | undefined;
    const from = via?.app ? ctx.apps.find((a) => a.key === via.app) : undefined;
    const due = block.due ? r.properties[block.due] : undefined;
    const rel = typeof due === 'string' && ctx.now && !done ? relDue(due, ctx.now) : null;
    const sub = shown.map((f) => {
      const v = r.properties[f.key];
      if (f.key === block.due && typeof v === 'string') return groupLabel.startsWith('Today') ? time(v) : rel && !rel.overdue ? rel.text + (time(v) ? `, ${time(v)}` : '') : fieldText(f, v, ctx.now, lookup);
      return fieldText(f, v, ctx.now, lookup);
    }).filter(Boolean).join(' · ');
    const google = r.properties.source === 'google';
    return (
      <SwipeRow key={r.id} className={`row ${done ? 'done' : ''}`} data-dye={ctx.spec.dye}
        onRight={!ctx.preview && !done && block.swipe?.right ? () => complete(r, rowEl(r.id), true) : undefined}
        onLeft={!ctx.preview && block.swipe?.left ? () => remove(r, rowEl(r.id)) : undefined}
        data-row={r.id}>
        <div className="row-in">
          <button className="tick" role="checkbox" aria-checked={done} aria-label={`Done: ${title(c, r)}`} disabled={ctx.preview || google || done}
            onClick={(e) => complete(r, e.currentTarget.closest('li'))}><Icon name="check" size={14} sw={2.6} /></button>
          <button className="main" aria-pressed={wide ? inPane === r.id : undefined} disabled={ctx.preview}
            onClick={() => { if (ctx.preview || google) return; if (wide) setDetail({ app: appKey, ref: block.source, id: r.id }); else setEditing(r); }}>
            <span className="t">{title(c, r)}{rel?.overdue && <span className="pill status">{rel.text}</span>}{r.example && <span className="pill soft">example</span>}</span>
            {sub && <span className="s">{sub}</span>}
            {from && <span className="from" data-dye={from.dye}><i />from {from.name}</span>}
            {via?.workflow && <span className="from">by rule ›</span>}
          </button>
        </div>
        {!ctx.preview && !r.example && (chipKeys.length > 0 || linksOf(r).length > 0 || backlinksOf(r).length > 0) && <RowRel rec={r} c={c} app={appKey} only={only} />}
      </SwipeRow>
    );
  };

  const groups = block.groups.map((g, i) => ({ g, i, rows: all.filter((r) => inSwitch(r) && passesAll(r, g.where, ctx.now)) }));
  const firstOpen = groups.find((x) => !x.g.done)?.i;
  const add = block.add && !ctx.preview ? block.add : undefined;
  const addInline = add && !add.pinned;
  // a new row should land in the list it was added from: the open section's `field eq "text"` tests (Classes' Due: kind assignment)
  const openDefaults: Record<string, string> = Object.fromEntries((block.groups.find((g) => !g.done)?.where ?? [])
    .filter((w) => w.op === 'eq' && typeof w.value === 'string').map((w) => [w.field, w.value as string]));
  const anyRows = groups.some((x) => x.rows.length);

  return (
    <>
      {sw && (
        <div className="chips scroll" role="group" aria-label={sw.label} data-dye={ctx.spec.dye}>
          {sw.options!.map((o) => (
            <button key={o.id} className="chip" aria-pressed={o.id === picked} onClick={() => setPicked(o.id)}>
              {o.label}<span className="n">{all.filter((r) => r.properties[sw.key] === o.id && block.groups[0] && passesAll(r, block.groups[0].where, ctx.now)).length}</span>
            </button>
          ))}
        </div>
      )}
      {!anyRows && !addInline && <EmptyState card onAdd={ctx.preview ? undefined : () => setAdding(true)} actions={!ctx.preview} compact={ctx.many} />}
      {groups.map(({ g, i, rows }) => {
        if (!rows.length && !(addInline && i === firstOpen)) return null;
        const label = fill(g.label, rows.length);
        const closed = g.collapsed && !openDone[i];
        return (
          <section key={i} className="cl-group" aria-label={label}>
            {g.collapsed
              ? <button className="sec sec-btn" aria-expanded={!closed} onClick={() => setOpenDone((o) => ({ ...o, [i]: !o[i] }))}><span>{label}</span><Icon name="chev" size={16} /></button>
              : <div className="sec"><span>{label}</span>{i === firstOpen && sw && <span className="meta">{sw.options?.find((o) => o.id === picked)?.hint ?? (picked === sw.options?.[0]?.id ? 'Default list' : '')}</span>}</div>}
            {!closed && (
              <ul className="card list">
                {(showAll[i] || rows.findIndex((r) => r.id === inPane) >= CAP ? rows : rows.slice(0, CAP)).map((r) => row(r, label))}
                {rows.length > CAP && <li><button className="more-rows" onClick={() => setShowAll((o) => ({ ...o, [i]: !o[i] }))}>{showAll[i] ? 'Show fewer' : `Show all ${rows.length}`}</button></li>}
                {addInline && i === firstOpen && (
                  <li><QuickAdd collection={c} app={appKey} defaults={{ ...(sw && picked ? { [sw.key]: picked } : {}), ...Object.fromEntries(Object.entries(add.set ?? {}).map(([k, v]) => [k, String(v)])) }}
                    placeholder={fill(add.placeholder, 0)} onMore={() => setAdding(true)} onAdded={() => ctx.reload?.()} /></li>
                )}
              </ul>
            )}
          </section>
        );
      })}
      {/* a checklist with no add field of its own (Classes' Due) still ends in "Add a …", as a list does */}
      {!block.add && !ctx.preview && anyRows && block.source.startsWith(appKey + '/') && (
        <ul className="card list"><li className="add-row-li quick-wrap"><button className="add-row" onClick={() => setAdding(true)}><Icon name="plus" size={16} />Add {aNoun(singular(c))}</button></li></ul>
      )}
      <ListActions block={block} ctx={ctx} />
      {add?.pinned && <AddDock block={block} ctx={ctx} placeholder={fill(add.placeholder, 0)} onMore={() => setAdding(true)} />}
      <AddSheet app={appKey} appName={ctx.spec.name} collection={c} now={ctx.now} apps={ctx.apps}
        defaults={{ ...openDefaults, ...(sw && picked ? { [sw.key]: picked } : {}), ...(rel ? { [rel.field]: rel.id } : {}), ...Object.fromEntries(Object.entries(block.add?.set ?? {}).map(([k, v]) => [k, String(v)])) }}
        open={adding} onClose={() => setAdding(false)} onAdded={() => ctx.reload?.()} />
      <AddSheet app={appKey} appName={ctx.spec.name} collection={c} now={ctx.now} apps={ctx.apps} record={editing ?? undefined}
        open={!!editing} onClose={() => setEditing(null)} onAdded={() => ctx.reload?.()} />
    </>
  );
}

/** The add field pinned above the bar (board To-dos): type and press Enter. */
function AddDock({ block, ctx, placeholder, onMore }: { block: ChecklistBlock; ctx: Ctx; placeholder: string; onMore: () => void }) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const c = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === block.source)!;
  const add = async () => {
    const t = text.trim();
    if (!t || busy) return;
    setBusy(true);
    try {
      const r = await request<CommandResult>('POST', '/records', { collection_id: block.source, fields: { ...(block.add?.set ?? {}), [c.titleField]: t } });
      setText(''); await afterCommand(r); ctx.reload?.();
      toast(`Added ${t}.`, { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } }, 4000);
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };
  return (
    <form className="add-dock" onSubmit={(e) => { e.preventDefault(); void add(); }}>
      <input value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} aria-label={placeholder} enterKeyHint="done" autoComplete="off" />
      {text.trim()
        ? <button className="go" aria-label="Add" disabled={busy}><Icon name="plus" size={18} /></button>
        : <button type="button" className="go" aria-label="Add with more details" onClick={onMore}><Icon name="plus" size={18} /></button>}
    </form>
  );
}
