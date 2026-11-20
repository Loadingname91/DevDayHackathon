import { useState } from 'react';
import { clairTurn, errorText, request } from '../../api/client';
import type { AppSpec, ClairEvent, CommandResult, Workflow } from '../../api/types';
import { afterCommand, loadApp, loadHome, toast } from '../../lib/store';

/** The Workflows tab (FR-W2): one sentence per rule, a switch, Run now. "Next run" only when the server sends one. */
export function Workflows({ spec }: { spec: AppSpec }) {
  const rules = spec.workflows ?? [];
  if (!rules.length) return <p className="card empty">No rules yet.</p>;
  return <div className="rules">{rules.map((w) => <Rule key={w.id} app={spec.key} w={w} />)}</div>;
}

function Rule({ app, w }: { app: string; w: Workflow }) {
  const [on, setOn] = useState(w.on);
  const [running, setRunning] = useState<string | null>(null);
  const flip = async () => {
    const next = !on;
    setOn(next); // a switch is a gesture: optimistic, rolled back on failure
    try { await afterCommand(await request<CommandResult>('PATCH', `/apps/${app}/workflows/${w.id}`, { on: next })); }
    catch (e) { setOn(!next); toast(errorText(e), undefined, 4000); }
  };
  const runNow = async () => {
    setRunning('Starting…');
    let proposed = false, said = '';
    await clairTurn({}, (e: ClairEvent) => {
      if (e.event === 'status') setRunning(e.data.text);
      if (e.event === 'proposal') proposed = true;
      if (e.event === 'text_delta') said += e.data.text;
      if (e.event === 'done' && e.data.status === 'error') said = e.data.message ?? 'The rule could not run.';
    }, undefined, `/apps/${app}/workflows/${w.id}/run`);
    setRunning(null);
    if (proposed) { await loadHome(); toast('A card is waiting in Needs your OK.', undefined, 5000); }
    else toast(said || 'Nothing to do.', undefined, 5000);
    void loadApp(app);
  };
  return (
    <div className="card rule">
      <span className="rule-row">
        <span className="rule-s">{w.sentence}</span>
        <button className="switch-btn" role="switch" aria-checked={on} aria-label={on ? 'Rule on' : 'Rule off'} onClick={flip} />
      </span>
      <span className="rule-row">
        <span className="muted rule-meta" role="status">{running ?? (w.next_run ? `Next run ${w.next_run}` : w.runs ?? (on ? 'On' : 'Off'))}</span>
        <button className="outline" onClick={runNow} disabled={!on || !!running}>Run now</button>
      </span>
    </div>
  );
}
