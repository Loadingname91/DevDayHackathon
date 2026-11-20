# Quilt: agent map

Quilt is a phone-first app: apps built from 9 blocks, linked by stitches, filled by Clair (Claude with tools) through basted proposals the user confirms. Lassonde DevDay demo, Fri 20 Nov 2026. Late Nov 19 cut: `spec/adr/010-web-only-devday-planner-cut.md` (read it first).

## Layout

- `spec/`: source of truth for building. Read these before writing code.
  - `prd.md` (FR-*, AB-*), `prd-stories.md` (US-*, Given/When/Then)
  - `backend.md`: DDL, canonical demo seed (§2.2), dates/repeats (§3), order (§4), command service (§5), formulas (§6), sync (§7), auth (§8), endpoints (§10), edge cases (§11), deferred (§12), build order (§13)
  - `clair-agent.md`: agent loop, tool registry, SSE events, snapshot, pause/resume, evals
  - `ui-tech-plan.md`: client stack, contracts, files, motion
  - `adr/`: decision records. ADRs live here, not in `docs/adr/`.
- `docs/`: written for people (start here, the product in plain words `docs/product.md`, pitch, demo-day guide, Home research, Claude Code setup). Prose there gets a `humanizer:humanizer` pass after edits.
- `design/`: the Home, Flows and motion prototypes (the client ports CSS and motion from them), `notes/fixspec.md` (cited as "fixspec"), the Soft Quilt tokens and the canvas generators in `tools/`. See `design/README.md`.
- Removed on Nov 19 to clear the decks for the build (all in git at commit `ee70002`; restore with `git checkout ee70002 -- <path>`): `founder/` (business review), `design/canvas/` (generated boards), `design/book/`, `design/tests/`, `design/stills/`, `design/prototypes/explorations/`, the rejected look generators, `docs/onboarding.md`, `docs/research/persona-sam-student.md`, `docs/research/tabos-app-audit.md`. Older spec sections still cite some of these paths; the decisions they fed are recorded in `spec/prd.md` and `docs/start-here.md`.
- `GLOSSARY.md` (terms; say "app", never "tab"), `PRODUCT.md` and `.impeccable/` (design context for the impeccable skill): keep at the root.

## Fixed decisions

- Client: React + Vite website for DevDay, on the phone's browser (Home screen icon) and the laptop. No Capacitor, no APK, no Next.js, no Expo (ADR-010). Native phone app after DevDay, framework undecided. Older spec sections that say "APK" or "Capacitor" mean the website on the phone.
- API: Python FastAPI on Vercel only (not Railway). Supabase Postgres + anonymous auth + Realtime + Storage. Claude key only on the server.
- Model `claude-opus-5-5` via the Anthropic Python SDK tool runner. Clair writes only through `propose_changes` (basted change sets).
- All formulas in Python on the server. Online writes; IndexedDB read cache. No encryption for DevDay (planned later; this includes the stored Google token).
- Google Calendar: read-only, Google OAuth run by the API (`spec/backend.md` §8a), not a Quilt sign-in. Imported events are read-only records marked `source: "google"`.
- Build split: the base tonight (Nov 19), the workflow engine v1 on the day as the judged feature (`spec/workflows.md`, built as a ladder; steps 1 and 2 are never cut).

## Canonical demo facts (keep every doc consistent)

