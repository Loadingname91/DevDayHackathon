import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ago } from '../lib/chats';
import { EASE, RM, T } from '../lib/motion';
import { getState, openClair, useStore } from '../lib/store';
import { fetchLatest, openThread, registerHandoff, resumable, routeChatVoice, send, sheetSettle, TRY, useTurns } from '../lib/turns';
import { beginTalk, finishTalk, getTalk, NOT_HEARD, onVoiceOutcome, resetTalk, toggleMuted, toggleScripted, TYPE_INSTEAD, useLongPress, useMuted, useTalk, canSpeak } from '../lib/voice';
import { DropHint, useAttachments, useDropPaste } from './attach';
import { Composer } from './clair/Composer';
import { CG } from './clair/Glyph';
import { TurnView } from './clair/TurnView';
import { Icon } from './Icon';
import { Glyph, ListeningPanel } from './ListeningPanel';
import { Sheet } from './Sheet';
import { Spool, type Expr } from './Spool';

/** Crossfade + height (catalogue: "State swap"): the content's height animates over 220 ms when it changes.
 *  A phase can change inside those 220 ms: the new animation starts from the height on screen, not from the last target.
 *  `reset` changes when the sheet itself is resized (big mode): the new height is taken as it is, the sheet's own grow carries it. */
function useAutoHeight(ref: React.RefObject<HTMLElement | null>, key: unknown, reset: unknown) {
  const last = useRef(0);
  const anim = useRef<Animation | null>(null);
  const lastReset = useRef(reset);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (lastReset.current !== reset) { lastReset.current = reset; anim.current?.cancel(); anim.current = null; last.current = el.offsetHeight; return; }
    const live = anim.current ? el.offsetHeight : last.current; // read before cancelling: with a run in flight this is the animated height
    anim.current?.cancel(); anim.current = null;
    const h = el.offsetHeight; // the natural height of the new content
    if (last.current && Math.abs(h - live) > 2 && !RM()) {
      const a = el.animate([{ height: `${live}px`, overflow: 'hidden' }, { height: `${h}px`, overflow: 'hidden' }], { duration: T.state, easing: EASE });
      anim.current = a;
      a.onfinish = a.oncancel = () => { if (anim.current === a) anim.current = null; };
    }
    last.current = h;
  }, [key, reset, ref]);
}

const fine = () => matchMedia('(pointer: fine)').matches;
/** Big mode is remembered on this device. */
const BIG = 'quilt-clair-big';
const readBig = () => { try { return localStorage.getItem(BIG) === '1'; } catch { return false; } };

/**
 * Clair: type a sentence, watch the status line, get a basted card. Floats above the bar so threads land on the pins.
 * Boards ClairSheet (start: header, the field, "Try this evening"), ClairResult (a capture's basted cards)
 * and ClairAsk (answers); CSS in styles/clair.css. The field sits under the header until a turn runs,
 * then pins to the bottom for a follow-up.
 *
 * The turns live in lib/turns.ts, shared with the Chat screen: a turn started here carries on there. The header's expand button
 * makes the sheet big (nearly the whole screen on a phone, a wide panel on a laptop) and shows every turn since it opened;
 * the choice is remembered. "Open chat" and "Continue" go to the Chat screen.
 */
