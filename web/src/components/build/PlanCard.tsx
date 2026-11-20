import type { Patch, Plan } from '../../api/types';
import { Icon } from '../Icon';
import { ChalkOl } from '../Stitch';

/**
 * "Here's the plan" (clair-agent.md §2 `plan`, §11): what Clair will build from the answers,
 * in plain words, before the Build preview. Chalk, because it is Clair's idea and nothing
 * is made yet. Build it shows the preview; Change answers goes back to the questions.
 */
export function PlanCard({ plan, apps, onBuild, onChange }: {
  plan: Plan;
  apps: Patch[];
  onBuild: () => void;
  onChange?: () => void;
}) {
  const n = plan.new_app;
  const dyeOf = (k?: string) => (k && n && k === n.key ? n.dye : apps.find((a) => a.key === k)?.dye);
  return (
    <section className="chalk bq-plan" aria-labelledby="bq-plan-h">
      <ChalkOl />
      <span className="chalk-mark">
        <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path className="tri" d="M12 4.5 L20.5 18.5 H3.5 Z" /><path className="dash" d="M8 15.5h8" /></svg>
        Here's the plan
      </span>
      <h2 id="bq-plan-h" className="bq-ptitle" data-dye={n?.dye}>
        {n && <span className="tile"><Icon name={n.icon} size={18} /></span>}
        <span className="t">{plan.title}</span>
        {plan.private && <span className="pill soft"><Icon name="lock" size={12} />&nbsp;Private</span>}
      </h2>
      <ul className="bq-lines">
        {plan.lines.map((l, i) => (
          <li key={i} data-dye={dyeOf(l.app)}>
            <i aria-hidden="true" />
            <span>{l.text}</span>
          </li>
        ))}
      </ul>
      <span className="btns">
        <button className="cta" onClick={onBuild}>Build it</button>
        {onChange && <button className="ghost" onClick={onChange}>Change answers</button>}
      </span>
    </section>
  );
}
