import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import type { Patch } from '../api/types';
import { Bold } from '../components/Bold';
import { Icon } from '../components/Icon';
import { ProposalCard } from '../components/ProposalCard';
import { Roll } from '../components/Roll';
import { Notch, Tag } from '../components/Tag';
import { useFresh } from '../lib/fresh';
import { EASE, exitUp, flip, RM, T } from '../lib/motion';
import { NextUp } from '../components/NextUp';
import { loadHome, sewn, useStore } from '../lib/store';
import { useWide } from '../lib/useWide';

// Home, from the Main board (design/screens-css.md §4, §11): logo and avatar, the greeting and
// status sentence, Needs your OK (one card, "Show N more"), the Next up thread, the quilt.

type Size = { w: number; h: number; fixed?: boolean }; // w in columns of the 6-column quilt, h in rows
type Place = { c: number; span: number; r: number; rows: number }; // grid column and row, 0-based
const COLS = 6;

/**
 * The quilt with no holes: first fit (dense) on a 6-column grid, most used first. A patch is 2 or 3 columns wide (a long face
 * or name takes 3 or more, see spanOf); then every row is justified: a gap in a row is closed by stretching the one-row patches
 * that begin in it, and a gap with nothing beginning in it is closed by the patches above growing down. The tall patch keeps
 * to the right edge (Workout on the board) and the "+" patch keeps its width unless it is alone in its row.
 */
function pack(sizes: Size[]): Place[] {
  const taken: boolean[][] = [];
  const fits = (r: number, c: number, w: number, h: number) => {
    for (let y = r; y < r + h; y++) for (let x = c; x < c + w; x++) if (taken[y]?.[x]) return false;
    return true;
  };
  const out: Place[] = sizes.map(({ w, h }) => {
    for (let r = 0; r < 200; r++) {
      for (let k = 0; k + w <= COLS; k++) {
        const c = h > 1 && w <= 3 ? COLS - w - k : k;
        if (!fits(r, c, w, h)) continue;
        for (let y = r; y < r + h; y++) for (let x = c; x < c + w; x++) (taken[y] ??= [])[x] = true;
        return { c, span: w, r, rows: h };
      }
    }
    return { c: 0, span: 2, r: 0, rows: 1 };
  });
  const last = Math.max(0, ...out.map((p) => p.r + p.rows - 1));
  for (let r = 0; r <= last; r++) {
    const held = (c: number) => out.some((p) => p.r < r && p.r + p.rows > r && c >= p.c && c < p.c + p.span); // a patch from above runs through here
    for (let c = 0; c < COLS;) {
      if (held(c)) { c++; continue; }
      let e = c;
      while (e < COLS && !held(e)) e++;
      const run = out.map((_, i) => i).filter((i) => out[i].r === r && out[i].c >= c && out[i].c < e).sort((a, b) => out[a].c - out[b].c);
      const used = run.reduce((n, i) => n + out[i].span, 0);
      if (run.length && used < e - c) {
        // only one-row patches stretch: a tall one would run into what sits under the gap
        const flat = run.filter((i) => out[i].rows === 1);
        const flex = flat.filter((i) => !sizes[i].fixed);
        const grow = flex.length ? flex : flat;
        let spare = e - c - used;
        grow.forEach((i, k) => { const add = Math.ceil(spare / (grow.length - k)); out[i].span += add; spare -= add; });
        if (!spare) { let x = c; run.forEach((i) => { out[i].c = x; x += out[i].span; }); }
      } else if (!run.length) {
        // nothing begins in this gap: the patches just above grow down into it
        out.forEach((p) => { if (p.r + p.rows === r && p.c >= c && p.c + p.span <= e) p.rows += 1; });
      }
      c = e;
    }
  }
  return out;
}

/**
 * How many of the 6 columns a patch takes, from the length of its words (the client never rewrites the server's text, so a
 * long face gets room instead). 2 columns hold about 11 characters at 390 px, 3 hold 18, 4 hold 30; names are 13 px and a
 * little narrower per character but carry an icon.
 */
