import { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Bar } from './components/Bar';
import { Detail } from './components/Detail';
import { Sidebar } from './components/Sidebar';
import { ClairSheet } from './components/ClairSheet';
import { anyMock } from './api/client';
import { MockMark } from './components/MockMark';
import { Peek } from './components/Peek';
import { Toast } from './components/Toast';
import { hasSession } from './lib/auth';
import { useWide } from './lib/useWide';
import { watchScrollEdges } from './lib/scrollEdge';
import { loadHome, loadMe, startSync, useStore } from './lib/store';
import { AppScreen } from './screens/AppScreen';
import { Build } from './screens/Build';
import { Chat } from './screens/Chat';
import { Session } from './screens/Session';
import { Home } from './screens/Home';
import { Join, SignIn } from './screens/SignIn';
import { You } from './screens/You';

export function App() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const nav = useNavigate();
  const wide = useWide();
  const { pathname } = useLocation();
  // an app whose screen is a notebook workspace takes the detail pane's room: the page and its preview are the detail
  const appKey = /^\/(?:a|app)\/([^/]+)/.exec(pathname)?.[1];
  const workspace = useStore((s) => !!appKey && !!s.apps[appKey]?.spec.tabs.some((t) => t.children.some((b) => b.kind === 'notebook')));
  useEffect(() => { void hasSession().then(setSignedIn); }, []);
  useEffect(() => watchScrollEdges(), []); // tabs, chip rows and the sidebar fade where they scroll (styles/blocks.css)
  useEffect(() => {
    if (!signedIn) return;
    void Promise.all([loadMe(), loadHome()]).then(() => startSync());
  }, [signedIn]);

  if (signedIn === null) return null;
  const entered = () => { setSignedIn(true); nav('/', { replace: true }); };
  if (!signedIn) {
    return (
      <div className="frame">
        <Routes>
          <Route path="/join" element={<Join onDone={entered} />} />
          <Route path="*" element={<SignIn onDone={entered} />} />
        </Routes>
      </div>
    );
  }
  // laptop: apps sidebar, the screen, a detail pane. Home's pane is Next up; an app's is the row you picked, or the app itself
  // until you pick one. The pane belongs to the route, never to loaded data, so the column can't jump when rows arrive.
  // A focused task (Build, Log a set, You) has none.
  const inApp = /^\/(a|app)\/[^/]+\/?$/.test(pathname);
  const pane = wide && (pathname === '/' || inApp) && !(inApp && workspace);
  return (
    <div className={`frame ${anyMock ? 'mocked' : ''}${wide ? ` shell${pane ? '' : ' no-detail'}${inApp && workspace ? ' ws' : ''}` : ''}`}>
      <MockMark />
      {wide && <Sidebar />}
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/a/:key" element={<AppScreen />} />
          <Route path="/a/:key/do/:blockId" element={<Session />} />
          <Route path="/app/:key" element={<AppScreen />} />{/* where the Google callback lands (backend.md §10) */}
          <Route path="/you" element={<You />} />
          <Route path="/build" element={<Build />} />
          <Route path="/chat" element={<Chat />} />{/* behind "Open chat ›": no detail pane (`pane` is only Home and an app), no bar */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {pane && <Detail />}
      <Toast />
      <ClairSheet />
      <Peek />
      <Bar />
    </div>
  );
}
