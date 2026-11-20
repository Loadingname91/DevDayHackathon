# Demo day: Quilt at Lassonde DevDay

The pitch is on Fri Nov 20, 2026. This guide covers the 90-second pitch in `docs/pitch.md` as it runs with the Clair button (`design/notes/fixspec.md` section D, `.impeccable/surfaces/app.md` "Decision Nov 19") on the current stack (`spec/backend.md`, `spec/clair-agent.md`, ADR-004 to 008). The demo clock is pinned at 5:45 pm.

The live demo is still NO-GO until the app runs the receipt beat on the Android phone. Everything still open is listed in section 5.

## 1. What the demo shows, beat by beat

The pitch is 90 seconds in eight beats. Only beat 4 is screen work, and the rest are slides. Lines in *italics* are rewrites for the Clair button and the "apps" wording.

| # | Time | Beat | What is said or shown |
| --- | --- | --- | --- |
| 1 | 0:00-0:10 | Hook | "Hands up if you pay for more than three apps to manage your money, workouts or to-dos. Keep it up if they don't talk to each other." |
| 2 | 0:10-0:20 | Problem with our numbers | "We surveyed [N] U students this week. They pay for [X] apps, about $[Y] a month, and none of them share data." Use real numbers only; PRODUCT.md says none exist yet. |
| 3 | 0:20-0:30 | What it is, who we are | *"Describe any app and Clair builds it: notes for each class, a workout log, a car tracker. Fill it from anywhere: type it, say it, snap it, drop a file. It's on your laptop before you sit down."* |
| 4 | 0:30-0:55 | Magic moment | See 4a to 4j below. |
| 5 | 0:55-1:05 | Why not Notion | *"Notion makes you build it. AI app builders build apps that sit alone. Quilt's apps arrive connected to your calendar, your budget and each other, and nothing changes without your OK."* |
| 6 | 1:05-1:15 | Traction and model | "[N] students joined our waitlist in [D] days. Free to start, $6 a month, $4 for students." |
| 7 | 1:15-1:25 | Bigger vision | "Students first. But parents, caregivers, athletes and freelancers all pay for apps that don't talk, or need one nobody built." |
| 8 | 1:25-1:30 | Close | "Quilt: your life, stitched together." |

### Beat 4, build an app from a photo, then fill it (25 s, must work)

The unique part is the build: one photo becomes a working app that's already connected to your other apps. **Plan (Nov 19):** record a clean run of Clair doing the build (steps 4b to 4d) and show it during the pitch. Say on stage that it's a recording ("here's a run we recorded this morning"), as `spec/prd.md`'s escalation rule asks, then do the 5-second fill live if the app is up. Capture follows in 5 seconds to show the new app fills like any other. If the build isn't solid at the go/no-go, run the whiteboard beat or the grocery receipt instead (`spec/clair-agent.md` §12.0a and §12.1).

| Step | ~Time | Action on the phone | What the room sees |
| --- | --- | --- | --- |
| 4a | 0:30 | Home | "Evening, Sam. $412 left this month." 8 apps. Say: *"I have a car. Quilt doesn't have a car app. Watch."* |
| 4b | 0:32 | Tap **Clair → Photo**, shoot the printed maintenance card, type or say *"make this an app"* | Viewfinder, shutter, "Looking at your photo…", then the build in chalk |
| 4c | 0:40 | Clair's card | "Make a Car app? 3 services. Calendar: Oil change Sat 5 Dec. Budget: service costs go to Transport." Say: *"It's already wired to my calendar and budget."* |
| 4d | 0:43 | Tap **Make it** | The Car patch sews onto Home; point at the laptop, where it has appeared too |
| 4e | 0:46 | Tap **Clair → Photo**, shoot the oil-change receipt | Card: Add to 3 apps: Car log, Budget $412 → $367, Calendar oil change moves to 20 May |
| 4f | 0:51 | Tap **Add to 3 apps** | Thread pull to the pins; the status line rolls to $367 |
| 4g | 0:53 | Undo on the toast | It goes back. Say: *"Any app you can describe, built and connected in seconds."* |

The must-work path ends with Undo on the toast. The Budget limit is $1,200 for November, so $412 before the receipt and $376 after.

If Clair hasn't proposed anything after 12 s, "Use sample" appears (a recorded build run, or the stored oil-change receipt). Any photo works live, so a judge's photo is fine too.

Voice is real. Speech goes in through on-device speech recognition, and Clair speaks a one-line reply only when Sam talked first. A hidden toggle keeps the scripted transcript as the stage fallback.

### Second beat, the fridge

The fridge comes after the receipt. Clair spots the missing usuals, asks with a menu, adds to Weekly shop and remembers the answer. Butter and Cheddar get added, Orange juice is marked not usual, and Weekly shop goes from 4 to 6.

## 2. The devices

- **Phone:** the Android app (Capacitor), as a debug APK sideloaded the night before. The first backup on the same phone is the website in Chrome, signed in to the demo account. The second backup is `design/prototypes/quilt-home.html`.
- **Laptop:** the same React app as a website on Vercel, joined to the demo account with the 6-digit join code. If the live laptop fails, show `design/canvas/Laptop.dc.html` (see section 4).

## 3. Before the pitch

