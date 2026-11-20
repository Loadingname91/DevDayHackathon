import { defineConfig, mergeConfig } from 'vite';
import base from './vite.config';

// A second dev server that talks to the LIVE API (spec/split.md §5), on its own port so the mock server keeps running.
// The API only allows https://… and http://localhost:5173 as origins, so this server proxies /api to it (same origin, no CORS).
//   VITE_API=live VITE_API_BASE=/api VITE_MOCK_ROUTES= VITE_DEV_PROXY=<the API's origin> npx vite --config vite.live.config.ts
const target = process.env.VITE_DEV_PROXY;
if (!target) throw new Error('Set VITE_DEV_PROXY to the API origin, e.g. https://api-production-a4c7e6bd.up.railway.app');

export default mergeConfig(base, defineConfig({
  server: { port: 5174, strictPort: true, proxy: { '/api': { target, changeOrigin: true } } },
}));
