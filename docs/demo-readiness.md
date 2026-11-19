# Demo readiness: Quilt at Lassonde DevDay

Nov 19, 2026, the night before the pitch (Fri Nov 20). This is a read-only audit of the demo screens against the 90-second pitch in `docs/Quilt full product, MVP and DevDay pitch.md`, updated for today's Clair button decision (fixspec section D, `.impeccable/surfaces/app.md` "Decision Nov 19").

## Update, Nov 19 evening: new stack and demo device

The build target changed after this audit (see `docs/backend.md`, `docs/clair-agent.md`, ADR-004 to 008). What it changes for the demo:

- **Phone:** the Android app (Capacitor, debug APK sideloaded the night before). Backup on the same phone: the website in Chrome, signed in to the demo account. Second backup: `quilt-home.html`.
- **Laptop:** the same React app as a website on Vercel, joined to the demo account with the 6-digit join code.
- **Beats:** the receipt (Clair → Photo → Add to 3 apps → threads → $412 → $376 → laptop updates → Undo) stays the must-work path. The fridge comes second: Clair spots missing usuals, asks with a menu, adds to Weekly shop and remembers. Any photo works live, with "Use sample" after 12 s.
- **Voice is real now:** on-device speech recognition in, a one-line spoken reply only when Sam talked first. A hidden toggle keeps the scripted transcript as the stage fallback.
- **Before the pitch:** warm the Vercel functions (open Home and run one Clair turn on each device 5 minutes before), check Supabase Realtime is connected (confirm on the phone, watch the laptop), reset the demo workspace (`POST /dev/reset`), run "Use sample" once for the receipt and dismiss it, to prove the fixture resolves against the fresh seed (`docs/backend.md` §13 reset checklist), and have the 6 weeks of seeded trips in place so the fridge's usuals are real.
- The NO-GO below still stands until the app runs the receipt beat on the Android phone.

## Verdict

- **Design screens: GO after four fixes tonight.** The receipt path is drawn end to end: Home → Clair → Photo → reading → Add to 3 apps → Budget $412 → $376 → Calendar → Laptop. It is clickable in the canvas boards, and the phone part runs in `quilt-home.html` with the thread pull. The figures $35.83 and $412 → $376 agree everywhere. The Groceries app contradicts itself, though, and the phone prototype has no clean starting state for a live photo.
- **Live demo: NO-GO until two things are confirmed.** First, a working app. Git in this repo tracks only the pitch doc, and I found no Next.js code in or next to `/home/hitesh/workfiles/ProjectWork/DevDay`. Second, a backup video. None exists; the one in `~/workfiles/ProjectWork/demovideo` is about Lassonde DevLab, not Quilt. If the engine lives somewhere else, check it against the beat table below tonight.
- These notes describe the files as they stood around 07:50. Two agents are adding motion to `quilt-home.html` and `quilt-flows.html` right now, so re-check anything marked as theirs.

## 1. The demo script, beat by beat (updated for the Clair button)

The pitch doc gives 90 seconds in eight beats. Only beat 4 is screen work; the rest are slides. Lines in *italics* are rewrites made necessary by today's decisions. The doc still says "snap a receipt" and "tabs".

| # | Time | Beat | What is said or shown |
| --- | --- | --- | --- |
| 1 | 0:00–0:10 | Hook | "Hands up if you pay for more than three apps to manage your money, workouts or to-dos. Keep it up if they don't talk to each other." |
| 2 | 0:10–0:20 | Problem with our numbers | "We surveyed [N] U students this week. They pay for [X] apps, about $[Y] a month, and none of them share data." Use real numbers only; PRODUCT.md says none exist yet. |
| 3 | 0:20–0:30 | What it is, who we are | *"Quilt is one app that builds the apps you describe and stitches them together. Tell Clair anything, and every app it touches updates."* (Was: "builds the tabs you describe".) |
| 4 | 0:30–0:55 | Magic moment | See 4a–4j below. |
| 5 | 0:55–1:05 | Why not Notion | *"Notion makes you build it and type into it. Quilt builds an app from a sentence and fills it from whatever you tell Clair."* (Was: "fills itself from a photo".) |
| 6 | 1:05–1:15 | Traction and model | "[N] students joined our waitlist in [D] days. Free to start, $6 a month for unlimited apps and Clair." |
| 7 | 1:15–1:25 | Bigger vision | "Students first. But parents, caregivers, athletes and freelancers all pay for apps that don't talk, or need one nobody built." |
| 8 | 1:25–1:30 | Close | "Quilt: your life, stitched together." |

**Beat 4, the magic moment (25 s), as it now runs with the Clair button.** Under the Clair-button decision, the receipt is shown as one example of telling Clair something, not as the product.

