const [,, pw, url] = process.argv; const { chromium } = require(pw);
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
 const errs = []; p.on('pageerror', e => errs.push(e.message));
 await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
 const cal = () => p.$eval('#quilt .qp[data-open="Calendar"] .face', e => e.textContent).catch(() => 'n/a');
 await p.click('[data-s="evening"]'); await p.waitForTimeout(800);
 console.log('before', await cal());
 const btn = await p.$('[data-f="receipt"] [data-act="add"]');
 if (btn) { await btn.click(); await p.waitForTimeout(3500); }
 console.log('after', await cal(), btn ? '' : '(no receipt button found)');
 const undo = await p.$('.toast button');
 if (undo) { await undo.click(); await p.waitForTimeout(2000); console.log('after undo', await cal()); }
 console.log('errors', errs); await b.close(); })();
