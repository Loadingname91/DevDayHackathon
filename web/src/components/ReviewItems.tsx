import type { ChangeSet, Patch } from '../api/types';
import { Sheet } from './Sheet';

/** Review items, read-only for DevDay: each row with its reason, its "also" line and the source app. */
export function ReviewItems({ cs, apps, open, onClose }: { cs: ChangeSet; apps: Patch[]; open: boolean; onClose: () => void }) {
  const name = (k: string) => apps.find((a) => a.key === k)?.name ?? k;
  const rows = cs.review ?? cs.lines.map((l) => ({ title: l.what, when: l.val, change: 'new' as const, reason: l.sub, source: undefined, also: undefined, also_source: undefined, app: l.apps[0] }));
  return (
    <Sheet open={open} onClose={onClose} label="Review items">
      <div className="clair-head"><h2>{cs.title}</h2><button className="ghost" onClick={onClose}>Done</button></div>
      <ul className="review">
        {rows.map((r, i) => (
          <li key={i} data-dye={apps.find((a) => a.key === r.app)?.dye}>
            <span className="r1"><span>{r.title}</span><span className={`pill ${r.change === 'kept' ? 'soft' : 'now'}`}>{r.change}</span></span>
            <span className="r2">{r.when}</span>
            {r.reason && <span className="r3">{r.reason} · {r.source ?? name(r.app)}</span>}
            {r.also && <span className="r3">Also: {r.also}{r.also_source ? ` · ${r.also_source}` : ''}</span>}
          </li>
        ))}
      </ul>
    </Sheet>
  );
}
