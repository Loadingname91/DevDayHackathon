import { useEffect, useState } from 'react';
import { errorText, request } from '../api/client';
import type { Collection, CommandResult, Field, Patch, Rec } from '../api/types';
import { addDays, dayKey } from '../lib/format';
import { afterCommand, toast } from '../lib/store';
import { Icon } from './Icon';
import { startValues } from './QuickAdd';
import { Sheet } from './Sheet';

const HIDDEN = new Set(['relation', 'formula', 'repeat', 'bool']);
const SYSTEM = new Set(['source', 'ext_id', 'bought_on', 'trip', 'usual']);
/** A row's name for "Add a note" and "New note": the collection's own `label`, else its name made singular. */
export const singular = (c: Collection) => (c.label ?? c.name.replace(/(ies)$/i, 'y').replace(/(ss|x|ch|sh)es$/i, '$1').replace(/s$/i, '')).toLowerCase();

type Props = {
  app: string; appName: string; collection: Collection; now: string; open: boolean; onClose: () => void; onAdded: () => void;
  defaults?: Record<string, string>;
  /** edit an existing row instead of adding one (board "Edit an item") */
  record?: Rec;
  apps?: Patch[];
};

/** Values as the form holds them: strings, money as "$3.49" so the server (and the mock) read it as money. */
function toForm(c: Collection, r: Rec): Record<string, string> {
  const out: Record<string, string> = {};
  for (const f of c.fields) {
    const v = r.properties[f.key];
    if (v === undefined || v === null || typeof v === 'object') continue;
    out[f.key] = f.type === 'money' ? `$${(Number(v) / 100).toFixed(2)}` : f.type === 'datetime' ? String(v).slice(0, 16) : String(v);
  }
  return out;
}

/**
 * Add one record by hand (US-17 AC-2), or edit one (tap a row). A gesture: it writes at
 * once, with Undo. The title first, choices as chips, numbers as steppers; a required time
 * (an event, a log) starts at now, any other date or time starts empty with Today and
 * Tomorrow chips; optional fields past the first three wait under "More details". Edit adds
 * where the row came from and Delete | Save (board "Edit an item").
 */
