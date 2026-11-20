import { useState } from 'react';
import { errorText, request } from '../api/client';
import type { Collection, CommandResult } from '../api/types';
import { afterCommand, toast } from '../lib/store';
import { Icon } from './Icon';

/** Sensible values a new row starts with: the open list, "to buy", not done. */
export function startValues(c: Collection, defaults: Record<string, string>): Record<string, string> {
  const v: Record<string, string> = { ...defaults };
  const status = c.fields.find((f) => f.key === 'status' && f.type === 'select');
  if (status?.options?.length && !v.status) v.status = status.options[0].id;
  return v;
}

/**
 * Type and press Enter: the row lands at the end of the list you're looking at.
 * One field, because most rows are one thing ("Peanut butter", "Call the dentist").
 * The ⋯ opens the full sheet for everything else.
 */
export function QuickAdd({ collection: c, app, defaults, placeholder, onMore, onAdded }: {
  collection: Collection; app: string; defaults: Record<string, string>; placeholder: string; onMore: () => void; onAdded: () => void;
}) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const titleField = c.fields.find((f) => f.key === c.titleField);
  if (titleField?.type !== 'text') {
    // the title isn't free text (a meditation session is its kind): the sheet asks properly
    return <button className="add-row" onClick={onMore}><Icon name="plus" size={16} /> New {c.label?.toLowerCase() ?? c.name.toLowerCase().replace(/s$/, '')}</button>;
  }
  const add = async () => {
    const t = text.trim();
    if (!t || busy) return;
    setBusy(true);
    try {
      const r = await request<CommandResult>('POST', '/records', { collection_id: `${app}/${c.key}`, fields: { ...startValues(c, defaults), [c.titleField]: t } });
      setText('');
      await afterCommand(r);
      onAdded();
      toast(`Added ${t}.`, { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); onAdded(); } catch (x) { toast(errorText(x)); } } }, 4000);
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };
  return (
    <form className="quick-add" onSubmit={(e) => { e.preventDefault(); void add(); }}>
      <span className="qa-plus" aria-hidden="true"><Icon name="plus" size={16} /></span>
      <input value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} aria-label={placeholder} enterKeyHint="done" autoComplete="off" />
      {text.trim()
        ? <button className="qa-go" disabled={busy}>Add</button>
        : <button type="button" className="qa-more" onClick={onMore} aria-label="Add with more details"><Icon name="more" size={18} /></button>}
    </form>
  );
}