| Step | ~Time | Action on the phone | What the room sees |
| --- | --- | --- | --- |
| 4a | 0:30 | Home | "Evening, Sam. $412 left this month. Pull day at 6 pm." |
| 4b | 0:32 | Tap **Clair** (right cell of the pinned bar) | Sheet: "Tell Clair anything", with chips for Talk, Photo and File. Say: *"Type it, say it, or show it. Tonight, a receipt."* |
| 4c | 0:35 | Tap **Photo** and shoot the known-good receipt | Viewfinder, then the shutter |
| 4d | 0:37 | Clair reads it | Spool "working" and "Reading the receipt…". With real AI this can take 4–10 s; past 6 s the status line says what it is still doing. |
| 4e | 0:45 | Review card: Corner Market, $35.83, 8 items, "Adding updates 3 apps", "Budget $412 → $376" | Nothing is saved yet (basted edge) |
| 4f | 0:47 | Tap **Add to 3 apps** | Thread pull from the card to the Budget, Groceries and Calendar pins; the status line rolls to $376 |
| 4g | 0:49 | Open Budget | "$376 left of $800 · just changed · Was $412" |
| 4h | 0:51 | (Groceries) | Bought items checked off or added; see the consistency problems |
| 4i | 0:52 | Open Calendar | "Grocery trip, Corner Market 5:41 pm · just changed", plus "Use the chicken and spinach" on Tue 24 Nov |
| 4j | 0:53 | Point at the laptop | Budget shows $376 with the "just changed" tag. No thread pull on the other device, by decision. |

Don't do Talk or File live. Voice is out of MVP (PRODUCT.md), so the chips should be visible but not demoed. If a judge asks, answer with the ClairTalk and ClairShare boards.

## 2. Each beat → screen, status, what's missing

Sources: **Canvas** = boards in `SP/artifact-files/d9e0bb03-…/project/` (published as "Mock App", https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P). **Home proto** = `SP/quilt-home.html`. **Flows proto** = `SP/quilt-flows.html`. **Motion lab** = `SP/workbench-motion.html`. SP = `/tmp/claude-1000/-home-hitesh-workfiles-ProjectWork-DevDay/c2d1a6dd-b96f-4aa8-b1d5-562aa46f99e8/scratchpad`.

| Beat | Screen / state | Status | What exactly is missing |
| --- | --- | --- | --- |
| 1, 2, 6, 7, 8 slides | None found | **Missing** | I found no deck. Beats 2 and 6 also need real survey and waitlist numbers. |
| 3 What it is | Canvas `Main.dc.html` "Home: the evening check-in waits in the queue"; Home proto "5:45 pm · typical" | Ready | Only the spoken line needs the "apps / tell Clair" update |
| 4a Home before | Canvas Main; Home proto evening | **Needs work** | In the Home proto's evening state, the Corner Market receipt card is **already waiting** before any photo is taken. Taking the photo just brings the same card to the top. It needs a start state with $412 and no receipt queued. |
| 4b Clair sheet | Canvas `ClairSheet.dc.html` "Tap Clair: tell Clair anything"; Home proto tap Clair | Ready | Small difference: the canvas suggestion reads "Spent $12 on lunch", the proto reads "…, gym tomorrow 6 pm" |
| 4c Camera | Home proto Photo → "Add a photo" viewfinder | Ready (proto) / **Missing** (canvas) | The canvas has no camera board; Photo jumps straight to Review receipt. The viewfinder is a drawn receipt, so it is fine for a fallback but not for a live shot. |
| 4d Reading | Home proto "Reading the receipt…" (1.2 s, scripted) | Ready (proto) | No canvas still. The real app's loading state is unverified. |
| 4e Review | Canvas `Receipt.dc.html` "Review receipt" (8 rows, untick, $35.83, three effects); Home proto receipt card | Ready (canvas) / **Needs work** (proto) | In the Home proto, "Review items" is only a toast ("Opens the items to review…"), so demo the card's "Add to 3 apps" there. |
| 4f Add + thread pull | Home proto (verified: threads to 3 pins, $412 → $376 roll, notches, Undo toast); Receipt board "Add to 3 apps" | Ready | None |
| 4g Budget drops | Canvas `Budget.dc.html`; Home proto status line | Ready | Home proto taps open a toast ("Opens Budget"), not a Budget screen, so use the canvas for this step |
| 4h Groceries | Canvas `Groceries.dc.html` | **Needs work** | It contradicts itself and the other apps; see section 3, items 1–2 |
| 4i Calendar | Canvas `Calendar.dc.html` "Calendar: dates from every app" | Ready | The Flows proto calendar ("2 · Connected in Calendar") has no grocery trip and puts "Spinach use by" under Sun 22 Nov, so don't use that one for this beat |
| 4j Laptop live | Canvas `Laptop.dc.html` (5:41 pm, $376, just changed); Flows proto "6 · Laptop" | **Needs work** | Both show only the after state, and no prototype pairs phone and laptop changing together. The Flows laptop says **12:41 pm**. Nothing proves real-time sync works. |
| 5 Why not Notion (optional visual) | Flows proto "1 · Build an app" (Describe → Build → Preview → Arrange → Add → Landed); canvas Build/Preview/Arrange/Connect/Empty | Ready | The Landed screen still has a "Snap a bill or receipt" button, and its note says "offers snap, type, or import" |
| Real app, beats 4a–4j | Next.js app with Claude vision photo fill | **Unverified / Missing here** | No code in this repo. This is the event-day judged feature, so the engine has to exist before Friday. |

