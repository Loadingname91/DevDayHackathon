import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clairTurn } from '../api/client';
import type { ChangeSet, ClairEvent, Offer, TurnRequest } from '../api/types';
import { EASE, RM, STAGGER, T } from '../lib/motion';
import { getState, loadMe, openClair, setBuildDraft, useStore } from '../lib/store';
import { beginTalk, canSpeak, finishTalk, getTalk, NOT_HEARD, onVoiceOutcome, resetTalk, speak, toggleMuted, toggleScripted, TYPE_INSTEAD, useLongPress, useMuted, useTalk } from '../lib/voice';
import { Bold } from './Bold';
import { Icon } from './Icon';
import { Glyph, ListeningPanel } from './ListeningPanel';
import { OfferCard } from './OfferCard';
import { ProposalCard } from './ProposalCard';
import { Sheet } from './Sheet';
import { Spool, type Expr } from './Spool';

type Turn = {
  said: string;
  status: string | null; // the status line is the only loading UI
  understood: string | null;
  cards: ChangeSet[];
  offer: Offer | null;
  answer: string;
  sources: string[];
  done: boolean;
  error: string | null;
  slow: boolean; // no card after 12 s: "Use sample"
  stitched: boolean;
  /** spoken to Clair: its answer is read aloud (clair-agent.md §4) */
  voice: boolean;
};
const blank = (said: string, voice = false): Turn => ({ said, status: 'Reading…', understood: null, cards: [], offer: null, answer: '', sources: [], done: false, error: null, slow: false, stitched: false, voice });
/** Board ClairSheet, "Try this evening": the three sentences the demo answers. */
const TRY = [
  { text: 'Spent $12 on lunch', meta: 'Log it · Budget', icon: 'receipt' },
  { text: 'Plan my training for next week', meta: 'Plan · Workout and Calendar', icon: 'dumbbell' },
  { text: 'Am I due for any appointments?', meta: 'Check · Calendar', icon: 'calendar' },
];

/** Crossfade + height (catalogue: "State swap"): the content's height animates over 220 ms when it changes.
 *  A phase can change inside those 220 ms: the new animation starts from the height on screen, not from the last target. */
function useAutoHeight(ref: React.RefObject<HTMLElement | null>, key: unknown) {
  const last = useRef(0);
  const anim = useRef<Animation | null>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const live = anim.current ? el.offsetHeight : last.current; // read before cancelling: with a run in flight this is the animated height
    anim.current?.cancel(); anim.current = null;
    const h = el.offsetHeight; // the natural height of the new content
    if (last.current && Math.abs(h - live) > 2 && !RM()) {
      const a = el.animate([{ height: `${live}px`, overflow: 'hidden' }, { height: `${h}px`, overflow: 'hidden' }], { duration: T.state, easing: EASE });
      anim.current = a;
      a.onfinish = a.oncancel = () => { if (anim.current === a) anim.current = null; };
    }
    last.current = h;
  }, [key, ref]);
}

const fine = () => matchMedia('(pointer: fine)').matches;

/**
 * Clair: type a sentence, watch the status line, get a basted card. Floats above the bar so threads land on the pins.
 * Boards ClairSheet (start: header, the field, "Try this evening"), ClairResult (a capture's basted cards)
 * and ClairAsk (answers); CSS in styles/clair.css. The field sits under the header until a turn runs,
 * then pins to the bottom for a follow-up.
 */
