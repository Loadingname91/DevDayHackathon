import { useState } from 'react';
import { Link } from 'react-router-dom';
import { request, errorText } from '../api/client';
import { signIn, signInWithTokenHash } from '../lib/auth';

/** "I have a quilt · Sign in": the demo account's email and password (backend.md §13, T2). */
export function SignIn({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    const m = await signIn(email.trim(), password).catch((x) => String(x.message ?? x));
    setBusy(false);
    if (m) setErr(m); else onDone();
  };
  return (
    <form className="center" onSubmit={go}>
      <h1>I have a quilt.</h1>
      <input className="input" type="email" autoComplete="username" placeholder="Email" aria-label="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input className="input" type="password" autoComplete="current-password" placeholder="Password" aria-label="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {err && <p role="alert" style={{ fontWeight: 600 }}>{err}</p>}
      <button className="cta" disabled={busy}>Sign in</button>
      <Link to="/join" className="ghost" style={{ textAlign: 'center', display: 'grid', placeItems: 'center' }}>Use a code from your phone</Link>
    </form>
  );
}

/** Second device: type the 5-minute code shown on the phone (POST /join-codes/redeem). */
export function Join({ onDone }: { onDone: () => void }) {
  const [code, setCode] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      const r = await request<{ email: string; token_hash: string }>('POST', '/join-codes/redeem', { code: code.trim().toUpperCase() });
      const m = await signInWithTokenHash(r.token_hash);
      if (m) setErr(m); else onDone();
    } catch (x) {
      const s = (x as { status?: number }).status;
      setErr(s === 404 ? 'That code is not right.' : s === 410 ? 'That code has run out. Make a new one on your phone.' : errorText(x));
    }
    setBusy(false);
  };
  return (
    <form className="center" onSubmit={go}>
      <h1>Open your quilt here.</h1>
      <p className="muted">On your phone: You, then "Open on another device". Type the code it shows.</p>
      <input className="input code" inputMode="text" autoCapitalize="characters" autoComplete="one-time-code" placeholder="CODE" aria-label="Join code" value={code} onChange={(e) => setCode(e.target.value)} required />
      {err && <p role="alert" style={{ fontWeight: 600 }}>{err}</p>}
      <button className="cta" disabled={busy}>Open</button>
      <Link to="/signin" className="ghost" style={{ textAlign: 'center', display: 'grid', placeItems: 'center' }}>Sign in with email</Link>
    </form>
  );
}
