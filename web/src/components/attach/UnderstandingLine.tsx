import { Glyph, glyphFor } from './Glyph';

/**
 * FR-C13: the one line before any proposal that says what Clair thinks the input is, with its thumbnail: "Corner Market
 * receipt · 8 items · $35.83". The words come from the run's `understood` event; nothing here works anything out. `thumb` is
 * the photo (an object URL the turn keeps); without one, a glyph for the kind of input stands in (a PDF, a CSV, a calendar).
 */
export function UnderstandingLine({ thumb, kind, text, live }: { thumb?: string; kind: string; text: string; live?: boolean }) {
  return (
    <p className="at-line" role={live ? 'status' : undefined} data-kind={kind}>
      <span className="at-line-thumb" aria-hidden="true">{thumb ? <img src={thumb} alt="" draggable={false} /> : <Glyph name={glyphFor(kind)} size={20} />}</span>
      <span className="at-line-txt">{text}</span>
    </p>
  );
}
