import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { clairTurn, errorText, request } from '../api/client';
import type { Answer, AppResponse, AskQuestion, ChangeSet, ClairEvent, CommandResult, Plan, Question } from '../api/types';
import { AppView } from '../components/AppView';
import { PlanCard } from '../components/build/PlanCard';
import { QuestionCard, toChoice, type Picks } from '../components/build/QuestionCard';
import { Icon } from '../components/Icon';
import { Spool, type Expr } from '../components/Spool';
import { ChalkOl, Edge } from '../components/Stitch';
import { listNames } from '../lib/format';
import { dyeOf, EASE, MOTION, RM, sleep, stitchIn, T, threadPull } from '../lib/motion';
import { afterCommand, loadMe, setBuildDraft, sew, toast, useStore } from '../lib/store';

/** The three recorded builds (clair-agent.md §12.11): a suggestion chip fills the box with the sentence; a pattern tile (name, icon, dye and block count as the build lays them out) runs it and skips the questions. */
const TRY: { key: string; say: string; name: string; icon: string; dye: string; blocks: number }[] = [
  { key: 'calories', say: 'Track what I eat, calories and protein', name: 'Calories', icon: 'flame', dye: 'apricot', blocks: 5 },
  { key: 'running', say: "I'm running a 10K on Sat 12 Dec. Track my runs", name: 'Running', icon: 'shoe', dye: 'sage', blocks: 6 },
  { key: 'cycle', say: 'Track my cycle and keep it private', name: 'Cycle', icon: 'drop', dye: 'pear', blocks: 2 },
];
/** The one frame around the preview: chalk while Clair cuts it, basted while it waits for Make it, stitched once it is made. */
type Frame = 'chalk' | 'basted' | 'stitched';
/** Where the screen is. reading: Clair reads the sentence; thinking: Clair works on the answers. */
type Stage = 'describe' | 'reading' | 'questions' | 'thinking' | 'plan' | 'preview' | 'expired';
/** The steps Back walks through, one history entry each (`/build?step=…`), so the phone's back works too. */
type Place = 'describe' | 'questions' | 'plan' | 'preview';
const ORDER: Place[] = ['describe', 'questions', 'plan', 'preview'];
const placeOf = (s: Stage): Place => (s === 'describe' || s === 'plan' || s === 'preview' ? s : 'questions');
/** A question card, whichever form it came in (clair-agent.md §2). */
type Card = { id: string; questions: AskQuestion[]; single: boolean; expires_at?: string };
const toCard = (q: Question): Card => ('questions' in q
  ? { id: q.id, questions: q.questions, single: false, expires_at: q.expires_at }
  : { id: q.id, single: true, expires_at: q.expires_at, questions: [{ id: q.id, header: 'Clair asks', text: q.text, multi: q.multi, options: q.options.map((o) => ({ label: o.label, description: o.hint })) }] });
const expired = (c: Card | null) => !!c?.expires_at && Date.parse(c.expires_at) <= Date.now();

/**
 * Build an app from one sentence (US-6; clair-agent.md §7 rule 7, §11, §12.11). Describe →
 * Clair asks a few questions in one card → the plan in plain words → Build it (chalk, then
 * basted pieces) → Make it (the sew finale) → Home, where the new patch sews in. Nothing is
 * saved before Make it. Choreography from design/prototypes/quilt-flows.html b1/b2/b5 and the
 * motion catalogue's "Building an app" rows; steps crossfade (out 140, in 220).
 */
