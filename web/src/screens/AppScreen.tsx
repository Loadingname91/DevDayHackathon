import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { AddSheet } from '../components/AddSheet';
import { AppView } from '../components/AppView';
import { ArrangeSheet } from '../components/Arrange';
import { Bold } from '../components/Bold';
import { ConnectGoogle } from '../components/ConnectGoogle';
import { Icon } from '../components/Icon';
import { RemoveRow, RemoveStep } from '../components/RemoveApp';
import { FilterChip, filterTab, parseFilter, tabFor, tabHasField, validFilter } from '../components/Links';
import { Sheet } from '../components/Sheet';
import { Spool } from '../components/Spool';
import { Tag } from '../components/Tag';
import { listNames } from '../lib/format';
import { applyBlocks, applyTabs, useLayout } from '../lib/layout';
import { RM, T } from '../lib/motion';
import { loadApp, loadHome, markOpened, openClair, setDetail, useStore } from '../lib/store';
import { useWide } from '../lib/useWide';
import type { Rec } from '../api/types';

/**
 * An app (boards Workout, Groceries, Budget, Calendar, To-dos, Empty): the back chevron
 * and the app menu; the icon tile and the title; the status sentence the server writes;
 * underlined tabs when there is more than one page; then the blocks.
 */
export function AppScreen() {
  const { key = '' } = useParams();
  const [q, setQ] = useSearchParams();
  const app = useStore((s) => s.apps[key]);
  const home = useStore((s) => s.home);
  const now = useStore((s) => s.me?.server_now) ?? app?.server_now ?? '';
  const error = useStore((s) => s.error);
  const [adding, setAdding] = useState(false);
  const [menu, setMenu] = useState(false);
  const [arranging, setArranging] = useState(false);
  const layout = useLayout(key); // Arrange: this person's order and hidden tabs (lib/layout.ts); the app's own spec is untouched
  // the menu's last row opens a confirm step in the same sheet: the menu fades out (`out`), then the step arrives (components/RemoveApp.tsx)
  const [step, setStep] = useState<'menu' | 'out' | 'remove'>('menu');
  useEffect(() => {
    if (step !== 'out' || !menu) return;
    const t = setTimeout(() => setStep('remove'), RM() ? T.fb : T.stateOut);
    return () => clearTimeout(t);
  }, [step, menu]);
  const [openRow, setOpenRow] = useState<{ ref: string; id: string; open: boolean } | null>(null);
  const wide = useWide();
  const tabsRef = useRef<HTMLDivElement>(null);
  const settled = useRef(false);
  const patch = home?.apps.find((a) => a.key === key);
  useEffect(() => { void loadApp(key); if (!home) void loadHome(); markOpened(key); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  // `?filter=<relationField>:<id>` shows the rows that hold that id, on the tab that lists them (a tab asked for that lists them too stays)
  const filter = app ? validFilter(app.spec, parseFilter(q.get('filter'))) : null;
  const asked = app?.spec.tabs.find((t) => t.id === q.get('tab'))?.id;
  const filterAt = app && filter ? filterTab(app.spec, filter.field) : undefined;
  // the tabs in this person's order; a tab a link or a filter asked for stays even when hidden
  const tabs = app ? applyTabs(app.spec, layout, [asked, filterAt]) : [];
  const tab = app && filter && filterAt && !(asked && tabHasField(app.spec, asked, filter.field)) ? filterAt : asked ?? tabs[0]?.id;

  // `?row=<id>` opens that record: the edit sheet on a phone, the pane on a laptop (and its row scrolls into view). Said once, then the query is cleared.
  const row = q.get('row');
  useEffect(() => {
    if (!row || !app) return;
    const ref = Object.keys(app.data).find((k) => k.startsWith(`${key}/`) && (app.data[k] as Rec[]).some((r) => 'properties' in r && r.id === row));
    if (!ref) return; // not in this app's data (yet): the effect runs again when the app arrives
    const next = new URLSearchParams(q);
    next.delete('row');
    // a page of a notebook workspace opens in the workspace (`?page=`); a notebook opens its edit sheet
    const nbk = app.spec.tabs.flatMap((t) => t.children).find((b) => b.kind === 'notebook' && (b.pages === ref || b.source === ref));
    if (nbk && nbk.kind === 'notebook') {
      if (nbk.pages === ref) next.set('page', row); else setOpenRow({ ref, id: row, open: true });
      setQ(next, { replace: true });
      return;
    }
    const here = app.spec.tabs.find((t) => t.id === (next.get('tab') ?? app.spec.tabs[0]?.id));
    const lists = !!here?.children.some((b) => (b.kind === 'list' || b.kind === 'checklist') && b.source === ref);
    const at = lists ? undefined : tabFor(app.spec, ref);
    if (at) next.set('tab', at);
    setQ(next, { replace: true });
    if (wide) {
      setTimeout(() => { // after the pane has cleared its pick for the new screen
        setDetail({ app: key, ref, id: row });
        setTimeout(() => document.querySelector(`[data-row="${CSS.escape(row)}"]`)?.scrollIntoView({ block: 'center', behavior: RM() ? 'auto' : 'smooth' }), 120);
      }, 0);
    } else setOpenRow({ ref, id: row, open: true });
  }, [row, app]); // eslint-disable-line react-hooks/exhaustive-deps

  // the selected tab scrolls into view when the tabs overflow (a deep link, or a tap on a half-hidden one); the page itself never moves
  const wanted = tab;
  useEffect(() => {
    const list = tabsRef.current, el = list?.querySelector<HTMLElement>('[aria-selected="true"]');
    if (!list || !el) return;
    const left = el.getBoundingClientRect().left - list.getBoundingClientRect().left + list.scrollLeft - (list.clientWidth - el.offsetWidth) / 2;
    list.scrollTo({ left: Math.max(0, left), behavior: settled.current && !RM() ? 'smooth' : 'auto' });
    settled.current = true;
  }, [wanted, !!app]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!app) return <div className="screen"><div className="top-row"><Link to="/" className="round back" aria-label="Back to Home"><Icon name="back" /></Link></div><p className="muted" role="status">{error ?? ''}</p></div>;
  const { spec } = app;
  const first = spec.collections[0];
  const fresh = !!patch?.isNew;
  // board Empty ("Subscriptions is ready"): a new app with no rows yet shows only the ready card; its tabs and empty blocks wait for the first row
  const landing = fresh && !!first && Object.values(app.data).every((rows) => rows.length === 0);
  const page = spec.tabs.find((t) => t.id === tab);
  const pinnedAdd = (page ? applyBlocks(page, layout) : []).some((b) => b.kind === 'checklist' && b.add?.pinned);
  const connected = [...new Set((spec.stitches ?? []).map((s) => s.from.split('/')[0]).filter((k) => k !== key))]
    .map((k) => home?.apps.find((a) => a.key === k)).filter((a) => !!a);
  const rules = spec.workflows ?? [];

  return (
    <div className={`screen ${pinnedAdd ? 'with-add' : ''}`} data-dye={spec.dye}>
      <div className="top-row">
        <Link to="/" className="round back" aria-label="Back to Home"><Icon name="back" /></Link>
        <button className="round end menu-btn" aria-label={`${spec.name} menu`} onClick={() => setMenu(true)}>···</button>
      </div>
      <div className="ident">
        <span className="tile" aria-hidden="true"><Icon name={spec.icon} size={18} /></span>
        <h1 title={spec.name}>{spec.name}</h1>
        {fresh ? <Tag show text="new" /> : null}
        {spec.private && <span className="pill soft"><Icon name="lock" size={12} />&nbsp;Private</span>}
      </div>
      {app.status && !landing && <p className="status-s"><span><Bold text={app.status} /></span><Tag show={!!patch?.changed && !fresh} text="just changed" id={`patch:${key}`} /></p>}
      {fresh && connected.length > 0 && <span className="connected">Connected to {connected.map((a) => <span key={a!.key} data-dye={a!.dye} className="connected-app"><i className="dyedot" />{a!.name}</span>)}</span>}
      {key === 'calendar' && <ConnectGoogle />}
      {landing && (
        <>
          <section className="card landed arrive">
            <Spool expr="hello" size={96} />
            <b>{spec.name} is ready</b>
            <p>Add your first one. The fastest way is usually to tell Clair.</p>
          </section>
          <div className="stack">
            <button className="ghost wide" onClick={() => openClair(true)}><Icon name="spool" size={18} />Tell Clair</button>
            <button className="ghost wide" onClick={() => setAdding(true)}><Icon name="plus" size={18} />Type one in</button>
          </div>
        </>
      )}
      {fresh && first && <AddSheet app={key} appName={spec.name} collection={first} now={now} apps={home?.apps} open={adding} onClose={() => setAdding(false)} onAdded={() => void loadApp(key)} />}
      {tabs.length > 1 && !landing && (
        // roving tabindex: Tab reaches the selected tab only; the arrow keys, Home and End move and select (like a tap)
        <div className="tabs" role="tablist" aria-label={`${spec.name} tabs`} ref={tabsRef} onKeyDown={(e: KeyboardEvent<HTMLDivElement>) => {
          const ids = tabs.map((t) => t.id), at = ids.indexOf(tab ?? ''), n = ids.length;
          const to = e.key === 'ArrowRight' ? (at + 1) % n : e.key === 'ArrowLeft' ? (at - 1 + n) % n : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : -1;
          if (to < 0 || at < 0) return;
          e.preventDefault();
          setQ({ tab: ids[to] }, { replace: true });
          tabsRef.current?.querySelector<HTMLElement>(`[role="tab"]:nth-child(${to + 1})`)?.focus();
        }}>
          {tabs.map((t) => (
            <button key={t.id} id={`tab-${t.id}`} role="tab" className="tab" aria-selected={t.id === tab} aria-controls={`panel-${t.id}`} tabIndex={t.id === tab ? 0 : -1}
              onClick={() => setQ({ tab: t.id }, { replace: true })}>{t.title}</button>
          ))}
        </div>
      )}
      {filter && !landing && <FilterChip spec={spec} filter={filter} onClear={() => { const n = new URLSearchParams(q); n.delete('filter'); if (tab) n.set('tab', tab); setQ(n, { replace: true }); }} />}
      {!landing && <AppView key={tab} app={app} tab={tab!} apps={home?.apps ?? []} now={now} tabbed={tabs.length > 1} filter={filter} />}
      {/* the other tabs' panels are not drawn; an empty hidden one each keeps every tab's aria-controls pointing at a real panel */}
      {!landing && tabs.length > 1 && tabs.filter((t) => t.id !== tab).map((t) => <div key={t.id} id={`panel-${t.id}`} role="tabpanel" aria-labelledby={`tab-${t.id}`} hidden />)}

      {(() => {
        const c = openRow ? spec.collections.find((x) => `${key}/${x.key}` === openRow.ref) : undefined;
        const rec = c && openRow ? (app.data[openRow.ref] as Rec[] | undefined)?.find((r) => r.id === openRow.id) : undefined;
        return c && rec ? <AddSheet app={key} appName={spec.name} collection={c} now={now} apps={home?.apps} record={rec} open={openRow!.open} onClose={() => setOpenRow((r) => r && { ...r, open: false })} onAdded={() => void loadApp(key)} /> : null;
      })()}
      <Sheet open={menu} onClose={() => setMenu(false)} onExited={() => setStep('menu')} label={step === 'remove' ? `Remove ${spec.name}?` : `${spec.name} menu`}>
        {step === 'remove'
          ? <RemoveStep appKey={key} app={app} name={spec.name} dye={spec.dye} apps={home?.apps ?? []} onClose={() => setMenu(false)} />
          : (
            <div className={`rm-menu${step === 'out' ? ' rm-out' : ''}`} inert={step === 'out'}>
              <div className="sheet-head"><span className="txt"><h2>{spec.name}</h2><span className="sub">{tabs.length} tab{tabs.length === 1 ? '' : 's'}</span></span></div>
              <ul className="card list">
                {rules.length > 0 && (
                  <li className="row"><button className="row-btn" onClick={() => { setMenu(false); setQ({ tab: 't_workflows' }, { replace: true }); }}>
                    <span className="main"><span className="t">Rules</span><span className="s">{rules.length} rule{rules.length === 1 ? '' : 's'} · {rules.filter((r) => r.on).length} on</span></span><Icon name="chev" size={18} />
                  </button></li>
                )}
                <li className="row"><span className="row-btn"><span className="main"><span className="t">Connected</span>
                  <span className="s">{connected.length ? `Gets rows from ${listNames(connected.map((a) => a!.name))}` : 'Not connected to other apps yet'}</span></span></span></li>
                {spec.private && <li className="row"><span className="row-btn"><span className="main"><span className="t">Private</span>
                  <span className="s">{spec.settings?.clair_read ? 'Clair can read this app (you turned it on).' : "Clair can't read this app."}</span></span></span></li>}
                {!landing && (
                  <li className="row"><button className="row-btn" onClick={() => { setMenu(false); setArranging(true); }}>
                    <span className="main"><span className="t">Arrange</span><span className="s">Order and hide this app's tabs and sections</span></span><Icon name="chev" size={18} />
                  </button></li>
                )}
              </ul>
              <RemoveRow onOpen={() => setStep('out')} />
            </div>
          )}
      </Sheet>
      <ArrangeSheet spec={spec} open={arranging} onClose={() => setArranging(false)} tab={tab} />
    </div>
  );
}
