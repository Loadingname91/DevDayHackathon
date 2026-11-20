import { useEffect, useRef, useState } from 'react';
import { errorText, request } from '../api/client';
import type { ChangeSet, CommandResult, Patch } from '../api/types';
import { listNames } from '../lib/format';
import { dyeOf, locate, MOTION, retractThreads, RM, seen, sheetOpen, sleep, stitchIn, T, threadPull } from '../lib/motion';
import { afterCommand, applyDelta, applyFaces, clearChanged, getState, peek, peekSettled, setBusy, toast, useStore } from '../lib/store';
import { Icon } from './Icon';
import { ReviewItems } from './ReviewItems';
import { Edge } from './Stitch';

type Props = {
  cs: ChangeSet;
  onStitched?: (cs: ChangeSet) => void;
  onUndone?: () => void;
  onDismissed?: () => void;
  /** a build card: the primary opens the Build preview instead of confirming here */
  onBuild?: (cs: ChangeSet) => void;
  /** arrival stagger, ms (catalogue N3: 40 ms apart, cap 3) */
  delay?: number;
};

/** A change line is at most two lines: the first few items (the text is ' · '-separated), then "+N more". Everything is in Review items. */
function brief(what: string, budget = 44): { text: string; more: number } {
  const parts = what.split(' · ');
  let n = 0, len = 0;
  while (n < parts.length && (n === 0 || len + parts[n].length + 3 <= budget)) { len += parts[n].length + 3; n++; }
  return { text: parts.slice(0, n).join(' · '), more: parts.length - n };
}

/**
 * One basted card for every Clair proposal (ADR-003). Confirm: the request fires at
 * once and is not awaited → the card's seam closes (220) → each target app you can
 * see (its pin first, else its Home patch) gets a running stitch sewn around its
 * tile, 120 ms apart; at 70% of each stitch its face rolls to the card's `deltas`
 * and takes "just now". Apps you can't see creep up above the bar and get the same
 * stitch (Peek). The confirm response's faces are final. Undo: the seam reopens
 * (140), the stitches pull out, tags fade, numbers roll back.
 * `?motion=threads` restores the earlier thread pull (fixspec §A) for comparison.
 * A confirmed change always reports back: closing the sheet mid-run only stops the stitching visuals, the result
 * (faces, sync, the receipt capsule with Undo, `onStitched`) still lands. Only Undo or a new confirm supersede a run.
 * The receipt (components/Toast.tsx) is for a card confirmed from Home or after its sheet closed; while the Clair sheet
 * shows the stitched card, the card's own "Added to … Undo" row is the Undo and no toast is raised.
 */
