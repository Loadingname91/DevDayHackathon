# Open decisions (as of Nov 19, 2026, evening)

Where things stand and what's waiting on you. Pick up from here on any device: clone the repo, open Claude Code in it, and say which decision you've made.

## 1. The new look (blocking the restyle)

We're replacing the cream background, warm palette and Bricolage/Hanken fonts, because they read as the Claude/ChatGPT house style. What stays no matter what: the quilt and stitching idea, the spool mascot, a colour for each app, and no red anywhere. Light and dark both get designed.

Three options are mocked on the canvas (https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P), each on its own page:

| Option | Canvas page | What it is | Your reaction so far |
| --- | --- | --- | --- |
| Cross-stitch Chart | Look: cross-stitch | Apps as floss colours with stitched pixel icons on an aida grid | "Looks like a spreadsheet" |
| Colour Blocks | Look: Gen Z options | Each app a solid block of bright colour, pieced like a modern quilt; money left set huge in wide, heavy type; dark by default | Not decided |
| Sticker Lid | Look: Gen Z options | Each app a die-cut sticker with a white border on a laptop lid; a waiting change is a sticker not yet pressed down | Not decided |

Not mocked yet: **Letterman Patches** (felt patches on a varsity jacket, heather grey in light mode and navy wool in dark mode). Ask for it and it gets built the same way.

Your choices:
- Pick one of the three.
- Mix them, for example Colour Blocks for Home with stickers for the app icons.
- Ask for Letterman Patches to be mocked first.
- Re-roll for a fresh set, optionally steered safer or bolder.
- Ask for the plain category-standard look done well.

Once you choose, Claude restyles every board (`design/tools/gen_all.py` and the hand-made boards), both prototypes and the Docs and Specs pages. It then writes DESIGN.md and updates `.impeccable/surfaces/app.md`, which still describes the old Quilter's Workbench direction. For Claude: the look was rolled with impeccable concept-seed key `57599b46` (re-roll round 1 done). The mock generators are `design/tools/gen_xstitch.py` and `design/tools/gen_looks.py`.

## 2. Before the pitch (from `docs/demo-day.md`)

- Get the receipt beat running end to end in the real app, on the Android phone and the laptop, over the hotspot, including "Use sample". Until it runs, the live demo is a no-go.
- Record a backup video of the receipt beat.
- Make the deck for the slide beats, with real survey and waitlist numbers. The pitch doc still has placeholders: [N], [X], [Y], [D].

## 2b. The business model (from the founder pack, Nov 19)

The founder pack ran twice. The current run, on Quilt as an app builder, is in `founder/` (start with `founder/summary.md`). The first run, on the photo-capture framing, is kept in `founder/run-1-photo-wedge/`. The plan's verdict is Not yet:

- 0 of 20 simulated buyers paid, but $6 is inside their acceptable range ($1.02 to $6.99). 15 of 20 passed on switching cost: their notes already live in Notes, Notion, Obsidian or Goodnotes.
- At $6, with Haiku 5.5 for capture and chat and Sonnet 5.5 for builds, each paying user leaves $3.24 (54%), and break-even is 26 paying users. With Opus 5.5 on every action, as `spec/clair-agent.md` says now, each one loses $19.58.
- The board (3 fund if, 4.7 out of 10) says to pick one hero job first. All three reviewers point at a class job: notes and syllabi filed into the right course, on the laptop.

Decided Nov 19, evening: the demo leads with building an app from a photo, connected on arrival (the Car app), with a 5-second fill. The whiteboard and grocery receipt are go/no-go fallbacks (`docs/demo-day.md` beat 4).

Your calls:
- the model split (a spec change);
- free import and export from Notion, Notes, Obsidian and Goodnotes;
- the student price ($4);
- the hero job for onboarding;
- whether the pitch doc's tiers change.

## 3. Smaller calls still open

- **Vercel limits:** check the function duration limit and the roughly 4.5 MB request limit on your plan. These are the first checks on the build list (`spec/backend.md` §13).
- **MCP:** a stub only for DevDay, nothing built. You haven't objected; say so if that's wrong.
- **Guests and a second device:** a guest can't add a second device until they add an email. The demo is unaffected because it uses the seeded account.
- **PRD open questions** (`spec/prd.md`): how long guest accounts are kept, how many credits a guest gets, and how long photos are kept.
- **Which apps come after DevDay:** `docs/research/tabos-app-audit.md` maps tabOS's 39 tabs onto Quilt. Notes with a notebook per class is proposed first; three questions sit at the end of that doc.
- **Pitch timing:** the pitch doc says to say what Quilt is "within 30 seconds", but the YC guidance it quotes says 20.

## Where everything lives

- Docs for people: `docs/`. Specs for building: `spec/`. Design files: `design/`. The repo map is `README.md`, and the map for Claude is `CLAUDE.md`.
- Setting up Claude Code on the new device: `docs/setup-claude-code.md`.