- Sideload the debug APK on the phone the night before.
- Five minutes before, warm the Vercel functions: open Home and run one Clair turn on each device.
- Check that Supabase Realtime is connected: confirm something on the phone and watch the laptop.
- Reset the demo workspace (`POST /dev/reset`).
- Run "Use sample" once for the receipt and dismiss it. This proves the fixture resolves against the fresh seed (`spec/backend.md` §13 reset checklist).
- Make sure the 6 weeks of seeded trips are in place, so the fridge's usuals are real.
- Have the phone hotspot ready, and open `design/prototypes/quilt-home.html` on it once so the fallback has loaded at least once.

## 4. Backup plan if live AI or Wi-Fi fails

The pitch doc plans a phone hotspot, a recorded backup video and one cached known-good receipt. In order of preference:

1. **"Use sample" in the real app.** It appears after 12 s and replays the stored Corner Market parse (the 8 rows on the Receipt board) instead of calling Claude, with the same UI.
2. **Scripted voice.** If speech recognition fails, use the hidden toggle for the scripted transcript.
3. **The website in Chrome on the phone,** signed in to the demo account, if the APK fails.
4. **Recorded backup video.** This doesn't exist yet (section 5).
5. **Phone fallback: `design/prototypes/quilt-home.html`.** Clair → Photo → shutter → "Reading the receipt…" → card → Add to 3 apps → thread pull → $376 → Undo. It is fully scripted, uses no AI, and gave no console errors at 1400×1000. It still needs a clean start state (section 5). It loads Google Fonts, so offline it falls back to system fonts.
6. **Click-through fallback: the canvas boards in `design/canvas/`** (published as "Mock App", https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P). Main → ClairSheet → (Photo) → Receipt → Add to 3 apps → See Budget › → Calendar (pin) → Laptop. All links are real `<a>`s. The local `.dc.html` files render offline from a local server with `support.js`, while the published artifact needs internet. There is no camera board, so you narrate the shot.
7. **Laptop side.** Show `Laptop.dc.html` on the laptop. It agrees with the phone at 5:41 pm. Don't use the Flows laptop, which says 12:41 pm, unless that time gets fixed.
8. **Last resort: still frames on a slide.** The render frames are a starting point: `design/stills/grid2.png` (Home proto: sheet, camera, reading, card, thread pull, after, ask) and `design/stills/grid.png` (canvas Main, ClairSheet, Receipt, Groceries, Budget, Calendar), where SP is `/tmp/claude-1000/-home-hitesh-workfiles-ProjectWork-DevDay/c2d1a6dd-b96f-4aa8-b1d5-562aa46f99e8/scratchpad`. They are scratch renders, not final slides.

The Motion lab (`design/prototypes/explorations/workbench-motion.html`) is not usable as a fallback because of its old copy and numbers, and neither is the Flows calendar, which has no grocery trip.

### Which design screen covers each beat

Canvas = boards in `design/canvas/`. Home proto = `design/prototypes/quilt-home.html`. Flows proto = `design/prototypes/quilt-flows.html`.

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
| 4h Groceries | Canvas `Groceries.dc.html` | **Needs work** | It contradicts itself and the other apps; see section 5, problem 1 |
| 4i Calendar | Canvas `Calendar.dc.html` "Calendar: dates from every app" | Ready | The Flows proto calendar ("2 · Connected in Calendar") has no grocery trip and puts "Spinach use by" under Sun 22 Nov, so don't use that one for this beat |
| 4j Laptop live | Canvas `Laptop.dc.html` (5:41 pm, $376, just changed); Flows proto "6 · Laptop" | **Needs work** | Both show only the after state, and no prototype pairs phone and laptop changing together. The Flows laptop says **12:41 pm**. Nothing proves real-time sync works. |
| 5 Why not Notion (optional visual) | Flows proto "1 · Build an app" (Describe → Build → Preview → Arrange → Add → Landed); canvas Build/Preview/Arrange/Connect/Empty | Ready | The Landed screen still has a "Snap a bill or receipt" button, and its note says "offers snap, type, or import" |

## 5. Still open

Checked against the files in `design/` on the evening of Nov 19. The Groceries numbers (12 to 4 to buy, $177.83 of $200), the 5:41 pm receipt time, "about $29 a day", the check-in, the "N more" label, the Flows wording and the pitch doc's wording all agree now, so they're no longer listed.

### Must fix before the pitch

1. **Run the receipt beat end to end in the real app** on the Android phone and the laptop, on the hotspot, including "Use sample". Until it does, the live demo is a no-go. If it can't be made to work, decide early to demo the prototypes and say so, because DevDay judges only the feature built on the day.
2. **Make the build beat work:** `propose_app` with `rows` and `stitches_into`, the Make it confirm, and the new patch appearing on the laptop. Print the maintenance card and the Campus Auto receipt, record a good run of each for "Use sample", and pass their test cases (`spec/clair-agent.md` §16). Seed the Notes app too: the whiteboard is the first fallback. Decide at the go/no-go which beat opens.
3. **Record the backup video** of beat 4. None exists yet. The one in `~/workfiles/ProjectWork/demovideo` is about Lassonde DevLab, not Quilt.
4. **Make the deck** for the slide beats (1, 2, 6, 7, 8), with real survey and waitlist numbers for beats 2 and 6.

### Nice to have

1. The Receipt board's Calendar line says "Use the chicken and spinach by Tue 24 Nov". The pitch says the grocery trip lands on the calendar, so the card could name the trip instead. The Calendar board already shows both.
2. Keep the motion catalogue (`design/prototypes/motion-catalogue.html`) and the explorations out of anything judges see. Their copy is older: 12:41 pm, "about $26 a day", "tabs", and Groceries going to 20 items.