- Clock `DEMO_NOW` Fri 20 Nov 2026 5:45 pm America/Denver.
- Receipt: Corner Market 5:41 pm, $35.83, 8 items (`spec/backend.md` §2.2).
- Faces: Budget $412 → $376 (limit $1,200); Groceries 12 → 4 to buy; Calendar 3 → 4 today; Classes 2 → 3 due this week after the ECON 1010 syllabus.
- Fridge beat: Butter, Cheddar added; Orange juice marked not usual; Weekly shop 4 → 6.
- **Demo screen work is two beats (third cut, ADR-010).** Beat 4, **recorded** and announced as such (`spec/clair-agent.md` §12.11): three sentences build Calories, Running (10K on Sat 12 Dec, on Calendar) and Cycle (private) on the 8-app "before" state. Beat 5, **live** (`spec/clair-agent.md` §12.9, rows in `spec/backend.md` §2.3): Sam types "Plan my training for next week" (Mon 23 to Sun 29 Nov). Understanding line: "Read 9 apps: Calendar, Classes, To-dos, Workout, Running, Calories, Cycle, Meditation and Groceries." Card: "Next week's training · 4 lifts (1 kept, 3 moved), 2 runs, 1 recovery to-do, 1 grocery item" and "Mon to Thu you logged 1,650 to 1,970 calories a day (target 2,200).", **Add to 5 apps** (Workout, Running, To-dos, Groceries, Calendar). Plan: Pull day Mon 6:00 pm kept; Leg day Tue 7:00 am → 5:00 pm (also: energy 2 logged on day 1 of the last 3 cycles); Push day Wed 6:00 pm → 7:00 am; Easy run 3 mi Thu 26 Nov 8:00 am; Long run 5.5 mi Sat 28 Nov 9:00 am; Pull day Fri 6:00 pm → Sun 29 Nov 4:00 pm; to-do "10 min body scan" Tue 24 Nov 9:30 pm; Oats on Weekly shop (Oatmeal 3 of 5 mornings). One Home face changes: Groceries 12 → 13. Then "Do this every Sunday at 7 pm?" → Turn on → Workout's Workflows tab (6 tabs): "Every Sunday at 7:00 pm, plan next week's training". Credits 32 → 31.
- The planner has four rungs (lifts; + runs; + cycle and calorie lines; + recovery and groceries). Rung 1 is "Add to 2 apps" and is the must-run; the demo uses the highest rung that passes 10 of 10. Facts come from a server-built planning brief, never from the model's arithmetic. Clair gives no health, diet, training or medical advice.
- Google Calendar events (demo Google account, marked "from Google"): Dentist Tue 24 Nov 7:30 to 8:30 am; Drive home for Thanksgiving Wed 25 Nov 5:00 to 9:00 pm; Thanksgiving at home Thu 26 to Sat 28 Nov all day; Back to campus Sun 29 Nov 12:00 pm. ECON 1010 skips Thu 26 Nov.
- Appointment check (ladder step 2b, `spec/clair-agent.md` §12.10): haircuts Sat 8 Aug, 12 Sep, 17 Oct (every 35 days) → "Haircut is due" → Haircut Sat 21 Nov 2:00 pm, reminder 1 day before, **Add to Calendar**; rule "Every Sunday at 7:00 pm, check for appointments that are due". Credits 31 → 30.
- Cycle is read by Clair only while its switch is on (`settings.clair_read`): off on every new Cycle app, **on in the demo account**. Calories, Running and Cycle are built by Clair from a sentence; Meditation is a starter; all four use only the six base blocks (FR-A8).
- Engine ladder example rule (steps 3 and 4): "When an exam is added to Classes, add a study to-do two days before".
- Car build (reference example, **not built for DevDay**; numbers stay canonical for boards): photo of a car maintenance card + "make this an app" → Clair builds Car (3 services), Oil change on Calendar Sat 5 Dec, Transport stitch on Budget; Make it; 8 → 9 apps. Then the fill: Campus Auto oil-change receipt $44.99 → Car log, next oil change Thu 20 May 2027, Budget $412 → $367 (Transport $86.99 of $100).
- Last, only if built: the grocery receipt ($412 → $376, from the fresh seed). Fallbacks: "Use sample" (`fixture: "planner"`, recorded at the rung demoed), seeded Google events (`DEMO_GCAL_FIXTURE=1`), a lower planner rung, and the Flows prototype in place of the clip. The whiteboard and the fridge are not built for DevDay.
- Quilt is an app builder first (describe any app, Clair builds it, data from anywhere, synced), and its apps work together through Clair and rules. Photos are one input; never frame Quilt as a receipt or photo app.
- Every value a board shows is a seeded row or a formula over seeded rows. The complete seed is `spec/backend.md` §2.2 + §2.3 (it wins over boards); the rule, its epics and the board fixes are `spec/prd-data-provenance.md`. Other faces at `DEMO_NOW`: Notes 3 this week, To-dos 2 today, Workout 3 this week, Subscriptions $38.46 a month, Calories 1,140 today (target 2,200), Running 7 mi this week (Winter 10K Sat 12 Dec; long runs 4, 4.5, 5 mi), Meditation 25 min this week, Cycle last period started Tue 27 Oct (starts Tue 1 Sep, 29 Sep, 27 Oct; energy 2 on days 1 and 2). **12 apps** (boards still draw 8); the recording's "before" state has 8. Pins: Groceries, Budget, Calendar, To-dos.

