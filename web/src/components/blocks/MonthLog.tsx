import { useEffect, useState } from 'react';
import { errorText, request } from '../../api/client';
import type { CommandResult, MonthBlock, Rec } from '../../api/types';
import { addDays, day, dayKey, dayNum, monthName, wall, weekStart } from '../../lib/format';
import { RM, T } from '../../lib/motion';
import { afterCommand, toast } from '../../lib/store';
import { Icon } from '../Icon';
import { Sheet } from '../Sheet';
import type { Ctx } from './index';

const SYMPTOMS = ['Cramps', 'Headache', 'Tired', 'Bloating', 'Low mood'];

/**
 * A month of days to log into (Cycle). Logged days are filled by flow, start days carry a
 * ring; tap a day to log or change flow, energy 1 to 5 and symptoms. Only what was logged is
 * shown: no prediction appears in the app (CLAUDE.md, "not built for DevDay").
 */
export function MonthLog({ block, ctx }: { block: MonthBlock; ctx: Ctx }) {
  const rows = (ctx.data[block.source] ?? []) as Rec[];
  const starts = ((ctx.data[`${ctx.spec.key}/cycles`] ?? []) as Rec[]).map((r) => String(r.properties.start ?? ''));
  const c = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === block.source);
  const flowField = c?.fields.find((f) => f.key === block.mark);
  const today = ctx.now ? dayKey(ctx.now) : '';
  const [month, setMonth] = useState(today.slice(0, 7) + '-01'); // this month; logged days from last month show in its first row
  const [open, setOpen] = useState<string | null>(null);
  const byDay = new Map(rows.map((r) => [String(r.properties[block.dateField]), r]));
  const gridStart = weekStart(month);
  const cells = Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
  const w = wall(month)!;
  const level = (r?: Rec) => ({ none: 0, light: 1, medium: 2, heavy: 3 } as Record<string, number>)[String(r?.properties[block.mark] ?? '')] ?? 0;

  return (
    <div className="month-log" data-dye={ctx.spec.dye}>
      <div className="d-nav">
        <button className="round" aria-label="Earlier month" onClick={() => setMonth((m) => addDays(m, -1).slice(0, 7) + '-01')}><Icon name="back" /></button>
        <strong>{monthName(month)} {w.y}</strong>
        <button className="round" aria-label="Later month" onClick={() => setMonth((m) => addDays(m, 32).slice(0, 7) + '-01')}><Icon name="fwd" /></button>
      </div>
      <div className="card m-grid" role="grid" aria-label={`${monthName(month)} ${w.y}`}>
        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d2, i) => <span key={i} className="m-dow">{d2}</span>)}
        {cells.map((k) => {
          const r = byDay.get(k), lv = level(r), out = k.slice(0, 7) !== month.slice(0, 7);
          return (
            <button key={k} className={`m-cell log ${out ? 'out' : ''} ${k === today ? 'today' : ''} ${starts.includes(k) ? 'start' : ''}`} data-lv={lv}
              aria-label={`${day(k)}${r ? `, ${flowField?.options?.find((o) => o.id === r.properties[block.mark])?.label ?? 'logged'}` : ''}${starts.includes(k) ? ', period started' : ''}`}
              onClick={() => !ctx.preview && k <= today && setOpen(k)} disabled={k > today}>
              <span className={`m-n${dayNum(k) === 1 ? ' first' : ''}`}>{dayNum(k)}{dayNum(k) === 1 && <span className="m-mo"> {monthName(k)}</span>}</span>
              <span className="m-dots">
                {lv > 0 && <Flow lv={lv} />}
                {r?.properties.energy !== undefined ? <i title={`energy ${r.properties.energy}`} /> : null}
              </span>
            </button>
          );
        })}
      </div>
      <div className="m-legend"><span><i data-lv="1" />Light<Flow lv={1} /></span><span><i data-lv="2" />Medium<Flow lv={2} /></span><span><i data-lv="3" />Heavy<Flow lv={3} /></span><span><i className="lg-start" />Started</span></div>
      {!ctx.preview && <button className="cta wide" onClick={() => setOpen(today)}>Log today</button>}
      {open && <DayLog block={block} ctx={ctx} date={open} record={byDay.get(open)} onClose={() => setOpen(null)} />}
    </div>
  );
}

/** Flow as stitches, one to three: readable without the tint. */
function Flow({ lv }: { lv: number }) {
  return <span className="m-fl" aria-hidden="true">{Array.from({ length: lv }, (_, i) => <b key={i} />)}</span>;
}

function DayLog({ block, ctx, date, record, onClose }: { block: MonthBlock; ctx: Ctx; date: string; record?: Rec; onClose: () => void }) {
  const c = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === block.source)!;
  const flowField = c.fields.find((f) => f.key === block.mark);
  const [flow, setFlow] = useState(String(record?.properties[block.mark] ?? ''));
  const [energy, setEnergy] = useState<number | null>(record?.properties.energy !== undefined ? Number(record.properties.energy) : null);
  const [sym, setSym] = useState<string[]>(String(record?.properties.symptoms ?? '').split(',').map((s) => s.trim()).filter(Boolean));
  const [open, setOpen] = useState(true);
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (!open) { const t = setTimeout(onClose, RM() ? T.fb : T.layoutOut); return () => clearTimeout(t); } }, [open, onClose]);
  const save = async () => {
    setBusy(true);
    const fields: Record<string, unknown> = { [block.dateField]: date, [block.mark]: flow || 'none', symptoms: sym.join(', ') };
    if (energy) fields.energy = energy;
    try {
      const r = record
        ? await request<CommandResult>('PATCH', `/records/${record.id}`, { fields, base_version: record.version })
        : await request<CommandResult>('POST', '/records', { collection_id: block.source, fields });
      await afterCommand(r); ctx.reload?.();
      toast(`Logged ${day(date)}.`, { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } });
      setOpen(false);
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };
  return (
    <Sheet open={open} onClose={() => setOpen(false)} label={`Log ${day(date)}`}>
      <div className="sheet-head"><span className="txt"><h2>{day(date)}</h2><span className="sub">Private · only you see this</span></span></div>
      <div className="add-field"><label>Flow</label>
        <span className="chips" role="radiogroup" aria-label="Flow">{flowField?.options?.map((o) => <button key={o.id} className="chip" role="radio" aria-checked={flow === o.id} onClick={() => setFlow(flow === o.id ? '' : o.id)}>{o.label}</button>)}</span>
      </div>
      <div className="add-field"><label>Energy</label>
        <span className="chips" role="radiogroup" aria-label="Energy" style={{ flexWrap: 'nowrap' }}>{[1, 2, 3, 4, 5].map((n) => <button key={n} className="chip mood" role="radio" aria-checked={energy === n} onClick={() => setEnergy(energy === n ? null : n)}>{n}</button>)}</span>
        <span className="t-scale"><span>low</span><span>high</span></span>
      </div>
      <div className="add-field"><label>Symptoms</label>
        <span className="chips">{SYMPTOMS.map((s) => <button key={s} className="chip" aria-pressed={sym.includes(s)} onClick={() => setSym(sym.includes(s) ? sym.filter((x) => x !== s) : [...sym, s])}>{s}</button>)}</span>
      </div>
      <button className="cta wide" onClick={save} disabled={busy}>{record ? 'Save' : 'Log day'}</button>
    </Sheet>
  );
}
