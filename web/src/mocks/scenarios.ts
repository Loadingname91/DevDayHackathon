// Named scenarios (spec/split.md §3): which scripted run answers a sentence, and
// which recorded effect lands once its change set is confirmed. The mock computes
// nothing; a value no fixture holds needs a new fixture.
import type { ClairEvent } from '../api/types';

export type ScriptedEvent = ClairEvent & { delay: number };

export type MockState = {
  base: 'seed' | 'before';
  rung: 1 | 4;
  applied: string[]; // effects confirmed, in order
  rulesOn: Record<string, boolean>; // app → has a rule that is on
};

export type Scenario = {
  /** Does this typed sentence start it? */
  match: (text: string) => boolean;
  /** The run fixture to play, and the effect it lands on confirm. `null` run: the sentence is not available in this state. */
  pick: (s: MockState) => { run: string; effect?: string } | null;
};

const r = (s: MockState) => `r${s.rung}`;

export const SCENARIOS: Record<string, Scenario> = {
  // order matters: the first match wins
  'google-move': { match: (t) => /move the dentist|dentist to/i.test(t), pick: () => ({ run: 'run.google-move' }) },
  'rule-unsupported': { match: (t) => /(email|text|notify) me when/i.test(t), pick: () => ({ run: 'run.rule-unsupported' }) },
  'exam-rule': {
    match: (t) => /when (i add )?an exam/i.test(t) && /to-?do/i.test(t),
    pick: (s) => (s.rulesOn.classes ? { run: 'run.already-built' } : { run: 'run.exam-rule', effect: 'exam-rule' }),
  },
  exam: {
    match: (t) => /(midterm|exam)/i.test(t) && /(dec|thu|on )/i.test(t),
    pick: (s) => (s.applied.some((e) => e === 'exam' || e === 'exam.rule') ? null : s.rulesOn.classes ? { run: 'run.exam.rule', effect: 'exam.rule' } : { run: 'run.exam', effect: 'exam' }),
  },
  lunch: { match: (t) => /lunch/i.test(t), pick: (s) => (s.applied.includes('lunch') ? null : { run: 'run.lunch', effect: 'lunch' }) },
  planner: {
    match: (t) => /\bplan\b/i.test(t) && /(training|workouts?|runs?|week)/i.test(t),
    pick: (s) => (s.applied.some((e) => e.startsWith('planner')) ? { run: 'run.planner.done' } : { run: `run.planner.${r(s)}`, effect: `planner.${r(s)}` }),
  },
  appointments: {
    match: (t) => /appointment|due for/i.test(t),
    pick: (s) => (s.applied.includes('appointments') ? { run: 'run.appointments.done' } : { run: 'run.appointments', effect: 'appointments' }),
  },
  'build-calories': {
    match: (t) => /calories|what i eat/i.test(t),
    pick: (s) => (s.base !== 'before' || s.applied.includes('build-calories') ? { run: 'run.already-built' } : { run: 'run.build-calories', effect: 'build-calories' }),
  },
  'build-running': {
    match: (t) => /10k|track my runs/i.test(t),
    pick: (s) => (s.base !== 'before' || s.applied.includes('build-running') ? { run: 'run.already-built' } : { run: 'run.build-running', effect: 'build-running' }),
  },
  'build-cycle': {
    match: (t) => /cycle/i.test(t),
    pick: (s) => (s.base !== 'before' || s.applied.includes('build-cycle') ? { run: 'run.already-built' } : { run: 'run.build-cycle', effect: 'build-cycle' }),
  },
};

/** "Use sample" ({fixture: "planner"}): the recorded run at the rung being demoed, marked sample. */
export const pickFixture = (name: string, s: MockState) =>
  name === 'planner' ? { run: `run.planner.${r(s)}.sample`, effect: `planner.${r(s)}` } : null;

/** Run now on a rule: the same run with source "workflow"; its card goes to Needs your OK. */
export function pickRuleRun(text: string, s: MockState) {
  if (SCENARIOS.planner.match(text)) {
    return s.applied.some((e) => e.startsWith('planner')) ? { run: 'run.planner.done' } : { run: `run.planner.${r(s)}.workflow`, effect: `planner.${r(s)}` };
  }
  if (SCENARIOS.appointments.match(text)) {
    return s.applied.includes('appointments') ? { run: 'run.appointments.done' } : { run: 'run.appointments.workflow', effect: 'appointments' };
  }
  return { run: 'run.unknown' };
}

/** Base GET answers. `?scenario=before` is the 8-app state for the recording. */
export const BASES = {
  seed: { '/home': 'home', '/apps': 'apps', '/me': 'me' },
  before: { '/home': 'home.before', '/apps': 'apps.before', '/me': 'me' },
} as const;

/**
 * URL switches, kept for the tab's session:
 *   ?scenario=seed|before   ?rung=1|4
 *   ?mock=slow|fail-confirm|no-card|drop|google-off|google-deny|google-stale
 */
export function params() {
  const q = new URLSearchParams(location.search);
  let saved: { scenario?: string; mock?: string; rung?: string } = {};
  try { saved = JSON.parse(sessionStorage.getItem('quilt:mock') ?? '{}'); } catch { /* private mode */ }
  const base = q.get('scenario') ?? saved.scenario ?? 'seed';
  const fault = q.get('mock') ?? saved.mock ?? '';
  const rung = q.get('rung') ?? saved.rung ?? '4';
  try { sessionStorage.setItem('quilt:mock', JSON.stringify({ scenario: base, mock: fault, rung })); } catch { /* private mode */ }
  return { base: (base === 'before' ? 'before' : 'seed') as MockState['base'], fault, rung: (rung === '1' ? 1 : 4) as MockState['rung'] };
}
