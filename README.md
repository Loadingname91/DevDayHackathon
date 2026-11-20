# Quilt

Quilt is a personal app builder for a student's money, groceries, classes, workouts and to-dos. Clair, the AI inside it, builds apps from a sentence, connects them to each other and to your calendar, and proposes changes across them that you approve with one tap. We're building it for Lassonde DevDay on Nov 20, 2026.

## Where things are

| Folder | For | What's in it |
| --- | --- | --- |
| `docs/` | People | Where to start, the product in plain words, the pitch, the demo-day guide and the Home research |
| `spec/` | Building it (written for coding agents) | Requirements and stories, the backend design, Clair's agent loop, the UI build plan, and the decision records in `spec/adr/` |
| `design/` | Design | The Home, Flows and motion prototypes the app copies its look and motion from, the design notes, and the generators. The boards themselves live on the design canvas (link below) |
| `docs/start-here.md` | Picking up | Read this first: where things stand, what to do before the pitch, decisions waiting on you, and what's parked |
| `setup/` | New machines | A copy of the Claude Code settings, hook and skills list to copy onto a new machine |

Start with `docs/start-here.md`. Then `docs/product.md` for the product in plain words, `docs/pitch.md` for the pitch, or `docs/demo-day.md` for the demo.

`GLOSSARY.md` defines the product's words (app, patch, Clair, basted, stitched). `PRODUCT.md` and `.impeccable/` hold the design brief the design tools read. `CLAUDE.md` is the map for Claude Code.

## Stack

React + Vite, served as a website on the phone and the laptop for DevDay (a native phone app comes after). The site's files are hosted on Vercel. A Python FastAPI server on Railway holds the only Claude key. Supabase provides Postgres, sign-in and live updates, and Claude powers Clair. Details are in `spec/backend.md`.

## Live design links

- **Design canvas, the one place to start; it links to all the others:** https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P
- Product overview: https://claude.ai/artifact/6TXLXKTmxbqjt3kv8bbgRP
- Home prototype: https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV
- Flows prototype: https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne
- Motion catalogue: https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC
- Design book: https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq

These links are private to the owner until shared from each page's Share menu.

On Nov 19 the business review (`founder/`), the generated canvas boards, the design book, the board tests, early explorations and three stale docs were removed to clear the decks for the build. They are in git at commit `ee70002`.
