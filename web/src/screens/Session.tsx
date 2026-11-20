import { useEffect, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { errorText, request } from '../api/client';
import type { BlockValue, CommandResult } from '../api/types';
import { useWakeLock } from '../components/blocks/Timer';
import { Icon } from '../components/Icon';
import { Spool } from '../components/Spool';
import { clock } from '../lib/format';
import { EASE, RM, T } from '../lib/motion';
import { afterCommand, loadApp, toast, useStore } from '../lib/store';

type Logged = { step: number; reps: number; weight: number };

/** The workout clock: it ticks on its own, so the steppers and the card are not re-rendered every second. */
function Clock({ t0 }: { t0: RefObject<number> }) {
  const [s, setS] = useState(0);
  useEffect(() => { const id = setInterval(() => setS((performance.now() - t0.current) / 1000), 1000); return () => clearInterval(id); }, [t0]);
  return <span className="num">· {clock(s)}</span>;
}
/** "Rest 1:30" counts down from a deadline, in its own component. */
function RestPill({ until }: { until: number }) {
  const [, tick] = useState(0);
  useEffect(() => {
    if (!until) return;
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [until]);
  const left = Math.ceil((until - performance.now()) / 1000);
  return until && left > 0 ? <span className="pill timer" role="timer">Rest {clock(left)}</span> : null;
}

/**
 * "New best": the banner rises and fades in (220 ms) and the proud spool hops once as it arrives; when the number stops being a
 * best it leaves with a 140 ms fade, nothing else. It is mounted while it shows and for the time it takes to leave, so the spool
 * hops when the banner appears, never on a re-render. A short buzz when it arrives (where the device has one).
 */
function Best({ on, name }: { on: boolean; name: string }) {
  const [shown, setShown] = useState(false);
  const [label, setLabel] = useState(name); // the leaving banner keeps the exercise it was for
  const el = useRef<HTMLSpanElement>(null);
  if (on && !shown) setShown(true);
  if (on && label !== name) setLabel(name);
  useLayoutEffect(() => {
    const e = el.current;
    if (!e) return;
    e.getAnimations().forEach((a) => a.cancel());
    const rm = RM();
    if (on) {
      try { navigator.vibrate?.(10); } catch { /* no buzz */ }
      e.animate(rm ? [{ opacity: 0 }, { opacity: 1 }] : [{ opacity: 0, transform: 'translateY(6px) scale(.97)' }, { opacity: 1, transform: 'none' }], { duration: rm ? T.fb : T.state, easing: EASE });
    } else {
      e.animate([{ opacity: 1 }, { opacity: 0 }], { duration: rm ? T.fb : T.stateOut, easing: EASE, fill: 'forwards' }).finished.then(() => setShown(false), () => {});
    }
  }, [on]);
  if (!shown) return null;
  return <span ref={el} className="s-best"><Spool expr="proud" size={30} /><span><b>New best</b> on {label.toLowerCase()}. Logged when you finish the set.</span></span>;
}

/** A logged set ("Set 2 · 10 reps"): it fades in as it is written and its check draws itself (120 ms). Under reduced motion: the fade only. */
function SetDone({ children }: { children: ReactNode }) {
  const el = useRef<HTMLSpanElement>(null);
  useLayoutEffect(() => {
    const e = el.current;
    if (!e) return;
    const rm = RM();
    e.animate([{ opacity: 0 }, { opacity: 1 }], { duration: rm ? T.fb : T.state, easing: EASE });
    const path = e.querySelector('svg path');
    if (path && !rm) {
      const len = (path as SVGPathElement).getTotalLength();
      (path as SVGPathElement).style.strokeDasharray = String(len);
      path.animate([{ strokeDashoffset: len }, { strokeDashoffset: 0 }], { duration: T.fb, delay: 60, easing: EASE, fill: 'backwards' });
    }
  }, []);
  return <span ref={el} className="s-done">{children}</span>;
}

/**
 * Log a set (board "Log a set"): a focused screen with no bar. A running clock; exercise k
 * of n; the exercise card with its plan and best, the sets done with ticks, reps and weight
 * steppers filled from the plan; "Rest 1:30" after each set; "New best" with the proud spool
 * when a set beats the best; Up next; Skip | Log set N. Each set is written as you log it;
 * Finish marks the session done. The screen stays awake.
 */
export function Session() {
  const { key = '', blockId = '' } = useParams();
  const app = useStore((s) => s.apps[key]);
  const nav = useNavigate();
  const v: BlockValue | undefined = app?.values?.[blockId];
  const steps = v?.steps ?? [];
  const block = app?.spec.tabs.flatMap((t) => t.children).find((b) => b.id === blockId);
  const logTo = block && block.kind === 'next' ? block.log : `${key}/sets`;
  const [i, setI] = useState(0);
  const [logged, setLogged] = useState<Logged[]>([]);
  const [reps, setReps] = useState(10);
  const [weight, setWeight] = useState(0);
  const [touched, setTouched] = useState(false); // the person changed a number: only then can a set be "a new best"
  const [restUntil, setRestUntil] = useState(0); // performance.now() deadline
  const [busy, setBusy] = useState(false);
  const [asking, setAsking] = useState(false); // "Finish with N sets left?"
  const t0 = useRef(performance.now());
  const card = useRef<HTMLElement>(null);
  useEffect(() => { if (!app) void loadApp(key); }, [app, key]);
  useWakeLock(true);
  // the steppers start from the plan of the exercise on screen, also when the app loads after the page (a deep link)
  const cur = steps[Math.min(i, Math.max(0, steps.length - 1))];
  useEffect(() => { if (cur) { setReps(cur.reps); setWeight(cur.weight); setTouched(false); } }, [cur?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!app || !v?.title || !steps.length) return <div className="screen focused"><button className="round back" onClick={() => nav(-1)} aria-label="Back"><Icon name="back" /></button></div>;
  const step = steps[Math.min(i, steps.length - 1)];
  const doneHere = logged.filter((l) => l.step === i);
  const setN = doneHere.length + 1;
  const allSets = steps.reduce((a, s) => a + s.sets, 0);
  const pct = Math.round((logged.length / allSets) * 100);
  const best = step.best;
  const isBest = touched && !!best && (weight > best.weight || (weight === best.weight && reps > best.reps));
  const left = allSets - logged.length;
  const upNext = steps.slice(i + 1);

  const goTo = (n: number) => {
    const el = card.current;
    const apply = () => setI(n); // the steppers follow the exercise (effect above)
    if (!el || RM()) { apply(); return; }
    el.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateX(-16px)' }], { duration: T.stateOut, easing: EASE }).finished.then(() => {
      apply(); el.animate([{ opacity: 0, transform: 'translateX(16px)' }, { opacity: 1, transform: 'none' }], { duration: T.state, easing: EASE });
    }, apply);
  };
  const logSet = async () => {
    setBusy(true);
    try {
      const r = await request<CommandResult>('POST', '/records', { collection_id: logTo, fields: { exercise: [step.id], session: [v.record_id], reps, weight } });
      void afterCommand(r);
      const next = [...logged, { step: i, reps, weight }];
      setLogged(next);
      try { navigator.vibrate?.(10); } catch { /* no buzz */ }
      if (doneHere.length + 1 >= step.sets && i < steps.length - 1) { setRestUntil(0); goTo(i + 1); }
      else setRestUntil(performance.now() + (v.rest ?? 90) * 1000);
    } catch (x) { toast(errorText(x), undefined, 4000); }
    setBusy(false);
  };
  /** Ends the workout; with sets still to do it asks first, inline. */
  const askFinish = () => { if (left > 0) setAsking(true); else void finish(); };
  const finish = async () => {
    setBusy(true); setAsking(false);
    const mins = Math.max(1, Math.round((performance.now() - t0.current) / 60000));
    try {
      const r = await request<CommandResult>('POST', `/records/${v.record_id}/complete`, { occurrence: v.occurrence, minutes: mins });
      await afterCommand(r);
      toast(`${v.title} logged · ${logged.length} sets in ${mins} min.`);
      nav(`/a/${key}`, { replace: true });
    } catch (x) { toast(errorText(x), undefined, 4000); setBusy(false); }
  };

  return (
    <div className="screen focused session" data-dye={app.spec.dye}>
      <div className="top-row">
        <button className="round back" onClick={() => nav(-1)} aria-label={`Back to ${app.spec.name}`}><Icon name="back" /></button>
        <h1>{v.title} <Clock t0={t0} /></h1>
        <button className="lk" onClick={askFinish} disabled={busy}>Finish</button>
      </div>
      {asking && (
        <div className="card s-ask arrive" role="alertdialog" aria-label="Finish the workout?">
          <span>Finish with {left} {left === 1 ? 'set' : 'sets'} left?</span>
          <span className="s-ask-btns"><button className="ghost" onClick={() => setAsking(false)}>Keep going</button><button className="cta" onClick={() => void finish()} disabled={busy}>Finish</button></span>
        </div>
      )}
      <div className="s-prog"><span>Exercise {Math.min(i + 1, steps.length)} of {steps.length}</span><span className="num">{pct}%</span></div>
      <span className="track b6"><span className="fill" style={{ width: `${pct}%` }} /></span>

      <section ref={card} className="card s-card" aria-live="polite">
        <div className="s-head"><b>{step.name}</b><RestPill until={restUntil} /></div>
        <span className="s-plan">{step.plan}{best ? ` · ${best.text}` : ''}</span>
        {doneHere.map((l, k) => (
          <SetDone key={k}><Icon name="check" size={18} sw={2.2} />Set {k + 1} · {l.reps} reps{l.weight ? ` × ${l.weight} ${step.unit}` : ''}</SetDone>
        ))}
        {doneHere.length < step.sets && (
          <>
            <span className="s-plan">Set {setN}</span>
            <div className="steppers">
              <div><span className="lbl">reps</span>
                <span className="stepper"><button className="sb" aria-label="Fewer reps" onClick={() => { setTouched(true); setReps((x) => Math.max(1, x - 1)); }}>−</button><span className="sv">{reps}</span><button className="sb" aria-label="More reps" onClick={() => { setTouched(true); setReps((x) => x + 1); }}>+</button></span>
              </div>
              <div><span className="lbl">weight, {step.unit}</span>
                <span className="stepper"><button className="sb" aria-label="Less weight" onClick={() => { setTouched(true); setWeight((x) => Math.max(0, x - 5)); }}>−</button><span className="sv">{weight}</span><button className="sb" aria-label="More weight" onClick={() => { setTouched(true); setWeight((x) => x + 5); }}>+</button></span>
              </div>
            </div>
            <Best on={isBest} name={step.name} />
          </>
        )}
      </section>

      {upNext.length > 0 && (
        <section className="cl-group">
          <div className="sec"><span>Up next</span></div>
          <ul className="card list">{upNext.map((s) => <li key={s.id} className="row plain"><span className="main"><span className="t">{s.name}</span><span className="s">{s.plan}{s.weight ? ` · ${s.weight} ${s.unit}` : ''}</span></span></li>)}</ul>
        </section>
      )}

      <div className="s-actions">
        <button className="ghost" onClick={() => (i < steps.length - 1 ? goTo(i + 1) : askFinish())} disabled={busy}>Skip</button>
        {doneHere.length < step.sets
          ? <button className="cta" onClick={logSet} disabled={busy}>Log set {setN}</button>
          : <button className="cta" onClick={finish} disabled={busy}>Finish {v.title.toLowerCase()}</button>}
      </div>
    </div>
  );
}
