import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError, isLive, request } from '../api/client';
import { Icon } from '../components/Icon';
import { signOut } from '../lib/auth';
import { cacheClear } from '../lib/cache';
import { useStore } from '../lib/store';

/** You: credits, the join code for a second device, sign out. Settings proper come after the cut line. */
export function You() {
  const me = useStore((s) => s.me);
  const [code, setCode] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const join = async () => {
    setMsg(null);
    try { setCode((await request<{ code: string; expires_at: string }>('POST', '/join-codes')).code); }
    catch (e) { setMsg(e instanceof ApiError && e.status === 403 ? 'Keep your quilt first, then you can open it on another device.' : 'Could not make a code. Try again.'); }
  };
  return (
    <div className="screen">
      <div className="top-row">
        <Link to="/" className="round back" aria-label="Home"><Icon name="back" /></Link>
      </div>
      <div className="ident">
        <span className="tile" aria-hidden="true" data-dye="blush"><Icon name="user" size={18} /></span>
        <h1 title={me?.user.display_name}>{me?.user.display_name ?? 'You'}</h1>
      </div>
      {me?.user.email && <p className="status-s muted">{me.user.email}</p>}
      <div className="card metric" aria-busy={!me}>
        <span className="lbl">Clair credits</span>
        <span className="big">{me ? `${me.credits.left} of ${me.credits.granted} left` : '–'}</span>
        <span className="sub">Resets on the 1st.</span>
      </div>
      <div className="card metric">
        <span className="lbl">Another device</span>
        {code ? <><span className="big" style={{ letterSpacing: '.2em' }}>{code}</span><span className="sub">Type this on the other device within 5 minutes.</span></>
          : <button className="outline" style={{ alignSelf: 'flex-start', marginTop: 6 }} onClick={join}>Open on another device</button>}
        {msg && <span className="sub" role="alert">{msg}</span>}
      </div>
      {isLive && <button className="outline" style={{ alignSelf: 'flex-start' }} onClick={async () => { await cacheClear(); await signOut(); location.href = '/'; }}>Sign out</button>}
    </div>
  );
}
