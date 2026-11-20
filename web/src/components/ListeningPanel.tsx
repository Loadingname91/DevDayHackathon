import { Fragment, useEffect, useRef, useState } from 'react';
import { RM } from '../lib/motion';
import { finishTalk, useLevels, useTalk } from '../lib/voice';
import { Icon } from './Icon';
import { Spool } from './Spool';

/** The two glyphs the voice controls need (Icon.tsx has neither a microphone nor a speaker). */
const PATHS: Record<string, string> = {
  mic: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM6 11a6 6 0 0 0 12 0M12 17v4M9 21h6',
  speaker: 'M4 9.5h3.5L12 6v12l-4.5-3.5H4zM15.5 9a4 4 0 0 1 0 6M18 6.5a8 8 0 0 1 0 11',
  'speaker-off': 'M4 9.5h3.5L12 6v12l-4.5-3.5H4zM16 9.5l5 5M21 9.5l-5 5',
};
export function Glyph({ name, size = 20 }: { name: keyof typeof PATHS; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: 'none' }}>
      <path d={PATHS[name]} />
    </svg>
  );
}

const SW = 3; // stroke width of the line; its round caps add half of it to each end of a stitch
const GAP = 5 + SW; // 5 px of cloth between two stitches

/** Stitch lengths from the recent levels, oldest on the left: 2 + level × 14 px, as many as the line is wide, newest at its right end. */
function stitches(levels: number[], width: number) {
  const dash: number[] = [];
  let sum = 0;
  for (let i = levels.length - 1; i >= 0 && sum < width + 24; i--) {
    const d = Math.max(0.1, 2 + levels[i] * 14 - SW); // a stitch is 2 + level × 14 px long on screen; the caps add SW to the dash
    dash.unshift(d, GAP);
    sum += d + GAP;
  }
  return { array: dash.join(' '), offset: Math.max(0, sum - width) };
}

/** The waveform IS stitches (fixspec "Talk"): a running-stitch line whose stitch lengths follow the voice level. */
function Wave({ still }: { still: boolean }) {
  const levels = useLevels();
  const box = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(326);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    setW(el.clientWidth || 326);
    const ro = new ResizeObserver(() => setW(el.clientWidth || 326));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  // reduced motion: a static dashed line (the title says "Listening")
  const s = RM() ? { array: '4 8', offset: 0 } : stitches(levels, w);
  return (
    <div ref={box} className={`vp-wave${still ? ' still' : ''}`} aria-hidden="true">
      <svg width={w} height="56" viewBox={`0 0 ${w} 56`}>
        <line className="vp-line" x1="0" y1="28" x2={w} y2="28" strokeWidth={SW} strokeLinecap="round" strokeDasharray={s.array} strokeDashoffset={s.offset} />
      </svg>
    </div>
  );
}

/**
 * The Talk state of the Clair sheet (board ClairTalk, fixspec "Talk"): the spool waiting, "Listening", the stitch line, the live
 * transcript (settled words in ink, the rest in the secondary colour), and what the release will do. Pointer events are
 * the Clair button's, not this panel's: a hold carries on from the bar (lib/voice.ts). `head` carries the header's long-press.
 */
export function ListeningPanel({ head }: { head: React.HTMLAttributes<HTMLElement> }) {
  const t = useTalk();
  const cancel = t.phase === 'cancel' || t.phase === 'leaving';
  const fw = t.final ? t.final.split(' ') : [];
  const iw = t.interim ? t.interim.split(' ') : [];
  const said = useRef<HTMLParagraphElement>(null);
  const send = useRef<HTMLButtonElement>(null);
  // the Talk button that started a tap-to-talk is gone: Send takes the focus, so Enter sends and Escape cancels from the keyboard
  const tap = t.mode === 'tap';
  useEffect(() => { if (tap) send.current?.focus({ preventScroll: true }); }, [tap]);
  // three lines show; a longer sentence keeps its newest words in view
  useEffect(() => { const el = said.current; if (el) el.scrollTop = el.scrollHeight; }, [t.final, t.interim]);
  return (
    <>
      <div className="cs-head vp-head" {...head}>
        <Spool expr="waiting" size={44} />
        <span className="cs-titles">
          <h2>Listening</h2>
          <span className="cs-sub">{t.mode === 'tap' ? 'Tap Send when you are done' : 'Hold the Clair button while you talk'}</span>
        </span>
      </div>
      <Wave still={cancel || t.phase === 'finishing'} />
      <p ref={said} className="vp-said" aria-live="polite">
        {/* a word fades in where it first appears; one that changes or settles keeps its place (index keys) */}
        {fw.map((w, i) => <Fragment key={i}><span className="vw">{w}</span>{' '}</Fragment>)}
        {iw.map((w, i) => <Fragment key={fw.length + i}><span className="vw int">{w}</span>{' '}</Fragment>)}
      </p>
      {t.mode === 'tap' && t.phase === 'listening'
        ? (
          <div className="vp-act">
            <button type="button" className="link" onClick={() => finishTalk(true)}>Cancel</button>
            <button ref={send} type="button" className="cta" onClick={() => finishTalk(false)}>Send</button>
          </div>
        )
        : (
          <div className={`vp-hint${cancel ? ' cancel' : ''}`}>
            <Icon name={cancel ? 'close' : 'up'} size={16} sw={1.8} />
            {t.phase === 'leaving' ? 'Cancelled' : t.phase === 'cancel' ? 'Release to cancel' : t.phase === 'finishing' ? 'Sending…' : 'Release to send · slide up to cancel'}
          </div>
        )}
    </>
  );
}
