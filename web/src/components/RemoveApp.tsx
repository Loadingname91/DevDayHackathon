import { useEffect, useId, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorText } from '../api/client';
import type { AppResponse, Dependent, Patch, Rec } from '../api/types';
import { RM, T } from '../lib/motion';
import { previewRemoveApp, removeApp } from '../lib/store';
import { Icon } from './Icon';

/**
 * Remove app (spec/backend.md §11 row 21, FR-S8): the last row of the app menu, after a running stitch, and the confirm step that
 * replaces the menu inside the same sheet (design/DESIGN.md §16). Ink, never red. The step asks the server what else reads the app
 * (`DELETE /apps/{id}` without `confirm`, a 409 preview), says it in plain words, and waits for a yes; Remove then sends
 * `?confirm=true` (one change set) and the capsule on Home carries Undo. The app then waits 3 days in You → Recently removed (components/RemovedApps.tsx). Keep, Escape, the scrim and the sheet's × all just close the sheet.
 */

/** "Remove app", under a running stitch. 44 tall, ink text and a trash icon. */
export function RemoveRow({ onOpen }: { onOpen: () => void }) {
  return (
    <>
      <div className="rm-seam" aria-hidden="true" />
      <button type="button" className="rm-open" onClick={onOpen}><Icon name="trash" size={18} />Remove app</button>
    </>
  );
}

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

/** The app's own rows (not the build preview's examples) and rules: what goes with it. */
function whatGoes(app: AppResponse, key: string): string {
  let rows = 0;
  for (const [ref, list] of Object.entries(app.data)) if (ref.startsWith(`${key}/`)) rows += (list as Rec[]).filter((r) => 'properties' in r && !r.example).length;
  const rules = app.spec.workflows?.length ?? 0;
  if (!rows && !rules) return 'It has no rows yet.';
  const parts = [rows && plural(rows, 'row'), rules && plural(rules, 'rule')].filter(Boolean);
  return `Its ${parts.join(' and ')} ${rows + rules === 1 ? 'goes' : 'go'} with it.`;
}

type Line = { id: string; app: string; who: string; dye?: string; text: string };

/**
 * One plain sentence per thing that reads the app. `what` is the server's phrase (api `dependents()`): `stitch from <app>/<coll>`,
 * `stitch to <app>/<coll>`, `reads <app>/<coll>…`, `shows <App name>`, `<ref>.<field> links to <app>/<coll>`. A phrase this does not know
 * is shown as the server wrote it, so nothing is hidden. The same app and sentence are said once.
 */
function lines(deps: Dependent[], app: AppResponse, name: string, apps: Patch[]): Line[] {
  const coll = (ref: string) => {
    const k = ref.split('/')[1]?.split(/[.\s]/)[0] ?? '';
    const c = app.spec.collections.find((x) => x.key === k);
    return `${name} ${(c?.name ?? k).toLowerCase()}`.trim();
  };
  const out: Line[] = [];
  for (const d of deps) {
    const p = apps.find((a) => a.key === d.app || a.id === d.app);
    const who = p?.name ?? d.app.charAt(0).toUpperCase() + d.app.slice(1);
    let m: RegExpMatchArray | null;
    let text: string;
    if ((m = d.what.match(/^stitch from (\S+)$/))) text = `reads ${coll(m[1])} and will stop getting new ones. Rows it already has stay.`;
    else if ((m = d.what.match(/^stitch to (\S+)$/))) text = `sends rows into ${coll(m[1])}. That stops.`;
    else if ((m = d.what.match(/^reads (\S+)/))) text = `reads ${coll(m[1])} and will stop showing them.`;
    else if (/^shows /.test(d.what)) text = `shows ${name} and will stop showing it.`;
    else if ((m = d.what.match(/ links to (\S+)$/))) text = `links its rows to ${coll(m[1])} and will lose those links.`;
    else text = d.what;
    const id = `${d.app}|${text}`;
    if (!out.some((l) => l.id === id)) out.push({ id, app: d.app, who, dye: p?.dye, text });
  }
  return out;
}