export function Build() {
  const draft = useStore((s) => s.buildDraft);
  const credits = useStore((s) => s.me?.credits.left);
  const apps = useStore((s) => s.home?.apps) ?? [];
  const now = useStore((s) => s.me?.server_now) ?? '';
  const nav = useNavigate();
  const [params] = useSearchParams();
  const urlPlace = (ORDER.find((p) => p === params.get('step')) ?? 'describe') as Place;

  const [stage, setStageS] = useState<Stage>(draft ? 'preview' : 'describe');
  const stageRef = useRef<Stage>(stage);
  const setStage = (s: Stage) => { stageRef.current = s; setStageS(s); };
  const [sentence, setSentence] = useState(draft?.sentence ?? '');
  const [card, setCardS] = useState<Card | null>(null);
  const cardRef = useRef<Card | null>(null);
  const setCard = (c: Card | null) => { cardRef.current = c; setCardS(c); };
  const [picks, setPicks] = useState<Picks>({});
  const [plan, setPlanS] = useState<Plan | null>(null);
  const planRef = useRef<Plan | null>(null);
  const setPlan = (p: Plan | null) => { planRef.current = p; setPlanS(p); };
  const got = useRef<ChangeSet | null>(draft?.cs ?? null); // the build proposal, held until Build it on the plan
  const [cs, setCs] = useState<ChangeSet | null>(draft?.cs ?? null); // the one the preview shows
  const [frame, setFrame] = useState<Frame>('chalk');
  const [pvTab, setPvTab] = useState(''); // the tab the preview shows (switching it navigates nowhere)
  const [status, setStatus] = useState('Reading your sentence…');
  const [expr, setExpr] = useState<Expr>('working');
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<{ text: string; on: 'sentence' | 'answer' } | null>(null);
  const [making, setMaking] = useState(false);
  const [made, setMade] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null); // Clair answered in words: nothing to build
  const lift = useRef<DOMRect | null>(null);
  const runId = useRef(0); // the Clair run being listened to
  const streaming = useRef(false); // that run has not sent `done` yet
  const pass = useRef(0); // the preview being animated
  const sent = useRef<{ key: string; body: Answer } | null>(null);
  const quick = useRef(false); // started from a pattern tile: the questions are skipped for you, on to the preview
  const at = useRef<Place>('describe'); // the place the URL says, as this screen last set it
  const depth = useRef(0); // history entries this screen pushed
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => { if (draft) setBuildDraft(null); }, [draft]);
  // the Clair sheet hands a sentence over when Clair needs to ask first: start it here, where the questions can be shown
  const handed = useRef(false);
  useEffect(() => {
    const say = params.get('say');
    if (!say || draft) return;
    // one tick later, so the step-sync effect below has run once against the plain /build URL
    const t = setTimeout(() => { if (handed.current) return; handed.current = true; start(say); }, 0);
    return () => clearTimeout(t);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => { runId.current++; pass.current++; }, []);

  // ---- steps and Back: every step is a history entry, so the phone's back walks back through them
  function push(p: Place) {
    if (at.current === p) return;
    at.current = p; depth.current++;
    nav(urlOf(p));
  }
  /** Crossfade between steps: the old one fades out (140), the new one fades in (220, .bq-stage). */
  async function swap(apply: () => void) {
    const el = root.current?.querySelector<HTMLElement>('.bq-stage');
    if (el && !RM()) {
      const a = el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: T.stateOut, easing: EASE, fill: 'forwards' });
      await a.finished.catch(() => {});
      apply();
      requestAnimationFrame(() => a.cancel());
    } else apply();
  }
  /** Show a place, when what it needs is still here. The old step fades out before anything in it changes. */
  function arrive(p: Place): boolean {
    const clear = () => { setCs(null); setFrame('chalk'); setReady(false); setError(null); };
    if (p === 'describe') {
      runId.current++; pass.current++; quick.current = false;
      dismissHeld();
      void swap(() => { clear(); setCard(null); setPlan(null); setAnswer(null); setStage('describe'); });
      return true;
    }
    if (p === 'questions') {
      if (!cardRef.current) return false;
      pass.current++;
      if (stageRef.current === 'thinking') runId.current++; // Back while Clair works on the answers: stop listening
      void swap(() => { clear(); setStage(expired(cardRef.current) ? 'expired' : 'questions'); });
      return true;
    }
    if (p === 'plan') {
      if (!planRef.current) return false;
      pass.current++;
      void swap(() => { clear(); setStage('plan'); });
      return true;
    }
    if (!planRef.current && !got.current) return false;
    enterPreview();
    return true;
  }
  const urlOf = (p: Place) => (p === 'describe' ? '/build' : `/build?step=${p}`);
  // the phone's back and forward land here
  useEffect(() => {
    if (urlPlace === at.current || making) return; // the sew finale can't be stepped out of
    const backwards = ORDER.indexOf(urlPlace) < ORDER.indexOf(at.current);
    let p: Place | undefined = urlPlace;
    while (p && !arrive(p)) p = backwards ? ORDER[ORDER.indexOf(p) - 1] : undefined; // a step with nothing left to show is skipped
    if (!p) { nav(urlOf(at.current), { replace: true }); return; }
    if (p !== urlPlace) nav(urlOf(p), { replace: true });
    at.current = p; depth.current = Math.max(0, depth.current + (backwards ? -1 : 1));
  }, [urlPlace]); // eslint-disable-line react-hooks/exhaustive-deps

  function back() {
    if (making) return;
    if (stageRef.current === 'describe' || (stageRef.current === 'preview' && !planRef.current && !cardRef.current)) return leave();
    if (stageRef.current === 'thinking') { arrive('questions'); return; } // same place: stop and show the questions again
    if (depth.current > 0) { nav(-1); return; }
    const prev = ORDER[Math.max(0, ORDER.indexOf(placeOf(stageRef.current)) - 1)];
    if (arrive(prev)) at.current = prev; else leave();
  }

  // ---- 1. describe → read: the brief lifts into the chalk card (catalogue N6), then Clair asks
  function start(text: string, via?: { from: DOMRect; quick: boolean }) {
    const t = text.trim();
    if (!t) return;
    lift.current = via?.from ?? document.querySelector('.describe-box')?.getBoundingClientRect() ?? null;
    quick.current = !!via?.quick;
    dismissHeld();
    setSentence(t); setError(null); setCs(null); setReady(false); setFrame('chalk'); setAnswer(null); setCard(null); setPicks({}); setPlan(null);
    sent.current = null; pass.current++;
    setExpr('working'); setStatus('Reading your sentence…');
    setStage('reading');
    push('questions');
    listen({ text: t, run_id: crypto.randomUUID() }, 'sentence');
  }

  // ---- 2. the answers: the plan comes back first, then the proposal it describes (held for Build it)
  function sendAnswers(skip = false, auto = false) {
    const c = cardRef.current;
    if (!c) return;
    quick.current = auto; // a pattern tile answers for you once; picking by hand takes the plan step back
    if (expired(c)) { void swap(() => setStage('expired')); return; }
    const body: Answer = skip ? { question_id: c.id, skip: true }
      : c.single ? { question_id: c.id, ...toChoice(c.questions[0], picks[c.questions[0].id]) }
      : { question_id: c.id, answers: Object.fromEntries(c.questions.map((q) => [q.id, toChoice(q, picks[q.id])])) };
    const key = JSON.stringify(body);
    // unchanged: the plan in hand still stands (its proposal is here, or still on its way on the same run)
    if (sent.current?.key === key && planRef.current && (got.current || streaming.current)) { push('plan'); void swap(() => setStage('plan')); return; }
    sent.current = { key, body };
    got.current = null; // the server replaces the basted card in place (same id); the new one comes with the new plan
    setPlan(null); setError(null); setAnswer(null);
    setStatus(skip ? 'Picking for you…' : 'Reading your answers…');
    if (auto) setStage('thinking'); // Reading and Thinking look the same: nothing to fade
    else void swap(() => setStage('thinking'));
    listen({ answer: body, run_id: crypto.randomUUID() }, 'answer');
  }

  function listen(body: Parameters<typeof clairTurn>[0], on: 'sentence' | 'answer') {
    const run = ++runId.current;
    let said = '', gotCard = false, gotQuestion = false;
    streaming.current = true;
    void clairTurn(body, (e: ClairEvent) => {
      if (run !== runId.current) return;
      if (e.event === 'done') streaming.current = false;
      switch (e.event) {
        case 'status': setStatus(e.data.text); break;
        case 'question': {
          gotQuestion = true;
          const c = toCard(e.data);
          setCard(c);
          setPicks((old) => Object.fromEntries(Object.entries(old).filter(([k]) => c.questions.some((q) => q.id === k)))); // answers to the same questions are kept
          if (quick.current && on === 'sentence') { sendAnswers(true, true); break; } // a pattern tile: "Skip, use your best guess", no card shown
          if (stageRef.current === 'reading' || stageRef.current === 'thinking') void swap(() => setStage('questions'));
          break;
        }
        case 'plan':
          setPlan(e.data);
          if (stageRef.current === 'reading' || stageRef.current === 'thinking') {
            if (quick.current) { quick.current = false; push('preview'); enterPreview(); } // a pattern tile skips the plan card too
            else { push('plan'); void swap(() => setStage('plan')); }
          }
          break;
        case 'proposal':
          if (e.data.change_set.kind !== 'app') break;
          gotCard = true; got.current = e.data.change_set;
          if (stageRef.current === 'preview') setCs(e.data.change_set); // Build it was tapped before it landed
          else if (!planRef.current && (stageRef.current === 'reading' || stageRef.current === 'thinking')) { quick.current = false; push('preview'); enterPreview(); } // no plan: straight to the preview
          break;
        case 'text_delta': said += e.data.text; setAnswer(said); break;
        case 'done':
          void loadMe();
          if (e.data.status === 'error') {
            quick.current = false;
            if (on === 'answer' && expired(cardRef.current)) { void swap(() => setStage('expired')); break; }
            setError({ text: e.data.message ?? 'Clair could not build that. Nothing was saved.', on });
            if (stageRef.current === 'preview') setExpr('oops');
          } else if (said && !gotCard && !gotQuestion) { setStatus(said); } // the chalk goes: nothing is being built
          break;
      }
    });
  }

  // ---- 3. Build it on the plan: the preview, chalk pieces basting in
  function enterPreview() {
    pass.current++;
    setFrame('chalk'); setReady(false); setMade(false); setExpr('working'); setError(null);
    if (got.current) setStatus('Cutting the pieces…');
    void swap(() => { setStage('preview'); setCs(got.current); });
  }

  useEffect(() => {
    if (stage === 'describe') return;
    const box = root.current?.querySelector<HTMLElement>('.brief');
    const say = box?.querySelector<HTMLElement>('.say'), ol = box?.querySelector<SVGElement>('.ol');
    if (!box || !say || !ol) return;
    const from = lift.current;
    lift.current = null;
    if (RM() || !from) { box.animate([{ opacity: 0 }, { opacity: 1 }], { duration: T.fb, easing: EASE }); return; }
    const to = say.getBoundingClientRect();
    ol.style.clipPath = 'inset(0 100% 0 0)';
    say.animate([{ transform: `translate(${from.left - to.left}px, ${from.top - to.top}px)` }, { transform: 'none' }], { duration: T.layout, easing: EASE })
      .finished.then(() => {
        ol.style.clipPath = '';
        ol.animate([{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: T.layout, easing: EASE });
      }, () => {});
  }, [stage === 'describe']); // eslint-disable-line react-hooks/exhaustive-deps

  // the frame: chalk while the proposal is still on its way; once it lands Clair checks the pieces (one per tab), then the frame bastes and waits for Make it
  useEffect(() => {
    if (!cs?.preview) return;
    const p = pass.current;
    const tabs = cs.preview.spec.tabs;
    (async () => {
      setFrame('chalk'); setPvTab(tabs[0]?.id ?? '');
      for (let i = 0; i < tabs.length; i++) {
        await sleep(RM() ? 0 : 240);
        if (p !== pass.current) return;
        setStatus(`Checked piece ${i + 1} of ${tabs.length}`);
        await sleep(RM() ? 0 : 380);
      }
      if (p !== pass.current) return;
      setExpr('waiting'); setStatus([cs.title, cs.summary].filter(Boolean).join(' ')); setFrame('basted'); setReady(true);
    })();
  }, [cs]);

  // the chalk outline wipes in left to right as the frame appears (catalogue: "Chalk outline", 350)
  useEffect(() => {
    root.current?.querySelectorAll<SVGElement>('.piece:not(.drawn) > .ol').forEach((ol) => {
      ol.parentElement!.classList.add('drawn');
      if (!RM()) ol.animate([{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: T.layout, easing: EASE });
    });
  }, [stage, frame]);

  // ---- 4. Make it: the sew finale (catalogue: "Sew finale", ~1.1 s)
  async function make() {
    if (!cs || making) return;
    setMaking(true);
    const run = ++runId.current, alive = () => run === runId.current;
    const call = request<CommandResult>('POST', `/change-sets/${cs.id}/confirm`).then((r) => ({ ok: true as const, r }), (e) => ({ ok: false as const, e }));
    // stitch-in: the basting tightens into a seam
    setFrame('stitched');
    await sleep(RM() ? 0 : T.state);
    // connect pull: a thread from each connection into the new patch
    const shell = document.querySelector<HTMLElement>('.frame')!;
    const tile = root.current?.querySelector('.ptitle .dye');
    const srcs = [...(root.current?.querySelectorAll('.make [data-thread-source]') ?? [])].filter((e) => e.getAttribute('data-thread-source') !== cs.preview?.spec.key);
    if (tile && MOTION === 'threads' && srcs.length) await threadPull({ frame: shell, pairs: srcs.map((from) => ({ from, to: tile, color: dyeOf(from) })), onLand: () => {}, alive });
    if (tile && MOTION === 'stitch') await stitchIn({ els: [{ el: tile, color: dyeOf(tile) }], onLand: () => {}, alive });
    const res = await call;
    if (!alive()) return;
    if (!res.ok) {
      setFrame('basted');
      setExpr('oops'); setStatus(errorText(res.e)); setMaking(false);
      return;
    }
    // dye sweep, then the label stamps on
    const dye = root.current?.querySelector<HTMLElement>('.ptitle .dye');
    if (dye && !RM()) await dye.animate([{ clipPath: 'circle(0% at 50% 50%)' }, { clipPath: 'circle(150% at 50% 50%)' }], { duration: T.layout, easing: EASE }).finished;
    root.current?.querySelector('.qlabel')?.animate(
      [{ opacity: 0, transform: RM() ? 'rotate(-1.5deg)' : 'rotate(-6deg) scale(1.15)' }, { opacity: 1, transform: 'rotate(-1.5deg)' }],
      { duration: RM() ? T.fb : T.state, easing: EASE, fill: 'forwards' });
    setMade(true);
    await sleep(60);
    setExpr('stitched'); setStatus("Stitched in. It's in your apps.");
    await sleep(RM() ? 200 : 900);
    if (!alive()) return;
    const key = cs.preview!.spec.key, name = cs.preview!.spec.name;
    sew(key);
    await afterCommand(res.r);
    nav('/');
    setTimeout(() => toast(`Added ${name} to your apps.`, { label: 'Undo', run: async () => {
      try { await afterCommand(await request<CommandResult>('POST', `/change-sets/${cs.id}/undo`)); } catch (x) { toast(errorText(x)); }
    } }), (RM() ? 0 : T.layout) + 700); // after the patch has sewn on, so the toast never covers it
  }

  /** A proposal that will not be made is dismissed (nothing was saved either way). */
  function dismissHeld() {
    const c = got.current;
    got.current = null;
    if (c && !made && c.status === 'basted') void request('POST', `/change-sets/${c.id}/dismiss`).catch(() => { /* nothing was saved */ });
  }
  function leave() {
    runId.current++; pass.current++;
    dismissHeld();
    nav('/');
  }

  const preview: AppResponse | undefined = stage === 'preview' ? cs?.preview : undefined;
  const spec = preview?.spec;
  const tabId = spec ? (spec.tabs.some((t) => t.id === pvTab) ? pvTab : spec.tabs[0]?.id ?? '') : '';
  // Clair's line: the server's status while it works; fixed words while it waits on you
  const line = error?.text ?? (stage === 'plan' ? "Here's what I'll build." : stage === 'expired' ? 'Those questions waited more than a day.' : status);
  const face: Expr = error ? 'oops'
    : stage === 'reading' || stage === 'thinking' ? (answer ? 'waiting' : 'working')
    : stage === 'questions' || stage === 'plan' || stage === 'expired' ? 'waiting'
    : expr;
  const dock = stage === 'preview' && ready && !!cs && !answer; // the pinned Make it row

  // header (boards Build, Preview): back chevron, the title centred, a 44 px spacer to keep it centred
  const head = (
    <header className="top-row bq-top">
      <button className="round back" onClick={back} disabled={making} aria-label={stage === 'describe' ? 'Back to Home' : 'Back'}><Icon name="back" /></button>
      <b className="bq-title" {...(stage === 'describe' || stage === 'preview' ? {} : { role: 'heading', 'aria-level': 1 })}>{stage === 'preview' ? 'Preview' : 'New app'}</b>
      <span className="bq-spacer" aria-hidden="true" />
    </header>
  );

  if (stage === 'describe') {
    const open = TRY.filter((t) => !apps.some((a) => a.key === t.key));
    return (
      <div className="screen build" ref={root}>
        {head}
        <div className="bq-stage">
          <form className="describe-form" onSubmit={(e) => { e.preventDefault(); start(sentence); }}>
            <div className="bq-ask"><Spool expr="hello" size={44} /><h1>What do you want to keep track of?</h1></div>
            <div className="bq-say">
              <label htmlFor="say">Say it the way you'd tell a friend</label>
              <textarea id="say" className="describe-box" rows={3} value={sentence} placeholder="Track my subscriptions and warn me before they renew" enterKeyHint="go"
                onChange={(e) => setSentence(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); start(sentence); } }} />
            </div>
            {open.length > 0 && (
              <div className="chips scroll" role="group" aria-label="Suggestions">
                {open.map((t) => <button type="button" key={t.key} className="chip" onClick={() => setSentence(t.say)}>{t.say}</button>)}
              </div>
            )}
            <button className="cta wide" disabled={!sentence.trim()}>Build it</button>
          </form>
          {open.length > 0 ? (
            <section className="bq-from" aria-label="Start from one of these">
              <div className="sec"><span>Or start from one of these</span><span className="meta">Skips to preview</span></div>
              <div className="bq-tiles">
                {open.map((t) => (
                  <button key={t.key} className="bq-tile" data-dye={t.dye} onClick={(e) => start(t.say, { from: e.currentTarget.getBoundingClientRect(), quick: true })}>
                    <Icon name={t.icon} size={18} />
                    <span className="nm"><b>{t.name}</b><span>{t.blocks} blocks</span></span>
                  </button>
                ))}
              </div>
            </section>
          ) : <p className="muted small">Calories, Running and Cycle are already in your apps. The recorded builds start from the 8-app account (demo menu → 8 apps).</p>}
          <p className="muted small">Clair asks a few questions and shows you the plan first. A build uses 10 credits; nothing is added until you tap Make it.</p>
        </div>
      </div>
    );
  }

  const extra = cs?.lines.filter((l) => !(l.apps.length === 1 && l.apps[0] === spec?.key)) ?? []; // what else Make it changes, beside the new app
  return (
    <div className={`screen build${dock ? ' has-dock' : ''}`} ref={root} data-dye={spec?.dye}>
      {head}
      <div className="chalk brief"><ChalkOl /><p className="say" title={sentence}>{/[.!?]$/.test(sentence) ? sentence : sentence + '.'}</p></div>
      <p className="clair-line bq-line" role="status"><Spool expr={face} size={30} /><span>{line}</span></p>

      <div className="bq-stage" key={stage}>
        {stage === 'questions' && card && (
          <QuestionCard questions={card.questions} picks={picks} onPicks={setPicks} onContinue={() => sendAnswers()} onSkip={() => sendAnswers(true)} />
        )}

        {stage === 'plan' && plan && (
          <PlanCard plan={plan} apps={apps} onBuild={() => { push('preview'); enterPreview(); }} onChange={card ? back : undefined} />
        )}

        {stage === 'expired' && (
          <section className="card bq-expired">
            <h2>Still want to build this?</h2>
            <p className="muted small">Your sentence is kept. Clair asks again from the start.</p>
            <span className="btns"><button className="cta" onClick={() => start(sentence)}>Build it</button><Link to="/" className="ghost">Not now</Link></span>
          </section>
        )}

        {stage === 'preview' && !answer && (
          <>
            {spec && (
              <div className="ptitle arrive" data-dye={spec.dye}>
                <span className="dye" data-thread-target={spec.key}><Icon name={spec.icon} size={18} /></span>
                <h1>{spec.name}</h1>
                {spec.private && <span className="pill soft"><Icon name="lock" size={12} />&nbsp;Private</span>}
                <span className="qlabel" style={{ opacity: 0 }}>pieced by clair</span>
              </div>
            )}
            {spec && <p className="bq-note muted small">Example rows · cleared when you make it</p>}
            <section className={`piece pv ${frame === 'chalk' ? 'is-chalk' : `st ${frame === 'basted' ? 'basted' : ''}`}`} aria-label={spec ? `${spec.name}, a preview` : 'The app Clair is cutting'}>
              {frame === 'chalk' ? <ChalkOl r={22} /> : <Edge r={15} />}
              {preview && spec && (
                <div className="pbody arrive">
                  {spec.tabs.length > 1 && <PvTabs tabs={spec.tabs} tab={tabId} set={setPvTab} name={spec.name} />}
                  <AppView key={tabId} app={preview} tab={tabId} apps={apps} now={preview.server_now ?? now} tabbed={spec.tabs.length > 1} />
                </div>
              )}
            </section>
            {ready && extra.length > 0 && (
              <div className="make arrive">
                <span className="sec"><span>Also changes</span></span>
                {extra.map((l, i) => {
                  const k = l.apps[0];
                  const a = apps.find((x) => x.key === k);
                  return (
                    <span className="line" key={i} data-dye={a?.dye}>
                      <span className="tile-ico" data-thread-source={k}><Icon name={a?.icon ?? 'app'} size={16} /></span>
                      <span className="txt"><b>{listNames(l.apps.map((x) => apps.find((y) => y.key === x)?.name ?? x))}</b> {l.what}</span>
                    </span>
                  );
                })}
              </div>
            )}
          </>
        )}

        {error && (
          <span className="btns bq-retry">
            {error.on === 'answer' && sent.current
              ? <><button className="cta" onClick={() => { const b = sent.current!.body; sent.current = null; b.skip ? sendAnswers(true) : sendAnswers(); }}>Try again</button><button className="ghost" onClick={() => arrive('questions')}>Change answers</button></>
              : <><button className="cta" onClick={() => start(sentence)}>Try again</button><Link to="/" className="ghost">Not now</Link></>}
          </span>
        )}
        {answer && !got.current && !card && stage === 'reading' && (
          <span className="btns arrive">
            <button className="cta" onClick={back}>Describe another app</button>
            <Link to="/" className="ghost">Home</Link>
          </span>
        )}

        {dock && cs && (
          // pinned like Log a set's actions (board Preview): the meta line over the pair, secondary then Make it
          <div className="bq-dock arrive">
            <p className="bq-meta" data-left={credits}>Uses 10 credits. Nothing is added until you tap Make it.</p>
            <div className="bq-pair">
              <button className="ghost" onClick={back} disabled={making}>{plan || card ? 'Change answers' : 'Not now'}</button>
              <button className="cta" onClick={make} disabled={making}>{cs.actions.primary}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/** The preview's tab strip: the app's own tabs, switched in place (nothing navigates). Same keys as AppScreen's. */
function PvTabs({ tabs, tab, set, name }: { tabs: { id: string; title: string }[]; tab: string; set: (id: string) => void; name: string }) {
  const list = useRef<HTMLDivElement>(null);
  return (
    <div className="tabs" role="tablist" aria-label={`${name} tabs`} ref={list} onKeyDown={(e) => {
      const at = tabs.findIndex((t) => t.id === tab), n = tabs.length;
      const to = e.key === 'ArrowRight' ? (at + 1) % n : e.key === 'ArrowLeft' ? (at - 1 + n) % n : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : -1;
      if (to < 0 || at < 0) return;
      e.preventDefault();
      set(tabs[to].id);
      list.current?.querySelectorAll<HTMLElement>('[role="tab"]')[to]?.focus();
    }}>
      {tabs.map((t) => (
        <button key={t.id} id={`tab-${t.id}`} role="tab" className="tab" aria-selected={t.id === tab} aria-controls={`panel-${t.id}`} tabIndex={t.id === tab ? 0 : -1}
          onClick={() => set(t.id)}>{t.title}</button>
      ))}
    </div>
  );
}
