import { Fragment, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listNames } from '../../lib/format';
import { STAGGER } from '../../lib/motion';
import type { SavedMsg } from '../../lib/chats';
import { markStitched, markUndone, send, type Turn } from '../../lib/turns';
import { openClair, setBuildDraft, useStore } from '../../lib/store';
import { Bold } from '../Bold';
import { Icon } from '../Icon';
import { OfferCard } from '../OfferCard';
import { ProposalCard } from '../ProposalCard';
import { Spool, type Expr } from '../Spool';
import { SentTiles, UnderstandingLine } from '../attach';
import { ATTACH_ONLY_TEXT } from '../../lib/attachments';

/** "From" + a chip per app Clair read; each opens its app. The contract gives the apps, not a row count, so there is no "· 6 rows". */
export function Sources({ keys, cls }: { keys: string[]; cls: string }) {
  const apps = useStore((s) => s.home?.apps) ?? [];
  const nav = useNavigate();
  if (!keys.length) return null;
  return (
    <span className={`cs-from ${cls}`} aria-label="Read from">
      <span className="cs-from-l">From</span>
      {keys.map((k) => {
        const a = apps.find((x) => x.key === k);
        return (
          <button key={k} type="button" className="chip" data-dye={a?.dye} onClick={() => { openClair(false); nav(`/a/${k}`); }}>
            <i className="dyedot" aria-hidden="true" />{a?.name ?? k}
          </button>
        );
      })}
    </span>
  );
}

/**
 * Clair's thinking, as it streams (`thinking_delta`). Open while the model thinks (a soft chalk box, the newest words at the bottom),
 * folds itself to one line "Thought for 4 s" once something else arrives, and opens again on a tap. A person's own tap wins over the
 * automatic open and close. Reduced motion: no pulse, the fold is a 120 ms fade (styles/clair.css).
 */
function Thinking({ turn }: { turn: Turn }) {
  const live = turn.thinkMs === null && !turn.done && !turn.cancelled;
  const [pick, setPick] = useState<boolean | null>(null);
  const open = pick ?? live;
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => { if (live && box.current) box.current.scrollTop = box.current.scrollHeight; }, [turn.thinking, live]);
  const secs = Math.round((turn.thinkMs ?? 0) / 1000);
  const label = live ? 'Thinking' : secs < 1 ? 'Thought briefly' : `Thought for ${secs} s`;
  return (
    <div className={`think${open ? ' open' : ''}${live ? ' live' : ''}`}>
      <button type="button" className="think-h" aria-expanded={open} onClick={() => setPick(!open)}>
        <span className="think-dots" aria-hidden="true"><i /><i /><i /></span>
        <span>{label}</span>
        <Icon name="chev" size={16} sw={1.8} />
      </button>
      <div className="think-body" aria-hidden={!open}>
        <div className="think-in chalk" ref={box} tabIndex={open ? 0 : -1} aria-label="What Clair thought">{turn.thinking}</div>
      </div>
    </div>
  );
}

type Props = {
  turn: Turn;
  /** the chat this turn belongs to */
  cid: string;
  variant: 'sheet' | 'chat';
  /** the last turn of the screen: it has Clair's spool; earlier ones keep their words */
  latest?: boolean;
  /** a card of this turn has landed (the sheet closes after it) */
  onLanded?: (t: Turn) => void;
  /** the sheet's last turn: "Open in chat ›" carries it on in the Chat screen. Beside "Waiting for your OK" while a card waits (no extra row,
   *  so a plan card still fits), else under the turn. */
  onOpenChat?: () => void;
};

/**
 * One turn, in the Clair sheet and in the Chat screen: your words, Clair's status line, the basted cards, the answer with its sources.
 * Boards ClairResult (a capture's cards) and ClairAsk (answers); CSS in styles/clair.css. In the chat the log is the live region,
 * so the lines inside do not announce a second time.
 */
