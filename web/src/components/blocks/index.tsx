// The blocks. Each gets { block, ctx } and is a pure view over ctx: blocks never fetch and
// never calculate (ADR-001). Computed figures arrive in ctx.values, keyed by block id.
// Styles: design/screens-css.md.
import { useState } from 'react';
import type { AppSpec, BlockValue, Collection, DatedRow, Field, LeafBlock, ListBlock, MetricBlock, Patch, ProgressBlock, Rec } from '../../api/types';
import { aNoun, day, dayKey, fieldText, relDue, time, title, type Lookup } from '../../lib/format';
import { setDetail, useStore } from '../../lib/store';
import { useWide } from '../../lib/useWide';
import { AddSheet, singular } from '../AddSheet';
import { EmptyState, NoData } from '../EmptyState';
import { Icon } from '../Icon';
import { backlinksOf, hasRel, linksOf, relFields, RowRel } from '../Links';
import { Checklist } from './Checklist';
import { Days } from './Days';
import { useRowEnter } from '../../lib/enter';
import { passesAll } from './filter';
import { Bars, Countdown, fill, fit, Gauge, Next, Picks, Ring, Strip } from './instruments';
import { MonthLog } from './MonthLog';
import { Timer } from './Timer';
import { Workflows } from './Workflows';

export type Ctx = {
  spec: AppSpec;
  data: Record<string, (Rec | DatedRow)[]>;
  values: Record<string, BlockValue>;
  now: string; // server_now
  apps: Patch[];
  /** a build preview: example rows, no writes */
  preview?: boolean;
  /** the tab shows more than one list or checklist: only the first empty one draws the spool */
  many?: boolean;
  /** `?filter=<relationField>:<id>`: lists of a collection with that relation field show only the rows that hold that id */
  filter?: { field: string; id: string };
  reload?: () => void;
};


const collectionOf = (ctx: Ctx, ref: string): Collection | undefined => {
  const [app, key] = ref.split('/');
  return app === ctx.spec.key ? ctx.spec.collections.find((c) => c.key === key) : undefined;
};
const lookupIn = (ctx: Ctx): Lookup => (ref, id) => {
  const c = collectionOf(ctx, ref);
  const r = (ctx.data[ref] as Rec[] | undefined)?.find((x) => x.id === id);
  return r && c ? title(c, r) : undefined; // a relation into another app: its name isn't in this response
};

