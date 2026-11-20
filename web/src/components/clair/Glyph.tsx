// The few glyphs the bigger Clair needs that Icon.tsx and ListeningPanel.tsx do not have. Drawn on the same 24 px grid, 1.8 stroke.
const P = {
  expand: 'M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7',
  collapse: 'M20 10h-6V4M4 14h6v6M14 10l7-7M10 14l-7 7',
  list: 'M4 7h16M4 12h16M4 17h10',
  plus: 'M12 5v14M5 12h14',
  more: 'M6 12h.01M12 12h.01M18 12h.01',
  pencil: 'M5 19l1-4 10-10 3 3-10 10zM14 6l3 3',
  trash: 'M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13',
  chat: 'M5 5h14v11H10l-4 4v-4H5zM9 9.5h6M9 12.5h4',
  clock: 'M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16M12 8v4l3 2',
  search: 'M11 5a6 6 0 1 0 0 12a6 6 0 1 0 0-12M20 20l-4.5-4.5',
  check: 'M5 12.5l4.5 4.5L19 7',
  back: 'M15 5l-7 7 7 7',
  close: 'M6 6l12 12M18 6L6 18',
};
export type GlyphName = keyof typeof P;
export function CG({ name, size = 20, sw = 1.8 }: { name: GlyphName; size?: number; sw?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: 'none' }}>
      <path d={P[name]} />
    </svg>
  );
}
