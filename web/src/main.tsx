import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { App } from './App';
import './styles/tokens.css';
import './styles/base.css';
import './styles/app.css';
import './styles/motion.css';
import './styles/home.css';
import './styles/clair.css';
import './styles/build.css';
import './styles/laptop.css';
import './styles/blocks.css';
import './styles/interaction.css';
import './styles/theme-cloth.css';
import './styles/theme-workbench.css';
import './styles/links.css';
import './styles/notes.css';
import './styles/demo.css';
import './styles/voice.css';
import './styles/chat.css';
import './styles/attach.css';
import './styles/remove.css';
import './styles/arrange.css';

// Look: Quilter's Workbench (theme-workbench.css) is the default (owner, Nov 20); `?look=cloth` or `?look=default` switch and are remembered.
// `?scheme=dark|light` forces a colour scheme for comparing; the default follows the phone.
try {
  const q = new URLSearchParams(location.search);
  if (q.has('look')) localStorage.setItem('quilt-look', q.get('look') ?? 'default');
  const look = localStorage.getItem('quilt-look') ?? (import.meta.env.VITE_LOOK as string | undefined) ?? 'workbench';
  if (look !== 'default') document.documentElement.dataset.look = look;
  if (q.has('scheme')) localStorage.setItem('quilt-scheme', q.get('scheme') ?? 'auto');
  const scheme = localStorage.getItem('quilt-scheme');
  if (scheme === 'dark' || scheme === 'light') document.documentElement.dataset.theme = scheme;
} catch { /* storage can be blocked: the default look is fine */ }

// iOS only fires :active on elements once a touch listener exists
document.addEventListener('touchstart', () => {}, { passive: true });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {import.meta.env.VITE_ROUTER === 'memory'
      ? <MemoryRouter><App /></MemoryRouter> /* the artifact build: no URL paths to route on */
      : <BrowserRouter><App /></BrowserRouter>}
  </StrictMode>,
);
