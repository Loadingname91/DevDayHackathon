// Measure each doc preview's height at 1280 px so the canvas frames fit.
// Usage: node measure_docs.js <playwright module> <docs-preview dir> <out heights.json>
const [,, pw, dir, out] = process.argv; const { chromium } = require(pw);
const fs = require('fs'), path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const res = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html'))) {
    await p.goto('file://' + path.resolve(dir, f), { waitUntil: 'networkidle' }).catch(() => {});
    await p.waitForTimeout(300);
    res[f.replace('.html', '')] = await p.evaluate(() => ({ total: document.documentElement.scrollHeight, h2: [...document.querySelectorAll('article > h2, article > h3')].map(e => Math.round(e.getBoundingClientRect().top + scrollY)) }));
  }
  fs.writeFileSync(out, JSON.stringify(res, null, 1)); console.log(res); await b.close();
})();
