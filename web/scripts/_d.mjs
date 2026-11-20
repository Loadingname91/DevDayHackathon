import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await (await b.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
await p.goto('http://localhost:3004', { waitUntil: 'networkidle' });
await p.waitForTimeout(6000); await p.mouse.click(800,300);
for (let i = 1; i <= 8; i++) {
  await p.screenshot({ path: process.argv[2] + `/s${i}.png` });
  await p.keyboard.press('ArrowRight');
  await p.waitForTimeout(2200);
}
await b.close();
