// Hold the Clair button to talk (spec/clair-agent.md §4; design/notes/fixspec.md, "The button" and "The Clair sheet").
// One module, four jobs: the hold gesture (useHoldToTalk), the talk session (the browser's SpeechRecognition, or the
// scripted stand-in for the demo), the waveform's levels, and speech out (speechSynthesis, with a mute switch).
// The session lives here, outside React, because the gesture starts on the bar or the sidebar while the sheet that
// shows it is somewhere else; the sheet reads it through useTalk() and gets the result through onVoiceOutcome().
import { useMemo, useRef, useSyncExternalStore, type PointerEvent as RPointerEvent } from 'react';
import { anyMock } from '../api/client';
import { RM } from './motion';
import { openClair } from './store';

/** Hold this long before talking starts: a tap never gets there. One hold time everywhere (fixspec). */
export const HOLD_MS = 450;
/** Slide up this far while holding to cancel. */
export const CANCEL_PX = 60;
/** A press that moves this far before the hold fires is a drag, not a hold. */
const SLOP = 12;
const TICK = 70; // one waveform sample
const SAMPLES = 90;

// ------------------------------------------------------------------------------------------------ the session store
export type TalkPhase = 'idle' | 'listening' | 'cancel' | 'finishing' | 'leaving';
export type Talk = {
  phase: TalkPhase;
  /** hold: opened by holding the Clair button (a release sends); tap: the Talk button in the sheet (Send and Cancel) */
  mode: 'hold' | 'tap';
  /** words the recognizer has settled on, and the tail it is still unsure of */
  final: string;
  interim: string;
  scripted: boolean;
};
const IDLE: Talk = { phase: 'idle', mode: 'hold', final: '', interim: '', scripted: false };
let talk: Talk = IDLE;
let levels: number[] = [];
const subs = new Set<() => void>();
const lvSubs = new Set<() => void>();
const sub = (f: () => void) => { subs.add(f); return () => { subs.delete(f); }; };
const lvSub = (f: () => void) => { lvSubs.add(f); return () => { lvSubs.delete(f); }; };
const setTalk = (p: Partial<Talk>) => { talk = { ...talk, ...p }; subs.forEach((f) => f()); };
const setLevels = (l: number[]) => { levels = l; lvSubs.forEach((f) => f()); };
export const getTalk = () => talk;
export const useTalk = () => useSyncExternalStore(sub, () => talk);
/** Recent sound levels, 0 to 1, newest last. Its own subscription: only the waveform redraws at 14 fps. */
export const useLevels = () => useSyncExternalStore(lvSub, () => levels);

/** What a finished session asks the sheet to do. */
export type Outcome =
  | { kind: 'send'; text: string }
  | { kind: 'edit'; text: string } // low confidence: held in the field, not sent
  | { kind: 'none' } // nothing heard: "Didn't catch that."
  | { kind: 'unavailable' } // mic denied, no recognizer, a recognizer error: type instead
  | { kind: 'cancel'; mode: 'hold' | 'tap' };
let sink: ((o: Outcome) => void) | null = null;
export function onVoiceOutcome(f: (o: Outcome) => void) { sink = f; return () => { if (sink === f) sink = null; }; }

export const TYPE_INSTEAD = 'Quilt needs the microphone to listen. You can type instead.';
export const NOT_HEARD = "Didn't catch that.";

// ------------------------------------------------------------------------------------------------ recognizer or script
type Alt = { transcript: string; confidence: number };
type Res = { isFinal: boolean; 0: Alt; length: number };
type RecEvent = { results: ArrayLike<Res> };
type Rec = {
  lang: string; continuous: boolean; interimResults: boolean; maxAlternatives: number;
  start(): void; stop(): void; abort(): void;
  onresult: ((e: RecEvent) => void) | null; onerror: ((e: { error: string }) => void) | null; onend: (() => void) | null;
  onsoundstart: (() => void) | null; onspeechstart: (() => void) | null; onspeechend: (() => void) | null;
};
const ctor = (): (new () => Rec) | undefined => {
  const w = window as unknown as { SpeechRecognition?: new () => Rec; webkitSpeechRecognition?: new () => Rec };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
};
/** A page the recognizer can run in: it exists, the page is secure (a phone on the LAN over http is not), and it is not framed
 *  (a framed page cannot ask for the microphone, which is where the published artifact lives). */
function canRecognize() {
  try { return !!ctor() && window.isSecureContext && window.self === window.top; } catch { return false; }
}

