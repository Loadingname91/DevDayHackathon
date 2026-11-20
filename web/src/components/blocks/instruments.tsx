// Instruments (design/DESIGN.md §10, design/screens-css.md §6 and §9): blocks that show
// what an app is for. Every figure comes from the server in ctx.values[block.id]; these
// components lay out and format, they never calculate.
import { useState, type CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorText, request } from '../../api/client';
import type { BarsBlock, CommandResult, CountdownBlock, GaugeBlock, NextBlock, PicksBlock, Rec, RingBlock, StripBlock } from '../../api/types';
import { afterCommand, toast } from '../../lib/store';
import { NoData } from '../EmptyState';
import { Icon } from '../Icon';
import { EditPencil, LimitsSheet } from '../LimitsSheet';
import type { Ctx } from './index';

/** `--len`: how many characters a figure has, so the stylesheet can size it to its card (styles/app.css). Layout only. */
export const fit = (text?: string): CSSProperties => ({ '--len': Math.max(1, (text ?? '').length) } as CSSProperties);
/** A bar's fill and its hatch: `--p` is how much of the track is filled, `--o` how much the excess takes from the right. The stylesheet clips to them,
 *  so a new value glides there with the number that rolls and a first paint does not animate (styles/app.css). */
export const fill = (pct: number, over?: number): CSSProperties => ({ '--p': `${over ? 100 - over : Math.min(100, Math.max(0, pct))}%`, '--o': `${over ?? 0}%` } as CSSProperties);

