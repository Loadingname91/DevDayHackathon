import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { errorText, request } from '../api/client';
import type { Connection } from '../api/types';
import { wall } from '../lib/format';
import { loadApp, toast, useStore } from '../lib/store';
import { Icon } from './Icon';

/** "2 min ago" from server time; the client never reads its own clock for this. */
function ago(at: string, now: string): string {
  const a = wall(at), b = wall(now);
  if (!a || !b || a.hh === undefined || b.hh === undefined) return 'just now';
  const mins = (Date.UTC(b.y, b.m - 1, b.d, b.hh, b.mm) - Date.UTC(a.y, a.m - 1, a.d, a.hh, a.mm!)) / 60000;
  if (mins < 1) return 'just now';
  if (mins < 60) return `${Math.round(mins)} min ago`;
  return `${Math.round(mins / 60)} h ago`;
}

/** Calendar's Google row (FR-G1, FR-G2; backend.md §8a). Read-only: Quilt never writes to Google. A card to connect or reconnect; one line once it is synced. */
export function ConnectGoogle() {
  const now = useStore((s) => s.me?.server_now) ?? '';
  const [conn, setConn] = useState<Connection | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [q] = useSearchParams();
  const nav = useNavigate();
  const failed = q.get('connected') === 'failed';
  useEffect(() => { request<Connection[]>('GET', '/connect').then((c) => setConn(c.find((x) => x.provider === 'google') ?? null), () => setConn(null)); }, [q]);
  if (conn === undefined) return <div className="gcal-slot" aria-hidden="true" />; // holds the connected row's height while we ask, so the page below doesn't drop

  const start = async () => {
    setBusy(true);
    try {
      const { url } = await request<{ url: string }>('POST', '/connect/google/start');
      if (url.startsWith('/')) { nav(url); setBusy(false); } // the mock's "redirect" is a route in this app
      else location.href = url; // Google's consent page: a whole-page redirect, no popup, so it works on the phone
    }
    catch (e) { toast(errorText(e), undefined, 4000); setBusy(false); }
  };
  const refresh = async () => {
    setBusy(true);
    try {
      const r = await request<{ last_synced_at: string }>('POST', '/connect/google/sync');
      setConn((c) => (c ? { ...c, last_synced_at: r.last_synced_at } : c));
      await loadApp('calendar');
    } catch (e) { toast(errorText(e), undefined, 4000); }
    setBusy(false);
  };

  if (!conn || conn.needs_reconnect) {
    return (
      <div className="card gcal">
        {failed && !conn && <p className="gcal-msg" role="alert">Google Calendar wasn't connected.</p>}
        <span className="gcal-row">
          <span className="gcal-ico" aria-hidden="true"><Icon name="calendar" size={18} /></span>
          <span className="grow">
            <b>{conn?.needs_reconnect ? 'Reconnect Google Calendar' : 'Add Google Calendar'}</b>
            <small>Quilt reads your calendar and never writes to it.</small>
          </span>
          <button className="outline" onClick={start} disabled={busy}>{conn ? 'Reconnect' : 'Connect'}</button>
        </span>
      </div>
    );
  }
  // connected: one quiet line, not a card; the full card is for adding, reconnecting and errors
  return (
    <div className="gcal-line" title={conn.account_email}>
      <Icon name="calendar" size={16} sw={1.8} />
      <span className="gl-t">Google Calendar · synced {busy ? 'now…' : ago(conn.last_synced_at, now)}</span>
      <button className="link" onClick={refresh} disabled={busy}>Refresh</button>
    </div>
  );
}