export function TurnView({ turn, cid, variant, latest = true, onLanded, onOpenChat }: Props) {
  const nav = useNavigate();
  const chat = variant === 'chat';
  // Clair understood and then never drafted anything: no card, no words, no question, no offer. Say so, and let the person send it again.
  const empty = turn.done && !turn.error && !turn.cancelled && !turn.cards.length && !turn.answer && !turn.offer;
  const thinking = !!turn.thinkAt && turn.thinkMs === null && !turn.done && !turn.cancelled;
  const expr: Expr = turn.cancelled ? 'sleepy' : turn.error || empty ? 'oops' : thinking ? 'thinking' : turn.stitched ? 'stitched' : turn.cards.length ? 'waiting' : turn.done ? 'stitched' : 'working';
  const waitingOn = !turn.stitched ? new Set(turn.cards.filter((c) => c.status === 'basted').flatMap((c) => c.targets)).size : 0;
  // a turn with a photo or a file shows what Clair understood as its own line with the thumbnail (FR-C13), so the status line leaves it out
  const files = turn.attach.length > 0;
  const line = turn.cancelled ? 'Stopped.' : (turn.status ?? (files ? null : turn.understood) ?? (turn.error ? 'That did not work.' : turn.cards.length ? 'Needs your OK.' : ''));
  const first = turn.attach[0];
  const thumb = turn.attach.find((a) => a.kind === 'image')?.url;
  const lineKind = !first || first.kind === 'image' ? turn.kind ?? 'receipt' : /\.csv$/i.test(first.name) ? 'csv' : /\.ics$/i.test(first.name) ? 'ics' : first.kind === 'pdf' ? 'pdf' : turn.kind ?? 'text';
  // what Use sample replays: a photo has the receipt; a file has none (Try again sends it once more); words have the planner
  const sample: 'planner' | 'receipt' | null = turn.paths?.images.length ? 'receipt' : files ? null : 'planner';
  const again = () => send(turn.paths ? { text: turn.said, ...turn.paths } : { text: turn.said }, turn.said, { replace: turn.id, attach: turn.attach });
  const live = chat ? {} : { role: 'status' as const };
  return (
    <div className="turn" data-turn={turn.id}>
      {files && <SentTiles items={turn.attach} />}
      {!(files && turn.said === ATTACH_ONLY_TEXT) && <p className="said">{turn.said}</p>}
      {/* an answer speaks for itself (board ClairAsk): the line goes once it has nothing to say */}
      {(line || !turn.answer) && (
        <p className={`cs-line${latest ? '' : ' past'}`} {...live}>
          {latest && <Spool expr={expr} size={30} />}
          <span>{line}</span>
        </p>
      )}
      {turn.thinking && <Thinking turn={turn} />}
      {files && turn.understood && <UnderstandingLine thumb={thumb} kind={lineKind} text={turn.understood} />}
      {!files && turn.status && turn.understood && <p className="cs-understood">{turn.understood}</p>}
      {waitingOn > 0 && (
        <div className="sec">
          <span>Waiting for your OK · {waitingOn} {waitingOn === 1 ? 'app' : 'apps'}</span>
          {onOpenChat && <button type="button" className="sec-link" onClick={onOpenChat}>Open in chat <span aria-hidden="true">›</span></button>}
        </div>
      )}
      {turn.cards.map((c, i) => (
        <ProposalCard key={c.id} cs={c} delay={STAGGER[Math.min(i, 2)]}
          onBuild={c.kind === 'app' ? (cs) => { setBuildDraft({ cs, sentence: turn.said }); openClair(false); nav('/build'); } : undefined}
          onStitched={(done) => { markStitched(cid, turn.id, done); onLanded?.(turn); }}
          onUndone={() => markUndone(cid, turn.id, c.id)} />
      ))}
      {turn.stitched && turn.offer && <OfferCard offer={turn.offer} />}
      {turn.answer && (
        <div className="chalk cs-answer arrive">
          <p className="answer" {...(chat ? {} : { 'aria-live': 'polite' as const })}><Bold text={turn.answer} /></p>
          {turn.done && <Sources keys={turn.sources} cls="in" />}
        </div>
      )}
      {turn.error && <p className="err cs-err" role="alert">{turn.error}</p>}
      {empty && (
        <div className="cs-empty arrive">
          <p className="err cs-err" role="alert">I understood that but couldn't draft the change. Nothing was changed.</p>
          <button type="button" className="outline" onClick={again}>Try again</button>
        </div>
      )}
      {turn.slow && !turn.cards.length && !turn.cancelled && !empty && (
        <span className="sample-row arrive">
          {sample
            ? <button type="button" className="outline" onClick={() => send({ fixture: sample }, turn.said, { replace: turn.id, attach: turn.attach })}>Use sample</button>
            : <button type="button" className="outline" onClick={again}>Try again</button>}
          <span className="muted">{sample ? 'A recorded run, marked "sample".' : 'The same files, sent once more.'}</span>
        </span>
      )}
      {/* a capture's cards already name their apps (board ClairResult); sources stand alone only without an answer or a card */}
      {!turn.answer && !turn.cards.length && turn.done && <Sources keys={turn.sources} cls="alone" />}
      {onOpenChat && waitingOn === 0 && (turn.done || turn.cards.length > 0) && <button type="button" className="link cs-open" onClick={onOpenChat}>Open in chat <span aria-hidden="true">›</span></button>}
    </div>
  );
}

/** What a saved card did, in a line: read back after a reload, so there is no card to confirm and no Undo (that lives in the card, in this session). */
function stub(status: string, names: string): string {
  if (status === 'stitched') return names ? `Added to ${names}` : 'Changes saved';
  if (status === 'undone') return 'Undone';
  if (status === 'dismissed') return 'Not added';
  return 'Waiting for your OK. It stays on Home.';
}

/**
 * Saved messages, read from the archive or the server, shown before the live turns. Your words, Clair's answer as a chalk card with its
 * sources, one stub line per card. Nothing here is confirmable: a card still waiting for OK waits on Home.
 */
export function PastView({ msgs }: { msgs: SavedMsg[] }) {
  const apps = useStore((s) => s.home?.apps) ?? [];
  const name = (k: string) => apps.find((a) => a.key === k)?.name ?? k;
  return (
    <>
      {msgs.map((m, i) => (
        <Fragment key={i}>
          {m.role === 'user' ? <p className="said">{m.text}</p> : (
            <div className="turn past">
              {m.text && (
                <div className="chalk cs-answer">
                  <p className="answer"><Bold text={m.text} /></p>
                  <Sources keys={m.sources ?? []} cls="in" />
                </div>
              )}
              {!m.text && !m.cards?.length && !m.csId && m.sources?.length ? <Sources keys={m.sources} cls="alone" /> : null}
              {m.cards?.map((c, k) => (
                <p key={k} className="cs-stub">
                  <span className="cs-stub-i" aria-hidden="true"><Icon name="check" size={16} sw={2} /></span>
                  <span><b>{c.title}</b> <span className="cs-stub-s">{stub(c.status, listNames(c.apps.map(name)))}</span></span>
                </p>
              ))}
              {m.csId && !m.cards && (
                <p className="cs-stub">
                  <span className="cs-stub-i" aria-hidden="true"><Icon name="check" size={16} sw={2} /></span>
                  <span>Changes saved</span>
                </p>
              )}
            </div>
          )}
        </Fragment>
      ))}
    </>
  );
}
