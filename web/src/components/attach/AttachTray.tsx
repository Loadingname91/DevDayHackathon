import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { type Attachment, sizeText, typeName } from '../../lib/attachments';
import { RM, T } from '../../lib/motion';
import { Glyph, glyphFor } from './Glyph';

type Shown = Attachment & { leaving?: boolean };

/** Keeps a removed tile on screen while it fades (140 ms), in its own place, then lets it go. New tiles append. */
function useLeaving(items: Attachment[]): Shown[] {
  const [shown, setShown] = useState<Shown[]>(items);
  const prev = useRef<Shown[]>(items);
  useLayoutEffect(() => {
    const was = prev.current;
    const now = new Map(items.map((a) => [a.id, a] as const));
    const next: Shown[] = was.map((a) => (now.has(a.id) ? now.get(a.id)! : a.leaving ? a : { ...a, leaving: true }));
    for (const a of items) if (!was.some((w) => w.id === a.id)) next.push(a);
    prev.current = next;
    setShown(next);
  }, [items]);
  const leaving = shown.some((a) => a.leaving);
  useEffect(() => {
    if (!leaving) return;
    const t = setTimeout(() => {
      prev.current = prev.current.filter((a) => !a.leaving);
      setShown(prev.current);
    }, RM() ? T.fb : T.stateOut);
    return () => clearTimeout(t);
  }, [leaving, shown]);
  return shown;
}

const busyText = (a: Attachment) => (a.state === 'preparing' ? 'Preparing…' : a.state === 'uploading' || a.state === 'ready' ? 'Uploading…' : null);

function Ring() {
  return <svg className="at-ring" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /></svg>;
}

function Tile({ a, onRemove, onRetry }: { a: Shown; onRemove: (id: string) => void; onRetry: (id: string) => void }) {
  const busy = busyText(a);
  const glyph = glyphFor(a.kind === 'text' ? (a.name.toLowerCase().endsWith('.csv') ? 'csv' : a.name.toLowerCase().endsWith('.ics') ? 'ics' : 'text') : a.kind);
  if (a.state === 'error') {
    return (
      <li className="at-tile at-err" data-state="error" data-leaving={a.leaving ? '' : undefined}>
        <svg className="at-edge" aria-hidden="true"><rect x="0" y="0" width="100%" height="100%" rx="15" /></svg>
        <span className="at-ico" aria-hidden="true"><Glyph name={glyph} size={18} /></span>
        <span className="at-meta">
          <span className="at-name">{a.name}</span>
          <span className="at-sub" role="alert">{a.error}</span>
        </span>
        {a.retry && <button type="button" className="at-act" onClick={() => onRetry(a.id)} aria-label={`Retry ${a.name}`}>Retry</button>}
        <button type="button" className="at-act" onClick={() => onRemove(a.id)} aria-label={`Remove ${a.name}`}>Remove</button>
      </li>
    );
  }
  const x = (
    <button type="button" className="at-x" onClick={() => onRemove(a.id)} aria-label={`Remove ${a.name}`}>
      <span aria-hidden="true"><Glyph name="close" size={14} sw={2.2} /></span>
    </button>
  );
  if (a.kind === 'image') {
    return (
      <li className="at-tile at-pic" data-state={a.state} data-leaving={a.leaving ? '' : undefined} aria-busy={!!busy}>
        <span className="at-thumb">{a.preview && <img src={a.preview} alt="" draggable={false} />}{busy && <Ring />}</span>
        <span className="sr">{a.name}{busy ? `, ${busy}` : ''}</span>
        {x}
      </li>
    );
  }
  return (
    <li className="at-tile at-doc" data-state={a.state} data-leaving={a.leaving ? '' : undefined} aria-busy={!!busy}>
      <span className="at-ico" aria-hidden="true">{busy ? <Ring /> : <Glyph name={glyph} size={18} />}</span>
      <span className="at-meta">
        <span className="at-name">{a.name}</span>
        <span className="at-sub">{busy ?? `${typeName(a)} · ${sizeText(a.size)}`}</span>
      </span>
      {x}
    </li>
  );
}

/**
 * The attachments above the field: a strip that scrolls sideways. A photo is a 56 px thumbnail of the prepared picture; a PDF,
 * CSV, ICS or text file is a typed tile with its name and size. Each has a 44 px remove button; a failed one shows a frayed
 * edge, the reason in words, and Retry (an upload) and Remove. A tile arrives in 220 ms (opacity and 8 px of rise) and leaves in
 * 140; reduced motion keeps the fades. `notice` is the one plain line under it ("Up to 5 per message").
 */
export function AttachTray({ items, onRemove, onRetry, notice }: { items: Attachment[]; onRemove: (id: string) => void; onRetry: (id: string) => void; notice?: string | null }) {
  const shown = useLeaving(items);
  return (
    <div className="at-tray" data-empty={shown.length ? undefined : ''}>
      {shown.length > 0 && (
        <ul className="at-strip scroll-x" aria-label="Attachments">
          {shown.map((a) => <Tile key={a.id} a={a} onRemove={onRemove} onRetry={onRetry} />)}
        </ul>
      )}
      <p className="at-notice" role="status">{notice ?? ''}</p>
    </div>
  );
}
