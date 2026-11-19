const [,, pw, base, out] = process.argv; const { chromium } = require(pw);
const assert = (c, m) => { if (!c) { console.log('FAIL', m); process.exitCode = 1; } };
(async () => {
  const b = await chromium.launch();
  const errs = [];
  const open = async (f) => { const p = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
    p.on('pageerror', e => errs.push(f + ': ' + e.message)); await p.goto(base + f, { waitUntil: 'networkidle' }); return p; };
  // horizontal overflow: any visible element whose right edge passes 390 (ignoring horizontally scrolling chip rows)
  const overflow = (p) => p.evaluate(() => [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); if (!r.width || r.right <= 390.5 && r.left >= -0.5) return false;
      for (let a = e.parentElement; a; a = a.parentElement) if (getComputedStyle(a).overflowX === 'auto') return false; return true; }).map(e => e.tagName + ':' + (e.textContent || '').trim().slice(0, 30)));
  const sheetVsBar = (p) => p.evaluate(() => { const s = document.querySelector('[role=dialog]'), n = document.querySelector('nav'); return s ? n.getBoundingClientRect().top - s.getBoundingClientRect().bottom : null; });
  const shot = async (p, n) => { await p.waitForTimeout(350); await p.screenshot({ path: out + '/' + n + '.png' }); const o = await overflow(p); assert(!o.length, n + ' overflow ' + o); console.log(n, 'ok', 'sheet-bar gap', await sheetVsBar(p)); };

  // ClairFridge
  let p = await open('ClairFridge.dc.html');
  await p.waitForTimeout(300); await shot(p, 'fridge-a-reading');
  assert(await p.getByText('Your fridge. I can see 14 things.').isVisible(), 'understanding line');
  await p.waitForTimeout(1400); await shot(p, 'fridge-b-ask');
  assert(await p.getByText("Looks like you're low on these. Add to Weekly shop?").isVisible(), 'question');
  await p.getByRole('button', { name: /^Butter/ }).tap(); await p.getByRole('button', { name: /^Cheddar/ }).tap();
  await p.getByLabel('Other').tap(); await p.keyboard.type('stopped buying orange juice'); await p.keyboard.press('Enter');
  await p.getByLabel('Other').blur();
  await shot(p, 'fridge-b2-picked');
  assert((await p.getByRole('button', { name: /^Butter/ }).getAttribute('aria-pressed')) === 'true', 'eggs pressed');
  await p.getByRole('button', { name: 'Add selected' }).tap(); await shot(p, 'fridge-c-answered');
  assert(await p.getByText('Noted: you stopped buying orange juice').isVisible(), 'noted chip');
  assert(await p.getByText('Add 2 to Weekly shop · mark orange juice not usual').isVisible(), 'proposal');
  assert(await p.locator('[role=dialog] section.st.basted').count() === 1, 'basted card');
  await p.getByRole('button', { name: 'Undo' }).tap(); await p.waitForTimeout(200);
  assert(await p.getByText('Add 2 to Weekly shop', { exact: true }).isVisible(), 'unnoted proposal'); await shot(p, 'fridge-c2-note-undone');
  await p.getByRole('button', { name: 'Start over' }).tap(); await p.waitForTimeout(200);
  assert((await p.getByRole('button', { name: /^Butter/ }).getAttribute('aria-pressed')) === 'false', 'start over resets');
  await p.getByRole('button', { name: /^Butter/ }).tap(); await p.getByRole('button', { name: /^Cheddar/ }).tap();
  await p.getByLabel('Other').fill('stopped buying orange juice');
  await p.getByRole('button', { name: 'Add selected' }).tap(); await p.waitForTimeout(200);
  await p.getByRole('button', { name: 'Add to Groceries' }).tap(); await shot(p, 'fridge-d-done');
  assert(await p.locator('nav a[aria-label=Groceries]').getByText(', just changed').count() === 1, 'pin tag');
  assert(await p.getByText('Butter, Cheddar · orange juice stops showing as low').isVisible(), 'sub line');
  assert(await p.evaluate(() => { const a = document.querySelector('nav a[aria-label=Groceries]'), d = a.querySelector('span[aria-hidden=true][style*="border-radius: 50%"]'); if (!d) return false; const r = a.getBoundingClientRect(), q = d.getBoundingClientRect(); return q.left >= r.left && q.right <= r.right && q.top >= r.top; }), 'notch inside pin');
  assert(await p.locator('[role=dialog] section.st.basted').count() === 0, 'stitched');
  // the start-over link scrolls into view in the done state
  await p.getByRole('button', { name: 'Start over' }).scrollIntoViewIfNeeded(); await shot(p, 'fridge-d2-done-scrolled');
  await p.getByRole('button', { name: 'Start over' }).tap(); await p.waitForTimeout(200);
  assert(await p.getByRole('button', { name: 'Add selected' }).isVisible(), 'back to ask');
  await p.close();

  // ClairNotes
  p = await open('ClairNotes.dc.html'); await p.waitForTimeout(500); await shot(p, 'notes-a');
  assert(await p.locator('a[href="You.dc.html"]').count() === 1, 'back to settings');
  await p.getByRole('button', { name: 'Delete note: Gym is pull day on Saturdays' }).tap(); await shot(p, 'notes-b-deleted-toast');
  assert(await p.getByRole('status').isVisible(), 'toast');
  await p.getByRole('status').getByRole('button', { name: 'Undo' }).tap(); await p.waitForTimeout(200);
  assert(await p.getByText('Gym is pull day on Saturdays').isVisible(), 'undo restores');
  await p.getByRole('switch').tap(); await shot(p, 'notes-c-off');
  assert((await p.getByRole('switch').getAttribute('aria-checked')) === 'true', 'switch');
  for (const t of ['You stopped buying orange juice', 'Gym is pull day on Saturdays', "Don't suggest snacks"]) await p.getByRole('button', { name: 'Delete note: ' + t }).tap();
  await shot(p, 'notes-d-empty');
  await p.close();

  // You -> link to notes
  p = await open('You.dc.html'); await p.waitForTimeout(400);
  await p.locator('a[href="ClairNotes.dc.html"]').scrollIntoViewIfNeeded(); await shot(p, 'you-entry'); await p.close();

  // Groceries
  p = await open('Groceries.dc.html'); await p.waitForTimeout(800);
  const chips = () => p.$$eval('button.chip', bs => bs.map(x => x.textContent.trim() + (x.getAttribute('aria-pressed') === 'true' ? '*' : '')));
  console.log('chips', await chips());
  const txt = await p.evaluate(() => document.body.innerText);
  assert(/14 to buy across 3 lists/.test(txt), 'summary counts'); assert(/Weekly shop · 4 to buy/.test(txt), 'weekly count');
  await shot(p, 'groc-a');
  await p.evaluate(() => document.querySelector('.scr').scrollTo(0, 400)); await shot(p, 'groc-b-usual-marks');
  console.log('usual marks', await p.getByText('usual', { exact: true }).count());
  await p.evaluate(() => document.querySelector('.scr').scrollTo(0, 0));
  await p.locator('.chips').evaluate(e => e.scrollLeft = 1000);
  await p.getByRole('button', { name: 'Usuals' }).tap(); await shot(p, 'groc-c-usuals');
  const t2 = await p.evaluate(() => document.body.innerText);
  assert(/Usuals · 8/.test(t2) && /every 6 days · bought today/.test(t2) && /every 2 weeks · last 15 days ago/.test(t2) && /every 10 days · last 6 days ago/.test(t2) && /14 to buy across 3 lists/.test(t2), 'usuals view');
  await p.getByRole('button', { name: /Taco night/ }).tap(); await p.waitForTimeout(300);
  await p.getByRole('button', { name: /Avocados/ }).tap(); await p.waitForTimeout(300);
  const t3 = await p.evaluate(() => document.body.innerText);
  assert(/Taco night · 4 to buy/.test(t3) && /13 to buy across 3 lists/.test(t3), 'taco toggle');
  await p.getByRole('button', { name: /New list/ }).tap(); await shot(p, 'groc-d-newlist');
  console.log('chips', await chips());
  await p.close();
  console.log('errors', errs); assert(!errs.length, 'page errors');
  await b.close();
})();
