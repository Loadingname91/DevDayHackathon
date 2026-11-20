// Supabase sign-in, live mode only. In mock mode there is no sign-in (split.md §3).
import type { SupabaseClient } from '@supabase/supabase-js';

const URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
const LIVE = (import.meta.env.VITE_API ?? 'mock') === 'live';

export const authConfigured = LIVE && !!URL && !!KEY;
let client: Promise<SupabaseClient> | null = null;

export function supabase(): Promise<SupabaseClient> {
  if (!authConfigured) return Promise.reject(new Error('Supabase is not configured'));
  client ??= import('@supabase/supabase-js').then(({ createClient }) =>
    createClient(URL!, KEY!, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } }));
  return client;
}

export async function getToken(): Promise<string | null> {
  if (!authConfigured) return null;
  const { data } = await (await supabase()).auth.getSession();
  return data.session?.access_token ?? null;
}

export async function hasSession(): Promise<boolean> {
  if (!authConfigured) return true; // mock mode, or live before the keys arrive
  if ((await getToken()) !== null) return true;
  if (import.meta.env.VITE_DEMO_OPEN === '1') return enterDemo(); // open-room demo: no form (server side DEMO_OPEN=1)
  return false;
}

async function enterDemo(): Promise<boolean> {
  try {
    const base = ((import.meta.env.VITE_API_BASE as string | undefined) ?? '').replace(/\/$/, '');
    const r = await fetch(`${base}/api/demo/enter`, { method: 'POST' });
    if (!r.ok) return false;
    const { token_hash } = (await r.json()) as { token_hash: string };
    return (await signInWithTokenHash(token_hash)) === null;
  } catch { return false; }
}

export async function signIn(email: string, password: string): Promise<string | null> {
  const { error } = await (await supabase()).auth.signInWithPassword({ email, password });
  return error ? error.message : null;
}

/** Second device: the join code's {email, token_hash} from POST /join-codes/redeem. */
export async function signInWithTokenHash(token_hash: string): Promise<string | null> {
  const { error } = await (await supabase()).auth.verifyOtp({ token_hash, type: 'magiclink' });
  return error ? error.message : null;
}

export async function signOut() {
  if (authConfigured) await (await supabase()).auth.signOut();
}