export function ClairSheet() {
  const open = useStore((s) => s.clairOpen);
  const apps = useStore((s) => s.home?.apps) ?? [];
  const credits = useStore((s) => s.me?.credits.left);
  const [text, setText] = useState('');
  const [note, setNote] = useState<string | null>(null); // one plain line under the field: what the microphone did
  const [turn, setTurn] = useState<Turn | null>(null);
  const talk = useTalk();
  const talking = talk.phase !== 'idle';
  const muted = useMuted();
  const abort = useRef<AbortController | null>(null);
  const slowTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const input = useRef<HTMLTextAreaElement>(null);
  const refocus = useRef(false); // the field moves to the bottom when a turn starts; keep the caret on a laptop
  const content = useRef<HTMLDivElement>(null);
  const nav = useNavigate();
  const close = useCallback(() => {
    // closing mid-talk: a hold leaves showing its state (resetTalk runs once the sheet has gone), anything else just stops
    const t = getTalk();
    if (t.phase === 'listening' || t.phase === 'cancel') { if (t.mode === 'hold') { finishTalk(true); return; } resetTalk(); } else if (t.phase === 'finishing') resetTalk();
    openClair(false);
  }, []);
  useEffect(() => () => { abort.current?.abort(); clearTimeout(slowTimer.current); }, []);
  // never auto-focus on touch: the keyboard would cover the suggestions (fixspec §D). On a laptop the field has the
  // caret as the sheet starts to rise, so the first keystroke is never lost.
  const opened = () => { if (fine() && getTalk().phase === 'idle') input.current?.focus({ preventScroll: true }); };
  const started = !!turn;
  useEffect(() => {
    if (refocus.current && fine()) input.current?.focus({ preventScroll: true });
    refocus.current = false;
  }, [started]);
  const phase = talking ? 'talk' : !turn ? 'start' : `${turn.cards.length}-${!!turn.understood}-${!!turn.answer}-${turn.done}-${!!turn.error}-${turn.slow}-${turn.stitched}`;
  useAutoHeight(content, phase);
  // a card arrives with its buttons under the pinned field's fade: bring the action row fully into view,
  // once the content has settled (each phase change runs its own 220 ms height animation)
  const cardCount = turn?.cards.length ?? 0;
  useEffect(() => {
    if (!cardCount) return;
    const t = setTimeout(() => {
      const rows = content.current?.querySelectorAll<HTMLElement>('.pcard .btn-area');
      const btn = rows?.[rows.length - 1], scroller = content.current?.closest<HTMLElement>('.body');
      if (!btn || !scroller) return;
      const over = btn.getBoundingClientRect().bottom - (scroller.getBoundingClientRect().bottom - 32); // 24 px fade + 8 padding
      if (over > 0) scroller.scrollTo({ top: scroller.scrollTop + over, behavior: RM() ? 'auto' : 'smooth' });
    }, RM() ? 0 : T.state + 40); // after the card has arrived and the height has settled
    return () => clearTimeout(t);
  }, [cardCount, phase]);

  const onExited = () => {
    if (getTalk().phase === 'leaving') resetTalk(); // a cancelled hold: the sheet has gone, so its Talk state can go
    // a finished turn starts fresh next time; one still waiting for OK stays
    if (turn && (turn.done || turn.error) && !turn.cards.some((c) => c.status === 'basted') || turn?.stitched) setTurn(null);
  };

  function send(body: TurnRequest, said: string) {
    const voice = 'voice' in body && !!body.voice;
    abort.current?.abort();
    const ac = new AbortController();
    abort.current = ac;
    refocus.current = !turn && document.activeElement === input.current;
    setText(''); setNote(null);
    setTurn(blank(said, voice));
    clearTimeout(slowTimer.current);
    slowTimer.current = setTimeout(() => setTurn((t) => (t && !t.cards.length && !t.done ? { ...t, slow: true } : t)), T.slow);
    const on = (e: ClairEvent) => {
      if (ac.signal.aborted) return;
      setTurn((t) => {
        if (!t) return t;
        switch (e.event) {
          case 'status': return { ...t, status: e.data.text };
          case 'understood': return { ...t, understood: e.data.summary };
          case 'proposal': {
            const i = t.cards.findIndex((c) => c.id === e.data.change_set.id); // the same id replaces the card
            const cards = i < 0 ? [...t.cards, e.data.change_set] : t.cards.map((c, k) => (k === i ? e.data.change_set : c));
            return { ...t, cards, status: null, slow: false };
          }
          case 'offer': return { ...t, offer: e.data }; // held until the card is confirmed
          case 'text_delta': return { ...t, answer: t.answer + e.data.text, status: null };
          case 'done':
            return { ...t, done: true, status: null, sources: e.data.sources ?? [], slow: e.data.status === 'error' ? true : t.slow,
              error: e.data.status === 'error' ? (e.data.message ?? 'Clair could not finish that. Nothing was changed.') : null };
          default: return t;
        }
      });
      if (e.event === 'done') {
        clearTimeout(slowTimer.current); void loadMe();
        if (voice && e.data.spoken && getState().clairOpen) speak(e.data.spoken); // Clair answers aloud only when Sam talked first
      }
      // Clair needs to ask before it builds: the Build screen shows the questions and the plan, so hand the sentence over
      if (e.event === 'question' && 'questions' in e.data) {
        ac.abort(); clearTimeout(slowTimer.current);
        setTurn(null); openClair(false);
        nav(`/build?say=${encodeURIComponent(said)}`);
      }
    };
    void clairTurn({ ...body, run_id: crypto.randomUUID() }, on, ac.signal);
  }
  const submit = () => { const t = text.trim(); if (t) send({ text: t }, t); };

  // what a finished talk asks of the sheet (lib/voice.ts): send it, hold it for Edit, say nothing was heard, or type instead
  useEffect(() => onVoiceOutcome((o) => {
    switch (o.kind) {
      case 'send': send({ transcript: o.text, voice: true }, o.text); break;
      case 'edit': setText(o.text); setNote('Is that right? Edit it, then send.'); setTimeout(() => input.current?.focus({ preventScroll: true }), 0); break;
      case 'none': setNote(NOT_HEARD); break;
      case 'unavailable': setNote(TYPE_INSTEAD); setTimeout(() => input.current?.focus({ preventScroll: true }), 0); break;
      case 'cancel': if (o.mode === 'hold') openClair(false); break; // the sheet the hold opened leaves; no request was made
    }
  }));
  // On stage (clair-agent.md §4): a long press on the sheet header switches the scripted transcript on or off. Hidden by design.
  const headPress = useLongPress(() => { toggleScripted(); });

  const expr: Expr = !turn ? 'hello'
    : turn.error ? 'oops'
    : turn.stitched ? 'stitched'
    : turn.cards.length ? 'waiting'
    : turn.done ? 'stitched'
    : 'working';

  const field = (
    <div className={`field cs-field${turn ? ' compact' : ''}`}>
      <textarea ref={input} rows={turn ? 1 : 2} value={text} aria-label="Tell Clair anything" enterKeyHint="send"
        placeholder={turn ? 'Add more or ask…' : 'Spent $12 on lunch, gym tomorrow 6 pm…'}
        onChange={(e) => { setText(e.target.value); setNote(null); }}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }} />
      <button className="send" onMouseDown={(e) => e.preventDefault()} onClick={submit} disabled={!text.trim()} aria-label="Send to Clair"><Icon name="up" size={20} sw={1.8} /></button>
    </div>
  );

  /** "From" + a chip per app Clair read; each opens its app. */
  const sources = (cls: string) => turn && turn.done && turn.sources.length > 0 && (
    <span className={`cs-from ${cls}`} aria-label="Read from">
      <span className="cs-from-l">From</span>
      {turn.sources.map((k) => {
        const a = apps.find((x) => x.key === k);
        return (
          <button key={k} className="chip" data-dye={a?.dye} onClick={() => { openClair(false); nav(`/a/${k}`); }}>
            <i className="dyedot" aria-hidden="true" />{a?.name ?? k}
          </button>
        );
      })}
    </span>
  );
  const waitingOn = turn && !turn.stitched ? new Set(turn.cards.filter((c) => c.status === 'basted').flatMap((c) => c.targets)).size : 0;
  const line = turn && (turn.status ?? turn.understood ?? (turn.error ? 'That did not work.' : turn.cards.length ? 'Needs your OK.' : ''));

  const noteEl = note && <p className="cs-note" role="status">{note}</p>;
  const mute = turn?.voice && canSpeak() && (
    <button type="button" className="cs-mute" aria-pressed={muted} onClick={toggleMuted} aria-label={muted ? 'Unmute Clair' : 'Mute Clair'}>
      <Glyph name={muted ? 'speaker-off' : 'speaker'} size={20} />
    </button>
  );

  return (
    <Sheet open={open} onClose={close} onExited={onExited} onOpened={opened} noClose keepBar label="Clair" footer={turn && !talking ? <>{noteEl}{field}</> : undefined}>
      <div ref={content} className={`cs${turn && !talking ? ' cs-turn' : ''}`}>
        {talking ? <ListeningPanel head={headPress} /> : (<>
        <div className="cs-head" {...headPress}>
          {turn
            ? <span className="cs-mark" aria-hidden="true"><Icon name="spool" size={20} sw={1.8} /></span>
            : <Spool expr={expr} size={44} />}
          <span className="cs-titles">
            <h2>{turn ? 'Clair' : 'Tell Clair anything'}</h2>
            {!turn && <span className="cs-sub">Type anything. It can land in several apps.</span>}
          </span>
          {turn && credits !== undefined && <span className="pill soft num">{credits} credits</span>}
          {mute}
          <button className="cs-close" onClick={close} aria-label="Close"><Icon name="close" size={20} sw={1.8} /></button>
        </div>

        {!turn && (
          <>
            <div className="cs-fieldrow">
              {field}
              <button type="button" className="cs-talk" onClick={() => beginTalk('tap')} aria-label="Talk to Clair"><Glyph name="mic" size={20} /></button>
            </div>
            {noteEl}
            <div className="sec"><span>Try this evening</span><span className="meta">Changes through the day</span></div>
            <div className="st-card cs-try">
              {TRY.map((s) => (
                <button key={s.text} className="cs-row" onClick={() => send({ text: s.text }, s.text)}>
                  <span className="cs-tile" aria-hidden="true"><Icon name={s.icon} size={18} sw={1.8} /></span>
                  <span className="cs-row-txt"><span className="t">{s.text}</span><span className="s">{s.meta}</span></span>
                </button>
              ))}
            </div>
          </>
        )}

        {turn && (
          <>
            <p className="said">{turn.said}</p>
            {/* an answer speaks for itself (board ClairAsk): the line goes once it has nothing to say */}
            {(line || !turn.answer) && (
              <p className="cs-line" role="status">
                <Spool expr={expr} size={30} />
                <span>{line}</span>
              </p>
            )}
            {turn.status && turn.understood && <p className="cs-understood">{turn.understood}</p>}
            {waitingOn > 0 && <div className="sec"><span>Waiting for your OK · {waitingOn} {waitingOn === 1 ? 'app' : 'apps'}</span></div>}
            {turn.cards.map((c, i) => (
              <ProposalCard key={c.id} cs={c} delay={STAGGER[Math.min(i, 2)]}
                onBuild={c.kind === 'app' ? (cs) => { setBuildDraft({ cs, sentence: turn.said }); openClair(false); nav('/build'); } : undefined}
                onStitched={(done) => {
                  // the card's status lives here too: it may reach the sheet after the sheet closed, and the next opening shows it stitched
                  setTurn((t) => (t ? { ...t, stitched: true, cards: t.cards.map((x) => (x.id === done.id ? { ...x, status: 'stitched' } : x)) } : t));
                  if (!turn.offer) setTimeout(() => openClair(false), T.land); // close after the last landing; Home shows the tags
                }}
                onUndone={() => setTurn((t) => (t ? { ...t, stitched: false, cards: t.cards.map((x) => (x.id === c.id ? { ...x, status: 'basted' } : x)) } : t))} />
            ))}
            {turn.stitched && turn.offer && <OfferCard offer={turn.offer} />}
            {turn.answer && (
              <div className="chalk cs-answer arrive">
                <p className="answer" aria-live="polite"><Bold text={turn.answer} /></p>
                {sources('in')}
              </div>
            )}
            {turn.error && <p className="err cs-err" role="alert">{turn.error}</p>}
            {turn.slow && !turn.cards.length && (
              <span className="sample-row arrive">
                <button className="outline" onClick={() => send({ fixture: 'planner' }, turn.said)}>Use sample</button>
                <span className="muted">A recorded run, marked "sample".</span>
              </span>
            )}
            {/* a capture's cards already name their apps (board ClairResult); sources stand alone only without an answer or a card */}
            {!turn.answer && !turn.cards.length && sources('alone')}
          </>
        )}
        </>)}
      </div>
    </Sheet>
  );
}
