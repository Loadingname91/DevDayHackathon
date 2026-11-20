# Quilt: agent map

Quilt is a phone-first app: apps built from 9 blocks, linked by stitches, filled by Clair (Claude with tools) through basted proposals the user confirms. Lassonde DevDay demo, Fri 20 Nov 2026.

## Layout

- `spec/`: source of truth for building. Read these before writing code.
  - `prd.md` (FR-*, AB-*), `prd-stories.md` (US-*, Given/When/Then)
  - `backend.md`: DDL, canonical demo seed (§2.2), dates/repeats (§3), order (§4), command service (§5), formulas (§6), sync (§7), auth (§8), endpoints (§10), edge cases (§11), deferred (§12), build order (§13)
  - `clair-agent.md`: agent loop, tool registry, SSE events, snapshot, pause/resume, evals
  - `ui-tech-plan.md`: client stack, contracts, files, motion
  - `adr/`: decision records. ADRs live here, not in `docs/adr/`.
- `docs/`: written for people (start here, pitch, onboarding journey, demo-day guide, research, Claude Code setup). Prose there gets a `humanizer:humanizer` pass after edits.
- `design/`: canvas boards (generated), prototypes, design book, Playwright tests, `notes/fixspec.md` (cited as "fixspec").
- `GLOSSARY.md` (terms; say "app", never "tab"), `PRODUCT.md` and `.impeccable/` (design context for the impeccable skill): keep at the root.

## Fixed decisions

- Client: React + Vite + Capacitor (Android debug APK); same build is the laptop website. No Next.js, no Expo.
- API: Python FastAPI on Vercel only (not Railway). Supabase Postgres + anonymous auth + Realtime + Storage. Claude key only on the server.
- Model `claude-opus-5-5` via the Anthropic Python SDK tool runner. Clair writes only through `propose_changes` (basted change sets).
- All formulas in Python on the server. Online writes; IndexedDB read cache. No encryption for DevDay.

## Canonical demo facts (keep every doc consistent)

- Clock `DEMO_NOW` Fri 20 Nov 2026 5:45 pm America/Denver.
- Receipt: Corner Market 5:41 pm, $35.83, 8 items (`spec/backend.md` §2.2).
- Faces: Budget $412 → $376 (limit $1,200); Groceries 12 → 4 to buy; Calendar 3 → 4 today; Classes 2 → 3 due this week after the ECON 1010 syllabus.
- Fridge beat: Butter, Cheddar added; Orange juice marked not usual; Weekly shop 4 → 6.
- Build beat (demo beat 4, first): photo of a car maintenance card + "make this an app" → Clair builds Car (3 services), Oil change on Calendar Sat 5 Dec, Transport stitch on Budget; Make it; 8 → 9 apps. Then the 5-second fill: Campus Auto oil-change receipt $44.99 → Car log, next oil change Thu 20 May 2027, Budget $412 → $367 (Transport $86.99 of $100). Credits 32 → 22 → 17.
- Fallback beats (go/no-go): the whiteboard (Notes 3 → 4, Classes 2 → 3, HW 4 Tue 24 Nov) and the grocery receipt ($412 → $376), each from the seed.
- Quilt is an app builder first (describe any app, Clair builds it, data from anywhere, synced). Photos are one input; never frame Quilt as a receipt or photo app.
- Every value a board shows is a seeded row or a formula over seeded rows. The complete seed is `spec/backend.md` §2.2 + §2.3 (it wins over boards); the rule, its epics and the board fixes are `spec/prd-data-provenance.md`. Other faces at `DEMO_NOW`: Notes 3 this week, To-dos 2 today, Workout 3 this week, Subscriptions $38.46 a month. 8 apps. Pins: Groceries, Budget, Calendar, To-dos.

## Design canvas

- Regenerate: `python3 design/tools/gen_all.py design/canvas && python3 design/tools/layout_canvas.py design/canvas`.
- Live canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P (the artifact serves files at `project/<file>`; publish by mapping each `project/<file>` to `design/canvas/<file>` in `files`). Home and Flows prototypes: see `design/README.md`.
- Never commit or publish `support.js` / `dc-runtime.js` (git-ignored; fetch from the artifact when needed).

## Current state (Nov 19 night; human version: `docs/start-here.md`)

- Positioning: app builder first, apps connected on arrival, data from anywhere. Never lead with photo capture.
- Demo beat 4: recorded build of the Car app (`spec/clair-agent.md` §12.0) + live 5 s oil-change fill; fallbacks §12.0a whiteboard, §12.1 grocery receipt. Script: `docs/demo-day.md`.
- Seed: `spec/backend.md` §2.2 + §2.3 is complete and wins over boards. Rule and fixes: `spec/prd-data-provenance.md` (audit rows in `spec/data-audit/`).
- Business: `founder/` (founder skill pack; verdict Not yet). Model split (`CLAIR_MODELS`), $4 student price, free import/export are owner decisions.
- Parked, don't build unless asked: `spec/workflows.md` (workflows/triggers + Internship hunt showcase); board restyle waits on the look pick (`docs/start-here.md`, Decisions); `.impeccable/surfaces/app.md` is the old look, don't polish it.
- Look mocks: canvas pages "Look: cross-stitch" and "Look: Gen Z options" (`design/tools/gen_xstitch.py`, `design/tools/gen_looks.py`); concept seed 57599b46.
- Stale for framing (receipt-first): `docs/research/persona-sam-student.md`, `docs/onboarding.md`, the DevDay application answer in `docs/pitch.md`.

## Working rules

- Commit or push only when asked.
- After changing a number or name, grep `docs/`, `spec/` and `design/tools/gen_all.py` for the old value.