const spanOf = (p: Patch): number => {
  const face = `${p.face.text} ${p.face.label}`.length, name = p.name.length;
  return face <= 11 && name <= 10 ? 2 : face <= 18 && name <= 14 ? 3 : face <= 30 && name <= 22 ? 4 : 6;
};

const area = (p: Place): CSSProperties => ({ gridColumn: `${p.c + 1} / span ${p.span}`, gridRow: `${p.r + 1} / span ${p.rows}` });

function PatchTile({ p, place, big, tall, sewing }: { p: Patch; place: Place; big: boolean; tall: boolean; sewing: boolean }) {
  const ref = useRef<HTMLAnchorElement>(null);
  // "just changed" pays off once: the seam draws itself (styles/motion.css, theme-cloth.css) on the commit where the patch becomes
  // changed, as its number starts to roll. A patch that is already changed when Home paints just has the seam.
  const changed = !!(p.changed || p.isNew);
  const was = useRef(changed);
  const [glint, setGlint] = useState(false);
  const live = useFresh(`patch:${p.key}`, p.changed && !p.isNew); // the chip/notch let go after FRESH_MS; opening the app clears `changed` sooner
  useLayoutEffect(() => {
    const became = changed && !was.current;
    was.current = changed;
    if (!changed) { setGlint(false); return; }
    if (!became || RM()) return;
    setGlint(true); // layout effect: the next render lands before the first paint, so the stitch never flashes gold
    const t = setTimeout(() => setGlint(false), T.focal + 400);
    return () => clearTimeout(t);
  }, [changed]);
  // a new app sews onto Home: slides in from the left with its "new" tag (catalogue: "Dock insert", 350)
  useLayoutEffect(() => {
    if (!sewing || !ref.current) return;
    ref.current.animate(RM() ? [{ opacity: 0 }, { opacity: 1 }] : [{ opacity: 0, transform: 'translateX(-24px)' }, { opacity: 1, transform: 'none' }], { duration: RM() ? T.fb : T.layout, easing: EASE });
    ref.current.scrollIntoView({ block: 'center', behavior: RM() ? 'auto' : 'smooth' }); // centred, clear of the bar and the toast
    const t = setTimeout(() => sewn(p.key), T.layout);
    return () => clearTimeout(t);
  }, [sewing, p.key]);
  return (
    <Link ref={ref} to={`/a/${p.key}`} className={`patch${big ? ' big' : ''}${tall ? ' tall' : ''}`} style={area(place)}
      data-dye={p.dye} data-thread-target={p.key} data-f={`p-${p.key}`} data-glint={glint ? '' : undefined}
      aria-label={`${p.name}, ${p.face.text} ${p.face.label}${p.isNew ? ', new' : live ? ', just changed' : ''}`}>
      <span className="name"><Icon name={p.icon} size={16} sw={1.8} /><span className="nm">{p.name}</span></span>
      {big
        ? <Tag show={p.changed || !!p.isNew} text={p.isNew ? 'new' : 'just changed'} id={p.isNew ? undefined : `patch:${p.key}`} />
        : <Notch show={!!(p.changed || p.isNew)} id={`patch:${p.key}`} className="notch2" />}
      <span className="face"><span className="fig"><Roll text={p.face.text} className="num" /></span><span className="unit">{p.face.label}</span></span>
    </Link>
  );
}

/** "**$412** left this month. Pull day at **6 pm**." Figures in bold; the leading money figure rolls when it changes. */
function Status({ text }: { text: string }) {
  const m = /^(\*\*)?(\$[\d,.]+)\1([\s\S]*)$/.exec(text);
  if (!m) return <p className="status"><Bold text={text} /></p>;
  return <p className="status">{m[1] ? <b className="num"><Roll text={m[2]} /></b> : <Roll text={m[2]} />}<Bold text={m[3]} /></p>;
}

