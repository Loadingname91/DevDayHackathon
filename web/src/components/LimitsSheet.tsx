import { useEffect, useState } from 'react';
import { errorText, request } from '../api/client';
import type { BlockValue, CommandResult, EditLimits, EditSetting } from '../api/types';
import { afterCommand, loadApp, toast, useStore } from '../lib/store';
import { Icon } from './Icon';
import { Sheet } from './Sheet';
import '../styles/limits.css';

/**
 * Change a limit or a goal (board "Limits"). One sheet for two things a block can declare with `edit`:
 *  - a setting (Budget's monthly amount, Calories' daily target): one field;
 *  - the limits on the options of a select field (Budget's categories): a field per option and "Add a category".
 * A gesture: it writes at once with Undo (`PATCH /apps/{id}/settings`, spec/backend.md §10). Money is typed as "$250" or "250"
 * and sent as cents; an empty limit means no limit. Nothing here works out what is left: the server sends the new words.
 */
export type LimitsMode =
  | { kind: 'setting'; edit: EditSetting; current?: number }
  | { kind: 'options'; edit: EditLimits; rows: NonNullable<BlockValue['rows']> };

const whole = (cents: number) => `$${Math.round(cents / 100).toLocaleString('en-US')}`;
/** "$1,250", "1250" or "12.50" to cents; '' to null; anything else to undefined (not a number). */
export function toCents(t: string): number | null | undefined {
  const s = t.replace(/[$,\s]/g, '');
  if (s === '') return null;
  return /^\d+(\.\d{1,2})?$/.test(s) ? Math.round(parseFloat(s) * 100) : undefined;
}
const toCount = (t: string): number | null | undefined => {
  const s = t.replace(/[,\s]/g, '');
  return s === '' ? null : /^\d+$/.test(s) ? parseInt(s, 10) : undefined;
};
const show = (n: number | undefined, money: boolean) => (n === undefined ? '' : money ? String(n / 100) : String(n));

type Props = { app: string; appName: string; mode: LimitsMode; open: boolean; onClose: () => void };

export function LimitsSheet({ app, appName, mode, open, onClose }: Props) {
  const seq = useStore((s) => s.apps[app]?.seq);
  const money = mode.kind === 'options' || mode.edit.format === 'money';
  const initial = (): Record<string, string> => mode.kind === 'setting' ? { value: show(mode.current, money) } : Object.fromEntries(mode.rows.map((r) => [r.id ?? r.label, show(r.limit, true)]));
  const [vals, setVals] = useState(initial);
  const [add, setAdd] = useState({ label: '', limit: '' });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (open) { setVals(initial()); setAdd({ label: '', limit: '' }); setErr(null); } }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  const parse = money ? toCents : toCount;

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    let body: Record<string, unknown>;
    if (mode.kind === 'setting') {
      const v = parse(vals.value ?? '');
      if (v === undefined || v === null || v <= 0) { setErr(money ? 'Type an amount, like $1,200.' : 'Type a number, like 2200.'); return; }
      body = { settings: { [mode.edit.setting]: v } };
    } else {
      const options: Record<string, unknown>[] = [];
      for (const r of mode.rows) {
        const key = r.id ?? r.label, v = toCents(vals[key] ?? '');
        if (v === undefined) { setErr(`Type an amount for ${r.label}, like $200, or leave it empty for no limit.`); return; }
        if ((v ?? undefined) !== r.limit) options.push({ field: mode.edit.field, id: r.id, limit: v });
      }
      if (add.label.trim()) {
        const v = toCents(add.limit);
        if (v === undefined) { setErr(`Type an amount for ${add.label.trim()}, like $50, or leave it empty for no limit.`); return; }
        options.push({ field: mode.edit.field, label: add.label.trim(), limit: v });
      }
      if (!options.length) { onClose(); return; }
      body = { options };
    }
    setBusy(true); setErr(null);
    try {
      const r = await request<CommandResult>('PATCH', `/apps/${app}/settings`, { ...body, base_version: seq });
      await afterCommand(r);
      toast('Saved.', { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); void loadApp(app); } catch (x) { toast(errorText(x)); } } });
      void loadApp(app); onClose();
    } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };

  const title = mode.edit.label;
  return (
    <Sheet open={open} onClose={onClose} label={title}>
      <form className="add-form limits" onSubmit={save}>
        <div className="sheet-head"><span className="txt"><h2>{title}</h2><span className="sub">{appName}</span></span></div>
        {mode.kind === 'setting' ? (
          <div className="add-field">
            <label htmlFor="lim_value">{mode.edit.label}</label>
            <input id="lim_value" className="fld" inputMode={money ? 'decimal' : 'numeric'} autoComplete="off" placeholder={money ? '$0' : '0'} value={vals.value ?? ''} onChange={(e) => setVals({ value: e.target.value })} />
            {mode.current !== undefined && <span className="lim-now">Right now {money ? whole(mode.current) : mode.current.toLocaleString('en-US')}</span>}
          </div>
        ) : (
          <>
            <ul className="card list lim-list">
              {mode.rows.map((r, i) => {
                const key = r.id ?? r.label;
                return (
                  <li key={key} className={`lim-row ${i ? 'sep' : ''}`}>
                    <label htmlFor={`lim_${key}`} className="lim-name"><span className="t">{r.label}</span>{r.spent !== undefined && <span className="s">{whole(r.spent)} so far</span>}</label>
                    <input id={`lim_${key}`} className="fld lim-in" inputMode="decimal" autoComplete="off" placeholder="No limit" aria-label={`${r.label} limit`} value={vals[key] ?? ''}
                      onChange={(e) => setVals((v) => ({ ...v, [key]: e.target.value }))} />
                  </li>
                );
              })}
            </ul>
            <div className="add-field">
              <span className="lbl" id="lim_add_l">Add a category</span>
              <span className="lim-add" role="group" aria-labelledby="lim_add_l">
                <input className="fld" placeholder="Name, like Fun" aria-label="New category name" value={add.label} onChange={(e) => setAdd((a) => ({ ...a, label: e.target.value }))} />
                <input className="fld lim-in" inputMode="decimal" placeholder="No limit" aria-label="New category limit" value={add.limit} onChange={(e) => setAdd((a) => ({ ...a, limit: e.target.value }))} />
              </span>
            </div>
          </>
        )}
        {err && <p className="err" role="alert">{err}</p>}
        <button className="cta" disabled={busy}>Save</button>
      </form>
    </Sheet>
  );
}

/** The pencil on a block that declares `edit`: 44 square, quiet, in the block's corner. */
export function EditPencil({ label, onClick, className = '' }: { label: string; onClick: () => void; className?: string }) {
  return <button type="button" className={`edit-pencil ${className}`} aria-label={label} onClick={onClick}><Icon name="pencil" size={18} sw={1.8} /></button>;
}