type Preview = { state: 'loading' } | { state: 'ready'; deps: Dependent[] } | { state: 'error' };

/**
 * The confirm step. An `alertdialog` labelled by its heading and described by its body; focus lands on Keep (the safe button) and the
 * sheet returns it to `···` on close. Remove stays disabled until the preview has arrived, so the yes is always about what was shown.
 */
export function RemoveStep({ appKey, app, name, dye, apps, onClose }: { appKey: string; app: AppResponse; name: string; dye?: string; apps: Patch[]; onClose: () => void }) {
  const go = useNavigate();
  const h = useId(), d = useId();
  const [preview, setPreview] = useState<Preview>({ state: 'loading' });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const keep = useRef<HTMLButtonElement>(null);
  const [tries, setTries] = useState(0);

  useEffect(() => { keep.current?.focus({ preventScroll: true }); }, []);
  useEffect(() => {
    let live = true;
    setPreview({ state: 'loading' });
    previewRemoveApp(appKey).then((deps) => { if (live) setPreview({ state: 'ready', deps }); }, () => { if (live) setPreview({ state: 'error' }); });
    return () => { live = false; };
  }, [appKey, tries]);

  // closing the sheet and going Home, in that order: the sheet leaves (220), then Home is there and the capsule rises
  const leave = () => new Promise<void>((ok) => { onClose(); setTimeout(() => { go('/'); ok(); }, (RM() ? T.fb : T.layoutOut) + 30); });
  async function remove() {
    if (busy || preview.state !== 'ready') return;
    setBusy(true); setErr(null);
    try { await removeApp(appKey, { name, dye, leave }); } catch (e) { setBusy(false); setErr(errorText(e)); }
  }

  const said = preview.state === 'ready' ? lines(preview.deps, app, name, apps) : [];
  const SHOWN = 5;
  return (
    <div className="rm-step" role="alertdialog" aria-labelledby={h} aria-describedby={d}>
      <div className="sheet-head"><span className="txt"><h2 id={h}>Remove {name}?</h2></span></div>
      <div id={d} className="rm-body" aria-busy={preview.state === 'loading'}>
        <p className="rm-lede">{whatGoes(app, appKey)}</p>
        {preview.state === 'loading' && <p className="rm-note" role="status">Checking what uses it…</p>}
        {preview.state === 'error' && (
          <p className="rm-note" role="alert">Could not check what uses it. Nothing was changed. <button type="button" className="rm-retry" onClick={() => setTries((n) => n + 1)}>Try again</button></p>
        )}
        {preview.state === 'ready' && said.length === 0 && <p className="rm-note">Nothing else uses it.</p>}
        {said.length > 0 && (
          <ul className="rm-deps">
            {said.slice(0, SHOWN).map((l) => (
              <li key={l.id}><span data-dye={l.dye}><i className="dyedot" /></span><span><b>{l.who}</b> {l.text}</span></li>
            ))}
            {said.length > SHOWN && <li className="rm-more"><span>and {said.length - SHOWN} more</span></li>}
          </ul>
        )}
        <p className="rm-note rm-kept"><Icon name="trash" size={14} sw={1.8} />Kept for 3 days in You → Recently removed.</p>
        <p className="rm-note">You can undo this right after.</p>
        {err && <p className="rm-note rm-err" role="alert">{err}</p>}
      </div>
      <div className="rm-btns">
        <button type="button" className="outline" ref={keep} onClick={onClose} disabled={busy}>Keep</button>
        <button type="button" className="cta" onClick={() => void remove()} disabled={busy || preview.state !== 'ready'} aria-busy={busy}>{busy ? 'Removing…' : 'Remove'}</button>
      </div>
    </div>
  );
}