// DEMO STAND-IN (not marked in the UI; the mock-data mark already says the data is mock).
// A mock-data build that cannot recognise speech (insecure phone, framed artifact, no recognizer), or any build with
// ?voice=demo, types this sentence into the Talk state word by word while the button is held, with the scripted
// waveform, and sends what has been "heard" on release. Long-press the sheet header toggles it on any device (§4, "On stage").
const SCRIPT = 'Spent $12 on lunch, gym tomorrow 6 pm'.split(' ');
const WORD_MS = 230;
let forced = false;
const DEMO = (() => { try { return new URLSearchParams(location.search).get('voice') === 'demo'; } catch { return false; } })();
export const scriptedNow = () => forced || DEMO || (anyMock && !canRecognize());
export function toggleScripted() { forced = !forced; try { navigator.vibrate?.(10); } catch { /* no haptics here */ } return forced; }

type Session = {
  id: number; mode: 'hold' | 'tap'; scripted: boolean;
  rec: Rec | null; ended: boolean; timers: ReturnType<typeof setInterval>[]; wait?: ReturnType<typeof setTimeout>;
  sound: boolean; speaking: boolean; lastWord: number; still: boolean; confidences: number[]; error: string | null;
};
let session: Session | null = null;
let sid = 0;
const tidy = (t: string) => t.replace(/\s+/g, ' ').trim();
const words = (t: string) => (t ? t.split(' ').length : 0);

/** Start listening. `hold` also opens the sheet (the sheet grows from the button as usual); `tap` is already inside it. */
export function beginTalk(mode: 'hold' | 'tap') {
  teardown();
  stopSpeaking();
  const scripted = scriptedNow();
  const s: Session = { id: ++sid, mode, scripted, rec: null, ended: false, timers: [], sound: false, speaking: false, lastWord: 0, still: false, confidences: [], error: null };
  session = s;
  setLevels(Array.from({ length: SAMPLES }, () => 0.06));
  setTalk({ phase: 'listening', mode, final: '', interim: '', scripted });
  if (mode === 'hold') openClair(true);
  if (scripted) runScript(s); else runRecognizer(s);
  if (session === s && !RM()) s.timers.push(setInterval(() => tick(s), TICK)); // the recognizer may have failed at once
}

function runScript(s: Session) {
  let n = 0;
  s.timers.push(setInterval(() => {
    if (session !== s || s.still || n >= SCRIPT.length) return;
    n += 1;
    s.lastWord = performance.now();
    const heard = SCRIPT.slice(0, n);
    const cut = Math.max(0, n - 2); // the last two words are still interim, like a recognizer's partial result
    setTalk({ final: heard.slice(0, cut).join(' '), interim: heard.slice(cut).join(' ') });
  }, WORD_MS));
}

function runRecognizer(s: Session) {
  const C = ctor();
  if (!canRecognize() || !C) { fail(s); return; }
  let rec: Rec;
  try { rec = new C(); } catch { fail(s); return; }
  s.rec = rec;
  rec.lang = 'en-US'; rec.continuous = true; rec.interimResults = true; rec.maxAlternatives = 1;
  // never getUserMedia here: Android lets only one owner hold the microphone (§4). The line follows the recognizer's own events.
  rec.onsoundstart = () => { s.sound = true; };
  rec.onspeechstart = () => { s.speaking = true; s.sound = true; };
  rec.onspeechend = () => { s.speaking = false; };
  rec.onresult = (e) => {
    const fin: string[] = [], interim: string[] = [], conf: number[] = [];
    for (let i = 0; i < e.results.length; i++) {
      const r = e.results[i], a = r[0];
      if (r.isFinal) { fin.push(a.transcript); if (a.confidence > 0) conf.push(a.confidence); } else interim.push(a.transcript);
    }
    s.confidences = conf; s.lastWord = performance.now(); s.sound = true;
    if (session === s) setTalk({ final: tidy(fin.join(' ')), interim: tidy(interim.join(' ')) });
  };
  rec.onerror = (e) => {
    s.error = e.error;
    if (session !== s || e.error === 'aborted' || e.error === 'no-speech') return; // no-speech: the release says "Didn't catch that."
    fail(s); // not-allowed, service-not-allowed, audio-capture, network, language-not-supported
  };
  rec.onend = () => { s.ended = true; if (session === s && talk.phase === 'finishing') settle(s); };
  try { rec.start(); } catch { fail(s); }
}

/** The recognizer cannot run: say so in one line, and the sheet opens its text field. */
function fail(s: Session) {
  if (session !== s) return;
  teardown();
  setTalk({ ...IDLE });
  sink?.({ kind: 'unavailable' });
}

