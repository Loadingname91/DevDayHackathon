---
version: 1
slug: "app"
primary_target: "app"
related_targets: []
---

# Quilt app surface brief

Scope: the Quilt phone-width web app (home, tab view, Clair build, Clair fill, calendar, chat) and its laptop layout. Visitor mode: Operate.

Audience and job: Sam, the "forgetting tax" student (docs/research/persona-sam-student.md). Capture in seconds, see what changed across tabs, approve what Clair proposes.

## Direction contract

THESIS: How a quilter works decides how the app behaves. Chalk is an idea, basting is a draft waiting for a yes, running stitch is saved. Refuses the category default of soft identical cards with sparkle-icon AI.

OWN-WORLD: Unbleached muslin ground, white patches edged in stitches, 8 pastel patch dyes x 3 woven prints for tab identity, denim for actions, mustard thread for "just changed", ink cross-hatch for over/conflict, no red anywhere. Bricolage Grotesque display, Hanken Grotesk UI, DM Mono tabular numbers. Clair's mark is a tailor's-chalk triangle; Clair's proposals are dotted chalk outlines.

STORY: Sam snaps a receipt, sees it basted, taps once, and watches the thread pull into groceries, budget and calendar. They trust Clair because nothing is sewn without a yes and every seam can be ripped.

FIRST VIEWPORT: Greeting, then whatever is basted and waiting (one card, primary action "Stitch all N" in thumb reach), then pinned patches with selvedge dots, then the quilt grid; dock pinned at the bottom.

FORM: Quilter's Workbench, own-list position 1 (IMPECCABLE'S PICK over assigned Receipt Quilt), seed key 73226588. Raises kept: cross-hatch not red, held "just changed" tag, Clair's checked stamp.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Settled decisions (Nov 18, 2026)

- UI copy plain; quilt words only "patch", "stitch it in", "pieced by clair".
- States: chalk = Clair idea; basting = waiting for OK; running stitch = saved; mustard tag = just changed (held until seen); cross-hatch = over/conflict; frayed edge = error; seam ripper = undo with re-stitch.
- Signature motion: thread pull on confirm. Everything else is feedback or continuity only.
- Quilt-block glyphs only in Build, Clair building and Inspect.
- Texture: stitches on edges only, no fabric photos or grain, one texture per card.
- Light only for DevDay; tokens ready for an indigo dark theme.
- Laptop: same components as a 2-3 column quilt grid.

## Settled decisions, round 3 (Nov 18, 2026)

- Many tabs: up to 8 big patches; 9-20 three pinned big + compact sorted by last opened; 21+ piles (money, body, school, home, other) with "Jump to a patch". Dock = 5 most recent + all.
- Tab identity: 8 dyes x (solid, gingham, stripe, dot) = 32; neighbours never share a dye; icon + name always. Printed patches get no stitch edge (one texture per card).
- Patches unopened 14+ days fade; at 21+ tabs Clair offers to fold them away (never automatic). Folded tabs keep data and links, unfold when something new lands in them, and are always found by "Jump to a patch".
- Other devices get the "just changed" tag, never the thread pull.
- Clair's status line is the only loading UI; past 6 s it says what it's still doing. No spinners.
- Tab switches have no loader: under 100 ms just paint; first visit on slow data shows the layout with basting where content will go; revisits show cached values with "updated N min ago".
- Mascot: the spool buddy is Clair's face (one character); UI copy never uses a pronoun for Clair. Eight expressions: hello, working, thinking, waiting, stitched, proud, oops, sleepy, each mapped to a stitch state. One per screen; never on tab switches, money warnings or dense lists. Proud only for real savings or records. Sizes 30 / 44 / 96 px. Hop and shake play once; reduced motion shows the face only. The spool replaces the chalk triangle as Clair's mark; dotted chalk outlines still mark proposals.
- Motion tokens: 120 feedback, 220 state, 350 layout, 600 focal; exits 0.5-0.7x; ease cubic-bezier(.16,1,.3,1); no bounce.
- Reference prototype: https://claude.ai/artifact/1wAsrxfWhJQYHuinU9J3e8

## Settled decisions, round 4: build flow, search, rows, settings, laptop (Nov 19, 2026)

