# Start here

Last updated the night of Thu 19 Nov 2026, the evening before DevDay. Open this first on any device: clone the repo, open Claude Code in it, and tell it which item you're picking up.

## Where things stand

Quilt is an app builder. You describe an app, or show Clair a photo of a paper thing, and Clair builds it from the shared blocks. The new app arrives already connected to your calendar, your budget and your other apps, and Clair fills any app from a photo, a sentence or a file. Nothing changes until you tap OK, and everything is live on the phone and the laptop.

The demo follows that order. Beat 4 opens with a recorded run of Clair building a Car app from a photo of a maintenance card: the next oil change goes on the calendar and service costs are wired to the budget. Then you take a photo of an oil-change receipt live, and it fills the new app in about 5 seconds. The whiteboard note and the grocery receipt are the fallbacks if the app isn't solid. The script is `docs/demo-day.md`, beat 4.

## Before the pitch, in order

1. **Record the build.** Print the maintenance card from `spec/clair-agent.md` §12.0 and record Clair turning it into the Car app on the phone, with the laptop in shot. Say on stage that it's a recording.
2. **Get the live fill working if you can.** The oil-change receipt fills the Car app, and Budget goes from $412 to $367. If it isn't solid at the go/no-go, run the whiteboard beat or the grocery receipt instead. Both are in `docs/demo-day.md`.
3. **Seed the demo account** from `spec/backend.md` §2.2 and §2.3: 8 apps, every row a screen shows. Notes is needed for the whiteboard fallback.
4. **Put up the waitlist page tonight** with a real price ($6 a month, $4 for students) and an "Import from Notion / Notes / Obsidian" button. Its sign-ups fill the [N] in pitch beats 2 and 6.
5. **Make the deck** for the slide beats, with real numbers only.
6. **Check the Vercel limits** on your plan (function duration and the request size of about 4.5 MB). These are the first checks in `spec/backend.md` §13.

## Decisions waiting on you

| Decision | Options | Where to look |
| --- | --- | --- |
| The new look | Colour Blocks, Sticker Lid, a mix, mock Letterman Patches first, re-roll, or a plain look done well. Cross-stitch read as a spreadsheet to you | The canvas pages "Look: cross-stitch" and "Look: Gen Z options" (https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P). Claude restyles everything once you pick |
| Which AI model does what | Haiku 5.5 for photos and chat and Sonnet 5.5 for building, after DevDay. With Opus on every action, each paying user loses about $19.58 a month | `founder/cfo.md`; the setting is `CLAIR_MODELS` in `spec/clair-agent.md` §9 |
| Free import and export | From Notion, Apple Notes, Google Docs, Obsidian and Goodnotes, on every plan. 15 of 20 simulated buyers passed because moving their notes looked like a weekend of work | `founder/summary.md`, `founder/pricing.md` |
| Student price | $4 a month or $15 a semester, next to Plus at $6 | `founder/pricing.md` |
| The first job new users see | All three board reviewers chose a class job: notes and syllabi filed into the right course | `founder/board.md` |
| Pitch timing | The pitch doc says to say what Quilt is within 30 seconds; the YC advice it quotes says 20 | `docs/pitch.md` |
| Smaller calls | MCP stays a stub for DevDay. A guest can't add a second device until they add an email. How long guest accounts, guest credits and photos are kept | `spec/prd.md` open questions |

## Parked for after DevDay

- Workflows and triggers. This is the layer Notion, Airtable, Taskade and Zapier charge for. Here you'd describe a rule in a sentence and Clair writes it, with AI steps still waiting for your OK. The design, and an "Internship hunt" app to demo it with, are in `spec/workflows.md`. Nothing is built.
- Restyling the boards. They still show the old look and some old numbers. The fixes are listed in `spec/prd-data-provenance.md` (epic E5) and get done in the same pass as the new look.
- Data fields the boards assumed. Category limits, reminders, Workout sets, your name and recently opened apps are epics E3 and E4 of `spec/prd-data-provenance.md`.
- Which apps to build next. `docs/research/tabos-app-audit.md` maps tabOS's 39 tabs onto about 9 Quilt templates.

## Docs that are behind

These still lean on the receipt or the old look. They're fine to read but shouldn't be copied from until they're updated:

- `docs/research/persona-sam-student.md` and `docs/onboarding.md` treat receipt capture as Sam's main reason to use Quilt.
- In `docs/pitch.md`, the application answer "What will you build during DevDay?" still describes the receipt. If the application is already submitted, leave it. If it isn't, say the build.
- `.impeccable/surfaces/app.md` describes the old Quilter's Workbench look.

## Where everything lives

| Folder | What's in it |
| --- | --- |
| `docs/` | Written for people: this page, the pitch, the demo-day script, onboarding, research, and setting up Claude Code on a new machine |
| `spec/` | Written for building: requirements, the backend and seed, Clair's agent, the UI plan, the data provenance PRD and its audit, parked workflows, and decision records in `spec/adr/` |
| `founder/` | The business review from the founder pack: board, competitors, the simulated buyer panel, pricing, unit economics and the plan. `founder/summary.md` is half a page. The first run, on the photo framing, is in `founder/run-1-photo-wedge/` |
| `design/` | Canvas boards and their generators, prototypes, the design book and board tests |
| `setup/` | Claude Code settings to copy onto a new machine (`docs/setup-claude-code.md`) |

`README.md` is the repo map, and `CLAUDE.md` is the map Claude Code reads first.
