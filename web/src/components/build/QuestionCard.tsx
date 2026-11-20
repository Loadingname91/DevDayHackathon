import { Fragment, useEffect, useRef, type FormEvent, type KeyboardEvent } from 'react';
import type { AskQuestion, Choice } from '../../api/types';

/** What is picked on one question, as the card holds it. `value`: the field of a picked option that takes one ("Set a number"). */
export type Pick = { picked: string[]; other: boolean; otherText: string; value: string };
export type Picks = Record<string, Pick>;
const EMPTY: Pick = { picked: [], other: false, otherText: '', value: '' };

/** A question counts as answered once an option is picked (with its value, if it takes one) or Other has text. */
export function answered(q: AskQuestion, p: Pick | undefined): boolean {
  if (!p) return false;
  if (p.other && p.otherText.trim()) return true;
  if (!p.picked.length) return false;
  const needs = q.options.find((o) => o.input && p.picked.includes(o.label));
  return !needs || !!p.value.trim();
}

/** One question's answer on the wire (clair-agent.md §2): the picked labels, and what was typed as `other`. */
export function toChoice(q: AskQuestion, p: Pick | undefined): Choice {
  const x = p ?? EMPTY;
  const choices = x.picked.filter((l) => q.options.some((o) => o.label === l));
  const needs = q.options.find((o) => o.input && choices.includes(o.label));
  const other = x.other && x.otherText.trim() ? x.otherText.trim() : needs ? x.value.trim() : '';
  return other ? { choices, other } : { choices };
}

type Item = { key: string; label: string; description?: string; input?: { placeholder: string; numeric?: boolean }; other?: true };

/**
 * Clair asks before building (clair-agent.md §7 rule 7): 1 to 3 questions in one card,
 * each a header, the question and its option rows (radio or checkbox), then Other.
 * Option rows follow the fridge question on board ClairFridge; CSS in styles/build.css.
 */
export function QuestionCard({ questions, picks, onPicks, onContinue, onSkip }: {
  questions: AskQuestion[];
  picks: Picks;
  onPicks: (p: Picks) => void;
  onContinue: () => void;
  onSkip: () => void;
}) {
  const left = questions.filter((q) => !answered(q, picks[q.id])).length;
  const submit = (e: FormEvent) => { e.preventDefault(); if (!left) onContinue(); };
  return (
    <form className="card bq-card" onSubmit={submit} aria-label="Clair's questions">
      {questions.map((q) => <Ask key={q.id} q={q} p={picks[q.id] ?? EMPTY} set={(p) => onPicks({ ...picks, [q.id]: p })} />)}
      <div className="bq-foot">
        <button type="submit" className="cta wide" disabled={left > 0}>Continue</button>
        <span className="bq-left" aria-live="polite">{left ? (left === 1 ? '1 question left' : `${left} questions left`) : 'Next: the plan, before anything is built'}</span>
        <button type="button" className="lk" onClick={onSkip}>Skip, use your best guess</button>
      </div>
    </form>
  );
}

function Ask({ q, p, set }: { q: AskQuestion; p: Pick; set: (p: Pick) => void }) {
  const group = useRef<HTMLDivElement>(null);
  const focusField = useRef<string | null>(null);
  const items: Item[] = [
    ...q.options.map((o) => ({ key: o.label, label: o.label, description: o.description, input: q.multi ? undefined : o.input })),
    ...(q.other === false ? [] : [{ key: '\u0000other', label: 'Other', description: 'Type your own answer', other: true as const }]),
  ];
  const isOn = (it: Item) => (it.other ? p.other : p.picked.includes(it.label));
  const pick = (it: Item) => {
    const on = isOn(it);
    if (q.multi) set(it.other ? { ...p, other: !on } : { ...p, picked: on ? p.picked.filter((x) => x !== it.label) : [...p.picked, it.label] });
    else set(it.other ? { ...p, picked: [], other: true } : { ...p, picked: [it.label], other: false });
    if (!on && (it.other || it.input)) focusField.current = it.key; // a field opens: type straight into it
  };
  useEffect(() => {
    if (!focusField.current) return;
    group.current?.querySelector<HTMLInputElement>(`input[data-for="${CSS.escape(focusField.current)}"]`)?.focus();
    focusField.current = null;
  });
  // radios: one tab stop, arrow keys move and pick (WAI-ARIA radio group)
  const current = Math.max(0, items.findIndex(isOn));
  const onKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    if (q.multi) return;
    const d = e.key === 'ArrowDown' || e.key === 'ArrowRight' ? 1 : e.key === 'ArrowUp' || e.key === 'ArrowLeft' ? -1 : 0;
    if (!d) return;
    e.preventDefault();
    const j = (i + d + items.length) % items.length;
    focusField.current = null;
    set(items[j].other ? { ...p, picked: [], other: true } : { ...p, picked: [items[j].label], other: false });
    group.current?.querySelectorAll<HTMLButtonElement>('[role="radio"]')[j]?.focus();
  };
  const hid = `bq-${q.id}-h`, tid = `bq-${q.id}-t`;
  return (
    <div className="bq-q">
      <span className="bq-head"><span id={hid}>{q.header}</span>{q.multi && <span className="meta">Pick any</span>}</span>
      <p className="bq-text" id={tid}>{q.text}</p>
      <div ref={group} className="bq-opts" role={q.multi ? 'group' : 'radiogroup'} aria-labelledby={`${hid} ${tid}`}>
        {items.map((it, i) => {
          const on = isOn(it);
          return (
            <Fragment key={it.key}>
              <button type="button" role={q.multi ? 'checkbox' : 'radio'} aria-checked={on} className={`bq-opt${q.multi ? ' multi' : ''}`}
                tabIndex={q.multi || i === current ? 0 : -1} onClick={() => pick(it)} onKeyDown={(e) => onKey(e, i)}>
                <span className="bq-mark" aria-hidden="true">
                  {q.multi && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg>}
                </span>
                <span className="bq-txt"><span className="l">{it.label}</span>{it.description && <span className="d">{it.description}</span>}</span>
              </button>
              {on && (it.other || it.input) && (
                <label className="bq-field">
                  <span>{it.input ? it.input.placeholder : 'Your answer'}</span>
                  <input className="input" data-for={it.key} enterKeyHint="done" autoComplete="off"
                    inputMode={it.input?.numeric ? 'numeric' : 'text'}
                    placeholder={it.input ? (it.input.numeric ? 'Your number' : 'Type it here') : 'Type your answer'}
                    value={it.other ? p.otherText : p.value}
                    onChange={(e) => set(it.other ? { ...p, otherText: e.target.value } : { ...p, value: e.target.value })} />
                </label>
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