- Build a tab, 5 screens: Describe (sentence first, suggestion chips, 4-6 patterns below that skip to preview) → Build (chalk → basted, spool; at most 2 quick-choice questions, only if truly ambiguous) → Preview (full tab with labelled example rows; swipe 3 layouts named by lead block: List first / Calendar first / Summary first) → Arrange, optional (drag reorder, seam-ripper remove, + add from 9 block marks, flip list/table/calendar, tell Clair) → Stitch (name, dye, icon pre-filled at top; Clair's connections pre-ticked with what flows; skippable; keep-examples off by default) → land on the new tab, spool Hello, snap / type / import first row.
- Stitched rows in receiving tabs carry a source dot in the source dye and "from <tab> ›"; first arrival gets "just changed". Tab menu: Stitches (in/out toggles), History, Arrange (same editor, can re-pick layouts).
- Search: pull down anywhere + dock search icon (dock = 5 recent + search + all); inside a tab it opens scoped ("in Budget ×") with filter chips from the tab's fields, "everywhere else (N)", and an Ask Clair answer row; ⌘K on laptop.
- Rows: tap → edit sheet with delete; swipe right complete, swipe left delete, both with undo; long-press multi-select. Delete is ink, never red.
- Profile button top-right on Home → Settings: Activity first (every Clair change with undo), what Clair can read (full / field names / none), export, delete account, credits meter (also in Clair's chat header). Per-tab History in the tab menu.
- Laptop split view: tab list | tab | row detail; while building, Clair conversation | live preview.
- DevDay rebuild includes: laptop, full build preview, search + find in tab, row edit/delete, activity log, settings with privacy + credits.

## Terminology (Nov 19, 2026)

- The thing Clair builds is an **app** ("New app", "All apps", "I built your Subscriptions app"). Sections inside an app are **tabs** (Workout app has 5 tabs). "Patch" is the visual and brand word only (each app is a patch in your quilt). Replaces earlier "tab" wording in this brief.

## Home and dock (Nov 19, 2026) · supersedes the earlier "dock = 5 recent + search + all" and the All-apps screen

- Home is the quilt: "Right now" at the top (Clair arranges up to 3 patches by time of day, with live numbers and a short reason), then every app below as a quilt sized by use, filterable by pile; faded patches = unopened 14+ days. No separate All-apps screen.
- Bottom border on every screen: 4 pinned apps sewn into one named strip + search. Pins stay in fixed places; Clair seeds them from the first week's use, then they only change when Sam long-presses to pin or unpin.
- Above the border: one chalk chip where Clair suggests an app for right now ("Workout · in 15 min").
- Inside an app, swipe up on the border: first fold = "Just used" (recent apps in order); keep going = Home's quilt.
- Research basis: Arc favourites, super-app service grids, Alipay/WeChat recently used, iOS Smart Stack and App Library. Study: https://claude.ai/artifact/WtBMJUDese1MWWMTjFu8Dd

## Home content, voice and theme (Nov 19, 2026) · from docs/research/home-jtbd.md

- Home is composed from signals every app spec emits (pending items, dated rows, a "face" = headline value + label, changes, cross-app patterns), never from per-app widgets. Every app spec must declare a face.
- Order = the job: greeting + status line → Waiting for you (basted items, Clair proposals; hidden when empty, replaced by a caught-up win) → Next up (a running-stitch thread of the next dated items from every app, each dot in its app's dye) → Right now (up to 3 faces Clair picks by time of day, with a reason) → Clair noticed (at most one cross-app pattern, "Not useful" to dismiss) → Your quilt (all apps by use, pile filter; "just changed" tag on the big patch, mustard notch on small ones) → pinned border (no chalk chip on Home).
- Day one replaces everything: spool hello, sentence field, 4 starter apps, "snap anything"; border says pins arrive after the first week.
- Voice: status line = 1–2 clauses from live data, most useful fact first, specific numbers, relative times, no exclamation, no judgement, no "it looks like"; money over = amount + category; wins stated once, never streaks; no badges or counts except "just changed".
- Theme: chrome stays muslin + ink; colour comes from the apps (the quilt is the most colourful thing on Home); Clair = denim chalk; just changed = mustard; no red.
- Prototype: https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV

## After PM review (Nov 19, 2026) · supersedes "Right now" and the stitch button words above

- Cut "Right now" (repeated the status line and Next up); Clair's time-of-day judgement decides the status line instead.
- Status line always carries money left + the next thing ("$412 left this month. Pull day at 6 pm.").
- "Needs your OK": one basted card style for receipts, suggestions and insights; one at a time + "N more". Nothing is counted or tagged "just changed" until Sam adds it (card previews "$412 → $376").
- Buttons are plain verbs: "Add to 3 apps", "Review items", "Remind me to cancel", "Add to Meals". Stitching stays in visuals and motion.
- Pinned bar = 4 pins + Snap/Ask (tap camera, hold for Clair and search). Pull-down search stays.

## Decision Nov 19 (supersedes Snap/Ask): the Clair button
- The bar's right cell is the Clair button: a faceless spool mark (not the character, does not count as a spool) labelled "Clair". Tap opens the Clair sheet (type, Talk, Photo, File; three time-of-day suggestions: one capture, one ask, one build). Hold 450ms = talk while held, release to send, slide up to cancel. Search = pull-down only.
- Return loops Quilt designs for: quick dump (say or type anything, Clair files it to the right apps after OK), ask across apps (answers cite their source apps), share into Quilt (screenshots, emails, PDFs from the OS share sheet), and Clair asks first (an evening check-in card in Needs your OK). The receipt is one example of the dump, not the product.
- Talk waveform is a running-stitch line whose stitch lengths follow voice level.
- Full spec: design/notes/fixspec.md section D.
- "Your apps" replaces "Your quilt": find box, no pile chips, a number on every patch, "not opened in N wk" on forgotten ones. Header clock removed.
- Canvas demo path rebuilt in Workbench (Home, Groceries, Review receipt, Budget, Calendar); final design book: https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq

- Platform (Nov 19, evening): one React app, wrapped with Capacitor for Android (APK) and served as a website for laptops; motion and CSS port from the prototypes unchanged. Clair reads any photo or file, asks with menu questions and keeps Clair notes; voice uses the phone's own speech in and out. See spec/backend.md and spec/clair-agent.md.
- Bar behaviour (Nov 19): the bar never swipes sideways and never moves on scroll. More apps = swipe up on the bar ("Just used", then Home's quilt). The bar hides only for focused tasks: keyboard up, camera, logging a set, reviewing a receipt, building an app; those screens carry their own Done/Back. The Clair sheet floats above the bar and keeps it visible so threads land on the pins.