export function AddSheet({ app, appName, collection: c, defaults = {}, now, open, onClose, onAdded, record, apps = [] }: Props) {
  const fields = c.fields.filter((f) => !HIDDEN.has(f.type) && !SYSTEM.has(f.key));
  const ordered = [...fields.filter((f) => f.key === c.titleField), ...fields.filter((f) => f.key !== c.titleField)];
  const main = record ? ordered : ordered.filter((f, i) => f.required || i < 3 || f.key === c.dateField);
  const extra = ordered.filter((f) => !main.includes(f));
  const fresh = () => {
    if (record) return toForm(c, record);
    const v = startValues(c, defaults);
    // an event or a log needs a time, so its required dateField starts at now; any other date (a to-do's due) starts empty
    for (const f of fields) if (f.key === c.dateField && f.required && !v[f.key] && now) v[f.key] = f.type === 'date' ? dayKey(now) : now.slice(0, 16);
    return v;
  };
  const [vals, setVals] = useState<Record<string, string>>(fresh);
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (open) { setVals(fresh()); setMore(false); setErr(null); } }, [open, record?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { // a new row asks for its title straight away (a fine pointer only: on a phone the keyboard would cover the form)
    if (!open || record || !matchMedia('(pointer: fine)').matches) return;
    const t = setTimeout(() => document.getElementById(`f_${c.titleField}`)?.focus({ preventScroll: true }), 60);
    return () => clearTimeout(t);
  }, [open, record, c.titleField]);
  const set = (k: string, v: string) => setVals((x) => ({ ...x, [k]: v }));
  const undoOf = (id: string) => async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${id}/undo`)); onAdded(); } catch (x) { toast(errorText(x)); } };

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    const out = Object.fromEntries(Object.entries(vals).filter(([, v]) => v !== '')); // as typed; the server parses (backend.md §3)
    try {
      const r = record
        ? await request<CommandResult>('PATCH', `/records/${record.id}`, { fields: out, base_version: record.version })
        : await request<CommandResult>('POST', '/records', { collection_id: `${app}/${c.key}`, fields: out });
      await afterCommand(r);
      toast(record ? 'Saved.' : `Added to ${appName}.`, { label: 'Undo', run: undoOf(r.change_set_id) });
      onAdded(); onClose();
    } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };
  const remove = async () => {
    if (!record) return;
    setBusy(true);
    try {
      const r = await request<CommandResult>('DELETE', `/records/${record.id}`);
      await afterCommand(r);
      toast('Deleted.', { label: 'Undo', run: undoOf(r.change_set_id) });
      onAdded(); onClose();
    } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };

  const input = (f: Field) => {
    const v = vals[f.key] ?? '';
    const id = `f_${f.key}`;
    if (f.type === 'select') {
      return (
        <span className="chips" role="radiogroup" aria-labelledby={`${id}_l`}>
          {f.options?.map((o) => <button type="button" key={o.id} role="radio" aria-checked={v === o.id} className="chip pick" onClick={() => set(f.key, v === o.id ? '' : o.id)}>{o.label}</button>)}
        </span>
      );
    }
    if (f.type === 'number') {
      const n = parseFloat(v) || 0, step = f.unit === 'cal' ? 50 : f.unit === 'mi' ? 0.5 : f.unit === 'min' ? 5 : 1;
      return (
        <span className="stepper">
          <button type="button" className="sb" aria-label={`Less ${f.label}`} onClick={() => set(f.key, String(Math.max(0, +(n - step).toFixed(2))))}>−</button>
          <input id={id} className="sv" type="number" inputMode="decimal" step="any" value={v} placeholder="0" onChange={(e) => set(f.key, e.target.value)} />
          {f.unit && <span className="unit">{f.unit}</span>}
          <button type="button" className="sb" aria-label={`More ${f.label}`} onClick={() => set(f.key, String(+(n + step).toFixed(2)))}>+</button>
        </span>
      );
    }
    if (f.type === 'date' || f.type === 'datetime') {
      const today = now ? dayKey(now) : '';
      const quick: [string, string][] = [['Today', today], ['Tomorrow', today && addDays(today, 1)]];
      if (f.type === 'datetime') {
        // a time of day for the chips: today at the next whole hour (never already due), tomorrow at 9
        const next = Math.min(23, (parseInt(now.slice(11, 13), 10) || 0) + 1);
        quick[0][1] = today && `${today}T${String(next).padStart(2, '0')}:00`;
        quick[1][1] = today && `${addDays(today, 1)}T09:00`;
        if (!record) quick.unshift(['Now', now.slice(0, 16)]); // an existing time is never overwritten with "now" by a chip
      }
      return (
        <span className="date-pick">
          <span className="chips">{quick.map(([t, q]) => <button type="button" key={t} className="chip pick" aria-pressed={v === q} onClick={() => set(f.key, q)}>{t}</button>)}</span>
          <input id={id} className="fld" type={f.type === 'date' ? 'date' : 'datetime-local'} value={v} onChange={(e) => set(f.key, e.target.value)} />
        </span>
      );
    }
    if (f.type === 'money') return <input id={id} className="fld" type="text" inputMode="decimal" placeholder={`${f.label}, $0.00`} value={v} onChange={(e) => set(f.key, e.target.value)} />;
    return <input id={id} className={`fld ${f.key === c.titleField ? 'title-in' : ''}`} type="text" value={v} required={f.required} placeholder={f.label}
      autoFocus={!record && f.key === c.titleField && matchMedia('(pointer: fine)').matches} onChange={(e) => set(f.key, e.target.value)} />;
  };
  const row = (f: Field) => (
    <div key={f.key} className="add-field">
      <label id={`f_${f.key}_l`} htmlFor={`f_${f.key}`}>{f.label}</label>
      {input(f)}
    </div>
  );
  const via = record?.properties._via as { app?: string; workflow?: string } | undefined;
  const from = via?.app ? apps.find((a) => a.key === via.app) : undefined;

  return (
    <Sheet open={open} onClose={onClose} label={record ? `Edit ${singular(c)}` : `New ${singular(c)}`}>
      <form className="add-form" onSubmit={save}>
        <div className="sheet-head"><span className="txt"><h2>{record ? `Edit ${singular(c)}` : `New ${singular(c)}`}</h2><span className="sub">{appName}</span></span></div>
        {main.map(row)}
        {extra.length > 0 && (more ? extra.map(row) : <button type="button" className="link" onClick={() => setMore(true)}>More details ›</button>)}
        {from && <span className="provenance" data-dye={from.dye}><i className="dyedot" />From {from.name}</span>}
        {via?.workflow && <span className="provenance">Added by a rule</span>}
        {err && <p className="err" role="alert">{err}</p>}
        {record
          ? <span className="sheet-actions"><button type="button" className="ghost" onClick={remove} disabled={busy}><Icon name="trash" size={16} />Delete</button><button className="cta" disabled={busy}>Save</button></span>
          : <button className="cta" disabled={busy}>Add {singular(c)}</button>}
      </form>
    </Sheet>
  );
}
