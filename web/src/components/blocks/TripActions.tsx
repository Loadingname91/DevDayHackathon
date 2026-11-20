import { useEffect, useMemo, useState, type FormEvent } from 'react';
import '../../styles/trips.css';
import { errorText, request } from '../../api/client';
import type { CommandResult, FinishAction, ListBlock, Rec } from '../../api/types';
import { day, isDone, money, relIds, title as titleOf } from '../../lib/format';
import { afterCommand, openClair, toast, useStore } from '../../lib/store';
import { send } from '../../lib/turns';
import { AttachButtons, AttachTray, useAttachments } from '../attach';
import { Glyph } from '../attach/Glyph';
import { Icon } from '../Icon';
import { Sheet } from '../Sheet';
import type { Ctx } from './index';

/**
 * The two ways a list of done-one-by-one rows (Groceries) turns into a group (a trip), under its card:
 *   Finish trip   the rows ticked since the last trip, picked in a sheet, plus the group's own fields; one command, one Undo.
 *   Snap a photo  a picture of a list or a receipt goes to Clair with the intent Sam chose; the answer is a basted card.
 * Generic: both are declared on the block (`finish`, `snap`), so an app Clair builds with the same shape gets them.
 */
/** What the actions read from a list or a checklist. */
export type ActionBlock = Pick<ListBlock, 'source' | 'finish' | 'snap' | 'switch'>;

export function ListActions({ block, ctx }: { block: ActionBlock; ctx: Ctx }) {
  const [finishing, setFinishing] = useState(false);
  const [snapping, setSnapping] = useState(false);
  const fin = block.finish;
  const snap = block.snap;
  if (ctx.preview || !(fin || snap) || !block.source.startsWith(ctx.spec.key + '/')) return null;
  const pending = fin ? pendingRows({ ...block, finish: fin }, ctx) : [];
  return (
    <>
      <div className="trip-acts" role="group" aria-label="Trips">
        {fin && (
          <button className={pending.length ? 'cta' : 'ghost'} onClick={() => setFinishing(true)}>
            <Icon name="check" size={16} sw={2.2} />{fin.label ?? 'Finish trip'}{pending.length > 0 && <span className="n">{pending.length}</span>}
          </button>
        )}
        {snap && <button className="ghost" onClick={() => setSnapping(true)}><Glyph name="camera" size={18} />{snap.label ?? 'Snap a photo'}</button>}
      </div>
      {fin && <FinishSheet block={block} ctx={ctx} open={finishing} onClose={() => setFinishing(false)} />}
      {snap && <SnapSheet block={block} ctx={ctx} open={snapping} onClose={() => setSnapping(false)} />}
    </>
  );
}

/** Rows that are done and not yet in a group: what a trip can take. */
const pendingRows = (block: ActionBlock & { finish: FinishAction }, ctx: Ctx): Rec[] =>
  ((ctx.data[block.source] ?? []) as Rec[]).filter((r) => 'properties' in r && isDone(r) && relIds(r.properties[block.finish!.link]).length === 0);

