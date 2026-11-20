import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ago } from '../lib/chats';
import { RM } from '../lib/motion';
import { useStore } from '../lib/store';
import { bootChat, canContinue, chatRows, newChat, openThread, registerChatVoice, send, surface, TRY, useTurns } from '../lib/turns';
import { beginTalk, NOT_HEARD, TYPE_INSTEAD, useTalk } from '../lib/voice';
import { useWide } from '../lib/useWide';
import { DropHint, useAttachments, useDropPaste } from '../components/attach';
import { ChatList } from '../components/clair/ChatList';
import { Composer } from '../components/clair/Composer';
import { Drawer } from '../components/clair/Drawer';
import { CG } from '../components/clair/Glyph';
import { PastView, TurnView } from '../components/clair/TurnView';
import { Icon } from '../components/Icon';
import { ListeningPanel } from '../components/ListeningPanel';
import { Spool } from '../components/Spool';

/**
 * The Chat screen, behind "Open chat ›" (board Clair): the current chat as a conversation, with the history of chats beside it
 * (a rail on a laptop, a drawer from the header's list button on a phone). The sheet and this screen share one turn engine
 * (lib/turns.ts): a turn started in the sheet carries on here, cards stay confirmable with the same Undo. The field is pinned
 * at the bottom, grows to 5 lines, Enter sends and Shift+Enter is a new line. CSS in styles/chat.css.
 */
