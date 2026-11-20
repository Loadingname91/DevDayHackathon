// Screenshots of the running client with headless Chromium (Playwright).
// Usage: node scripts/shot.mjs <outDir> [--base http://localhost:5173] [--scheme light|dark|both]
//        [--viewport 390x844] [--attr data-look=name] [--full] <path> [<path> ...]
// Example: node scripts/shot.mjs /tmp/shots --scheme both / /a/budget /a/calendar
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const outDir = args.shift();
if (!outDir) { console.error('need an output folder'); process.exit(1); }
let base = 'http://localhost:5173', scheme = 'light', viewport = '390x844', full = false, attr = null;
const paths = [];
while (args.length) {
  const a = args.shift();
  if (a === '--base') base = args.shift();
  else if (a === '--scheme') scheme = args.shift();
  else if (a === '--viewport') viewport = args.shift();
  else if (a === '--attr') attr = args.shift();
  else if (a === '--full') full = true;
  else paths.push(a);
}
if (!paths.length) paths.push('/');
const [width, height] = viewport.split('x').map(Number);
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
for (const s of scheme === 'both' ? ['light', 'dark'] : [scheme]) {
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2, colorScheme: s, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  for (const p of paths) {
    await page.goto(base + p, { waitUntil: 'networkidle' });
    if (attr) {
      const [k, v] = attr.split('=');
      await page.evaluate(([k, v]) => document.documentElement.setAttribute(k, v), [k, v]);
    }
    await page.waitForTimeout(500);
    const name = (p.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home') + (attr ? '.' + attr.split('=')[1] : '') + '.' + s + '.png';
    await page.screenshot({ path: join(outDir, name), fullPage: full });
    console.log(join(outDir, name));
  }
  await ctx.close();
}
await browser.close();