// ---------------------------------------------------------------- Finish trip
function FinishSheet({ block, ctx, open, onClose }: { block: ActionBlock; ctx: Ctx; open: boolean; onClose: () => void }) {
  const fin = block.finish!;
  const c = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === block.source)!;
  const into = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === fin.into);
  const rows = pendingRows({ ...block, finish: fin }, ctx);
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [store, setStore] = useState('');
  const [total, setTotal] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const key = rows.map((r) => r.id).join('|');
  useEffect(() => { if (open) { setSel(new Set(rows.map((r) => r.id))); setErr(''); } }, [open, key]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (!open) { setStore(''); setTotal(''); } }, [open]);

  const nameField = into?.titleField ?? 'store';
  const recent = useMemo(() => {
    const seen: string[] = [];
    const trips = [...((ctx.data[fin.into] ?? []) as Rec[])].sort((a, b) => String(b.properties.at ?? '').localeCompare(String(a.properties.at ?? '')));
    for (const t of trips) { const s = String(t.properties[nameField] ?? ''); if (s && !seen.includes(s)) seen.push(s); }
    return seen.slice(0, 4);
  }, [ctx.data, fin.into, nameField]);
  const listField = c.fields.find((f) => f.key === block.switch);
  const sub = (r: Rec) => [r.properties.qty, listField?.options?.find((o) => o.id === r.properties[listField.key])?.label].filter(Boolean).join(' · ');
  const cents = Math.round(parseFloat(total.replace(/[$,\s]/g, '')) * 100);
  const valid = store.trim().length > 0 && Number.isFinite(cents) && cents > 0;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!valid) { setErr(`Enter the ${nameField} and the total.`); return; }
    setBusy(true); setErr('');
    try {
      const r = await request<CommandResult>('POST', '/trips/finish', {
        collection_id: fin.into, link: fin.link, record_ids: [...sel], fields: { [nameField]: store.trim(), total: (cents / 100).toFixed(2) },
      });
      await afterCommand(r);
      toast(`Trip added: ${store.trim()}, ${money(cents)}.`, { label: 'Undo', run: async () => {
        try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); }
      } }, 6000);
      ctx.reload?.(); onClose();
    } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });

  return (
    <Sheet open={open} onClose={onClose} label={fin.label ?? 'Finish trip'}>
      <form className="add-form" onSubmit={submit} noValidate>
        <div className="sheet-head"><span className="txt"><h2>{fin.label ?? 'Finish trip'}</h2><span className="sub">{ctx.now ? `Today, ${day(ctx.now)}` : ctx.spec.name}</span></span></div>
        {rows.length > 0 ? (
          <div className="trip-pick" role="group" aria-label="What was on this trip">
            <div className="sec"><span>Bought, not on a trip yet</span><span className="meta">{sel.size} of {rows.length}</span></div>
            {rows.map((r) => (
              <button type="button" key={r.id} role="checkbox" aria-checked={sel.has(r.id)} className="trip-opt" onClick={() => toggle(r.id)}>
                <i className="box" aria-hidden="true"><Icon name="check" size={14} sw={2.6} /></i>
                <span className="main"><span className="t">{titleOf(c, r)}</span>{sub(r) && <span className="s">{sub(r)}</span>}</span>
              </button>
            ))}
          </div>
        ) : <p className="trip-none">Nothing is bought yet. Tick items as you shop, or log the trip without them.</p>}
        <div className="add-field">
          <label htmlFor="trip_store">{into?.fields.find((f) => f.key === nameField)?.label ?? 'Store'}</label>
          {recent.length > 0 && <span className="chips" role="group" aria-label="Recent">{recent.map((s) => <button type="button" key={s} className="chip pick" aria-pressed={store === s} onClick={() => setStore(s)}>{s}</button>)}</span>}
          <input id="trip_store" className="fld" type="text" value={store} placeholder="Store" onChange={(e) => setStore(e.target.value)} autoComplete="off" />
        </div>
        <div className="add-field">
          <label htmlFor="trip_total">Total</label>
          <input id="trip_total" className="fld" type="text" inputMode="decimal" value={total} placeholder="$0.00" onChange={(e) => setTotal(e.target.value)} autoComplete="off" />
        </div>
        {err && <p className="err" role="alert">{err}</p>}
        <span className="sheet-actions"><button type="button" className="ghost" onClick={onClose}>Cancel</button><button className="cta" disabled={busy}>{fin.label ?? 'Finish trip'}</button></span>
      </form>
    </Sheet>
  );
}

// ---------------------------------------------------------------- Snap a photo
function SnapSheet({ block, ctx, open, onClose }: { block: ActionBlock; ctx: Ctx; open: boolean; onClose: () => void }) {
  const snap = block.snap!;
  const wid = useStore((s) => s.me?.workspace.id);
  const a = useAttachments({ workspaceId: wid });
  const [intent, setIntent] = useState(snap.intents[0]?.id ?? '');
  useEffect(() => { if (!open) a.clear(); }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  const chosen = snap.intents.find((i) => i.id === intent) ?? snap.intents[0];
  const ready = a.ready && a.hasSendable;

  const go = () => {
    if (!ready || !chosen) return;
    const sent = send({ text: chosen.ask, ...a.request(), context: { app: ctx.spec.key, collection: block.source, intent: chosen.id } }, chosen.ask);
    if (!sent) { toast('Clair is still on your last message.', undefined, 3000); return; }
    a.clear(); onClose(); openClair(true);
  };
  return (
    <Sheet open={open} onClose={onClose} label={snap.label ?? 'Snap a photo'}>
      <div className="add-form">
        <div className="sheet-head"><span className="txt"><h2>{snap.label ?? 'Snap a photo'}</h2><span className="sub">What is the picture of?</span></span></div>
        <div className="trip-pick" role="radiogroup" aria-label="What is the picture of?">
          {snap.intents.map((i) => (
            <button type="button" key={i.id} role="radio" aria-checked={i.id === intent} className="trip-opt" onClick={() => setIntent(i.id)}>
              <i className="dot" aria-hidden="true" />
              <span className="main"><span className="t">{i.label}</span>{i.hint && <span className="s">{i.hint}</span>}</span>
            </button>
          ))}
        </div>
        <AttachTray items={a.list} onRemove={a.remove} onRetry={a.retry} notice={a.notice} />
        <div className="trip-photo">
          <AttachButtons onFiles={a.add} labelled disabled={a.full} />
        </div>
        <p className="trip-note">Clair reads it and shows what it would add. Nothing is saved until you confirm.</p>
        <span className="sheet-actions"><button type="button" className="ghost" onClick={onClose}>Cancel</button><button type="button" className="cta" disabled={!ready} onClick={go}>Read it</button></span>
      </div>
    </Sheet>
  );
}