export function Home() {
  const home = useStore((s) => s.home);
  const error = useStore((s) => s.error);
  const sewing = useStore((s) => s.sewing);
  const wide = useWide();
  const [more, setMore] = useState(false);
  const [find, setFind] = useState('');
  const queue = useRef<HTMLElement>(null);
  useEffect(() => { void loadHome(); }, []);
  if (!home) return <div className="screen home"><p className="muted" role="status">{error ?? ''}</p></div>;

  const cards = home.needsOk.flatMap((c) => (c.kind === 'change_set' ? [c.change_set] : []));
  const shown = more ? cards : cards.slice(0, 1);

  // Queue advance (catalogue: Home): the handled card exits up, everything below FLIPs, the next card enters
  const advance = async (id: string) => {
    const el = queue.current?.querySelector(`[data-f="${id}"]`) ?? null;
    await exitUp(el);
    const root = document.querySelector<HTMLElement>('.screen');
    if (root) await flip(root, () => loadHome()); else await loadHome();
  };

  // Your apps: Budget leads as the big patch, then by last opened; Workout is the tall one (Main board).
  // While finding, every match is a plain patch.
  const q = find.trim().toLowerCase();
  const byUse = [...home.apps].sort((a, b) => b.lastOpened.localeCompare(a.lastOpened));
  const budget = byUse.find((a) => a.key === 'budget');
  const ordered = budget ? [budget, ...byUse.filter((a) => a !== budget)] : byUse;
  const list = q ? ordered.filter((a) => a.name.toLowerCase().includes(q)) : ordered;
  const bigKey = !q && budget ? budget.key : null;
  const tallKey = q ? null : (list.find((a) => a.key === 'workout') ?? list.find((a) => a.key !== bigKey))?.key ?? null;
  const places = pack([
    ...list.map((p): Size => (p.key === bigKey ? { w: 4, h: 2 } : p.key === tallKey ? { w: Math.min(3, spanOf(p)), h: 2 } : { w: spanOf(p), h: 1 })),
    { w: 2, h: 1, fixed: true },
  ]);

  return (
    <div className="screen home">
      <div className="home-top">
        <span className="logo">
          <svg className="logo-mark" width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
            <rect x="1" y="1" width="9" height="9" rx="2" /><rect x="12" y="1" width="9" height="9" rx="2" />
            <rect x="1" y="12" width="9" height="9" rx="2" /><rect x="12" y="12" width="9" height="9" rx="2" />
          </svg>
          quilt
        </span>
        <Link to="/you" className="avatar" data-dye="blush" aria-label="You and settings"><Icon name="user" size={18} sw={1.8} /></Link>
      </div>
      <header className="greet">
        <h1>{home.greeting}</h1>
        <Status text={home.status} />
      </header>
      <div className="home-grid">
        <div className="col">
          {cards.length > 0 && (
            <section className="section" aria-label="Needs your OK" ref={queue} data-f="queue">
              <h2 className="sec"><span>Needs your OK · <span className="n num">{cards.length}</span></span></h2>
              {shown.map((cs) => (
                <ProposalCard key={cs.id} cs={cs}
                  onDismissed={() => void advance(cs.id)} onStitched={() => setTimeout(() => void advance(cs.id), 400)} />
              ))}
              {cards.length > 1 && (
                <button type="button" className="link" aria-expanded={more} onClick={() => setMore(!more)}>
                  {more ? 'Show one at a time' : `Show ${cards.length - 1} more`}
                </button>
              )}
            </section>
          )}
          {!wide && <NextUp home={home} />}
        </div>
        <section className="section col" aria-label="Your apps" data-f="apps">
          <h2 className="sec"><span>Your apps · <span className="n num">{home.apps.length}</span></span><span className="meta">Most used first</span></h2>
          <label className="find">
            <Icon name="search" size={16} sw={1.8} />
            <input type="search" value={find} onChange={(e) => setFind(e.target.value)} placeholder="Find an app" aria-label="Find an app" enterKeyHint="search" autoComplete="off" />
          </label>
          <div className="quilt">
            {list.map((p, i) => (
              <PatchTile key={p.key} p={p} place={places[i]} big={p.key === bigKey} tall={p.key === tallKey} sewing={sewing.includes(p.key)} />
            ))}
            <Link to="/build" className="patch newapp" style={area(places[list.length])} aria-label="New app: tell Clair what to track">
              <Icon name="plus" size={18} sw={2} /><span>New app</span>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
