const [,, pw, base, out] = process.argv; const { chromium } = require(pw);
const assert = (c, m) => { if (!c) { console.log('FAIL', m); process.exitCode = 1; } };
(async () => {
  const b = await chromium.launch(); const errs = [];
  const open = async (f, w = 390, h = 844) => { const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2, hasTouch: true, isMobile: w < 500 });
    p.on('pageerror', e => errs.push(f + ': ' + e.message)); await p.goto(base + f, { waitUntil: 'networkidle' }); await p.waitForTimeout(400); return p; };
  const check = (p, W) => p.evaluate((W) => {
    const o = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); if (!r.width || r.right <= W + .5 && r.left >= -.5) return false;
      for (let a = e.parentElement; a; a = a.parentElement) if (getComputedStyle(a).overflowX === 'auto') return false; return true; }).map(e => e.tagName + ':' + (e.textContent || '').trim().slice(0, 30));
    const s = document.querySelector('[role=dialog]'), n = document.querySelector('nav');
    return { o, gap: s && n ? n.getBoundingClientRect().top - s.getBoundingClientRect().bottom : null };
  }, W);
  const shot = async (p, n, W = 390) => { await p.waitForTimeout(300); await p.screenshot({ path: out + '/' + n + '.png' }); const c = await check(p, W);
    assert(!c.o.length, n + ' overflow ' + c.o); if (c.gap !== null) assert(c.gap >= 11, n + ' sheet covers bar ' + c.gap); console.log(n, 'ok', c.gap); };
  const href = async (p, sel) => p.locator(sel).first().getAttribute('href');

  let p = await open('OnWelcome.dc.html'); await shot(p, 'ob01-welcome');
  assert(await href(p, 'a:has-text("Start")') === 'OnSlips.dc.html', 'start link'); assert(await p.getByText('I have a join code').count() === 1, 'join link'); await p.close();

  p = await open('OnSlips.dc.html'); await shot(p, 'ob02-slips-empty');
  assert(await p.locator('a:has-text("Make my apps")').count() === 0, 'make disabled when none');
  for (const n of ['Money', 'Groceries', 'To-dos']) await p.getByRole('button', { name: n }).tap();
  await shot(p, 'ob03-slips-picked');
  assert(/Budget & subscriptions, Groceries, To-dos and Calendar/.test(await p.evaluate(() => document.body.innerText)), 'makes line');
  assert(await href(p, 'a:has-text("Make my apps")') === 'OnMaking.dc.html', 'make link'); assert(await href(p, 'a:has-text("Skip")') === 'Welcome.dc.html', 'skip link'); await p.close();

  p = await open('OnMaking.dc.html'); await p.screenshot({ path: out + '/ob04a-making-mid.png' }); await p.waitForTimeout(1200); await shot(p, 'ob04-making-done');
  assert(await href(p, 'a:has-text("Open Home")') === 'OnHome.dc.html', 'home link');
  assert((await p.$$eval('nav a[aria-label]', a => a.map(x => x.getAttribute('aria-label')))).join() === 'Budget,Groceries,To-dos,Calendar,Clair: type, talk or add a photo. Hold to talk', 'pins'); await p.close();

  p = await open('OnHome.dc.html'); await shot(p, 'ob05-home-first-prompt');
  assert(await href(p, 'nav a[role=button]') === 'OnSheet.dc.html', 'clair -> OnSheet');
  await p.getByRole('button', { name: 'Got it' }).tap(); await shot(p, 'ob05b-home-hint-dismissed'); await p.close();

  p = await open('OnSheet.dc.html'); await shot(p, 'ob06-sheet');
  assert(await href(p, '[role=dialog] a:has-text("Photo")') === 'OnCamera.dc.html', 'photo link'); await p.close();

  p = await open('OnCamera.dc.html'); await shot(p, 'ob07-camera-ask');
  assert(await href(p, 'a:has-text("Continue")') === 'Receipt.dc.html', 'continue -> receipt');
  await p.getByRole('button', { name: 'Not now' }).tap(); await shot(p, 'ob07b-camera-off');
  assert(await p.getByText(/Camera is off for Quilt/).isVisible(), 'camera off');
  await p.getByRole('button', { name: 'Back' }).tap(); await p.waitForTimeout(200); assert(await p.getByText('Use your camera?').isVisible(), 'back to ask'); await p.close();

  p = await open('Receipt.dc.html'); await p.getByRole('button', { name: 'Add to 3 apps' }).tap(); await shot(p, 'ob08-receipt-stitched'); await p.close();

  p = await open('OnCheckin.dc.html'); await shot(p, 'ob09-checkin');
  await p.getByRole('button', { name: 'Review' }).tap(); await shot(p, 'ob09b-checkin-offer');
  await p.getByRole('button', { name: 'Remind me' }).tap(); await shot(p, 'ob09c-checkin-reminded');
  assert(/Reminders at 8/.test(await p.evaluate(() => document.body.innerText)), 'reminded');
  assert(await href(p, 'a:has-text("Keep your quilt")') === 'OnKeep.dc.html', 'keep link'); await p.close();

  p = await open('OnKeep.dc.html'); await shot(p, 'ob10-keep');
  await p.getByRole('button', { name: 'Continue with Google' }).tap(); await shot(p, 'ob10b-kept');
  assert(await href(p, 'a:has-text("Add a device")') === 'OnDevice.dc.html', 'device link'); await p.close();
  p = await open('OnKeep.dc.html'); await p.getByRole('button', { name: 'Not now' }).tap(); await shot(p, 'ob10c-keep-later'); await p.close();

  p = await open('OnDevice.dc.html'); await shot(p, 'ob11-device');
  await p.getByRole('button', { name: 'Get a new code' }).tap(); await p.waitForTimeout(200);
  assert(/730 155/.test(await p.evaluate(() => document.body.innerText)), 'new code'); await p.close();

  p = await open('OnLaptop.dc.html', 1280, 800); await shot(p, 'ob12-laptop', 1280);
  await p.locator('#jc').click(); await p.keyboard.type('111111'); await shot(p, 'ob12b-laptop-bad', 1280);
  assert(/didn't work/.test(await p.evaluate(() => document.body.innerText)), 'bad code');
  await p.keyboard.type('482'); await shot(p, 'ob12c-laptop-typing', 1280);
  await p.keyboard.type('913'); await shot(p, 'ob12d-laptop-joined', 1280);
  assert(/Joined. Same quilt as your phone./.test(await p.evaluate(() => document.body.innerText)), 'joined'); await p.close();

  p = await open('Welcome.dc.html'); await shot(p, 'ob13-skipped-home');
  const wt = await p.evaluate(() => document.body.innerText); assert(!/Sam|Snap/.test(wt), 'welcome stale copy'); await p.close();
  p = await open('OnOffline.dc.html'); await shot(p, 'ob14-offline'); await p.close();
  p = await open('Empty.dc.html'); await shot(p, 'ob15-empty-updated');
  assert(await p.getByText('Tell Clair or add a photo').count() === 1, 'empty button'); await p.close();
  console.log('errors', errs); assert(!errs.length, 'page errors'); await b.close();
})();
