// Mock for `PATCH /apps/{id}/settings` (spec/backend.md §10): a limit or a goal changed by hand.
// The mock is a tape player and never evaluates a formula (spec/split.md §3). This is the one place it re-words: the fixture's
// instrument values carry what the server would send with the words (`spent`, `limit`, a row's `id`, in cents), so a new limit
// only restates "$142.00 of $200" and the bar's percentage. The server computes all of it for real; faces on Home stay as recorded.
import type { AppResponse, BlockValue, Option } from '../api/types';

type Added = Option & { field: string };
type St = { settings: Record<string, number>; limits: Record<string, number | null>; added: Added[] };
type Row = NonNullable<BlockValue['rows']>[number];
export type LimitsBody = { settings?: Record<string, number>; options?: { field: string; id?: string; label?: string; limit: number | null }[]; base_version?: number };

const S: Record<string, St> = {};
const prev = new Map<string, { app: string; snap: St | undefined }>();
let n = 0;

export function patchLimits(app: string, body: LimitsBody): string {
  const id = `cs_lim_${++n}`;
  const cur = S[app];
  prev.set(id, { app, snap: cur && structuredClone(cur) });
  const next: St = cur ? structuredClone(cur) : { settings: {}, limits: {}, added: [] };
  Object.assign(next.settings, body.settings ?? {});
  for (const o of body.options ?? []) {
    if (o.id) next.limits[o.id] = o.limit;
    else if (o.label) next.added.push({ field: o.field, id: 'c_' + o.label.toLowerCase().replace(/[^a-z0-9]+/g, '_'), label: o.label, ...(o.limit != null ? { limit: o.limit } : {}) });
  }
  S[app] = next;
  return id;
}
export const undoLimits = (id: string) => { const p = prev.get(id); if (!p) return; if (p.snap) S[p.app] = p.snap; else delete S[p.app]; prev.delete(id); };
export const resetLimits = () => { for (const k of Object.keys(S)) delete S[k]; prev.clear(); };

const usd = (c: number) => '$' + (c / 100).toFixed(2);
const whole = (c: number) => '$' + Math.round(c / 100).toLocaleString('en-US');
const pct = (a: number, b: number) => Math.round((100 * a) / b);

function row(label: string, id: string | undefined, spent: number, limit: number | null | undefined): Row {
  if (limit == null) return { label, text: usd(spent), note: 'No limit', id, spent };
  return spent > limit
    ? { label, text: `${usd(spent)} of ${whole(limit)}`, pct: pct(limit, spent), over_pct: 100 - pct(limit, spent), note: `${whole(spent - limit)} over.`, id, spent, limit }
    : { label, text: `${usd(spent)} of ${whole(limit)}`, pct: pct(spent, limit), id, spent, limit };
}

/** Lays this session's limit changes over an app's response: its settings, its options' limits and the words that read them. */
export function applyLimits(key: string, app: AppResponse) {
  const st = S[key];
  if (!st || !app.values) return;
  const values = app.values;
  app.spec.settings = { ...app.spec.settings, ...st.settings };
  app.spec.collections = app.spec.collections.map((c) => ({
    ...c,
    fields: c.fields.map((f) => {
      if (f.type !== 'select' || !f.options) return f;
      const options = [...f.options, ...st.added.filter((a) => a.field === f.key).map(({ field: _f, ...o }) => o)].map((o) => {
        if (!(o.id in st.limits)) return o;
        const { limit: _l, ...rest } = o, l = st.limits[o.id];
        return l == null ? rest : { ...rest, limit: l };
      });
      return { ...f, options };
    }),
  }));
  for (const tab of app.spec.tabs) for (const b of tab.children) {
    if ((b.kind === 'gauge' || b.kind === 'ring') && b.edit) {
      const lim = st.settings[b.edit.setting], v = values[b.id];
      if (lim === undefined || v?.spent === undefined) continue;
      if (b.edit.format === 'money') {
        const left = lim - v.spent;
        values[b.id] = { ...v, limit: lim, text: whole(Math.abs(left)), target: left >= 0 ? `left of ${whole(lim)}` : `over ${whole(lim)}`, pct: left >= 0 ? pct(v.spent, lim) : 100 };
      } else {
        values[b.id] = { ...v, limit: lim, target: `of ${lim.toLocaleString('en-US')}`, pct: pct(v.spent, lim) };
      }
    }
    if (b.kind === 'bars' && b.edit) {
      const v = values[b.id];
      if (!v?.rows) continue;
      const rows = v.rows.map((r) => (r.id && r.spent !== undefined ? row(r.label, r.id, r.spent, r.id in st.limits ? st.limits[r.id] : r.limit) : r));
      for (const a of st.added) if (a.field === b.edit.field && !rows.some((r) => r.id === a.id)) rows.push(row(a.label, a.id, 0, st.limits[a.id] ?? a.limit));
      values[b.id] = { ...v, rows };
    }
  }
}