export function ClairSheet() {
  const open = useStore((s) => s.clairOpen);
  const apps = useStore((s) => s.home?.apps) ?? [];
  const credits = useStore((s) => s.me?.credits.left);
  const ts = useTurns();
  const chat = ts.convs[ts.current];
  const [big, setBig] = useState(readBig);
  const shown = chat.turns.slice(ts.sheetFrom);
  const visible = big ? shown : shown.slice(-1);
  const turn = visible[visible.length - 1] ?? null;
  const blocked = !!turn && !turn.done && !turn.cancelled && !turn.slow; // a turn is running: one at a time
  const resume = resumable(ts);
  const [text, setText] = useState('');
  const [note, setNote] = useState<string | null>(null); // one plain line under the field: what the microphone did
  // photos and files for the next turn; the sheet is the drop target, and a screenshot can be pasted into the field
  const att = useAttachments({ workspaceId: useStore((s) => s.me?.workspace.id) });
  const host = useRef<HTMLElement | null>(null);
  const { dragging } = useDropPaste(host, att.add, { enabled: open });
  const talk = useTalk();
  const talking = talk.phase !== 'idle';
  const muted = useMuted();
  const input = useRef<HTMLTextAreaElement>(null);
  const refocus = useRef(false); // the field moves to the bottom when a turn starts; keep the caret on a laptop
  const content = useRef<HTMLDivElement>(null);
  const grow = useRef<DOMRect | null>(null);
  useLayoutEffect(() => { host.current = content.current?.closest<HTMLElement>('.sheet') ?? null; });
  const nav = useNavigate();
  const close = useCallback(() => {
    // closing mid-talk: a hold leaves showing its state (resetTalk runs once the sheet has gone), anything else just stops
    const t = getTalk();
    if (t.phase === 'listening' || t.phase === 'cancel') { if (t.mode === 'hold') { finishTalk(true); return; } resetTalk(); } else if (t.phase === 'finishing') resetTalk();
    openClair(false);
  }, []);
  // a finished turn starts fresh when the sheet opens; the server's latest chat is asked for, so "Continue" can offer it
  useLayoutEffect(() => { if (open) { sheetSettle(); void fetchLatest(); } }, [open]);
  // Clair needs to ask before it builds: the Build screen shows the questions and the plan, so hand the sentence over
  useEffect(() => registerHandoff((said) => { openClair(false); nav(`/build?say=${encodeURIComponent(said)}`); }), [nav]);
  // never auto-focus on touch: the keyboard would cover the suggestions (fixspec §D). On a laptop the field has the
  // caret as the sheet starts to rise, so the first keystroke is never lost.
  const opened = () => { if (fine() && getTalk().phase === 'idle') input.current?.focus({ preventScroll: true }); };
  const started = !!turn;
  useEffect(() => {
    if (refocus.current && fine()) input.current?.focus({ preventScroll: true });
    refocus.current = false;
  }, [started]);
  const phase = talking ? 'talk' : !turn ? 'start' : `${visible.length}-${turn.cards.length}-${!!turn.understood}-${!!turn.thinking}-${turn.thinkMs === null}-${!!turn.answer}-${turn.done}-${!!turn.error}-${turn.slow}-${turn.stitched}`;
  useAutoHeight(content, phase, big);
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

  // ---- big mode: the sheet grows from where it is to where it goes (350, EASE); reduced motion is a 120 ms fade. A turn is never touched.
  const toggleBig = () => {
    const s = content.current?.closest<HTMLElement>('.sheet');
    grow.current = s ? s.getBoundingClientRect() : null;
    setBig((b) => { const n = !b; try { localStorage.setItem(BIG, n ? '1' : '0'); } catch { /* not remembered */ } return n; });
  };
  useLayoutEffect(() => {
    const from = grow.current;
    grow.current = null;
    const s = content.current?.closest<HTMLElement>('.sheet');
    if (!from || !s) return;
    if (RM()) { s.animate([{ opacity: 0.4 }, { opacity: 1 }], { duration: T.fb, easing: EASE }); return; }
    const to = s.getBoundingClientRect();
    const frame = (r: DOMRect) => ({ left: `${r.left}px`, right: 'auto', bottom: `${innerHeight - r.bottom}px`, width: `${r.width}px`, height: `${r.height}px`, maxHeight: `${r.height}px` });
    s.animate([frame(from), frame(to)], { duration: T.layout, easing: EASE });
  }, [big]);

  const onExited = () => {
    if (getTalk().phase === 'leaving') resetTalk(); // a cancelled hold: the sheet has gone, so its Talk state can go
    sheetSettle(); // a finished turn starts fresh next time; one still waiting for OK stays
  };

  const go = (body: Parameters<typeof send>[0], said: string, o?: Parameters<typeof send>[2]) => {
    if (blocked) return false;
    refocus.current = !turn && document.activeElement === input.current;
    const sent = send(body, said, o);
    if (sent) { setText(''); setNote(null); }
    return sent;
  };
  // Send waits while a photo is being prepared or uploaded, or an upload failed; an attachment alone is enough to send
  const sendable = att.ready && (!!text.trim() || att.hasSendable);
  const submit = () => {
    if (!sendable) return;
    const t = text.trim(), f = att.request();
    if (!f.images.length && !f.files.length) { go({ text: t }, t); return; }
    const said = t || att.fallbackText; // the backend needs words: an attachment alone sends the default sentence
    if (go({ text: said, ...f }, said, { attach: att.peek() })) att.take();
  };

  // what a finished talk asks of the sheet (lib/voice.ts): send it, hold it for Edit, say nothing was heard, or type instead
  useEffect(() => onVoiceOutcome((o) => {
    if (!getState().clairOpen && routeChatVoice(o)) return; // a Talk started in the Chat screen is the chat's
    switch (o.kind) {
      case 'send': go({ transcript: o.text, voice: true }, o.text); break;
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

  const noteEl = note && <p className="cs-note" role="status">{note}</p>;
  const mute = turn?.voice && canSpeak() && (
    <button type="button" className="cs-mute" aria-pressed={muted} onClick={toggleMuted} aria-label={muted ? 'Unmute Clair' : 'Mute Clair'}>
      <Glyph name={muted ? 'speaker-off' : 'speaker'} size={20} />
    </button>
  );
  const openChat = () => { openClair(false); nav('/chat'); };
  const carryOn = () => { if (resume) { openThread(resume.id, { resume: true }); openChat(); } };
  const field = (compact: boolean) => (
    <Composer value={text} onChange={(v) => { setText(v); setNote(null); }} onSubmit={submit} onTalk={() => beginTalk('tap')} inputRef={input}
      compact={compact} rows={compact ? 1 : 2} disabled={blocked} attach={att} sendable={sendable}
      placeholder={compact ? 'Add more or ask…' : 'Spent $12 on lunch, gym tomorrow 6 pm…'} />
  );

  return (
    <Sheet open={open} onClose={close} onExited={onExited} onOpened={opened} noClose keepBar label="Clair" footer={turn && !talking ? <>{noteEl}{field(true)}</> : undefined}>
      <div ref={content} className={`cs${turn && !talking ? ' cs-turn' : ''}${big ? ' cs-big' : ''}`}>
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
          {(turn || big) && (
            <button type="button" className="cs-expand" onClick={toggleBig} aria-label={big ? 'Make Clair smaller' : 'Make Clair bigger'}>
              <CG name={big ? 'collapse' : 'expand'} />
            </button>
          )}
          <button className="cs-close" onClick={close} aria-label="Close"><Icon name="close" size={20} sw={1.8} /></button>
        </div>

        {!turn && (
          <>
            {field(false)}
            {noteEl}
            <div className="sec"><span>Try this evening</span><span className="meta">Changes through the day</span></div>
            <div className="st-card cs-try">
              {TRY.map((s) => (
                <button key={s.text} className="cs-row" onClick={() => go({ text: s.text }, s.text)}>
                  <span className="cs-tile" aria-hidden="true"><Icon name={s.icon} size={18} sw={1.8} /></span>
                  <span className="cs-row-txt"><span className="t">{s.text}</span><span className="s">{s.meta}</span></span>
                </button>
              ))}
            </div>
            {resume && (
              <div className="st-card cs-try cs-resume">
                <button className="cs-row" onClick={carryOn}>
                  <span className="cs-tile" aria-hidden="true"><CG name="clock" size={18} /></span>
                  <span className="cs-row-txt"><span className="t">Continue: {resume.title}</span><span className="s">{ago(resume.last)}</span></span>
                </button>
              </div>
            )}
            <button type="button" className="link cs-open" onClick={openChat}>Open chat <span aria-hidden="true">›</span></button>
          </>
        )}

        {visible.map((t, i) => (
          <TurnView key={t.id} turn={t} cid={chat.id} variant="sheet" latest={i === visible.length - 1}
            onOpenChat={i === visible.length - 1 ? openChat : undefined}
            onLanded={(done) => { if (!done.offer) setTimeout(() => openClair(false), T.land); }} /> /* close after the last landing; Home shows the tags */
        ))}
        </>)}
        <DropHint show={dragging} />
      </div>
    </Sheet>
  );
}