export function Chat() {
  const wide = useWide();
  const nav = useNavigate();
  const ts = useTurns();
  const user = useStore((s) => s.me?.user.id);
  const credits = useStore((s) => s.me?.credits.left);
  const sheetOpen = useStore((s) => s.clairOpen);
  const talk = useTalk();
  const chat = ts.convs[ts.current];
  const last = chat.turns[chat.turns.length - 1];
  const blocked = !!last && !last.done && !last.cancelled && !last.slow; // a turn is running: one at a time
  const talking = talk.phase !== 'idle' && !sheetOpen; // a hold from the laptop's sidebar talks in the sheet, not here
  const empty = !chat.past.length && !chat.turns.length;
  const [text, setText] = useState('');
  const [note, setNote] = useState<string | null>(null);
  // photos and files for the next turn: drop them anywhere on the chat, or paste a screenshot into the field
  const att = useAttachments({ workspaceId: useStore((s) => s.me?.workspace.id) });
  const main = useRef<HTMLElement>(null);
  const [drawer, setDrawer] = useState(false);
  const [inert, setInert] = useState(false);
  const input = useRef<HTMLTextAreaElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const stuck = useRef(true); // the log follows new words only while it is at the bottom
  const seen = useRef({ id: '', turns: 0 });
  const readOnly = chat.readOnly;
  const { dragging } = useDropPaste(main, att.add, { enabled: !readOnly });
  const can = canContinue(ts, chat);
  const rows = chatRows(ts);

  useEffect(() => { surface.chat = true; return () => { surface.chat = false; }; }, []);
  useEffect(() => { if (user) void bootChat(user); }, [user]);
  useEffect(() => { if (sheetOpen) setDrawer(false); }, [sheetOpen]);
  useEffect(() => { if (wide) setDrawer(false); }, [wide]);
  const focusField = () => { if (matchMedia('(pointer: fine)').matches) setTimeout(() => input.current?.focus({ preventScroll: true }), 0); };

  const go = (body: Parameters<typeof send>[0], said: string, o?: Parameters<typeof send>[2]) => {
    if (blocked) return false;
    stuck.current = true;
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
  // a Talk started on this screen: Send and Cancel in place of the field; what it heard is sent, held for Edit, or noted
  useEffect(() => registerChatVoice((o) => {
    switch (o.kind) {
      case 'send': go({ transcript: o.text, voice: true }, o.text); break;
      case 'edit': setText(o.text); setNote('Is that right? Edit it, then send.'); focusField(); break;
      case 'none': setNote(NOT_HEARD); break;
      case 'unavailable': setNote(TYPE_INSTEAD); focusField(); break;
      case 'cancel': break;
    }
  }));

  // follow the conversation: to the bottom when a chat opens or a turn is added, and while it grows if the person has not scrolled up
  const sig = `${chat.id}|${chat.past.length}|${chat.turns.map((t) => `${t.id}.${t.cards.length}.${t.answer.length}.${t.thinking.length}.${t.done}.${t.status ?? ''}.${t.stitched}.${t.slow}`).join(',')}`;
  useLayoutEffect(() => {
    const el = log.current;
    if (!el) return;
    const swapped = seen.current.id !== chat.id, added = chat.turns.length > seen.current.turns;
    seen.current = { id: chat.id, turns: chat.turns.length };
    if (swapped) stuck.current = true;
    if (stuck.current) el.scrollTo({ top: el.scrollHeight, behavior: swapped || RM() || !added ? 'auto' : 'smooth' });
  }, [sig]); // eslint-disable-line react-hooks/exhaustive-deps

  const back = () => { if ((window.history.state?.idx ?? 0) > 0) nav(-1); else nav('/'); };
  const fresh = () => { newChat(); setText(''); setNote(null); focusField(); };
  const noteEl = note && <p className="cs-note" role="status">{note}</p>;

  return (
    <div className={`chat${wide ? ' wide' : ''}`}>
      {wide && <aside className="chat-rail" aria-label="Chats"><ChatList onPick={focusField} /></aside>}
      <section ref={main} className="chat-main" inert={inert}>
        <header className="chat-head">
          {!wide && <button type="button" className="round chat-back" onClick={back} aria-label="Back"><Icon name="back" size={22} sw={1.8} /></button>}
          <span className="cs-mark" aria-hidden="true"><Icon name="spool" size={20} sw={1.8} /></span>
          <span className="chat-titles">
            <span className="chat-t"><h1>Ask Clair</h1>{credits !== undefined && <Link to="/you" className="pill soft num chat-credits">{credits} credits <span aria-hidden="true">›</span></Link>}</span>
            <span className="cs-sub">Answers from your apps first</span>
          </span>
          {!wide && <>
            <button type="button" className="round chat-ico" onClick={fresh} aria-label="New chat"><CG name="plus" size={22} /></button>
            <button type="button" className="round chat-ico" onClick={() => setDrawer(true)} aria-label="Chat history" aria-expanded={drawer} aria-haspopup="dialog"><CG name="list" size={22} /></button>
          </>}
        </header>

        <div ref={log} className="chat-log" role="log" aria-live="polite" aria-relevant="additions text" aria-label="Conversation" tabIndex={0}
          onScroll={(e) => { const el = e.currentTarget; stuck.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80; }}>
          <div key={chat.id} className="chat-swap">
            {empty ? (
              <div className="chat-empty">
                <Spool expr="hello" size={96} />
                <p className="chat-empty-t">{rows.length ? 'Ask Clair something.' : 'No chats yet. Ask Clair something.'}</p>
                <p className="chat-empty-s">Answers come from your apps. Anything it would change waits for your OK.</p>
              </div>
            ) : (
              <>
                {chat.demo && <p className="chat-from">A sample chat, not from your apps.</p>}
                <PastView msgs={chat.past} />
                {chat.turns.map((t, i) => <TurnView key={t.id} turn={t} cid={chat.id} variant="chat" latest={i === chat.turns.length - 1} />)}
              </>
            )}
          </div>
        </div>

        <footer className="chat-foot">
          {talking ? <ListeningPanel head={{}} /> : readOnly ? (
            <div className="chat-closed">
              <p>{chat.demo ? 'This is a sample chat.' : can ? `From ${ago(chat.last)}.` : `From ${ago(chat.last)}. Start a new chat to ask more.`}</p>
              <div className="btns">
                {can && <button type="button" className="cta" onClick={() => { openThread(chat.id, { resume: true }); focusField(); }}>Continue</button>}
                <button type="button" className={can ? 'ghost' : 'outline'} onClick={fresh}>New chat</button>
              </div>
            </div>
          ) : (
            <>
              <div className="chips scroll chat-chips" aria-label="Suggestions">
                {TRY.map((s) => <button key={s.text} type="button" className="chip" disabled={blocked} onClick={() => go({ text: s.text }, s.text)}>{s.text}</button>)}
              </div>
              {noteEl}
              <Composer value={text} onChange={(v) => { setText(v); setNote(null); }} onSubmit={submit} onTalk={() => beginTalk('tap')} inputRef={input}
                compact rows={1} max={136} disabled={blocked} attach={att} sendable={sendable} placeholder="Ask Clair, or tell it something…" />
            </>
          )}
        </footer>
        <DropHint show={dragging} />
      </section>
      {!wide && <Drawer open={drawer} onClose={() => setDrawer(false)} label="Chat history" onInert={setInert}><ChatList onPick={() => setDrawer(false)} /></Drawer>}
    </div>
  );
}
