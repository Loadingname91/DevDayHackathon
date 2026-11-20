import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// VITE_SINGLE=1: one JS and one CSS file with relative paths, for the artifact page
// (scripts/artifact.mjs inlines them). The normal build is the website on Vercel.
const single = process.env.VITE_SINGLE === '1';

export default defineConfig({
  plugins: [react()],
  base: single ? './' : '/',
  server: { port: 5173, strictPort: true },
  build: single
    ? { outDir: 'dist-artifact', cssCodeSplit: false, assetsInlineLimit: 1e6, rollupOptions: { output: { inlineDynamicImports: true } } }
    : {},
});
