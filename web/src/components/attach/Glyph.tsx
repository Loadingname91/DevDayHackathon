// Line glyphs for the attachment pieces, on the 24 px grid of components/Icon.tsx. The camera, the paperclip and the file
// are drawn as on the boards ClairSheet and ClairShare; the rest match them.
const P = {
  camera: 'M4 8h3l2-3h6l2 3h3v11H4zM12 9.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7',
  clip: 'M19.5 11.5l-7.8 7.8a4.6 4.6 0 0 1-6.5-6.5l8.2-8.2a3.1 3.1 0 0 1 4.4 4.4l-8 8a1.5 1.5 0 0 1-2.2-2.2l7.3-7.3',
  file: 'M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6',
  table: 'M4 5h16v14H4zM4 10h16M4 15h16M10 5v14',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
  receipt: 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h4',
  close: 'M6 6l12 12M18 6L6 18',
  retry: 'M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5',
} as const;
export type GlyphName = keyof typeof P;

export function Glyph({ name, size = 20, sw = 1.8 }: { name: GlyphName; size?: number; sw?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: 'none' }}>
      <path d={P[name]} />
    </svg>
  );
}

/** The glyph for a kind of input, from the `understood` event's `kind` (clair-agent.md §7) or an attachment's own kind. */
export function glyphFor(kind: string): GlyphName {
  switch (kind) {
    case 'receipt': return 'receipt';
    case 'calendar': case 'schedule': case 'ics': return 'calendar';
    case 'csv': case 'table': return 'table';
    case 'pdf': case 'syllabus': case 'document': case 'text': case 'note': return 'file';
    default: return 'camera';
  }
}
