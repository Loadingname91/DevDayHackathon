// One request function and one SSE reader. Every screen calls these; nothing else
// touches fetch. Routes go to the mock or to the live API (spec/split.md §3).
import type { ClairEvent, TurnRequest } from './types';
import { getToken } from '../lib/auth';

const MODE = (import.meta.env.VITE_API ?? 'mock') as 'mock' | 'live';
const BASE = ((import.meta.env.VITE_API_BASE as string | undefined) ?? '').replace(/\/$/, '');
const MOCK_ROUTES = ((import.meta.env.VITE_MOCK_ROUTES as string | undefined) ?? '')
  .split(',').map((s) => s.trim()).filter(Boolean);

export const isLive = MODE === 'live';
export function isMocked(path: string): boolean {
  if (MODE !== 'live') return true;
  return MOCK_ROUTES.some((p) => path === p || path.startsWith(p.endsWith('/') ? p : p + '/') || path.startsWith(p + '?'));
}
/** True when any part of what is on screen may come from fixtures: drives the "mock data" mark. */
export const anyMock = MODE !== 'live' || MOCK_ROUTES.length > 0;

export class ApiError extends Error {
  constructor(public status: number, public body: unknown, message?: string) {
    super(message ?? `API ${status}`);
  }
}

type Method = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  if (isMocked(path)) {
    const { mockRequest } = await import('../mocks/handler');
    return mockRequest<T>(method, path, body);
  }
  const token = await getToken();
  const res = await fetch(`${BASE}/api${path}`, {
    method,
    headers: { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

/** question id → the thread it was asked on, so its answer goes back to the same thread */
const threadOf = new Map<string, string>();

/**
 * Sends a Clair turn and calls onEvent for each SSE event. Resolves when the stream
 * ends. If the stream closes before `done`, a `done {status: "error"}` is delivered,
 * so callers handle one path (clair-agent.md §2).
 */
export async function clairTurn(body: TurnRequest, onEvent: (e: ClairEvent) => void, signal?: AbortSignal, path = '/clair/turns'): Promise<void> {
  let sawDone = false;
  let thread: string | null = null; // the server's thread for this turn (X-Thread-Id), known once the stream opens
  const emit = (e: ClairEvent) => {
    if (e.event === 'done') sawDone = true;
    if (e.event === 'question' && thread) threadOf.set(e.data.id, thread);
    onEvent(e);
  };
  // The live API needs `thread_id` on an answer (api/models.py AnswerTurn; the contract and the mock say optional): it is the thread of the
  // turn that asked the question. Live finding: an answer without it is 422 and the Build screen shows "Try again" after the questions.
  if ('answer' in body && !body.thread_id) { const t = threadOf.get(body.answer.question_id); if (t) body = { ...body, thread_id: t }; }
  try {
    if (isMocked(path)) {
      const { mockTurn } = await import('../mocks/handler');
      await mockTurn(path, body, emit, signal);
    } else {
      const token = await getToken();
      const res = await fetch(`${BASE}/api${path}`, {
        method: 'POST', signal,
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(body),
      });
      if (!res.ok || !res.body) throw new ApiError(res.status, await res.json().catch(() => null));
      thread = res.headers.get('X-Thread-Id');
      await readSSE(res.body, emit);
    }
  } catch (err) {
    if (signal?.aborted) return;
    if (!sawDone) emit({ event: 'done', data: { status: 'error', sources: [], message: errorText(err) } });
    return;
  }
  if (!sawDone && !signal?.aborted) emit({ event: 'done', data: { status: 'error', sources: [], message: 'The connection closed before Clair finished.' } });
}

async function readSSE(stream: ReadableStream<Uint8Array>, emit: (e: ClairEvent) => void) {
  const reader = stream.getReader();
  const dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true }).replace(/\r\n/g, '\n');
    let i: number;
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const frame = buf.slice(0, i);
      buf = buf.slice(i + 2);
      let event = 'message';
      const data: string[] = [];
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) data.push(line.slice(5).trimStart());
      }
      if (!data.length) continue;
      try { emit({ event, data: JSON.parse(data.join('\n')) } as ClairEvent); } catch { /* a frame we can't read is skipped */ }
    }
  }
}

export function errorText(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 402) return 'You are out of credits for this month.';
    if (err.status === 409) return 'That was already changed on another device.';
    if (err.status === 429) return 'Too many requests. Try again in a moment.';
    if (err.status === 401) return 'You are signed out. Sign in again.';
    return 'That did not save. Nothing was changed.';
  }
  return 'Could not reach Quilt. Nothing was changed.';
}