/** The waveform's next sample: a smooth pseudo-random envelope, quiet until sound is heard, livelier while words arrive. */
let level = 0.06;
function tick(s: Session) {
  if (session !== s || s.still) return;
  const t = performance.now();
  const talking = s.speaking || t - s.lastWord < 650;
  const base = talking ? 0.55 : s.sound ? 0.2 : 0.07;
  const swing = talking ? 0.42 : 0.1;
  const wob = (Math.sin(t / 130) + 0.6 * Math.sin(t / 57 + 1.3) + 0.4 * Math.sin(t / 311 + 0.4)) / 2;
  const target = Math.max(0.04, Math.min(1, base + swing * wob));
  level += (target - level) * 0.55;
  setLevels([...levels.slice(-(SAMPLES - 1)), level]);
}

/** Slide-up zone: the line goes still and the hint changes. */
function setCancelZone(on: boolean) {
  const s = session;
  if (!s || (talk.phase !== 'listening' && talk.phase !== 'cancel')) return;
  s.still = on;
  if ((talk.phase === 'cancel') !== on) setTalk({ phase: on ? 'cancel' : 'listening' });
}

function teardown() {
  const s = session;
  session = null;
  if (!s) return;
  s.timers.forEach(clearInterval);
  clearTimeout(s.wait);
  if (s.rec && !s.ended) { s.rec.onresult = s.rec.onerror = s.rec.onend = null; try { s.rec.abort(); } catch { /* already stopped */ } }
}

/** Release (`cancel` false) or discard (`cancel` true). Cancel never sends a request. */
export function finishTalk(cancel: boolean) {
  const s = session;
  if (!s || (talk.phase !== 'listening' && talk.phase !== 'cancel')) return;
  if (cancel) {
    teardown();
    // a hold opened the sheet: it leaves, still showing this state while it does; a tap leaves the sheet as it was
    setTalk(s.mode === 'hold' ? { phase: 'leaving' } : { ...IDLE });
    sink?.({ kind: 'cancel', mode: s.mode });
    return;
  }
  setTalk({ phase: 'finishing' });
  s.still = true;
  if (s.scripted || !s.rec || s.ended) { settle(s); return; }
  s.wait = setTimeout(() => settle(s), 900); // stop() makes the recognizer finalise what it heard, then end
  try { s.rec.stop(); } catch { settle(s); }
}

function settle(s: Session) {
  if (session !== s) return;
  const text = tidy(`${talk.final} ${talk.interim}`);
  const conf = s.confidences, avg = conf.length ? conf.reduce((a, b) => a + b, 0) / conf.length : 1;
  const error = s.error;
  teardown();
  setTalk({ ...IDLE });
  // the scripted stand-in needs three words; a real recognizer needs one
  if (words(text) < (s.scripted ? 3 : 1)) sink?.(error && error !== 'no-speech' && error !== 'aborted' ? { kind: 'unavailable' } : { kind: 'none' });
  else if (avg < 0.6) sink?.({ kind: 'edit', text });
  else sink?.({ kind: 'send', text });
}

/** The sheet has left after a cancelled hold, or closed some other way. */
export function resetTalk() { teardown(); setTalk({ ...IDLE }); }

// ------------------------------------------------------------------------------------------------ the hold gesture
let swallow = false; // the click that follows a hold must not open the sheet a second time
let swallowTimer: ReturnType<typeof setTimeout> | undefined;
/** Once a hold has fired, the lift of that finger (whenever it comes: Escape and blur end the hold early) sends a click that is eaten.
 *  A new press first disarms it, so a later tap is never swallowed. */
function eatNextClick() {
  const arm = () => { disarm(); swallow = true; clearTimeout(swallowTimer); swallowTimer = setTimeout(() => { swallow = false; }, 400); };
  const disarm = () => { removeEventListener('pointerup', arm, true); removeEventListener('pointercancel', arm, true); removeEventListener('pointerdown', disarm, true); };
  addEventListener('pointerup', arm, true); addEventListener('pointercancel', arm, true); addEventListener('pointerdown', disarm, true);
}

/**
 * Props for the Clair button (the bar's cell, the sidebar's "Tell Clair anything"). Hold 450 ms to talk; release sends; slide up
 * 60 px and release cancels; a shorter press is a tap and opens the sheet (the click). Navigation happens on release, not mid-hold.
 */
