# Quilt

Quilt is a personal app builder for a student's money, groceries, classes, workouts and to-dos. Clair, the AI inside it, builds apps from a sentence, connects them to each other and to your calendar, and proposes changes across them that you approve with one tap. We're building it for Lassonde DevDay on Nov 20, 2026.

## Where things are

| Folder | For | What's in it |
| --- | --- | --- |
| `docs/` | People | The pitch, the onboarding journey, the demo-day guide, research on the first user, and how to set up Claude Code on a new machine |
| `spec/` | Building it (written for coding agents) | Requirements and stories, the backend design, Clair's agent loop, the UI build plan, and the decision records in `spec/adr/` |
| `design/` | Design | The design canvas boards and their generator, the clickable prototypes, the design book and the board tests |
| `docs/start-here.md` | Picking up | Read this first: where things stand, what to do before the pitch, decisions waiting on you, and what's parked |
| `founder/` | The business | The founder-pack review: board, competitors, simulated buyer panel, pricing, unit economics and the plan (start with `founder/summary.md`); the first run is in `founder/run-1-photo-wedge/` |
| `setup/` | New machines | A copy of the Claude Code settings and hook (see `docs/setup-claude-code.md`) |

Start with `docs/start-here.md`. Then `docs/product.md` for the product in plain words, `docs/pitch.md` for the pitch, or `docs/demo-day.md` for the demo.

`GLOSSARY.md` defines the product's words (app, patch, Clair, basted, stitched). `PRODUCT.md` and `.impeccable/` hold the design brief the design tools read. `CLAUDE.md` is the map for Claude Code.

## Stack

React + Vite, served as a website on the phone and the laptop for DevDay (a native phone app comes after). A Python FastAPI API on Vercel holds the only Claude key. Supabase provides Postgres, sign-in and live updates, and Claude powers Clair. Details are in `spec/backend.md`.

## Live design links

- Design canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P
- Home prototype: https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV
- Flows prototype: https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne
- Motion catalogue: https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC
- Design book: https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq

These links are private to the owner until shared from each page's Share menu.
