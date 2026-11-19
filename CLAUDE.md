# Quilt: agent map

Quilt is a phone-first app: apps built from 9 blocks, linked by stitches, filled by Clair (Claude with tools) through basted proposals the user confirms. Lassonde DevDay demo, Fri 20 Nov 2026.

## Layout

- `spec/`: source of truth for building. Read these before writing code.
  - `prd.md` (FR-*, AB-*), `prd-stories.md` (US-*, Given/When/Then)
  - `backend.md`: DDL, canonical demo seed (§2.2), dates/repeats (§3), order (§4), command service (§5), formulas (§6), sync (§7), auth (§8), endpoints (§10), edge cases (§11), deferred (§12), build order (§13)
  - `clair-agent.md`: agent loop, tool registry, SSE events, snapshot, pause/resume, evals
  - `ui-tech-plan.md`: client stack, contracts, files, motion
  - `adr/`: decision records. ADRs live here, not in `docs/adr/`.
- `docs/`: written for people (pitch, onboarding journey, demo-day guide, research, Claude Code setup). Prose there gets a `humanizer:humanizer` pass after edits.
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

## Design canvas

- Regenerate: `python3 design/tools/gen_all.py design/canvas && python3 design/tools/layout_canvas.py design/canvas`.
- Live canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P (the artifact serves files at `project/<file>`; publish by mapping each `project/<file>` to `design/canvas/<file>` in `files`). Home and Flows prototypes: see `design/README.md`.
- Never commit or publish `support.js` / `dc-runtime.js` (git-ignored; fetch from the artifact when needed).

## Working rules

- Commit or push only when asked.
- After changing a number or name, grep `docs/`, `spec/` and `design/tools/gen_all.py` for the old value.
