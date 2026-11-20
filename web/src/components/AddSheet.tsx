import { lazy, Suspense, useEffect, useState } from 'react';
import { errorText, request } from '../api/client';
import type { Collection, CommandResult, Field, Patch, Rec } from '../api/types';
import { dayKey, relIds, singular } from '../lib/format';
import { afterCommand, toast } from '../lib/store';
import { Disclosure } from './Disclosure';
import { Icon } from './Icon';
import { BodyField, LinkedSection, RelationPicker, SYSTEM_KEYS, useLive } from './Links';
import { startValues } from './QuickAdd';
import { RepeatField, ruleOf } from './RepeatField';
import { Sheet } from './Sheet';

// the date picker (react-aria) is its own chunk: it loads when the first sheet with a date opens, so Home does not carry it
const DateTimeField = lazy(() => import('./DateTimeField').then((m) => ({ default: m.DateTimeField })));
const HIDDEN = new Set(['formula', 'bool']); // a tick is the row's checkbox, a formula is the server's
const SYSTEM = SYSTEM_KEYS;
export { singular };
const NONE: Rec = { id: '', position: '', version: 0, properties: {} };

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
export function AddSheet({ app, appName, collection: c, defaults = {}, now, open, onClose, onAdded, record: opened, apps = [] }: Props) {
  // the row as the store has it now: a link made from this sheet changes the record under it (its version too)
  const live = useLive(app, c, opened ?? NONE);
  const record = opened ? live : undefined;
  const fields = c.fields.filter((f) => !HIDDEN.has(f.type) && !SYSTEM.has(f.key) && (f.type !== 'relation' || !!f.target));
  const ordered = [...fields.filter((f) => f.key === c.titleField), ...fields.filter((f) => f.key !== c.titleField)];
  const main = record ? ordered : ordered.filter((f, i) => f.required || i < 3 || f.key === c.dateField || f.type === 'repeat');
  const extra = ordered.filter((f) => !main.includes(f));
  const fresh = () => {
    if (record) return toForm(c, record);
    const v = startValues(c, defaults);
    // an event or a log needs a time, so its required dateField starts at now; any other date (a to-do's due) starts empty
    for (const f of fields) if (f.key === c.dateField && f.required && !v[f.key] && now) v[f.key] = f.type === 'date' ? dayKey(now) : now.slice(0, 16);
    return v;
  };
  const relKeys = new Set(fields.filter((f) => f.type === 'relation').map((f) => f.key));
  // relation values are arrays of record ids, held apart from the typed strings
  const freshRels = (): Record<string, string[]> => Object.fromEntries([...relKeys].map((k) => [k, record ? relIds(record.properties[k]) : defaults[k] ? [defaults[k]] : []]));
  const [vals, setVals] = useState<Record<string, string>>(fresh);
  const [rels, setRels] = useState<Record<string, string[]>>(freshRels);
  // a repeat is sent only when it was touched (an edit that leaves it alone keeps the series' log and skips)
  const repeatKeys = fields.filter((f) => f.type === 'repeat').map((f) => f.key);
  const freshRepeat = (): Record<string, string> => Object.fromEntries(repeatKeys.map((k) => [k, record ? ruleOf(record.properties[k]) : '']));
  const [rules, setRules] = useState<Record<string, string>>(freshRepeat);
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (open) { setVals(fresh()); setRels(freshRels()); setRules(freshRepeat()); setTouched(new Set()); setMore(false); setErr(null); } }, [open, record?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { // a new row asks for its title straight away (a fine pointer only: on a phone the keyboard would cover the form)
    if (!open || record || !matchMedia('(pointer: fine)').matches) return;
    const t = setTimeout(() => document.getElementById(`f_${c.titleField}`)?.focus({ preventScroll: true }), 60);
    return () => clearTimeout(t);
  }, [open, record, c.titleField]);
  const set = (k: string, v: string) => setVals((x) => ({ ...x, [k]: v }));
  const undoOf = (id: string) => async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${id}/undo`)); onAdded(); } catch (x) { toast(errorText(x)); } };

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    const out: Record<string, unknown> = Object.fromEntries(Object.entries(vals).filter(([k, v]) => v !== '' && !relKeys.has(k))); // as typed; the server parses (backend.md §3)
    for (const k of relKeys) { const ids = rels[k] ?? []; if (record || ids.length) out[k] = ids; } // an edit always says what it holds, so clearing the last one clears it
    for (const k of repeatKeys) { // a new row with a rule sends it; an edit sends it only if changed ("Never" clears it)
      if (!touched.has(k)) continue;
      if (rules[k]) out[k] = rules[k]; else if (record && ruleOf(record.properties[k])) out[k] = null;
    }
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
    if (f.type === 'relation') return <RelationPicker field={f} app={app} value={rels[f.key] ?? []} onChange={(ids) => setRels((x) => ({ ...x, [f.key]: ids }))} labelId={`${id}_l`} />;
    if (f.type === 'text' && f.multiline) return <BodyField id={id} value={v} onChange={(x) => set(f.key, x)} placeholder={f.label} app={app} recId={record?.id} />;
    if (f.type === 'repeat') {
      return <RepeatField id={id} labelId={`${id}_l`} rule={rules[f.key] ?? ''} onChange={(x) => { setRules((r) => ({ ...r, [f.key]: x })); setTouched((t) => new Set(t).add(f.key)); }} />;
    }
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
      // a day and, when the field asks, a time; "now" is the server's, and the line under it says what was chosen (DateTimeField)
      return <Suspense fallback={<span className="dt-wait" aria-hidden="true" />}><DateTimeField id={id} labelId={`${id}_l`} value={v} onChange={(x) => set(f.key, x)} now={now} kind={f.type}
        timeOptional={f.timeOptional} allDay={f.allDay} showNow={!record && f.type === 'datetime' && !f.timeOptional && !f.allDay && f.key === c.dateField} /></Suspense>;
    }
    if (f.type === 'money') return <input id={id} className="fld" type="text" inputMode="decimal" placeholder={`${f.label}, $0.00`} value={v} onChange={(e) => set(f.key, e.target.value)} />;
    return <input id={id} className={`fld ${f.key === c.titleField ? 'title-in' : ''}`} type="text" value={v} required={f.required} placeholder={f.label}
      autoFocus={!record && f.key === c.titleField && matchMedia('(pointer: fine)').matches} onChange={(e) => set(f.key, e.target.value)} />;
  };
  const row = (f: Field) => (
    <div key={f.key} className="add-field">
      {f.type === 'relation' || f.type === 'repeat' || f.type === 'date' || f.type === 'datetime' ? <span id={`f_${f.key}_l`} className="lbl">{f.label}</span> : <label id={`f_${f.key}_l`} htmlFor={`f_${f.key}`}>{f.label}</label>}
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
        {extra.length > 0 && (
          <>
            <Disclosure open={!more}><button type="button" className="link" onClick={() => setMore(true)}>More details ›</button></Disclosure>
            <Disclosure open={more}>{extra.map(row)}</Disclosure>
          </>
        )}
        {record && <LinkedSection app={app} collection={c} record={record} onNavigate={onClose} />}
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