export function useHoldToTalk() {
  const active = useRef<(() => void) | null>(null);
  return useMemo(() => ({
    onPointerDown(e: RPointerEvent<HTMLElement>) {
      if (!e.isPrimary || (e.pointerType === 'mouse' && e.button !== 0)) return;
      active.current?.(); // a stray earlier press
      const el = e.currentTarget, id = e.pointerId, x0 = e.clientX, y0 = e.clientY;
      let fired = false, over = false;
      el.classList.add('holding'); // the light fill (CSS: 120 ms delay, 330 ms linear), so a quick tap never shows it
      const timer = setTimeout(() => {
        fired = true;
        el.classList.remove('holding');
        try { navigator.vibrate?.(10); } catch { /* no haptics here */ }
        try { el.setPointerCapture(id); } catch { /* the window listeners below carry the release */ }
        eatNextClick();
        beginTalk('hold');
      }, HOLD_MS);
      const off = () => {
        clearTimeout(timer);
        el.classList.remove('holding');
        removeEventListener('pointermove', move); removeEventListener('pointerup', up); removeEventListener('pointercancel', cancel);
        removeEventListener('blur', cancel); removeEventListener('keydown', key); document.removeEventListener('visibilitychange', hide);
        try { if (el.hasPointerCapture(id)) el.releasePointerCapture(id); } catch { /* gone with the element */ }
        if (active.current === off) active.current = null;
      };
      const end = (discard: boolean) => {
        const was = fired;
        off();
        if (!was) return; // a tap: the click opens the sheet
        finishTalk(discard || over);
      };
      const move = (e2: PointerEvent) => {
        if (e2.pointerId !== id) return;
        if (!fired) { if (Math.hypot(e2.clientX - x0, e2.clientY - y0) > SLOP) { clearTimeout(timer); el.classList.remove('holding'); } return; }
        over = y0 - e2.clientY >= CANCEL_PX;
        setCancelZone(over);
      };
      const up = (e2: PointerEvent) => { if (e2.pointerId === id) end(false); };
      const cancel = () => end(true);
      const key = (e2: KeyboardEvent) => { if (e2.key === 'Escape') end(true); };
      const hide = () => { if (document.hidden) end(true); };
      addEventListener('pointermove', move); addEventListener('pointerup', up); addEventListener('pointercancel', cancel);
      addEventListener('blur', cancel); addEventListener('keydown', key); document.addEventListener('visibilitychange', hide);
      active.current = off;
    },
    onContextMenu(e: React.MouseEvent) { e.preventDefault(); }, // a long press must not open the browser's menu
    onClick(e: React.MouseEvent) {
      if (swallow) { swallow = false; e.preventDefault(); return; }
      openClair(true);
    },
  }), []);
}

/** Long-press (450 ms) for a hidden control: the sheet header's on-stage fallback toggle. Presses on buttons inside don't count. */
export function useLongPress(fire: () => void, ms = HOLD_MS) {
  const t = useRef<ReturnType<typeof setTimeout>>(undefined);
  const p0 = useRef<[number, number]>([0, 0]);
  const stop = () => clearTimeout(t.current);
  return {
    onPointerDown(e: RPointerEvent<HTMLElement>) {
      if (e.button || (e.target as Element).closest('button,a,input,textarea')) return;
      p0.current = [e.clientX, e.clientY];
      stop(); t.current = setTimeout(fire, ms);
    },
    onPointerMove(e: RPointerEvent<HTMLElement>) { if (Math.hypot(e.clientX - p0.current[0], e.clientY - p0.current[1]) > SLOP) stop(); },
    onPointerUp: stop, onPointerCancel: stop, onPointerLeave: stop,
  };
}

// ------------------------------------------------------------------------------------------------ speech out
const MUTE_KEY = 'quilt-voice-muted';
let muted = (() => { try { return localStorage.getItem(MUTE_KEY) === '1'; } catch { return false; } })();
const mSubs = new Set<() => void>();
export const useMuted = () => useSyncExternalStore((f) => { mSubs.add(f); return () => { mSubs.delete(f); }; }, () => muted);
export const canSpeak = () => typeof window !== 'undefined' && 'speechSynthesis' in window && typeof SpeechSynthesisUtterance !== 'undefined';
export function toggleMuted() {
  muted = !muted;
  try { localStorage.setItem(MUTE_KEY, muted ? '1' : '0'); } catch { /* a device preference we may not be able to keep */ }
  if (muted) stopSpeaking();
  mSubs.forEach((f) => f());
}
let stopOnTap: (() => void) | null = null;
/** Clair answers aloud, only when Sam talked first (§4). Stops at once on a tap anywhere, or a new hold. */
export function speak(text: string) {
  if (muted || !canSpeak() || !text.trim()) return;
  stopSpeaking();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-US';
  const stop = () => stopSpeaking();
  document.addEventListener('pointerdown', stop, { capture: true, once: true });
  stopOnTap = () => document.removeEventListener('pointerdown', stop, true);
  u.onend = u.onerror = () => { stopOnTap?.(); stopOnTap = null; };
  speechSynthesis.speak(u);
}
export function stopSpeaking() {
  stopOnTap?.(); stopOnTap = null;
  if (canSpeak()) speechSynthesis.cancel();
}
