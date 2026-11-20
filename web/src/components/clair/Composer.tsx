import { useLayoutEffect, type RefObject } from 'react';
import { Icon } from '../Icon';
import { AttachButtons, AttachTray, type AttachmentsApi, useRoomy } from '../attach';
import { Glyph } from '../ListeningPanel';

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onTalk: () => void;
  inputRef?: RefObject<HTMLTextAreaElement | null>;
  placeholder: string;
  /** the field's resting height in lines */
  rows?: number;
  /** a follow-up field pinned at the bottom: 48 tall */
  compact?: boolean;
  /** it grows with what is typed, up to this many pixels (5 lines in the chat) */
  max?: number;
  /** a send is on its way: Enter and the button wait */
  disabled?: boolean;
  /** photos and files for the turn: the tray above the field and the Photo and File buttons in the slot */
  attach?: AttachmentsApi;
  /** Send may go (words, or an attachment that is ready, and nothing still preparing); without it, words decide */
  sendable?: boolean;
};

/**
 * The field row of the Clair sheet (start state and pinned follow-up) and of the Chat screen: the field with its send, then the
 * attachment slot, then Talk. Enter sends, Shift+Enter is a new line. The slot is where Photo and File chips go
 * (agent A wires `components/attach/` into it); it takes no room while it is empty.
 */
export function Composer({ value, onChange, onSubmit, onTalk, inputRef, placeholder, rows = 1, compact, max = 120, disabled, attach, sendable }: Props) {
  // the field grows with its text: back to one line first, so deleting shrinks it
  useLayoutEffect(() => {
    const el = inputRef?.current;
    if (!el) return;
    el.style.height = 'auto';
    if (el.scrollHeight > el.clientHeight + 1) el.style.height = `${Math.min(el.scrollHeight, max)}px`;
  }, [value, inputRef, max]);
  const blocked = disabled || !(sendable ?? !!value.trim());
  const roomy = useRoomy();
  return (
    <div className="cs-composer">
    {attach && (attach.list.length > 0 || !!attach.notice) && <AttachTray items={attach.list} onRemove={attach.remove} onRetry={attach.retry} notice={attach.notice} />}
    <div className="cs-fieldrow">
      <div className={`field cs-field${compact ? ' compact' : ''}`}>
        <textarea ref={inputRef} rows={rows} value={value} aria-label="Tell Clair anything" enterKeyHint="send" placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); if (!disabled) onSubmit(); } }} />
        <button type="button" className="send" onMouseDown={(e) => e.preventDefault()} onClick={onSubmit} disabled={blocked} aria-label="Send to Clair"><Icon name="up" size={20} sw={1.8} /></button>
      </div>
      <div className="clair-attach-slot">{attach && compact && <AttachButtons variant={roomy ? 'icons' : 'one'} onFiles={attach.add} />}</div>
      <button type="button" className="cs-talk" onClick={onTalk} aria-label="Talk to Clair"><Glyph name="mic" size={20} /></button>
    </div>
    {attach && !compact && <AttachButtons variant="chips" onFiles={attach.add} />}
    </div>
  );
}
