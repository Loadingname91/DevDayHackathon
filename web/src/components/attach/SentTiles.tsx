import { type Thumb, typeName } from '../../lib/attachments';
import { Glyph, glyphFor } from './Glyph';

const glyphOf = (t: Thumb) => glyphFor(t.kind === 'text' ? (/\.csv$/i.test(t.name) ? 'csv' : /\.ics$/i.test(t.name) ? 'ics' : 'text') : t.kind);

/** What was sent with a turn, above the words (the same tiles as the tray, without Remove). The turn keeps only these names and thumbnails, never the bytes. */
export function SentTiles({ items }: { items: Thumb[] }) {
  if (!items.length) return null;
  return (
    <ul className="at-sent" aria-label="Attached">
      {items.map((t, i) => t.kind === 'image' ? (
        <li key={i} className="at-tile at-pic" data-state="uploaded">
          <span className="at-thumb">{t.url ? <img src={t.url} alt="" draggable={false} /> : <span className="at-ico" aria-hidden="true"><Glyph name="camera" size={18} /></span>}</span>
          <span className="sr">{t.name}</span>
        </li>
      ) : (
        <li key={i} className="at-tile at-doc" data-state="uploaded">
          <span className="at-ico" aria-hidden="true"><Glyph name={glyphOf(t)} size={18} /></span>
          <span className="at-meta"><span className="at-name">{t.name}</span><span className="at-sub">{typeName(t)}</span></span>
        </li>
      ))}
    </ul>
  );
}