/** "$412 left of $1,200", the bar, "11 days to go" (board Budget). */
export function Gauge({ block, ctx }: { block: GaugeBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  const [editing, setEditing] = useState(false);
  if (!v || v.text === undefined) return <NoData label={block.label} failed={!!v} />;
  const edit = !ctx.preview ? block.edit : undefined; // a build preview writes nothing
  return (
    <section className={`card gauge${edit ? ' editable' : ''}`} data-dye={ctx.spec.dye} aria-label={block.label}>
      {edit && <EditPencil label={`Change ${edit.label.toLowerCase()}`} onClick={() => setEditing(true)} />}
      {edit && <LimitsSheet app={ctx.spec.key} appName={ctx.spec.name} mode={{ kind: 'setting', edit, current: v.limit }} open={editing} onClose={() => setEditing(false)} />}
      <div className="g-row"><span className="g-big" style={fit(v.text)}>{v.text}</span>{v.target && <span className="g-of">{v.target}</span>}</div>
      {v.pct !== undefined && <span className="track" role="meter" aria-valuenow={v.pct} aria-valuemin={0} aria-valuemax={100} aria-label={block.label}><span className="fill" style={fill(v.pct)} /></span>}
      {v.sub && <span className="g-sub">{v.sub}</span>}
      {v.link && <span className="link">{v.link} ›</span>}
    </section>
  );
}

/** One bar per category; the excess over a limit is an ink cross-hatch (board Budget, "Where it went"). */
export function Bars({ block, ctx }: { block: BarsBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  const [editing, setEditing] = useState(false);
  if (!v?.rows) return <NoData label={block.label} failed={!!v} />;
  const rows = v.rows;
  if (!rows.length) return null; // nothing to draw: no label and no empty card
  const edit = !ctx.preview && rows.some((r) => r.id) ? block.edit : undefined; // the limits sheet needs each row's option id
  return (
    <>
      <div className="sec"><span>{block.label}</span>
        {edit && <button type="button" className="sec-edit" onClick={() => setEditing(true)}><Icon name="pencil" size={16} sw={1.8} />{edit.label}</button>}
      </div>
      {edit && <LimitsSheet app={ctx.spec.key} appName={ctx.spec.name} mode={{ kind: 'options', edit, rows }} open={editing} onClose={() => setEditing(false)} />}
      <section className="card bars" data-dye={ctx.spec.dye}>
        {rows.map((r, i) => (
          <div className={`bar-row ${i ? 'sep' : ''}`} key={r.label}>
            <div className="b-head"><span className="b-l">{r.label}</span><span className="b-v">{r.text}</span></div>
            {r.pct !== undefined && (
              <span className="track b7" role="img" aria-label={`${r.label}: ${r.text}${r.note ? `, ${r.note}` : ''}`}>
                <span className="fill" style={fill(r.pct, r.over_pct)} />
                {r.over_pct ? <span className="hatch" style={fill(r.pct, r.over_pct)} /> : null}
              </span>
            )}
            {r.note && <span className="b-note">{r.note}</span>}
          </div>
        ))}
      </section>
    </>
  );
}

/** A goal ring: "1,140 of 2,200". Progress only, never a judgement. */
export function Ring({ block, ctx }: { block: RingBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  const [editing, setEditing] = useState(false);
  if (!v || v.text === undefined) return <NoData label={block.label} failed={!!v} />;
  const edit = !ctx.preview ? block.edit : undefined;
  const pct = Math.min(100, v.pct ?? 0), R = 52, C = 2 * Math.PI * R;
  return (
    <section className={`card ring${edit ? ' editable' : ''}`} data-dye={ctx.spec.dye} aria-label={`${block.label}: ${v.text} ${v.target ?? ''}`}>
      {edit && <EditPencil label={`Change ${edit.label.toLowerCase()}`} onClick={() => setEditing(true)} />}
      {edit && <LimitsSheet app={ctx.spec.key} appName={ctx.spec.name} mode={{ kind: 'setting', edit, current: v.limit }} open={editing} onClose={() => setEditing(false)} />}
      <svg width="132" height="132" viewBox="0 0 132 132" aria-hidden="true">
        <circle cx="66" cy="66" r={R} fill="none" stroke="var(--hair)" strokeWidth="12" />
        {pct > 0 && <circle className="ring-fill" cx="66" cy="66" r={R} fill="none" stroke="var(--deep)" strokeWidth="12" strokeLinecap="round"
          strokeDasharray={`${(C * pct) / 100} ${C}`} transform="rotate(-90 66 66)" />}
      </svg>
      <span className="r-txt">
        <span className="r-big" style={fit(v.text)}>{v.text}</span>
        {v.target && <span className="r-of">{v.target}</span>}
        {v.sub && <span className="r-sub">{v.sub}</span>}
      </span>
    </section>
  );
}

/** Days to the next dated row: "Winter 10K · 22 days to go · Sat 12 Dec". */
export function Countdown({ block, ctx }: { block: CountdownBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  if (!v) return null;
  return (
    <section className="card countdown" data-dye={ctx.spec.dye}>
      <span className="c-title">{v.title}</span>
      <span className="c-row"><span className="g-big" style={fit(v.text)}>{v.text}</span><span className="g-of">{v.unit}</span></span>
      {v.sub && <span className="g-sub">{v.sub}</span>}
      {v.note && <span className="g-sub">{v.note}</span>}
    </section>
  );
}

/** Mon to Sun with each day's figure; days with something logged take the app's colour. History, not a streak. */
export function Strip({ block, ctx }: { block: StripBlock; ctx: Ctx }) {
  const d = ctx.values[block.id]?.days;
  if (!d) return null;
  return (
    <>
      <div className="sec"><span>{block.label}</span></div>
      <div className="strip" data-dye={ctx.spec.dye}>
        {d.map((c, i) => (
          <span key={i} className={`s-cell ${c.on ? 'on' : ''} ${c.today ? 'today' : ''}`}>
            <span className="s-dow">{c.dow}</span>
            <b className="s-v">{c.text ?? '·'}</b>
          </span>
        ))}
      </div>
    </>
  );
}

/** "Again": tap a saved row to log it once more (Calories' foods into meals). */
export function Picks({ block, ctx }: { block: PicksBlock; ctx: Ctx }) {
  const rows = (ctx.data[block.from] ?? []) as Rec[];
  const [done, setDone] = useState<string | null>(null);
  if (!rows.length) return null;
  const log = async (r: Rec) => {
    const fields = Object.fromEntries(block.fields.map((k) => [k, r.properties[k]]).filter(([, v]) => v !== undefined));
    try {
      const res = await request<CommandResult>('POST', '/records', { collection_id: block.log, fields }); // the server stamps the time
      setDone(r.id); setTimeout(() => setDone(null), 1200);
      await afterCommand(res);
      ctx.reload?.();
      toast(`Logged ${String(r.properties.name ?? '')}.`, { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${res.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } }, 4000);
    } catch (x) { toast(errorText(x), undefined, 4000); }
  };
  return (
    <>
      <div className="sec"><span>{block.label}</span><span className="meta">Tap to log</span></div>
      <div className="chips scroll" data-dye={ctx.spec.dye}>
        {rows.map((r) => (
          <button key={r.id} className="chip pickchip" onClick={() => log(r)} aria-label={`Log ${String(r.properties.name)}`}>
            {done === r.id ? <Icon name="check" size={16} sw={2.4} /> : <Icon name="plus" size={16} />}
            {String(r.properties.name)}
            {r.properties.calories !== undefined && <span className="n muted">{Number(r.properties.calories).toLocaleString('en-US')}</span>}
          </button>
        ))}
      </div>
    </>
  );
}

/** Workout's "Next up · today 6 pm · Pull day · Start pull day" (board Workout). Opens the guided log. */
export function Next({ block, ctx }: { block: NextBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  const nav = useNavigate();
  if (!v?.title) return null;
  return (
    <section className="card next-card" data-dye={ctx.spec.dye}>
      <div className="n-head"><span>{v.eyebrow}</span><span>{v.meta}</span></div>
      <span className="n-title" style={fit(v.title)}>{v.title}</span>
      {!ctx.preview && v.steps?.length ? <button className="cta wide" onClick={() => nav(`/a/${ctx.spec.key}/do/${block.id}`)}>{v.action ?? 'Start'}</button> : null}
    </section>
  );
}
