import { Link } from 'react-router-dom';
import type { Home } from '../api/types';
import { day, dayKey, time } from '../lib/format';

/** Next up (Main board): the thread of what's coming, from every app. On a laptop it sits in the detail pane. */
export function NextUp({ home }: { home: Home }) {
  if (!home.nextUp.length) return null;
  // the time today, else the day ("Sun 22 Nov"); "6 pm", never "6:00 pm" (DESIGN.md §8)
  const at = (iso: string) => {
    const t = time(iso);
    return !t || (home.server_now && dayKey(iso) !== dayKey(home.server_now)) ? day(iso) : t.replace(':00 ', ' ');
  };
  const dye = (app: string) => home.apps.find((a) => a.key === app || a.id === app)?.dye;
  return (
    <section className="section next-up" aria-label="Next up" data-f="next">
      <h2 className="sec next-sec"><span>Next up</span><span className="meta">From every app</span></h2>
      <ul className="next">
        {home.nextUp.map((n) => (
          <li key={n.record_id + (n.occurrence ?? '')} data-dye={dye(n.app)}>
            <Link to={`/a/${n.app}`} className="nx">
              <span className="dot" aria-hidden="true" />
              <span className="at num">{at(n.at)}</span>
              <span className="what"><span className="t">{n.title}</span><span className="s">{n.sub}</span></span>
            </Link>
          </li>
        ))}
      </ul>
      <Link to="/a/calendar" className="link">See the week in Calendar ›</Link>
    </section>
  );
}