## Design canvas

- The live canvas is the single place to look at the design; its Screens page links to every other Quilt artifact. The local boards were removed (above). Regenerate if needed: `python3 design/tools/gen_all.py design/canvas && python3 design/tools/layout_canvas.py design/canvas` (`layout_canvas.py` resets note positions).
- Live canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P (the artifact serves files at `project/<file>`; publish by mapping each `project/<file>` to `design/canvas/<file>` in `files`). Home and Flows prototypes: see `design/README.md`.
- Never commit or publish `support.js` / `dc-runtime.js` (git-ignored; fetch from the artifact when needed).

## Current state (late Nov 19; human version: `docs/start-here.md`)

- Positioning: app builder first, apps connected on arrival and working together, data from anywhere. Never lead with photo capture.
- No application code exists in this repo yet. Build order: `spec/backend.md` §13 (T1 to T4 tonight, D1 to D10 on the day, clip recorded by early afternoon). Go/no-go 10:00 Nov 20; freeze 2 hours before the pitch.
- Demo: a recorded clip of three builds, then the live training planner as the first rule of the workflow engine, with Google Calendar connected before the pitch. Script: `docs/demo-day.md`. The owner asked for all of it (builder, broad planner, Google, full engine ladder); the cut order in `spec/backend.md` §13 keeps a safe point.
- Seed: `spec/backend.md` §2.2 + §2.3 is complete and wins over boards. Rule and fixes: `spec/prd-data-provenance.md` (audit rows in `spec/data-audit/`, which describe the removed boards). The demo account starts with no rules.
- Owner decisions made Nov 19 (recorded in `spec/prd.md` Future Considerations and `docs/start-here.md`): model split after DevDay (Haiku 5.5 capture and chat, Sonnet 5.5 builds; Opus 5.5 at DevDay), Student Plus $4, free import and export, Calories as a starter app, appointments as a kind on Calendar events, pattern runs on Plus with a cap, health data on Plus (Android first, after the native app), Cycle app only with its own read switch, starter-app tab names (`spec/backend.md` §10).
- Business: the founder review was removed from the repo (commit `ee70002` has it; verdict was Not yet). Its decisions that stand: Student Plus $4, free import and export, the model split after DevDay.
- Not built for DevDay, don't build unless asked: the Car photo build, whiteboard, fridge, onboarding, builds from sentences other than the three recorded ones, the engine beyond v1 (dates, notifications, sending, connectors, Internship hunt showcase), anything deeper in Calories, Running, Meditation or Cycle (photo meals, pace, charts, timer, a prediction shown in the app), the planner changing weights or planning meals, health data; restyling the Screens boards to the new look.
- Look, decided Nov 19: Soft Quilt (pastel stitched patches on a soft gradient ground, Figtree, no red), light = Mint air, dark = Denim dusk. Canvas page "Look: Soft Quilt", tokens in `design/tools/gen_soft.py`, contract at the end of `.impeccable/surfaces/app.md`. Rejected options stay on "Look: cross-stitch" and "Look: Gen Z options".
- Stale: the DevDay application answer in `docs/pitch.md` (receipt-first) and its older sections (Android stack plan); the prototypes and the live canvas (receipt flow, 8 apps, no planner boards).
- Open: what to tell the DevDay organisers (the application named the receipt as the event-day feature); the native framework after DevDay; whether Calories sets a daily target.

## Working rules

- Commit or push only when asked.
- After changing a number or name, grep `docs/`, `spec/` and `design/tools/gen_all.py` for the old value.