## 3. Consistency problems on the demo path

Numbers that agree everywhere: receipt line items add up to **$35.83** (canvas Receipt board), **$412 → $376** (Main, Receipt, Budget, Laptop, Home proto, Flows laptop), Groceries **$177.83 of $200** (Budget, Laptop, Flows), subscriptions **$38.46** (= 11.99 + 9.99 + 13.49 + 2.99), Hulu **$120 a year**. Every weekday checks against Nov 2026; the old "Fri 21 Nov" bug is already fixed to "Sat 21 Nov". App dyes match across canvas and both protos (Budget #D3ECE7, Groceries #DDEBD2, Calendar #DCE4F3, To-dos #FBEBC4, Subscriptions #EADCF0, Workout #F8DCC2). No red anywhere.

Problems, in demo order:

1. **Groceries spend.** The canvas Groceries board says "**$142** of $200 spent this month", yet its "Last trip" is today's Corner Market receipt for $35.83. Budget and Laptop both say **$177.83** of $200 (142 + 35.83). The Groceries board is mixing the before and after states.
2. **What a receipt does to Groceries.** There are three different models:
   - The Receipt board effect says "Check off 8 items you bought".
   - Home's Groceries face goes from **12 items to 20 items** (Main board, Tabs board, Home proto `items += 8`, Motion lab "8 from your receipt").
   - The Groceries board still lists Oat milk, Eggs and Spinach as unbought "to buy" items after the trip.

   Pick one model. The smallest fix: Groceries is the to-buy list. The receipt ticks Oat milk, Eggs and Spinach (the 3 receipt items that are on it), the face reads "9 to buy", the effect line reads "Check off 3 items on your list", and the board shows $177.83.
3. **Time of the receipt.** The canvas boards and the Home proto use **5:41 pm** (evening story). The Flows proto uses **12:41 pm** in four places: the laptop "was $412 · …receipt from your phone, 12:41 pm", the Settings activity, the History sheet and the "Clair added a receipt" card. The Motion lab uses "fri nov 20 · 12:41" and greets "**Morning**, Sam." at 12:41. In the live app, use "just now".
4. **"About $26 a day."** The Ask answer (ClairResult/ClairAsk boards, Home proto, Flows proto) reads "$376 left until 1 Dec; after $60 you'd have $316, about $26 a day". Budget says "11 days to go", and $316 / 11 = **$28.73**. The Home proto divides by 12. Change it to "about $29 a day".
5. **The check-in has three versions.**
   - fixspec D: Lunch $12, Gym logged? 6 pm, Hulu renews Fri.
   - Main board: Blue Copper $5.25 "Apple Pay, 8:12 am"…
   - Home proto: Lunch $12 "from Apple Pay", Morning run 7 am, Spotify renews Sun.

   "Hulu renews Fri" also contradicts Budget's "cancel before Wed 2 Dec". "From Apple Pay" implies a payment feed, which conflicts with the pitch's "no bank logins, receipts and manual entries only". A judge can catch that. The check-in is not in the 90 s path, but it is on the Home screen behind the receipt.
6. **Calendar effect wording.** The pitch says "the shopping trip lands on the calendar". The Receipt board's Calendar effect is "Use the chicken and spinach by Tue 24 Nov". The Calendar board shows both, so it works, but the receipt card should name the one you point at.
7. **Budget total rounding. Resolved (Nov 19).** The canonical November total is **$1,200** (`docs/backend.md` §2.2, Budget `limit` 120000 cents): $1,200 − $788.00 = $412 before the receipt, $1,200 − $823.83 = $376.17 after, shown as $376. No $0.54 workaround. No current board shows a monthly total, so nothing on the canvas needs changing.
8. **Leftover "snap" and "tab" wording that contradicts Nov 19 decisions.**
   - Flows proto Landed: "Snap a bill or receipt" button, and the note "offers snap, type, or import from Budget".
   - Motion lab copy still uses tabs-era wording: "Your tabs 6", "new tab", "Clair builds a tab", "Stitch all 8", "Fix a row" and "1 receipt basted, waiting for your OK" (quilt jargon in UI copy). Its pin names are lowercase, and its receipt lines (Chicken thighs **$8.49**, Greek yogurt ×2 **$6.98**) don't match the Receipt board ($8.62, $4.29). The canvas boards are clean.
   - The pitch doc itself still says "snap a receipt" or "photograph a receipt" (Focus #3, the hero line, beat 4, the one-line description, "What will you build"), and "tabs" for what are now "apps" (beat 3, "five demo tabs").
9. **"N more" label.** The Main board says "Show 3 more"; the Home proto says "3 more waiting". Small, but they sit side by side in the design book.

## 4. Backup plan if live AI (or Wi-Fi) fails

In order of preference. The pitch doc already plans a phone hotspot, a recorded backup video and one cached known-good receipt.

1. **Cached parse in the real app.** A demo flag returns the stored Corner Market parse (the 8 rows on the Receipt board) instead of calling Claude, with the same UI. I couldn't verify this, since the code isn't here.
2. **Recorded backup video.** **Missing.** Record the 25 s beat from the real app, or from the fallbacks below, tonight.
3. **Phone fallback: `quilt-home.html`.** Clair → Photo → shutter → "Reading the receipt…" → card → Add to 3 apps → thread pull → $376 → Undo. It is fully scripted, uses no AI, and gave no console errors at 1400×1000. It needs the clean start state from problem 4a. It loads Google Fonts, so offline it falls back to system fonts. Open it once on the hotspot beforehand.
4. **Click-through fallback: canvas boards.** Main → ClairSheet → (Photo) → Receipt → Add to 3 apps → See Budget › → Calendar (pin) → Laptop. All links are real `<a>`s. The local `.dc.html` files render offline from a local server with `support.js`; the published artifact needs internet. There is no camera board, so you narrate the shot.
5. **Laptop side.** Show `Laptop.dc.html` on the laptop. It agrees with the phone at 5:41 pm. Don't use the Flows laptop (12:41 pm) unless that time is fixed.
6. **Last resort: still frames on a slide.** My render frames are a starting point: `SP/d1/grid2.png` (Home proto: sheet, camera, reading, card, thread pull, after, ask) and `SP/d1/grid.png` (canvas Main, ClairSheet, Receipt, Groceries, Budget, Calendar). They are scratch renders, not final slides.

Not usable as fallbacks: the Motion lab (old copy and numbers) and the Flows calendar (no grocery trip).

## 5. Fix list for tonight

**P0: must fix before the pitch**

1. **Confirm the real app runs beat 4 end to end** on phone plus laptop on the hotspot, including the cached-receipt flag. If there is no app, decide now to demo the prototypes and say so honestly. Remember that DevDay judges only the feature built on the day.
2. **Record the backup video** of beat 4. None exists.
3. **Groceries contradiction** (section 3, items 1–2):
   - Groceries board: $142 → $177.83, and tick Oat milk, Eggs and Spinach.
   - Receipt effect: "Check off 3 items on your list".
   - Home, Tabs and Home proto face: "12 items → 20 items" becomes "12 to buy → 9 to buy".
   - Make the same change in the real app's seed data.
4. **Home proto start state for a live photo:** $412, receipt not yet queued (the morning state minus the meals card, or a new "Demo" chip). Otherwise the receipt is on screen before the shutter. This file is owned by the motion agents, so hand it to them.
5. **Rewrite the spoken lines** for beats 3, 4 and 5 and the hero line to the Clair button and "apps" wording (section 1). The pitch doc still says "snap a receipt" and "tabs".
6. **Pick the laptop screen**: canvas Laptop (5:41 pm), or fix the Flows laptop's 12:41 pm.

**P1: nice to have tonight**

1. "About $26 a day" → "about $29 a day" in four places (ClairResult/ClairAsk boards, Home proto, Flows proto).
2. Pick one check-in. Drop "Apple Pay" (it conflicts with "no bank logins") and "Hulu renews Fri" (it conflicts with Wed 2 Dec).
3. Flows proto: "Snap a bill or receipt" → "Tell Clair or add a photo", and fix the Landed note. Move "Spinach use by" to Tue 24 Nov and add the Corner Market trip to the Flows calendar.
4. In the live app, show the Talk and File chips but don't demo them (voice is out of MVP). Have the ClairTalk and ClairShare boards ready for Q&A.
5. Make the Receipt card's Calendar line name the grocery trip, which is what the pitch says out loud.
6. Keep the Motion lab out of anything judges see, or update its copy (apps, "Add to 3 apps", 5:41 pm, Evening, matching line items).
7. Budget rounding: Eating out $165 → $164.46 so that $376 is exact.
8. Main board "Show 3 more" → "3 more waiting" to match the Home proto.