export function ProposalCard({ cs, onStitched, onUndone, onDismissed, onBuild, delay = 0 }: Props) {
  const apps = useStore((s) => s.home?.apps) ?? [];
  const [status, setStatus] = useState(cs.status);
  const [busy, setLocalBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [review, setReview] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const runId = useRef(0); // bumped by confirm() and undo() only: the visuals of a superseded run stop
  const undone = useRef(false); // Undo already pressed: no "Added" toast after it
  const mounted = useRef(true); // the card left with its sheet: state and the error line are not its to set any more
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const app = (k: string): Patch | undefined => apps.find((a) => a.key === k || a.id === k);
  const names = cs.targets.map((t) => app(t)?.name ?? t);
  const isRule = cs.kind === 'rule';

  /** A thread from the card's line for each target to that app's pin (or its patch). */
  const pairs = () => {
    const frame = document.querySelector<HTMLElement>('.frame')!;
    const out: { from: Element; to: Element; top?: boolean; color?: string; app: string }[] = [];
    for (const t of cs.targets) {
      const from = ref.current?.querySelector(`[data-thread-source="${t}"]`) ?? ref.current?.querySelector('.cta');
      // pins first, then a Home patch; only a target you can actually see (not under a sheet) gets a thread
      const all = [...document.querySelectorAll(`[data-thread-target="${t}"]`)];
      const to = [...all.filter((e) => e.closest('.bar')), ...all.filter((e) => !e.closest('.bar'))].find(seen);
      if (from && to) out.push({ from, to, top: true, color: dyeOf(to), app: t });
    }
    return { frame, out };
  };

  /** A hidden app's tile for Peek: its face before and after (from the card's deltas). */
  const peekItem = (app: string, reverse: boolean) => {
    const d = cs.deltas.find((x) => x.app === app);
    const now = getState().home?.apps.find((a) => a.key === app)?.face.text ?? '';
    return reverse ? { app, from: d?.after ?? now, to: d?.before ?? now } : { app, from: d?.before ?? now, to: d?.after ?? now };
  };

  async function confirm() {
    if (busy) return;
    const run = ++runId.current;
    const alive = () => run === runId.current; // guards the visuals only
    const live = (f: () => void) => { if (mounted.current) f(); };
    setLocalBusy(true); setErr(null); setBusy(true); undone.current = false;
    const call = request<CommandResult>('POST', `/change-sets/${cs.id}/confirm`).then((r) => ({ ok: true as const, r }), (e) => ({ ok: false as const, e }));
    setStatus('stitched'); // the stitch tightens
    await sleep(RM() ? 0 : T.state);
    const land = (t: string) => { const d = cs.deltas.find((x) => x.app === t); applyDelta(t, d?.before, d?.after); };
    let back: () => Promise<void>;
    if (MOTION === 'threads') {
      const { frame, out } = pairs();
      if (alive()) {
        await threadPull({ frame, pairs: out, onLand: (i) => land(out[i].app), alive });
        cs.targets.filter((t) => !out.some((p) => p.app === t)).forEach(land);
      }
      back = () => retractThreads({ frame, pairs: out, alive });
    } else {
      const { visible, hidden } = locate(cs.targets, cs.deltas.map((d) => d.app));
      if (alive()) {
        peek(hidden.map((app) => peekItem(app, false)));
        hidden.forEach(land);
        await stitchIn({ els: visible.map((v) => ({ el: v.el, color: dyeOf(v.el) })), onLand: (i) => land(visible[i].app), alive });
      }
      back = () => stitchIn({ els: locate(cs.targets, cs.deltas.map((d) => d.app)).visible.map((v) => ({ el: v.el, color: dyeOf(v.el) })), onLand: () => {}, alive, reverse: true });
    }
    const res = await call;
    live(() => setLocalBusy(false)); setBusy(false);
    if (!alive()) return; // Undo or a new confirm took over
    if (!res.ok) {
      // nothing was saved, so nothing to repair: the stitches pull out, the card re-bastes with a frayed edge
      cs.deltas.forEach((d) => applyDelta(d.app, d.after, d.before, false));
      clearChanged(cs.targets);
      await back();
      live(() => { setStatus('basted'); setErr(errorText(res.e)); });
      if (!mounted.current) toast(errorText(res.e), undefined, 4000, { error: true }); // the card is gone with its sheet: say it here
      return;
    }
    // the result is saved: it reports back whether or not the sheet is still open
    applyFaces(res.r.faces); // final values: a face that differs from its delta rolls once more
    void afterCommand(res.r);
    onStitched?.({ ...cs, status: 'stitched' });
    await peekSettled(); // the receipt capsule rises out of the bar as the raised tiles fold into it
    if (undone.current) return;
    // a card still open in the Clair sheet or the Chat screen says "Added to … Undo" itself: no second Undo, and none at the top of the screen
    if ((ref.current?.closest('.sheet') && sheetOpen()) || ref.current?.closest('.chat-log')) return; // in the Chat screen the card's own row is the Undo too
    const said = names.length > 2 ? `${names.length} apps` : listNames(names);
    toast(isRule ? `Rule on in ${said}` : `Added to ${said}`, { label: 'Undo', run: undo }, 8000, { dyes: cs.targets.map((t) => app(t)?.dye) });
  }

  async function undo() {
    undone.current = true;
    const run = ++runId.current;
    const alive = () => run === runId.current;
    try {
      const r = await request<CommandResult>('POST', `/change-sets/${cs.id}/undo`);
      if (mounted.current) setStatus('basted');
      if (MOTION === 'threads') {
        if (ref.current?.isConnected) {
          const { frame, out } = pairs();
          void retractThreads({ frame, pairs: out.map((p) => ({ from: p.to, to: p.from, color: p.color })), alive });
        }
      } else {
        // the seam ripper: visible tiles lose their stitch; hidden ones creep up and roll back
        const { visible, hidden } = locate(cs.targets, cs.deltas.map((d) => d.app));
        peek(hidden.map((app) => peekItem(app, true)), true);
        void stitchIn({ els: visible.map((v) => ({ el: v.el, color: dyeOf(v.el) })), onLand: () => {}, alive, reverse: true });
      }
      cs.deltas.forEach((d) => applyDelta(d.app, d.after, d.before, false));
      applyFaces(r.faces);
      clearChanged(cs.targets);
      await afterCommand(r);
      onUndone?.();
    } catch (e) { toast(errorText(e), undefined, 4000, { error: true }); }
  }

  async function dismiss() {
    try { await request('POST', `/change-sets/${cs.id}/dismiss`); } catch { /* already gone */ }
    onDismissed?.();
  }

  const basted = status !== 'stitched';
  return (
    <div ref={ref} className={`pcard st arrive ${basted ? 'basted' : ''} ${err ? 'frayed' : ''}`} style={{ animationDelay: `${delay}ms` }} data-f={cs.id}>
      <Edge />
      <span className="src">
        <span>{cs.source.label}</span>
        {cs.mode === 'fixture' && <span className="pill soft">sample</span>}
      </span>
      <h3>{cs.title}</h3>
      {cs.summary && <p className="sum">{cs.summary}</p>}
      {cs.lines.map((l, i) => {
        const a = app(l.apps[0]);
        const who = listNames(l.apps.map((k) => app(k)?.name ?? k));
        const b = brief(l.what, 60 - who.length); // two lines of about 36 characters, the app name included
        return (
          <span className="line" key={i} data-dye={a?.dye}>
            <span className="tile-ico" data-thread-source={l.apps[0]}><Icon name={a?.icon ?? 'app'} size={16} /></span>
            <span className="txt">
              <span className="what"><b>{who}</b> {b.text}{b.more > 0 && <span className="more"> +{b.more} more</span>}</span>
              {l.sub && <small>{l.sub}</small>}
            </span>
            {l.val && <span className="val">{l.val}</span>}
          </span>
        );
      })}
      {err && <p className="err" role="alert">{err}</p>}
      <div className="btn-area">
        {basted ? (
          <span className="btns">
            <button className="cta" onClick={() => (onBuild ? onBuild(cs) : confirm())} disabled={busy}>{cs.actions.primary}</button>
            {isRule
              ? <button className="ghost" onClick={dismiss} disabled={busy}>{cs.actions.secondary ?? 'Not now'}</button>
              : cs.actions.secondary && <button className="ghost" onClick={() => setReview(true)} disabled={busy}>{cs.actions.secondary}</button>}
          </span>
        ) : (
          <span className="done-row"><span>{isRule ? 'Rule is on' : `Added to ${listNames(names)}`}</span><button className="outline" onClick={undo}>Undo</button></span>
        )}
      </div>
      <ReviewItems cs={cs} apps={apps} open={review} onClose={() => setReview(false)} />
    </div>
  );
}
