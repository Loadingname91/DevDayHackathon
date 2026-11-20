import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { errorText, request } from '../../api/client';
import type { CommandResult, TimerBlock } from '../../api/types';
import { clock } from '../../lib/format';
import { EASE, RM, T } from '../../lib/motion';
import { afterCommand, toast } from '../../lib/store';
import { Disclosure } from '../Disclosure';
import { Icon } from '../Icon';
import { Spool } from '../Spool';
import type { Ctx } from './index';

type Phase = 'idle' | 'running' | 'paused' | 'done';
const MOODS = [1, 2, 3, 4, 5];
/** The controls crossfade when this changes: idle, a session in progress, done. Pause and resume only relabel a button. */
const stage = (p: Phase) => (p === 'idle' ? 0 : p === 'done' ? 2 : 1);
type Lock = { release: () => Promise<void>; addEventListener?: (t: 'release', f: () => void) => void };
type WakeNav = Navigator & { wakeLock?: { request: (t: 'screen') => Promise<Lock> } };

/**
 * Keep the screen awake while `on`; fine if the browser says no. A lock that arrives after the cleanup is released at once,
 * and the browser drops the lock when the tab is hidden, so it is asked for again when the tab is visible.
 */
export function useWakeLock(on: boolean) {
  useEffect(() => {
    if (!on) return;
    let dead = false, lock: Lock | null = null;
    const get = async () => {
      if (dead || lock || document.visibilityState !== 'visible') return;
      try {
        const l = await (navigator as WakeNav).wakeLock?.request('screen');
        if (!l) return;
        if (dead) { void l.release().catch(() => {}); return; }
        lock = l;
        l.addEventListener?.('release', () => { if (lock === l) lock = null; });
      } catch { /* no lock: fine */ }
    };
    void get();
    const visible = () => { if (document.visibilityState === 'visible') void get(); };
    document.addEventListener('visibilitychange', visible);
    return () => { dead = true; document.removeEventListener('visibilitychange', visible); void lock?.release().catch(() => {}); lock = null; };
  }, [on]);
}

/** One audio context for the whole timer, made and resumed inside the Start tap (iOS keeps a context made later suspended). */
function audio(ac: { current: AudioContext | null }) {
  try {
    const A = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    ac.current ??= new A();
    void ac.current.resume();
  } catch { /* no sound */ }
}
/** A soft two-note chime at the end. */
function chime(ac: AudioContext | null) {
  try {
    if (ac) {
      [523.25, 783.99].forEach((f, i) => {
        const o = ac.createOscillator(), g = ac.createGain();
        o.type = 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, ac.currentTime + i * 0.35);
        g.gain.exponentialRampToValueAtTime(0.18, ac.currentTime + i * 0.35 + 0.04);
        g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + i * 0.35 + 1.4);
        o.connect(g).connect(ac.destination); o.start(ac.currentTime + i * 0.35); o.stop(ac.currentTime + i * 0.35 + 1.5);
      });
    }
    navigator.vibrate?.([30, 120, 30]);
  } catch { /* no sound */ }
}

/** How long the session was, in words a person would say: seconds under a minute, minutes after. */
const spent = (s: number) => (s < 60 ? `${Math.max(1, Math.floor(s))} sec` : `${Math.round(s / 60)} min`);
/** Under this the session is probably a mis-tap: Discard leads, saving it is the second choice. */
const SHORT = 30;

/**
 * A timer that logs a row when it ends. Countdown (Meditation): pick a kind and a length,
 * sit; the ring empties; a chime; say how you feel now; save. Stopwatch
 * (Running): start, pause, finish, then the distance and kind; save. The time is measured
 * here, like any gesture; nothing is written until Save.
 * One clock: the ring is a single linear animation over the time left (restarted on resume), the
 * numbers tick on the whole second.
 */
