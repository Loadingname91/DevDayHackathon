// Builds the artifact page: the mock-data app inlined into one HTML file, so the
// motion can be checked on claude.ai. Usage: node scripts/artifact.mjs <out.html>
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const dir = 'dist-artifact/assets';
const files = readdirSync(dir);
const js = readFileSync(join(dir, files.find((f) => f.endsWith('.js'))), 'utf8').replace(/<\/script/gi, '<\\/script');
const css = readFileSync(join(dir, files.find((f) => f.endsWith('.css'))), 'utf8').replace(/<\/style/gi, '<\\/style');
const out = process.argv[2];
const title = process.argv[3] ?? 'Quilt motion check';
writeFileSync(out, `<title>${title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400..800&display=swap">
<style>${css}</style>
<div id="root"></div>
<script type="module">${js}</script>
`);
console.log(out, Math.round((js.length + css.length) / 1024), 'KB');
