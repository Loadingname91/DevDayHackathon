// Stroke icons, 24 px grid. App icons from design/tools/gen_soft.py ICON; the rest drawn to match.
const P: Record<string, string> = {
  wallet: 'M3 7h15a3 3 0 0 1 3 3v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 7l2-3h12M16 13h2',
  basket: 'M3 4h2l2 11h11l2-8H6M9 20h.01M17 20h.01',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v5M16 3v5',
  check: 'M4 12l5 5L20 6',
  dumbbell: 'M3 9v6M6 7v10M18 7v10M21 9v6M6 12h12',
  book: 'M4 5h6a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H4zM20 5h-6a2 2 0 0 0-2 2v12a2 2 0 0 1 2-2h6z',
  repeat: 'M4 12a8 8 0 0 1 14-5l2 2M20 12a8 8 0 0 1-14 5l-2-2M20 4v5h-5M4 20v-5h5',
  note: 'M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h5',
  flame: 'M12 3c1 3 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3.500 2-4.500 0 2 1 3 2 3 0-3-1-5.500 1-8.500z',
  moon: 'M20 14.500A8 8 0 1 1 9.500 4a6.500 6.500 0 0 0 10.500 10.500z',
  shoe: 'M3 17v-6l4 1 3-4 3 5 6 2a2 2 0 0 1 2 2zM3 20h18',
  drop: 'M12 3c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11z',
  spool: 'M6 3h12M6 21h12M8 3v18M16 3v18M8 8l8 2M8 12l8 2M8 16l8 2',
  arrow: 'M5 12h14M13 6l6 6-6 6',
  up: 'M12 19V5M6 11l6-6 6 6',
  back: 'M15 5l-7 7 7 7',
  fwd: 'M9 5l7 7-7 7',
  close: 'M6 6l12 12M18 6L6 18',
  lock: 'M6 11h12v9H6zM8.500 11V8a3.500 3.500 0 0 1 7 0v3',
  app: 'M5 5h6v6H5zM13 5h6v6h-6zM5 13h6v6H5zM13 13h6v6h-6z',
  plus: 'M12 5v14M5 12h14',
  trash: 'M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13',
  search: 'M11 5a6 6 0 1 0 0 12a6 6 0 1 0 0-12M20 20l-4.5-4.5',
  user: 'M12 5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7M5 20c1.2-3.6 4-5 7-5s5.8 1.4 7 5',
  receipt: 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h4',
  ask: 'M5 4h14v12H9l-4 4zM12 12h.01M10 8a2 2 0 1 1 3 1.7c-.6.4-1 .8-1 1.3',
  build: 'M5 5h6v6H5zM13 5h6v6h-6zM5 13h6v6H5zM13 13h6v6h-6z',
  pause: 'M8 5v14M16 5v14',
  chev: 'M9 6l6 6-6 6',
  logo: '',
  more: 'M6 12h.01M12 12h.01M18 12h.01',
  minus: 'M5 12h14',
  play: 'M8 5l11 7-11 7z',
};
export function Icon({ name, size = 20, sw = 2 }: { name: string; size?: number; sw?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: 'none' }}>
      <path d={(P[name] ?? P.app).replace(/\.500/g, '.5')} />
    </svg>
  );
}