export function Timer({ block, ctx }: { block: TimerBlock; ctx: Ctx }) {
  const c = ctx.spec.collections.find((x) => `${ctx.spec.key}/${x.key}` === block.log);
  const kindField = block.kindField ? c?.fields.find((f) => f.key === block.kindField) : undefined;
  const stopwatch = block.mode === 'stopwatch';
  const [phase, setPhase] = useState<Phase>('idle');
  const [kind, setKind] = useState(kindField?.options?.[stopwatch ? 0 : 1]?.id ?? '');
  const [minutes, setMinutes] = useState(block.presets?.[1] ?? 10);
  const [elapsed, setElapsed] = useState(0); // seconds, exact at every pause and end, whole seconds while it runs
  const [before, setBefore] = useState<number | null>(null);
  const [feel, setFeel] = useState(false); // the optional "how do you feel?" row is behind a link
  const [after, setAfter] = useState<number | null>(null);
  const [distance, setDistance] = useState(3);
  const [busy, setBusy] = useState(false);
  const [cheer, setCheer] = useState(false); // the spool beside "Done", once the ring has closed
  const started = useRef(0), banked = useRef(0);
  const ac = useRef<AudioContext | null>(null);
  const arc = useRef<SVGCircleElement>(null);
  const total = minutes * 60;
  const R = 84, C = 2 * Math.PI * R;
  useWakeLock(phase === 'running');
  useEffect(() => () => { void ac.current?.close().catch(() => {}); }, []);
  const now = () => banked.current + (phase === 'running' ? (performance.now() - started.current) / 1000 : 0);
  const short = elapsed < SHORT;

  // Every phase change goes through here. When the controls change (idle, in progress, done) the old ones are copied first and
  // left to fade out (120 ms) as the new ones fade in (220 ms, opacity only): the ring and the clock stay where they are.
  const cur = useRef<Phase>('idle'), inner = useRef<HTMLDivElement>(null), old = useRef<HTMLElement | null>(null);
  const goto = (next: Phase) => {
    if (stage(next) !== stage(cur.current) && inner.current) old.current = inner.current.cloneNode(true) as HTMLElement;
    cur.current = next;
    setPhase(next);
  };
  useLayoutEffect(() => {
    const el = inner.current, gone = old.current;
    old.current = null;
    if (!el || !gone) return;
    const box = el.parentElement!;
    box.querySelectorAll('.t-ghost').forEach((g) => g.remove());
    gone.classList.add('t-ghost'); gone.inert = true; gone.setAttribute('aria-hidden', 'true');
    box.append(gone);
    const rm = RM();
    box.animate([{ clipPath: 'inset(-8px -8px 0 -8px)' }, { clipPath: 'inset(-8px -8px 0 -8px)' }], { duration: T.fb }); // a taller old block does not spill out of the card
    gone.animate([{ opacity: 1 }, { opacity: 0 }], { duration: T.fb, easing: EASE, fill: 'forwards' }).finished.then(() => gone.remove(), () => gone.remove());
    el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: rm ? T.fb : T.state, easing: EASE });
  }, [phase]);

  // the clock: one timer, ticking on the whole second of the elapsed time
  useEffect(() => {
    if (phase !== 'running') return;
    started.current = performance.now();
    let id: ReturnType<typeof setTimeout>;
    const tick = () => {
      const s = banked.current + (performance.now() - started.current) / 1000;
      if (!stopwatch && s >= total - 0.01) { banked.current = total; setElapsed(total); goto('done'); chime(ac.current); return; }
      setElapsed(s);
      id = setTimeout(tick, (1 - (s % 1)) * 1000 + 8);
    };
    id = setTimeout(tick, (1 - (banked.current % 1)) * 1000 + 8); // the first tick is the next whole second too
    return () => { clearTimeout(id); if (banked.current < total || stopwatch) banked.current += (performance.now() - started.current) / 1000; };
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  // the ring: one linear animation from where it is to empty; paused or finished it rests on the attribute
  useEffect(() => {
    const el = arc.current;
    if (phase !== 'running' || stopwatch || !el || RM()) return;
    const from = C * Math.min(1, banked.current / total);
    const a = el.animate([{ strokeDashoffset: from }, { strokeDashoffset: C }], { duration: Math.max(0, (total - banked.current) * 1000), easing: 'linear', fill: 'forwards' });
    return () => a.cancel();
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  // The finish (about once a day, so it may be a little moment): the ring closes (350 ms), then its stroke eases to the gold line
  // (220 ms; it stays the dye where there is no gold), and the spool arrives beside "Done" and hops once. A session of seconds is
  // a mis-tap: no celebration. Reduced motion: the ring is simply whole, the colour fades in 120 ms, the spool does not hop.
  const closes = phase === 'done' && !stopwatch && !short;
  useLayoutEffect(() => {
    const el = arc.current;
    if (!closes || !el) return;
    const gold = [{ stroke: 'var(--deep)' }, { stroke: 'var(--gold-line, var(--deep))' }];
    const run = RM()
      ? [el.animate(gold, { duration: T.fb, fill: 'forwards' })]
      : [el.animate([{ strokeDashoffset: C * Math.min(1, elapsed / total) }, { strokeDashoffset: 0 }], { duration: T.layout, easing: EASE }),
        el.animate(gold, { duration: T.state, delay: T.layout, easing: EASE, fill: 'forwards' })];
    return () => run.forEach((a) => a.cancel());
  }, [closes]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (phase !== 'done' || short) return;
    const id = setTimeout(() => setCheer(true), RM() ? 0 : stopwatch ? T.state : T.layout);
    return () => { clearTimeout(id); setCheer(false); };
  }, [phase, short, stopwatch]);

  if (!c) return null;
  const left = Math.max(0, total - elapsed);
  const pct = stopwatch ? 0 : Math.min(1, elapsed / total);
  const kindLabel = kindField?.options?.find((o) => o.id === kind)?.label ?? '';
  const reset = () => { goto('idle'); setElapsed(0); banked.current = 0; setBefore(null); setFeel(false); setAfter(null); };
  const start = () => { audio(ac); banked.current = 0; setElapsed(0); goto('running'); };
  const pause = () => { setElapsed(now()); goto('paused'); };
  const resume = () => { audio(ac); goto('running'); };
  const end = () => { setElapsed(now()); goto('done'); if (!stopwatch) chime(ac.current); };
  /** The word under the clock; a finished session has the spool beside it. */
  const eyebrow = (text: string) => <span className="t-eyebrow">{text}{cheer && <span className="t-cheer"><Spool expr="stitched" size={30} /></span>}</span>;

  const save = async () => {
    setBusy(true);
    const mins = Math.max(1, Math.round(elapsed / 60));
    const fields: Record<string, unknown> = { ...(block.set ?? {}), [block.minutesField]: mins };
    if (block.kindField && kind) fields[block.kindField] = kind;
    if (block.moodFields) { if (before) fields[block.moodFields[0]] = before; if (after) fields[block.moodFields[1]] = after; }
    if (stopwatch) { fields.distance = distance; fields.name = `${kindLabel} run`; }
    try {
      const r = await request<CommandResult>('POST', '/records', { collection_id: block.log, fields }); // the server stamps the time
      await afterCommand(r); ctx.reload?.();
      toast(stopwatch ? `Run logged · ${distance} mi in ${mins} min.` : `Logged ${mins} min of ${kindLabel.toLowerCase()}.`,
        { label: 'Undo', run: async () => { try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${r.change_set_id}/undo`)); ctx.reload?.(); } catch (x) { toast(errorText(x)); } } });
      reset();
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };

  /** Discard leads when the session was only a few seconds; saving it (as a minute) is the quieter choice. */
  const finishActions = (label: string) => short
    ? <span className="t-actions"><button className="ghost" onClick={save} disabled={busy}>Save as 1 min</button><button className="cta" onClick={reset}>Discard</button></span>
    : <span className="t-actions"><button className="ghost" onClick={reset}>Discard</button><button className="cta" onClick={save} disabled={busy}>{label}</button></span>;

  const moodRow = (val: number | null, set: (n: number) => void, label: string) => (
    <div className="t-mood" role="radiogroup" aria-label={label}>
      <span className="lbl">{label}</span>
      <span className="chips">{MOODS.map((m) => <button key={m} type="button" className="chip mood" role="radio" aria-checked={val === m} onClick={() => set(m)}>{m}</button>)}</span>
      <span className="t-scale"><span>low</span><span>good</span></span>
    </div>
  );

  // ---- stopwatch (a run)
  if (stopwatch) {
    return (
      <section className="card timer" data-dye={ctx.spec.dye} aria-label={block.label}>
        <div className="t-controls"><div className="t-in" ref={inner}>
          {phase === 'idle' && <button className="cta wide" onClick={start} disabled={ctx.preview}><Icon name="play" size={18} />{block.label}</button>}
          {(phase === 'running' || phase === 'paused') && (
            <>
              <span className="t-eyebrow">{phase === 'paused' ? 'Paused' : 'Running'}</span>
              <span className="t-clock" aria-live="off">{clock(Math.floor(elapsed))}</span>
              <span className="t-actions">
                <button className="ghost" onClick={phase === 'paused' ? resume : pause}>{phase === 'paused' ? 'Resume' : 'Pause'}</button>
                <button className="cta" onClick={end}>Finish</button>
              </span>
            </>
          )}
          {phase === 'done' && (
            <>
              {eyebrow(`Run · ${clock(Math.floor(elapsed))}`)}
              {short && <p className="t-note">Only {spent(elapsed)}. Discard it, or save it as a minute.</p>}
              {kindField && <span className="chips" role="radiogroup" aria-label="Kind">{kindField.options!.filter((o) => o.id !== 'race').map((o) => <button key={o.id} className="chip" role="radio" aria-checked={kind === o.id} onClick={() => setKind(o.id)}>{o.label}</button>)}</span>}
              <div className="add-field"><label>Distance</label>
                <span className="stepper">
                  <button type="button" className="sb" aria-label="Less distance" onClick={() => setDistance((d) => Math.max(0.5, +(d - 0.5).toFixed(1)))}>−</button>
                  <span className="sv">{distance}</span><span className="unit">mi</span>
                  <button type="button" className="sb" aria-label="More distance" onClick={() => setDistance((d) => +(d + 0.5).toFixed(1))}>+</button>
                </span>
              </div>
              {finishActions('Save run')}
            </>
          )}
        </div></div>
      </section>
    );
  }

  // ---- countdown (a sit)
  return (
    <section className="card timer" data-dye={ctx.spec.dye} aria-label={block.label}>
      {kindField && (
        <Disclosure open={phase === 'idle'} className="t-kinds">
          <span className="chips kinds" role="radiogroup" aria-label="Kind">
            {kindField.options!.map((o) => <button key={o.id} className="chip" role="radio" aria-checked={kind === o.id} onClick={() => setKind(o.id)}>{o.label}</button>)}
          </span>
        </Disclosure>
      )}
      <div className="t-ring">
        <svg width="200" height="200" viewBox="0 0 200 200" aria-hidden="true">
          <circle cx="100" cy="100" r={R} fill="none" stroke="var(--hair)" strokeWidth="10" />
          <circle ref={arc} className="t-arc" cx="100" cy="100" r={R} fill="none" stroke="var(--deep)" strokeWidth="10" strokeLinecap="round"
            strokeDasharray={C} strokeDashoffset={closes ? 0 : C * pct} transform="rotate(-90 100 100)" />
        </svg>
        <span className="t-center">
          <span className="t-clock" aria-live="off">{clock(phase === 'idle' ? total : phase === 'done' ? Math.floor(elapsed) : Math.ceil(left))}</span>
          {eyebrow(phase === 'done' ? 'Done' : phase === 'paused' ? 'Paused' : kindLabel)}
        </span>
      </div>
      <div className="t-controls"><div className="t-in" ref={inner}>
        {phase === 'idle' && (
          <>
            <span className="seg" role="group" aria-label="Length">
              {(block.presets ?? [10]).map((m) => <button key={m} aria-pressed={minutes === m} onClick={() => setMinutes(m)}>{m} min</button>)}
            </span>
            <button className="cta wide" onClick={start} disabled={ctx.preview}><Icon name="play" size={18} />Start</button>
            {block.moodFields && (
              <div className="t-feelbox">
                <Disclosure open={!feel && before === null} className="t-feel-link"><button className="link t-feel" onClick={() => setFeel(true)}>Add how you feel ›</button></Disclosure>
                <Disclosure open={feel || before !== null}>{moodRow(before, setBefore, 'How do you feel?')}</Disclosure>
              </div>
            )}
          </>
        )}
        {(phase === 'running' || phase === 'paused') && (
          <span className="t-actions">
            <button className="ghost" onClick={phase === 'paused' ? resume : pause}>{phase === 'paused' ? 'Resume' : 'Pause'}</button>
            <button className="cta" onClick={end}>End</button>
          </span>
        )}
        {phase === 'done' && (
          <>
            <p className="t-done">{spent(elapsed)} · {kindLabel}</p>
            {short && <p className="t-note">That was brief. Discard it, or save it as a minute.</p>}
            {block.moodFields && moodRow(after, setAfter, 'How do you feel now?')}
            {finishActions('Save session')}
          </>
        )}
      </div></div>
    </section>
  );
}
