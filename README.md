# Quilt

Quilt is a phone app for a student's money, groceries, classes, workouts and to-dos. Clair, the assistant inside it, reads a photo (a receipt, a fridge shelf, a syllabus) and updates every app it touches once you tap OK. We're building it for Lassonde DevDay on Nov 20, 2026.

## Where things are

| Folder | For | What's in it |
| --- | --- | --- |
| `docs/` | People | The pitch, the onboarding journey, the demo-day guide, research on the first user, and how to set up Claude Code on a new machine |
| `spec/` | Building it (written for coding agents) | Requirements and stories, the backend design, Clair's agent loop, the UI build plan, and the decision records in `spec/adr/` |
| `design/` | Design | The design canvas boards and their generator, the clickable prototypes, the design book and the board tests |
| `setup/` | New machines | A copy of the Claude Code settings and hook (see `docs/setup-claude-code.md`) |

Start with `docs/pitch.md` for the idea, or `docs/demo-day.md` for the demo.

`GLOSSARY.md` defines the product's words (app, patch, Clair, basted, stitched). `PRODUCT.md` and `.impeccable/` hold the design brief the design tools read. `CLAUDE.md` is the map for Claude Code.

## Stack

React + Vite, wrapped with Capacitor for Android (the same build runs as a website on the laptop). A Python FastAPI API on Vercel holds the only Claude key. Supabase provides Postgres, sign-in and live updates, and Claude powers Clair. Details are in `spec/backend.md`.

## Live design links

- Design canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P
- Home prototype: https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV
- Flows prototype: https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne
- Motion catalogue: https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC
- Design book: https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq

These links are private to the owner until shared from each page's Share menu.
