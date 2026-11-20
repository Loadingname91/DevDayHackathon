import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { DatedRow, DaysBlock } from '../../api/types';
import { addDays, day, dayKey, dayNum, dowShort, monthName, time, wall, weekStart } from '../../lib/format';
import { EASE, RM, T } from '../../lib/motion';
import { Icon } from '../Icon';
import { Tag } from '../Tag';
import type { Ctx } from './index';

type View = 'day' | 'week' | 'month';
const HOURS = { from: 6, to: 23, px: 52 }; // the day timeline: 6 am to 11 pm, 52 px an hour
/** The first day of the month before or after the month `k` is in (functional, so quick taps add up). */
const monthStart = (k: string, dir: -1 | 1) => (dir < 0 ? addDays(k.slice(0, 7) + '-01', -1) : addDays(k.slice(0, 7) + '-01', 32)).slice(0, 7) + '-01';

/**
 * Dates from every app (board Calendar): Week is the day strip over an agenda grouped by
 * day; Day is an hour timeline with a now-line; Month is a grid with a dot per item in its
 * app's colour. Tapping a day in the strip or the grid picks it. "From Google" rows are
 * outlined and read-only. Laying out dates is the client's job; counting them is the server's.
 */
export function Days({ block, ctx }: { block: DaysBlock; ctx: Ctx }) {
  const rows = ((ctx.data[block.source] ?? []) as DatedRow[]).filter((r) => !block.apps || block.apps.includes(r.app));
  const today = ctx.now ? dayKey(ctx.now) : '';
  const [view, setView] = useState<View>(block.view);
  const [sel, setSel] = useState(today);
  const [page, setPage] = useState(0); // week view: 7 days from today, then 7-day pages (board Calendar)
  const on = (k: string) => rows.filter((r) => (r.all_day && r.ends ? dayKey(r.at) <= k && k <= dayKey(r.ends) : dayKey(r.at) === k))
    .sort((a, b) => (a.all_day ? -1 : b.all_day ? 1 : a.at < b.at ? -1 : 1));
  const dye = (r: DatedRow) => ctx.apps.find((a) => a.key === r.app)?.dye;
  const appName = (r: DatedRow) => (r.source === 'google' ? 'Google' : ctx.apps.find((a) => a.key === r.app)?.name ?? r.sub);
  const panel = useRef<HTMLDivElement>(null);
  const fresh = useRef(false);
  /** A tap changes the view at once (two quick taps are two steps); the incoming content fades in (140 ms). */
  const swap = (fn: () => void) => {
    fn();
    fresh.current = true;
    requestAnimationFrame(() => { fresh.current = false; }); // nothing rendered: no fade for the next, unrelated render
  };
  useLayoutEffect(() => {
    if (!fresh.current) return;
    fresh.current = false;
    if (!RM()) panel.current?.animate([{ opacity: 0 }, { opacity: 1 }], { duration: T.stateOut, easing: EASE });
  });
  const dayList = useRef<HTMLElement>(null);
  const pickDay = (k: string) => { // the month's day list sits below the 6-row grid: bring it up
    setSel(k);
    requestAnimationFrame(() => {
      const r = dayList.current?.getBoundingClientRect();
      if (r && r.top > innerHeight * 0.55) scrollBy({ top: r.top - innerHeight * 0.4, behavior: RM() ? 'auto' : 'smooth' });
    });
  };

  const agendaRow = (r: DatedRow, i: number, k: string) => (
    <li key={r.record_id + (r.occurrence ?? '') + k} className={`row ag ${r.source === 'google' ? 'google' : ''} ${i ? 'sep' : ''}`} data-dye={dye(r)}>
      <span className="main">
        <span className="t">{r.title}<Tag show={!!r.changed} text="just changed" /></span>
        <span className="from"><i />From {appName(r)}{r.ends && !r.all_day ? ` · until ${time(r.ends)}` : ''}</span>
      </span>
      <span className="ag-at">{r.all_day ? 'All day' : time(r.at).replace(':00 ', ' ')}</span>
    </li>
  );

  const week = () => {
    const start = addDays(today, 7 * page), end = addDays(start, 6);
    const cells = Array.from({ length: 7 }, (_, i) => addDays(start, i));
    const agendaDays = cells.filter((k) => on(k).length);
    const label = page === 0 ? 'This week' : `${dayNum(start)} ${monthName(start)} to ${dayNum(end)} ${monthName(end)}`;
    return (
      <>
        <div className="d-nav">
          <button className="round" aria-label="Earlier week" onClick={() => swap(() => setPage((p) => p - 1))}><Icon name="back" /></button>
          <strong>{label}</strong>
          <button className="round" aria-label="Later week" onClick={() => swap(() => setPage((p) => p + 1))}><Icon name="fwd" /></button>
        </div>
        <div className="d-strip" role="group" aria-label="Days">
          {cells.map((k) => {
            const n = on(k).length;
            return (
              <button key={k} className={`d-cell ${k === today ? 'today' : ''}`} aria-pressed={k === sel} aria-label={`${day(k)}, ${n} item${n === 1 ? '' : 's'}`}
                onClick={() => { setSel(k); document.getElementById(`ag-${k}`)?.scrollIntoView({ block: 'start', behavior: RM() ? 'auto' : 'smooth' }); }}>
                <span className="dw">{dowShort(k).slice(0, 1)}</span><b>{dayNum(k)}</b><span className="dots">{'•'.repeat(Math.min(n, 4))}</span>
              </button>
            );
          })}
        </div>
        {agendaDays.length === 0 && <p className="card empty">Nothing on these days.</p>}
        {agendaDays.map((k) => (
          <section key={k} id={`ag-${k}`} className="cl-group">
            <div className="sec"><span>{k === today ? `Today · ${day(k)}` : day(k)}</span></div>
            <ul className="card list ag-list">{on(k).map((r, i) => agendaRow(r, i, k))}</ul>
          </section>
        ))}
      </>
    );
  };

  const dayView = () => {
    const list = on(sel), allDay = list.filter((r) => r.all_day || !time(r.at)), timed = list.filter((r) => !r.all_day && time(r.at));
    const top = (iso: string) => { const w = wall(iso)!; return ((w.hh ?? 0) - HOURS.from) * HOURS.px + ((w.mm ?? 0) / 60) * HOURS.px; };
    const dur = (r: DatedRow) => { if (!r.ends || !time(r.ends)) return HOURS.px * 0.9; return Math.max(HOURS.px * 0.6, top(r.ends) - top(r.at)); };
    const nowTop = sel === today && ctx.now ? top(ctx.now) : null;
    // Each event gets its box. Events that overlap in time share the width in lanes, so none covers another; one under EV_MIN
    // px has no room for a second line and draws as one row (app.css .tl-ev.short).
    const EV_MIN = 42;
    const placed = timed.map((r) => ({ r, t: top(r.at) + 8, h: dur(r) - 4, lane: 0, lanes: 1 })).sort((a, b) => a.t - b.t);
    let group: typeof placed = [], laneEnds: number[] = [], groupEnd = -Infinity;
    const closeGroup = () => group.forEach((e) => { e.lanes = laneEnds.length; });
    for (const e of placed) {
      if (e.t >= groupEnd) { closeGroup(); group = []; laneEnds = []; }
      let lane = laneEnds.findIndex((end) => end <= e.t);
      if (lane < 0) lane = laneEnds.push(0) - 1;
      laneEnds[lane] = e.t + e.h; e.lane = lane; group.push(e); groupEnd = Math.max(groupEnd, e.t + e.h);
    }
    closeGroup();
    return (
      <>
        <div className="d-nav">
          <button className="round" aria-label="Day before" onClick={() => swap(() => setSel((k) => addDays(k, -1)))}><Icon name="back" /></button>
          <strong>{sel === today ? `Today · ${day(sel)}` : day(sel)}</strong>
          <button className="round" aria-label="Day after" onClick={() => swap(() => setSel((k) => addDays(k, 1)))}><Icon name="fwd" /></button>
        </div>
        {allDay.length > 0 && <ul className="card list ag-list">{allDay.map((r, i) => agendaRow(r, i, sel))}</ul>}
        <div ref={timeline} className="card timeline" style={{ height: (HOURS.to - HOURS.from) * HOURS.px + 16 }}>
          {Array.from({ length: HOURS.to - HOURS.from + 1 }, (_, i) => {
            const h = HOURS.from + i;
            return <span key={h} className="hr" style={{ top: i * HOURS.px + 8 }}><span>{h === 12 ? '12 pm' : h > 12 ? `${h - 12} pm` : `${h} am`}</span></span>;
          })}
          {placed.map(({ r, t, h, lane, lanes }) => (
            <span key={r.record_id + r.at} className={`tl-ev ${r.source === 'google' ? 'google' : ''} ${h < EV_MIN ? 'short' : ''}`} data-dye={dye(r)}
              style={{ top: t, height: h, ...(lanes > 1 ? { left: `calc(64px + (100% - 76px) * ${lane / lanes})`, right: 'auto', width: `calc((100% - 76px) / ${lanes} - 4px)` } : {}) }}>
              <b>{r.title}</b><small>{time(r.at)}{r.ends && time(r.ends) ? ` to ${time(r.ends)}` : ''}<span className="tl-app"> · {appName(r)}</span></small>
            </span>
          ))}
          {nowTop !== null && nowTop >= 0 && <span className="now-line" role="img" style={{ top: nowTop + 8 }} aria-label={`Now, ${time(ctx.now)}`} />}
        </div>
      </>
    );
  };

  const month = () => {
    const w = wall(sel || today)!;
    const first = `${w.y}-${String(w.m).padStart(2, '0')}-01`;
    const gridStart = weekStart(first);
    const cells = Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
    const inMonth = (k: string) => k.slice(0, 7) === first.slice(0, 7);
    const list = on(sel);
    return (
      <>
        <div className="d-nav">
          <button className="round" aria-label="Earlier month" onClick={() => swap(() => setSel((k) => monthStart(k, -1)))}><Icon name="back" /></button>
          <strong>{monthName(first)} {w.y}</strong>
          <button className="round" aria-label="Later month" onClick={() => swap(() => setSel((k) => monthStart(k, 1)))}><Icon name="fwd" /></button>
        </div>
        <div className="card m-grid" role="grid" aria-label={`${monthName(first)} ${w.y}`}>
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d2, i) => <span key={i} className="m-dow">{d2}</span>)}
          {cells.map((k) => {
            const items = on(k);
            return (
              <button key={k} className={`m-cell ${inMonth(k) ? '' : 'out'} ${k === today ? 'today' : ''}`} aria-pressed={k === sel} aria-label={`${day(k)}, ${items.length} item${items.length === 1 ? '' : 's'}`} onClick={() => pickDay(k)}>
                <span className={`m-n${dayNum(k) === 1 ? ' first' : ''}`}>{dayNum(k)}{dayNum(k) === 1 && <span className="m-mo"> {monthName(k)}</span>}</span>
                <span className="m-dots">{items.slice(0, 3).map((r, i) => <i key={i} data-dye={dye(r)} className={r.source === 'google' ? 'g' : ''} />)}</span>
              </button>
            );
          })}
        </div>
        <section ref={dayList} className="cl-group">
          <div className="sec"><span>{sel === today ? `Today · ${day(sel)}` : day(sel)}</span><span className="meta">{list.length ? `${list.length} item${list.length === 1 ? '' : 's'}` : ''}</span></div>
          {list.length ? <ul className="card list ag-list">{list.map((r, i) => agendaRow(r, i, sel))}</ul> : <p className="card empty">Nothing that day.</p>}
        </section>
      </>
    );
  };

  // the day timeline starts at 6 am: bring "now" (today) or the day's first event to a third of the way down
  const timeline = useRef<HTMLDivElement>(null);
  const nowAt = ctx.now;
  const wasDay = useRef(false);
  useEffect(() => {
    const smooth = wasDay.current && !RM(); // a day change glides; arriving in the Day view just lands there
    wasDay.current = view === 'day';
    if (view !== 'day' || !timeline.current) return;
    const w = (iso: string) => wall(iso);
    const top = (iso: string) => { const q = w(iso)!; return ((q.hh ?? 0) - HOURS.from) * HOURS.px + ((q.mm ?? 0) / 60) * HOURS.px; };
    const timed = on(sel).filter((r) => !r.all_day && time(r.at));
    const y = sel === today && nowAt ? top(nowAt) : timed.length ? Math.min(...timed.map((r) => top(r.at))) : null;
    if (y === null) return;
    const at = timeline.current.getBoundingClientRect().top + scrollY + y + 8 - innerHeight / 3;
    scrollTo({ top: Math.max(0, at), behavior: smooth ? 'smooth' : 'auto' });
  }, [view, sel]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="days-block" data-dye={ctx.spec.dye}>
      {block.views.length > 1 && (
        <div className="seg" role="group" aria-label="Calendar view">
          {block.views.map((v) => <button key={v} aria-pressed={view === v} onClick={() => swap(() => setView(v))}>{v === 'day' ? 'Day' : v === 'week' ? 'Week' : 'Month'}</button>)}
        </div>
      )}
      <div ref={panel} className="days-panel">{view === 'day' ? dayView() : view === 'month' ? month() : week()}</div>
    </div>
  );
}