// ---------------------------------------------------------------- text, figure tile, progress
function Text({ block }: { block: Extract<LeafBlock, { kind: 'text' }> }) {
  return <div className="sec"><span>{block.text}</span></div>;
}
/** A figure tile (board Workout: "Lifted this week · 12,450 lb"). */
function Metric({ block, ctx }: { block: MetricBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  if (!v || v.text === undefined) return <NoData label={block.label} failed={!!v} className="metric" />;
  return (
    <div className="card metric">
      <span className="lbl">{block.label}</span>
      <span className="big" style={fit(v.text)}>{v.text}</span>
      {v?.sub && <span className="sub">{v.sub}</span>}
    </div>
  );
}
/** "Sessions this week · 3 of 4" and its bar; an excess over the target is a cross-hatch, never red. */
function Progress({ block, ctx }: { block: ProgressBlock; ctx: Ctx }) {
  const v = ctx.values[block.id];
  if (!v || (v.text === undefined && v.pct === undefined)) return <NoData label={block.label} failed={!!v} />;
  return (
    <div className="card progress" data-dye={ctx.spec.dye}>
      <span className="prow"><span className="lbl">{block.label}</span><span className="v">{v.text ?? '–'}{v.target ? ` of ${v.target}` : ''}</span></span>
      <span className="track" role="progressbar" aria-valuenow={v.pct ?? 0} aria-valuemin={0} aria-valuemax={100} aria-label={block.label}>
        <span className="fill" style={fill(v.pct ?? 0, v.over_pct)} />
        {v.over_pct ? <span className="hatch" style={fill(v.pct ?? 0, v.over_pct)} /> : null}
      </span>
      {v.over && <span className="over-t">{v.over}</span>}
    </div>
  );
}

// ---------------------------------------------------------------- list
function List({ block, ctx }: { block: ListBlock; ctx: Ctx }) {
  const c = collectionOf(ctx, block.source);
  const lookup = lookupIn(ctx);
  const [all, setAll] = useState(false);
  const [editing, setEditing] = useState<Rec | null>(null);
  const [adding, setAdding] = useState(false);
  const wide = useWide();
  const picked = useStore((s) => s.detail?.id);
  // a row that arrives in a list already on screen grows in (every row the list holds counts, drawn or not; lib/enter.ts)
  const rel = c && ctx.filter && relFields(c).some((f) => f.key === ctx.filter!.field) ? ctx.filter : undefined;
  const held = ((ctx.data[block.source] ?? []) as Rec[]).filter((r) => passesAll(r, block.where, ctx.now) && (!rel || hasRel(r, rel.field, rel.id)));
  useRowEnter(ctx.preview ? null : held.map((r) => r.id), { scope: rel ? `${block.id}|${rel.field}:${rel.id}` : block.id }); // a filter is a new list, not rows arriving
  if (!c) return null;
  const chipKeys = relFields(c).map((f) => f.key); // drawn as chips under the row, so not again in its meta line
  const only = block.fields?.length ? block.fields : undefined; // a block that lists fields shows those relations; one that lists none, all
  let rows = held;
  if (block.sort) {
    const { field, dir } = block.sort, s = dir === 'asc' ? 1 : -1;
    rows = [...rows].sort((a, b) => {
      const x = a.properties[field], y = b.properties[field];
      if (x === undefined || x === null) return 1;
      if (y === undefined || y === null) return -1;
      return (x < y ? -1 : x > y ? 1 : 0) * s;
    });
  }
  const total = rows.length;
  const limit = block.limit ?? 30; // a long list shows its first rows and a "Show all N"; a block's own limit wins
  const full = all || (!!picked && rows.findIndex((r) => r.id === picked) >= limit); // a row opened from a link (`?row=`) is drawn even past "Show all N"
  if (total > limit && !full) rows = rows.slice(0, limit);
  const shown = (block.fields ?? []).map((k) => c.fields.find((f) => f.key === k)).filter((f): f is Field => !!f && !(f.type === 'relation' && chipKeys.includes(f.key)));
  const amount = c.amountField ? c.fields.find((f) => f.key === c.amountField) : undefined;
  const groupField = block.group ? c.fields.find((f) => f.key === block.group) : undefined;
  const groupOf = (r: Rec) => {
    if (!groupField) return '';
    const v = r.properties[groupField.key];
    if ((groupField.type === 'date' || groupField.type === 'datetime') && typeof v === 'string') return dayKey(v) === dayKey(ctx.now) ? 'Today' : day(v);
    return fieldText(groupField, v, ctx.now, lookup);
  };
  const groups: [string, Rec[]][] = [];
  for (const r of rows) {
    const g = groupOf(r), last = groups[groups.length - 1];
    if (last && last[0] === g) last[1].push(r); else groups.push([g, [r]]);
  }
  const canEdit = !ctx.preview && block.source.startsWith(ctx.spec.key + '/');
  const canAdd = canEdit && block.add !== false; // a list of this app's own rows can add one, unless the block says add: false

  const row = (r: Rec) => {
    const via = r.properties._via as { app?: string; workflow?: string } | undefined;
    const from = via?.app ? ctx.apps.find((a) => a.key === via.app) : undefined;
    const google = r.properties.source === 'google';
    const due = block.due ? r.properties[block.due] : undefined;
    const rel = typeof due === 'string' && ctx.now ? relDue(due, ctx.now) : null;
    const sub = shown.map((f) => {
      const v = r.properties[f.key];
      if (groupField && f.key === groupField.key && typeof v === 'string') return time(v);
      return fieldText(f, v, ctx.now, lookup);
    }).filter(Boolean).join(' · ');
    const inner = (
      <>
        <span className="main">
          <span className="t">{title(c, r, ctx.now, lookup)}{r.example && <span className="pill soft">example</span>}</span>
          {(sub || rel) && <span className="s">{[rel && !rel.overdue ? rel.text : '', sub].filter(Boolean).join(' · ')}</span>}
          {from && <span className="from" data-dye={from.dye}><i />from {from.name}</span>}
          {via?.workflow && <span className="from">by rule ›</span>}
          {google && <span className="from">from Google</span>}
        </span>
        {rel?.overdue && <span className="pill status">{rel.text}</span>}
        {amount && r.properties[amount.key] !== undefined && <span className="amt">{fieldText(amount, r.properties[amount.key])}</span>}
      </>
    );
    return (
      <li className="row" key={r.id} data-dye={ctx.spec.dye} data-row={r.id}>
        {canEdit && !google ? <button className="row-btn" aria-pressed={wide ? picked === r.id : undefined}
          onClick={() => (wide ? setDetail({ app: ctx.spec.key, ref: block.source, id: r.id }) : setEditing(r))}>{inner}</button> : <span className="row-btn">{inner}</span>}
        {!ctx.preview && !r.example && (chipKeys.length > 0 || linksOf(r).length > 0 || backlinksOf(r).length > 0) && <RowRel rec={r} c={c} app={ctx.spec.key} only={only} />}
      </li>
    );
  };

  return (
    <>
      {block.label && <div className="sec"><span>{block.label}</span>{total > limit ? <span className="meta">{total}</span> : null}</div>}
      <ul className="card list">
        {rows.length === 0 && <li className="empty-li"><EmptyState onAdd={canAdd ? () => setAdding(true) : undefined} actions={!ctx.preview} compact={ctx.many} /></li>}
        {groups.map(([g, rs]) => [g ? <li key={`g-${g}`} className="grp">{g}</li> : null, ...rs.map(row)])}
        {total > limit && <li><button className="more-rows" onClick={() => setAll(!full)}>{full ? 'Show fewer' : `Show all ${total}`}</button></li>}
        {canAdd && rows.length > 0 && <li className="add-row-li quick-wrap"><button className="add-row" onClick={() => setAdding(true)}><Icon name="plus" size={16} />Add {aNoun(singular(c))}</button></li>}
      </ul>
      {canAdd && <AddSheet app={ctx.spec.key} appName={ctx.spec.name} collection={c} now={ctx.now} apps={ctx.apps} defaults={rel ? { [rel.field]: rel.id } : undefined}
        open={adding} onClose={() => setAdding(false)} onAdded={() => ctx.reload?.()} />}
      {canEdit && <AddSheet app={ctx.spec.key} appName={ctx.spec.name} collection={c} now={ctx.now} apps={ctx.apps} record={editing ?? undefined}
        open={!!editing} onClose={() => setEditing(null)} onAdded={() => ctx.reload?.()} />}
    </>
  );
}

// ---------------------------------------------------------------- dispatch
export function Block({ block, ctx }: { block: LeafBlock; ctx: Ctx }) {
  switch (block.kind) {
    case 'text': return <Text block={block} />;
    case 'metric': return <Metric block={block} ctx={ctx} />;
    case 'progress': return <Progress block={block} ctx={ctx} />;
    case 'list': return <List block={block} ctx={ctx} />;
    case 'calendar': return <Days block={{ kind: 'days', id: block.id, source: block.source, views: ['day', 'week', 'month'], view: block.window === 'today' ? 'day' : 'week' }} ctx={ctx} />;
    case 'days': return <Days block={block} ctx={ctx} />;
    case 'checklist': return <Checklist block={block} ctx={ctx} />;
    case 'gauge': return <Gauge block={block} ctx={ctx} />;
    case 'bars': return <Bars block={block} ctx={ctx} />;
    case 'ring': return <Ring block={block} ctx={ctx} />;
    case 'countdown': return <Countdown block={block} ctx={ctx} />;
    case 'strip': return <Strip block={block} ctx={ctx} />;
    case 'picks': return <Picks block={block} ctx={ctx} />;
    case 'next': return <Next block={block} ctx={ctx} />;
    case 'timer': return <Timer block={block} ctx={ctx} />;
    case 'month': return <MonthLog block={block} ctx={ctx} />;
    case 'workflows': return <Workflows spec={ctx.spec} />;
    default: return null; // table, form, chart: after the base cut line
  }
}
