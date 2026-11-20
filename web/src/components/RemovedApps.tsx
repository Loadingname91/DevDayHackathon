import { useEffect, useId, useRef, useState } from 'react';
import { errorText } from '../api/client';
import type { RemovedApp } from '../api/types';
import { loadRemoved, purgeApp, restoreApp, toast, useStore } from '../lib/store';
import { Icon } from './Icon';
import { Sheet } from './Sheet';

/**
 * Recently removed (You, design/DESIGN.md §17): the trash for removed apps. The server keeps a removed app 3 days and then deletes it
 * (`GET /apps/removed`, `POST /apps/{id}/restore`, `DELETE /apps/{id}/purge`, spec/backend.md §10 and §11 row 21). The client words the
 * countdown from the server's `purge_at` against `me.server_now` and never decides when an app is gone. Ink, never red.
 */

const DAY = 86_400_000;
/** "Deleted in 3 days", "Deleted in 1 day", "Deleted today". Rounds up, so an app with 2 days and 1 hour left reads 3. */
export function untilGone(purgeAt: string, now: string): string {
  const left = Date.parse(purgeAt) - Date.parse(now);
  if (!Number.isFinite(left)) return 'Deleted soon';
  const d = Math.ceil(left / DAY);
  return d <= 0 ? 'Deleted today' : `Deleted in ${d} ${d === 1 ? 'day' : 'days'}`;
}

export function RemovedApps() {
  const removed = useStore((s) => s.removed);
  const now = useStore((s) => s.me?.server_now) ?? '';
  const [busy, setBusy] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<RemovedApp | null>(null);
  const last = useRef<RemovedApp | null>(null);
  if (confirm) last.current = confirm; // the sheet keeps its words through its exit
  useEffect(() => { void loadRemoved(); }, []);

  const restore = async (a: RemovedApp) => {
    setBusy(a.key);
    try { await restoreApp(a.key, a.name, a.dye); } catch (e) { toast(errorText(e), undefined, 4000); }
    setBusy(null);
  };

  return (
    <section className="trash" aria-labelledby="trash-h">
      <span className="sec"><span id="trash-h">Recently removed</span></span>
      {removed === null && <div className="card trash-empty" aria-busy="true"><span className="sub">Looking…</span></div>}
      {removed?.length === 0 && (
        <div className="card trash-empty">
          <span className="trash-ico" aria-hidden="true"><Icon name="trash" size={18} /></span>
          <span className="sub">Nothing here. An app you remove waits here for 3 days before it is deleted.</span>
        </div>
      )}
      {!!removed?.length && (
        <ul className="card list trash-list">
          {removed.map((a) => (
            <li key={a.key} className="row plain trash-row" data-dye={a.dye}>
              <span className="tile-ico" aria-hidden="true"><Icon name={a.icon} size={16} sw={1.8} /></span>
              <span className="main"><span className="t">{a.name}</span><span className="s">{untilGone(a.purge_at, now)}</span></span>
              <span className="trash-btns">
                <button type="button" className="outline trash-btn" onClick={() => void restore(a)} disabled={busy === a.key} aria-label={`Restore ${a.name}`}>Restore</button>
                <button type="button" className="trash-del" onClick={() => setConfirm(a)} disabled={busy === a.key} aria-label={`Delete ${a.name} now`}><Icon name="trash" size={18} sw={1.8} /></button>
              </span>
            </li>
          ))}
        </ul>
      )}
      <Sheet open={!!confirm} onClose={() => setConfirm(null)} label={`Delete ${last.current?.name ?? 'app'} now?`}>
        {last.current && <PurgeStep app={last.current} onClose={() => setConfirm(null)} />}
      </Sheet>
    </section>
  );
}

/** Delete now: says what is lost and that it cannot be undone; Keep is the default and takes focus. */
function PurgeStep({ app, onClose }: { app: RemovedApp; onClose: () => void }) {
  const h = useId(), d = useId();
  const keep = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { keep.current?.focus({ preventScroll: true }); }, []);
  const go = async () => {
    if (busy) return;
    setBusy(true); setErr(null);
    try { await purgeApp(app.key, app.name, app.dye); onClose(); } catch (e) { setBusy(false); setErr(errorText(e)); }
  };
  return (
    <div className="rm-step" role="alertdialog" aria-labelledby={h} aria-describedby={d}>
      <div className="sheet-head"><span className="txt"><h2 id={h}>Delete {app.name} now?</h2></span></div>
      <div id={d} className="rm-body">
        <p className="rm-lede">Its rows, rules and links are deleted for good.</p>
        <p className="rm-note">This can’t be undone. Restore it instead if you might want it back.</p>
        {err && <p className="rm-note rm-err" role="alert">{err}</p>}
      </div>
      <div className="rm-btns">
        <button type="button" className="outline" ref={keep} onClick={onClose} disabled={busy}>Keep</button>
        <button type="button" className="cta" onClick={() => void go()} disabled={busy} aria-busy={busy}>{busy ? 'Deleting…' : 'Delete now'}</button>
      </div>
    </div>
  );
}
