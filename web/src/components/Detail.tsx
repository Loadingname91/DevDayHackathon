import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { errorText, request } from '../api/client';
import type { CommandResult, Rec } from '../api/types';
import { fieldText, listNames, title } from '../lib/format';
import { afterCommand, loadApp, setDetail, toast, useStore } from '../lib/store';
import { AddSheet } from './AddSheet';
import { Bold } from './Bold';
import { Icon } from './Icon';
import { NextUp } from './NextUp';

const SKIP = new Set(['relation', 'formula', 'repeat', 'bool']);
const SYSTEM = new Set(['source', 'ext_id', 'bought_on', 'trip', 'usual']);

/**
 * What the pane shows while no row is picked: the app itself, in plain words (what the `···` menu holds on a phone).
 * The pane is always there on an app screen, so nothing shifts when the rows arrive, and it is never empty.
 */
function AppInfo() {
  const { pathname } = useLocation();
  const key = /^\/(?:a|app)\/([^/]+)/.exec(pathname)?.[1] ?? '';
  const app = useStore((s) => s.apps[key]);
  const home = useStore((s) => s.home);
  const pickable = useStore((s) => s.pickable);
  if (!app) return <aside className="detail" aria-label="About this app"><span className="sec"><span>About</span></span></aside>;
  const { spec } = app;
  const from = [...new Set((spec.stitches ?? []).map((st) => st.from.split('/')[0]).filter((k) => k !== key))]
    .map((k) => home?.apps.find((a) => a.key === k)?.name).filter((n): n is string => !!n);
  const rules = spec.workflows ?? [];
  return (
    <aside className="detail" aria-label="About this app" data-dye={spec.dye}>
      <span className="sec"><span>About</span></span>
      <h2 className="d-title">{spec.name}</h2>
      {app.status && <p className="d-meta"><Bold text={app.status} /></p>}
      <dl className="card d-fields">
        <div><dt>Connected</dt><dd>{from.length ? `Gets rows from ${listNames(from)}` : 'Not connected to other apps yet'}</dd></div>
        {rules.length > 0 && <div><dt>Rules</dt><dd>{rules.length} · {rules.filter((r) => r.on).length} on</dd></div>}
        {spec.private && <div><dt>Private</dt><dd>{spec.settings?.clair_read ? 'Clair can read it (you turned that on)' : "Clair can't read it"}</dd></div>}
      </dl>
      {pickable > 0 && <p className="detail-empty">Pick a row to see it here.</p>}
    </aside>
  );
}

/**
 * The laptop's right pane (Laptop board, "Detail"): on Home the Next up thread; in an app the
 * row you picked, big, with its other fields, where it came from, and Edit and Delete.
 * Nothing here is computed: it shows the row the server sent.
 */
export function Detail() {
  const { pathname } = useLocation();
  const home = useStore((s) => s.home);
  const detail = useStore((s) => s.detail);
  const app = useStore((s) => (detail ? s.apps[detail.app] : undefined));
  const now = useStore((s) => s.me?.server_now) ?? '';
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => { setDetail(null); }, [pathname]); // a new screen starts with nothing picked

  if (pathname === '/') return <aside className="detail" aria-label="Next up">{home && <NextUp home={home} />}</aside>;

  const c = app?.spec.collections.find((x) => `${app.spec.key}/${x.key}` === detail?.ref);
  const rec = c && detail ? (app?.data[detail.ref] as Rec[] | undefined)?.find((r) => r.id === detail.id) : undefined;
  if (!app || !c || !rec) return <AppInfo />;

  const amount = c.amountField ? c.fields.find((f) => f.key === c.amountField) : undefined;
  const date = c.dateField ? c.fields.find((f) => f.key === c.dateField) : undefined;
  const rest = c.fields.filter((f) => f.key !== c.titleField && f.key !== c.amountField && f.key !== c.dateField && !SKIP.has(f.type) && !SYSTEM.has(f.key)
    && rec.properties[f.key] !== undefined && rec.properties[f.key] !== '' && rec.properties[f.key] !== null);
  const via = rec.properties._via as { app?: string } | undefined;
  const from = via?.app ? home?.apps.find((a) => a.key === via.app) : undefined;
  const meta = [date ? fieldText(date, rec.properties[date.key], now) : '', from ? `from ${from.name}` : ''].filter(Boolean).join(' · ');

  const remove = async () => {
    setBusy(true);
    try {
      const r = await request<CommandResult>('DELETE', `/records/${rec.id}`);
      await afterCommand(r);
      void loadApp(app.spec.key);
      setDetail(null);
      toast('Deleted.', { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); void loadApp(app.spec.key); } catch (x) { toast(errorText(x)); } } });
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };

  return (
    <aside className="detail" aria-label="Detail" data-dye={app.spec.dye}>
      <span className="sec"><span>Detail</span></span>
      <h2 className="d-title">{title(c, rec, now)}</h2>
      {amount && rec.properties[amount.key] !== undefined && <span className="d-amount num">{fieldText(amount, rec.properties[amount.key])}</span>}
      {meta && <span className="d-meta">{meta}</span>}
      {rest.length > 0 && (
        <dl className="card d-fields">
          {rest.map((f) => <div key={f.key}><dt>{f.label}</dt><dd>{fieldText(f, rec.properties[f.key], now)}</dd></div>)}
        </dl>
      )}
      {from && <span className="d-also" data-dye={from.dye}><i className="dyedot" />also in {from.name}</span>}
      <div className="d-actions">
        <button className="ghost" onClick={() => setEditing(true)}>Edit</button>
        <button className="ghost" onClick={remove} disabled={busy}><Icon name="trash" size={16} sw={1.8} />Delete</button>
      </div>
      <AddSheet app={app.spec.key} appName={app.spec.name} collection={c} now={now} apps={home?.apps} record={rec}
        open={editing} onClose={() => setEditing(false)} onAdded={() => void loadApp(app.spec.key)} />
    </aside>
  );
}
