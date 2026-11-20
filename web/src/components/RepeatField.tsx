/**
 * The repeat of a row, in plain words: Never, Daily, Weekly (with the days), Monthly. It builds the RRULE subset of
 * backend.md §3 (`FREQ`, `BYDAY`; `UNTIL` and `INTERVAL` of an existing rule ride along untouched) and sends it as a plain
 * rule string, which the server accepts on write. Shared by every collection with a `repeat` field: classes, to-dos, workouts.
 */
const DAYS: [string, string, string][] = [['MO', 'M', 'Monday'], ['TU', 'T', 'Tuesday'], ['WE', 'W', 'Wednesday'], ['TH', 'T', 'Thursday'], ['FR', 'F', 'Friday'], ['SA', 'S', 'Saturday'], ['SU', 'S', 'Sunday']];
const FREQS: [string, string][] = [['', 'Never'], ['DAILY', 'Daily'], ['WEEKLY', 'Weekly'], ['MONTHLY', 'Monthly']];

type Parsed = { freq: string; days: string[]; rest: string[] };
const parse = (rule: string): Parsed => {
  const parts = rule.split(';').filter(Boolean);
  const get = (k: string) => parts.find((p) => p.startsWith(k + '='))?.slice(k.length + 1) ?? '';
  return { freq: get('FREQ'), days: get('BYDAY').split(',').filter(Boolean), rest: parts.filter((p) => /^(UNTIL|INTERVAL)=/.test(p)) };
};
const build = ({ freq, days, rest }: Parsed) => (freq ? [`FREQ=${freq}`, ...(freq === 'WEEKLY' && days.length ? [`BYDAY=${days.join(',')}`] : []), ...rest].join(';') : '');

/** The rule a row holds now, from the `{rule, …}` the server sends or a plain string. */
export const ruleOf = (v: unknown): string => (typeof v === 'string' ? v : v && typeof v === 'object' && typeof (v as { rule?: unknown }).rule === 'string' ? (v as { rule: string }).rule : '');

export function RepeatField({ id, rule, onChange, labelId }: { id: string; rule: string; onChange: (rule: string) => void; labelId: string }) {
  const p = parse(rule);
  const set = (next: Partial<Parsed>) => onChange(build({ ...p, ...next }));
  return (
    <span className="repeat-pick" id={id}>
      <span className="chips" role="radiogroup" aria-labelledby={labelId}>
        {FREQS.map(([f, label]) => (
          <button type="button" key={f} role="radio" aria-checked={p.freq === f} className="chip pick"
            onClick={() => set({ freq: f, days: f === 'WEEKLY' && !p.days.length ? ['MO'] : p.days })}>{label}</button>
        ))}
      </span>
      {p.freq === 'WEEKLY' && (
        <span className="chips days-pick" role="group" aria-label="On these days">
          {DAYS.map(([code, short, long]) => (
            <button type="button" key={code} className="chip pick" aria-pressed={p.days.includes(code)} aria-label={long}
              onClick={() => { const on = p.days.includes(code); if (on && p.days.length === 1) return; set({ days: DAYS.map((d) => d[0]).filter((d) => (d === code ? !on : p.days.includes(d))) }); }}>{short}</button>
          ))}
        </span>
      )}
    </span>
  );
}
