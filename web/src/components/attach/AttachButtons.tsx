import { useRef, useSyncExternalStore, type ChangeEvent } from 'react';
import { Glyph } from './Glyph';

const COARSE = '(pointer: coarse)';
const subscribe = (cb: () => void) => { const m = matchMedia(COARSE); m.addEventListener('change', cb); return () => m.removeEventListener('change', cb); };
/** A touch device: the Photo chip opens the camera. A laptop opens a plain picker (ADR-010, FR-C3). */
export const useCoarse = () => useSyncExternalStore(subscribe, () => matchMedia(COARSE).matches, () => false);

const ROOMY = '(min-width: 600px)';
const subRoomy = (cb: () => void) => { const m = matchMedia(ROOMY); m.addEventListener('change', cb); return () => m.removeEventListener('change', cb); };
/** Room for two buttons beside a field (a laptop or a tablet); a phone's field row has room for one. */
export const useRoomy = () => useSyncExternalStore(subRoomy, () => matchMedia(ROOMY).matches, () => false);

type Variant = 'icons' | 'chips' | 'one';

/**
 * Photo and File, the two ways to attach (boards ClairSheet and ClairShare). Photo takes a picture on a phone
 * (`capture="environment"`) and picks one on a laptop; File takes a PDF, a picture or a text, CSV or ICS file, several at once.
 * Both are real buttons that open a hidden file input, so the keyboard reaches them.
 * `variant`: `chips` are labelled (the sheet's start state, under the field, like the board); `icons` are 44 px squares for a field
 * row with room; `one` is a single paperclip for a narrow row: the file input accepts pictures too, so a phone's own sheet still
 * offers "Take Photo".
 */
export function AttachButtons({ onFiles, disabled, labelled, variant }: { onFiles: (files: File[]) => void; disabled?: boolean; labelled?: boolean; variant?: Variant }) {
  const v: Variant = variant ?? (labelled ? 'chips' : 'icons');
  const coarse = useCoarse();
  const photo = useRef<HTMLInputElement>(null);
  const file = useRef<HTMLInputElement>(null);
  const picked = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = ''; // the same file picked twice must still fire
    if (files.length) onFiles(files);
  };
  const lab = v === 'chips';
  return (
    <div className={`at-btns${lab ? ' lab' : ''}`} role="group" aria-label="Attach">
      {v !== 'one' && (
        <>
          <button type="button" className="at-btn" disabled={disabled} onClick={() => photo.current?.click()} aria-label={coarse ? 'Take a photo' : 'Add a photo'}>
            <Glyph name="camera" />{lab && <span>Photo</span>}
          </button>
          <input ref={photo} type="file" accept="image/*" capture={coarse ? 'environment' : undefined} hidden tabIndex={-1} onChange={picked} data-at="photo" />
        </>
      )}
      <button type="button" className="at-btn" disabled={disabled} onClick={() => file.current?.click()} aria-label={v === 'one' ? 'Attach a photo or file' : 'Attach a file'}>
        <Glyph name="clip" />{lab && <span>File</span>}
      </button>
      <input ref={file} type="file" multiple accept="application/pdf,image/*,.csv,.txt,.ics,.md,text/*" hidden tabIndex={-1} onChange={picked} data-at="file" />
    </div>
  );
}
