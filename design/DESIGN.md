# Quilt design system (what the client applies)

Fri 20 Nov 2026. One page that says what every screen in `web/` must look and move like. Read it before building or changing a screen. It gathers what was spread across the design canvas, the prototypes, `design/notes/` and the ADRs, and says which source wins where they disagree.

## 0. Sources, in order of precedence

1. **The owner's latest words** in the conversation or a decision record.
2. **Colours: ADR-013, Mint** (`spec/adr/013-mint-one-family-palette.md`, Nov 20). Tokens live in `web/src/styles/tokens.css`. It replaces every colour value below that comes from the canvas.
3. **Layout and components: the Screens page of the design canvas** (https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P, page "Screens", 40 boards, regenerated in the Mint colours on Nov 20). Each screen has a board; section 9 maps screens to boards. Boards are 390 × 844. **Every component's exact CSS, with the board it comes from and its token, is in `design/screens-css.md`**; the full machine inventory is `design/board-css-inventory.md` (rerun `design/tools/board_css.py` when the canvas changes).
4. **Motion: `design/notes/fixspec.md` §A** and **`design/notes/motion-catalogue.md`** (live: https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC), with the confirm change in section 6.
5. **Clair's face: the Spool board** (canvas "Clair, motion and loading") and `spool()` in `design/prototypes/quilt-home.html`.
6. **Rules that outlived the old look: the design-system board** (canvas "Quilter's Workbench design system v0.4"). Its colours and fonts (muslin, denim, mustard, Bricolage, Hanken, DM Mono) are superseded. Its radius and spacing scales, type roles, button and link rules, stitch states, motion table and copy rules still apply, as restated here.
7. `.impeccable/surfaces/app.md` for the product voice and the settled interaction decisions.

The canvas has no boards for Calories, Running, Meditation, Cycle, Classes, Notes or Subscriptions. Section 10 designs them in the same language.

## 1. The idea

Soft Quilt: every app is a soft patch with a stitched edge. Chalk is Clair's idea, a basted (dashed) edge waits for your yes, a running stitch is saved. Calm, hand-made, plain words, no red. Each app opens on the thing you do in it, not on a list of rows.

## 2. Colour (ADR-013, Mint)

One cloth family from pear through teal to blue. The ground is a plain pale mint with no gradient. Ink, cards and buttons take the ground's hue. Dark mode is a deep green-black from the same tokens through `light-dark()`. No red anywhere: "over" is an ink cross-hatch, errors are a frayed edge.

| Token | Use |
| --- | --- |
| `--ground` | Page background |
| `--ink` | Text, filled primary buttons, the "just changed" pill |
| `--sec` | Meta text only (13 px lines, section labels). Sentences people read are in `--ink` |
| `--card`, `--card-line`, `--shadow` | Cards (`.st`), sheets |
| `--line` | Stitch lines: dashed row separators, secondary-button, chip and field edges, the grabber, the tab baseline |
| `--hair` | Faint fills: bar tracks, pressed rows, stepper buttons |
| `--focus` | The accent: links, the selected chip, the tab underline, focus rings, chalk |
| `--said` | Your own words in Clair (the chat bubble), text selection |
| `--cta`, `--cta-ink` | Primary button fill and text |
| `[data-dye] --fill / --deep` | An app's patch colour and its deep tone (icon, stitch, progress fill, done check) |

The canvas boards now render these exact colours (ground `#EAF8F2`, ink `#0F241E`, meta `#475E56`, line `#A5B5AF`, accent `#00665D`, links `#005652`). `design/screens-css.md` §1 maps every board value to its token; in code always use the token.

**App dyes** keep their names because the API stores them. Since Nov 20 (ADR-013, amendment) each dye is a distinct hue at nearly equal lightness and chroma, so patches read as different cloths without clashing: `butter` 95, `pear` 125, `sage` 150, `sea glass` 188, `chambray` 245, `lavender` 292, `blush` 340 (mauve, never red), `apricot` 60, `linen` 85 (warm neutral). Icon and name still go with the colour. The demo account's dyes: Budget `sea glass`, Groceries `sage`, Calories `apricot`, Calendar `chambray`, To-dos `butter`, Meditation `lavender`, Workout `blush`, Running `sage`, Notes `linen`, Classes `chambray`, Subscriptions `lavender`, Cycle `pear`; neighbours on Home never share one. Unknown dye names are mapped to one of the nine (`web/src/lib/dye.ts`). The hex values in `screens-css.md` §1 are the Nov 20 morning one-family Mint dyes and are superseded for the dyes only.

## 3. Type (Figtree only)

Figtree for everything, `font-variant-numeric: tabular-nums` on every figure that can change. Sentence case everywhere, no tracked capitals. The text floor is 13 px.

| Role | Size / weight / tracking | Example |
| --- | --- | --- |
| Display (hero figure) | 44 / 700 / −.035em, line-height 1 (laptop 46) | "$376" in Budget |
| Greeting on Home | 36 / 700 / −.025em | "Evening, Sam." |
| App title (h1) | 28 / 700 / −.025em, line-height 1.05 | "Groceries" |
| Card title, large | 30 / 700 / −.025em | "Pull day" (Workout's Next up) |
| Card title | 22 / 700 / −.015em | "Lat pulldown" |
| Focused-screen title (centred in the top row) | 17 / 700 / −.005em | "Pull day · 18:42", "Settings" |
| Status sentence | 16 / 400, figures in `<b>` | "**14** to buy across 3 lists." |
| Row title | 16 / 500 | "Return library books" |
| Body | 15–16 / 400 | Clair's answers |
| Clair's own line | 15 / 500 | "Built 4 pieces." |
| Section label | 13 / 600, `--sec`; optional right-hand meta 13 / 500 | "Today · Fri 20 Nov" … "Default list" |
| Meta | 13 / 400, `--sec` | "Marriott Library", "From Workout" |
| Link | 15 / 600, `--focus`, 44 tall; › only when it goes somewhere | "See the week in Calendar ›" |
| Tag | 13 / 600, padding 2 8 | "just changed", "Overdue · 2 days" |
| Pinned-bar label | 13 / 600, no ellipsis | "Groceries" |

## 4. Space and shape

- **Spacing** on a 4 px scale: 4, 8, 12, 16, 24, 32. Gap between blocks 16. Side gutter 16.
- **Radius**: 4 tags and bars · 8 day cells, swatches · 12 icon tiles, stepper buttons · 16 chips, inputs, the add field · 22 cards and sheets · 99 buttons and pills.
- **Targets** at least 44 × 44.
- **Phone column**: padding-top 44 (+ safe area), sides 16, gap 16. Bottom clearance 96 for the bar; 150–160 when an add field or action row is pinned above it.
- **Laptop (≥ 900 px)**: three columns, 240 apps | the app | 320 row detail (board "Laptop"). The bar becomes the left column: "Tell Clair anything", Search ⌘K, the app list with "just changed", New app, "Sam · 32 credits".

## 5. Components (with the board that shows each)

**App header** (Workout, Groceries, To-dos, Budget). Top row: a plain back chevron (44 × 44, margin-left −12, no circle) and, on the right, `···` (the app menu) or a text action ("Finish"). Then the identity row: a 36 px icon tile (radius 12, the app's `--fill`, icon in `--ink` at 18) and the h1. Then the **status sentence**: one line written by the server with the figures in bold, plus "just changed" when the app changed.

**Tabs** (Workout). Text tabs on a dashed `--line` baseline; the selected tab is `--ink` 600 with a 2.5 px `--focus` underline; others `--sec`. 44 tall, scroll sideways. An app with one page shows no tab bar: Budget, Groceries, Calendar and To-dos have none on their boards.

**Card** (`.st`): `--card`, radius 22, the card line and shadow. Padding 16 for content, `12px 16px` compact, `4px 16px` for a card of rows, `4px 0` when rows are full-width buttons with their own 16 inset.

**Rows**: min-height 56 (agenda 58), gap 12, title 16 / 500 over meta 13 `--sec`; rows after the first carry a dashed separator on top (`linear-gradient(90deg, var(--line) 58%, transparent 0)`, 8 px × 1 px). A row's source app is a 10 px dot in the app's fill with a 1.5 px inner ring, then "From Workout". Amounts sit right, 14 tabular.

**Check circle** (To-dos, Groceries): 24 px, 1.5 px `--sec` ring; done is filled with the app's `--deep` and a white tick, and the title strikes through in `--sec`. Ticked rows move to the done section.

**Section label**: 13 / 600 `--sec`, sentence case, right-hand meta optional ("Weekly shop · 4 to buy" … "Default list").

**Chips** (Groceries lists, Clair suggestions): 44 tall, radius 16, `--card` ground, 1.5 px `--line` edge, 13 / 600; selected = `--focus` 12% ground, 1.5 px `--focus` edge, `--focus` text. A count follows the name in 600. A "New list" chip carries a + in `--focus`.

**Buttons**: 48 tall, pill, 16 / 600, padding 0 20. Primary is filled `--cta`; secondary is transparent with a 1.5 px `--line` edge. One filled primary per view. Pairs at the bottom of a focused screen: Skip | Log set 2 (1 : 2).

**Stepper** (Log a set): a 1.5 px `--line` frame, radius 16, padding 2; − and + are 44 × 44 radius-12 buttons on `--hair`; the value 18 / 700 centred. Label above in 13 `--sec` ("reps", "weight, lb").

**Bars** (Budget "Where it went", Workout sessions): 7–8 px, radius 4, track `--hair`, fill the app's `--deep`. Over a limit: fill to the limit, then an ink cross-hatch for the excess, and a meta line "$15 over".

**Hero figure card** (Budget): display figure, "left of $1,200" in 14 `--sec`, the bar, a meta line ("Was $412 · 11 days to go"), an optional link.

**Day strip** (Calendar): seven cells in a grid, radius 12, padding 8 0, day initial 13, date 15 / 700, dots for how many things fall that day; today is filled `--ink` with `--cta-ink` text; others `--card` with a 1 px `--line` edge.

**Agenda** (Calendar): a section label per day ("Today · Fri 20 Nov"), a card of rows: title (+ "just changed"), "From <app>" with its dot, the time right in 13 / 600 `--sec`.

**Add field, pinned** (To-dos): 48 tall, radius 16, `--card`, 1.5 px `--line` edge, placeholder that shows how to type ("Add a to-do, like "email TA Friday""), a 40 px round `--cta` + on the right. It sits 12 above the bar.

**Edit sheet** (Edit an item): the bottom sheet over the app, "Edit item" 22 / 700, fields with 13 labels and white inputs (radius 16, 1.5 px `--line`), a provenance line with dots ("From your Corner Market receipt · also in Budget"), then Delete (secondary, trash icon) | Save (primary). "From Google" rows open no edit sheet.

**Tags**: "just changed" is a 13 / 600 pill in `--ink` with `--cta-ink` text; status tags ("Overdue · 2 days") are `--ink` with radius 4; a timer tag ("Rest 0:47") uses the app's `--fill`, radius 4.

**Chalk** (Clair's idea, not a change): `--focus` 7% fill, 2 px dotted `--focus` edge, radius 22; the line in 15 / 500 `--focus`; the small chalk-triangle mark on the left.

**Pinned bar** (every board): four pins and Clair, near-opaque (94% card, no blur: fixspec §A allows none). A pin is a 46 × 30 tile (radius 13) in the app's fill with its deep icon, label 13 / 600 under it; the current app's tile gets a 2 px `--ink` inner ring and a 700 label. Clair's cell is an `--ink` tile with the faceless spool mark. Pressing a cell darkens it (no scale). The bar hides on focused tasks: keyboard up, Log a set, a running timer, building an app.

**Toast** (What Clair remembers) is the receipt capsule of section 6: a pill on the bar's top edge, never a card at the top; the message 15 px, **Undo** a link on the right.

**Sheet**: on `--ground` (not white), radius 22, padding `8px 16px 16px`, gap 16, a 40 × 4 grabber in `--line`, then the header (spool 44 · 22 / 700 title over a 13 px line · close ×).

**Home quilt** (Home board, "Your apps · 7 … Most used first", then a find field): a 6-column grid of 58 px rows, gap 6, filled with no holes, most used first (Budget 4 × 2, Workout 2 × 2, the rest 2 or 3 wide). A patch is the app's fill, radius 22, padding `8px 12px`, an inner dashed stitch (inset 6, radius 11), the icon and name at the top (13 / 600) and the figure at the bottom (28 / 700 on the big patch, 14 / 700 on small ones), "just changed" in the corner. The last cell is a white "+" patch.

**Clair sheet** (Tap Clair): spool 44 "hello" + "Tell Clair anything" 22 / 700 + a 13 `--sec` line, a close ×; the field (radius 22, 1.5 px `--line`) with a round send; Talk | Photo | File as secondary buttons; "Try this evening" with three rows, each with an icon tile and a "Log it · Budget" meta; "Open chat ›".

**New app: header, every step** (boards Build and Preview). The top row is a back chevron (44, margin-left −12) and the step's title centred, 15 / 600 ("New app", "Preview"), with a 32 px spacer on the right that keeps it on the screen's centre. No credits pill on any step: credits live in the footnote on Describe ("A build uses 10 credits…") and in the Preview's meta line. One spool per screen: 44 on Describe, 30 in Clair's line on Reading, Thinking, Questions, Plan and Preview, 96 on the landing. After Describe the sentence stays as a quiet chalk line under the top row (15 / 500 `--focus`, padding `8px 16px`, at most 2 lines) and Clair's line follows it (15 / 500 `--focus`). On a laptop the whole screen is one centred column, 560 wide, so no field stretches.

**New app: Describe** (board Build). Spool 44 hello beside the question "What do you want to keep track of?" (24 / 700 / −.015em, 2 lines), the label "Say it the way you'd tell a friend" (13 `--sec`), the box (3 rows, radius 16, 1.5 px `--edge`, `--card`, 16 px, the example as the placeholder), one row of suggestion chips that scrolls sideways with the edge fade (`.chips.scroll`; they are the three recorded sentences, tap fills the box), **Build it** (primary, full width, disabled while the box is empty), then the section label "Or start from one of these" with "Skips to preview" on the right and a 2-column grid of pattern tiles (min-height 92, radius 22, the app's `--fill`, icon 18, name 15 / 700, "N blocks" 13 `--sec`; Calories, Running, Cycle, the third spans both columns; in Cloth a seam in the tile's own thread). A tile runs its recorded sentence, answers the questions with "Skip, use your best guess" and shows the short Reading state, then the Preview: no question card, no plan card. Back from that Preview lands on the questions with nothing picked. A tile or chip for an app that is already built is not shown. Footnote 13 `--sec`: "Clair asks a few questions and shows you the plan first. A build uses 10 credits; nothing is added until you tap Make it."

**New app: Preview** (board Preview; one layout, the 3-layout pager and Arrange are Beta). After the sentence and Clair's line ("Make a Calories app? Meals with calories and protein, and foods you save.", the card's own title and summary, 15 / 500 `--focus`): the app's header (36 px dye tile, icon 18, name 28 / 700, Private tag), the note "Example rows · cleared when you make it" (13 `--sec`), then the app drawn by the real `AppView` inside ONE frame: the app's own tab strip and one tab's blocks, switched in place (nothing navigates), rows tagged "example". The frame is chalk while Clair cuts the pieces, then one thin gold basting (1.75 px, 12 / 8) while it waits for Make it, then a solid seam. Other apps Make it changes (Running adds a race to Calendar) are listed under the frame as "Also changes". Pinned at the bottom like Log a set's actions (fixed, above the safe area, a fade of the page colour under it): the meta line "Uses 10 credits. Nothing is added until you tap Make it." (13 `--sec`, centred), then **Change answers** (secondary, back one step, answers kept) | **Make it** (primary). With no questions or plan behind it the secondary reads "Not now". The sew finale after Make it is unchanged (the basting tightens to a seam, stitch around the dye tile, dye sweep, "pieced by clair" stamp, spool hop, the patch slides onto Home).

**Question card** (New app, after Build it; Clair asks before building, `spec/clair-agent.md` §7 rule 7). Clair's line first (spool 30, "A few questions first, then I'll show you the plan."), then one white card (`.card`, padding 16, gap 16) with 1 to 3 questions split by a dashed `--line` rule. Each question: the header as a section label (13 / 600 `--sec`, "Pick any" on the right when it's multi-select), the question 17 / 700, then option rows like the fridge question (board ClairFridge): full width, min-height 56, radius 16, padding `8px 12px`, gap 12, `--card` with a 1.5 px `--line` edge; label 16 / 600 over a 13 `--sec` description. Single select is a 22 px circle with a 10 px `--focus` dot (`role="radio"`, arrow keys move); multi is a radius-7 square filled `--focus` with a tick (`role="checkbox"`). Selected = `--focus` 12% ground, 1.5 px `--focus` edge, label in `--focus`. Every question ends with an **Other** row; picking it, or an option that takes a value ("Set a number"), opens a field under it, indented to the label (46), with a 13 / 600 label ("Calories a day"). Then **Continue** (primary, full width, disabled until each question is answered; a 13 `--sec` line under it says how many are left) and the link "Skip, use your best guess". No option ever suggests a number.

**Plan card** ("Here's the plan"): chalk, because it is Clair's idea and nothing is made yet. The chalk-triangle mark + "Here's the plan" (13 / 600), the new app's 36 px tile and name (22 / 700) with a Private tag when private, one line per change (16 / 1.4) behind a 10 px dye dot of the app it touches, then **Build it** (primary) | **Change answers** (secondary, no wrap; back to the questions with the answers kept). Build it shows the Build preview; nothing is saved before Make it. Steps on New app crossfade (out 140, in 220, opacity only); each step is a history entry, so Back (and the phone's back) walks describe ← questions ← plan ← preview. Expired (the questions waited over 24 h): a white card "Still want to build this?" with **Build it** (re-sends the sentence) | Not now.

**Empty app** (New app 5 · ready, board Empty): "new" tag beside the h1, "Connected to ● Calendar ● Budget" (only when the spec has stitches), a card with spool 96 hello, "<App> is ready" and one sentence, then secondary buttons: "Tell Clair or add a photo", "Type one in", "Bring 4 in from Budget". **While the new app has no rows in any collection this is the whole screen**: the tabs and the empty blocks stay hidden (one spool on the screen) until the first row exists. A new app that already has a row (Running's race) opens as the normal app with the "new" tag and the connected line, no ready card. DevDay builds "Tell Clair" and "Type one in" only; the photo and "Bring N in" buttons are not built.

## 6. Motion

Tokens: feedback 120, state 220, layout 350, focal 600; exits 140, 220, 360. Ease `cubic-bezier(.16,1,.3,1)` for everything, no bounce; the thread curve `(.45,0,.15,1)` only for a stitch being drawn. Gesture releases use the critically damped `spring()` and keep the finger's speed (`design/notes/fixspec.md` §A, ported in `web/src/lib/motion.ts`).

| Moment | Motion |
| --- | --- |
| Press | Buttons and chips scale .97; patches .98; bar cells and full-width rows darken instead |
| Hold | 450 ms; the fill starts after 120 ms; a 10 ms buzz when it fires |
| Sheet | Grows from where it was opened (the Clair cell: origin bottom right), translateY 16 + scale .96 → 1 over 350; leaves in 220; drag down to close (spring .35, closes past .35 of its height with momentum) |
| Toast | The receipt capsule (below): docked on the bar, rises out of it in 220 as the raised tiles fold into it, sinks back in 220 |
| Confirm a card | The basted edge closes (220). Then each target app you can see gets a running stitch sewn around its tile in its own colour (600, 120 apart, lands at 70%: the number rolls, "just now" scales in). Apps you can't see, or whose number changes but only a pin shows, creep up above the bar as small tiles, get the same stitch and roll, then sink. Owner's idea, Nov 20; the earlier thread pull stays behind `?motion=threads` until the owner confirms |
| Undo | The edge re-bastes (140), the stitches pull out (360), tags fade, numbers roll back |
| Number roll | Old and new share a grid cell; increases roll up, decreases roll down, 220 |
| Tags | Scale .95 → 1 from the left, 220; fade out 140 |
| Lists | A ticked row's circle fills (120), the title strikes, then the row folds away (220). Swipe right to complete, left to delete: the row follows the finger, arms at 90 px with a short buzz, commits past 90 or with a fling (spring .25), springs back otherwise (.3) |
| Queue on Home | The handled card leaves up 8 px (140), everything below FLIPs (350), the next card enters (220) |
| Build | The sentence lifts into the chalk card (350), the preview's chalk frame wipes in left to right (350) while Clair checks a piece per tab (240 + 380 apart, in her line), the frame bastes, then the sew finale: the basting tightens to a seam (220), stitch around the dye tile, dye sweep (350), "pieced by clair" stamps (220), spool hops, the patch slides onto Home (350) with "new". Steps crossfade (out 140, in 220); with reduced motion every step is a 120 ms fade |
| Reduced motion | No movement anywhere: 120 ms opacity fades (every duration token becomes 120), springs jump, no stitches drawn, no rolls, spool face only. One exception: the 3% press scale on buttons stays, it is the finger's own feedback, not movement on screen |

**The receipt** (owner's words, Nov 20: "the animation before that is so satisfying and the toast just throws it off"). What just happened and its Undo are said once, in one capsule docked on the bar's top edge, so the confirm reads as one gesture: stitch, tiles, receipt.

- **Where.** A 48 px pill (`--card`, the bar's shadow) 10 px above the bar, centred on it; on a laptop (no bar) 24 px from the bottom, centred on the main column. Over a pinned add field (To-dos, Groceries) it sits 12 px above the field. Never at the top of the screen, never over a sheet's header.
- **One slot.** Every toast uses it ("Added to Budget", "Done: …", "Deleted. Undo", "Run logged…", errors). A new one replaces the old with the 120 ms text fade. Up to three dye dots say which apps it concerns (the card's apps; else the open app's). While a sheet is open a toast waits (an error shows at once) and shows 220 ms after the last sheet has closed, unless it is more than 30 s old. While the Clair sheet shows the stitched card there is no capsule: the card's own "Added to … Undo" row is the Undo.
- **Motion.** The raised tiles sink (24 px, opacity, 140) and the capsule rises out of the bar (14 px and scale .97 to none, opacity, 220, ease), overlapping the end of the sink by 80 ms. With nothing raised it rises on its own. It leaves back into the bar (14 px, opacity, 220).
- **The thread.** An Undo capsule has a gold running stitch around it that unthreads over its life (8 s, or the toast's own length; linear, because it is a timeline and not a transition): `--gold-line` in Cloth, `--focus` in the flat look. A press, the pointer or focus on the capsule holds the thread and the clock (WCAG 2.2.1); leaving resumes. Plain notes have no thread; an error has a frayed edge (2 / 5, ink), still.
- **Undo.** The stitch snaps whole (120), the action runs, the capsule dissolves in place (140), and the usual reverse runs above the bar (tiles rise, numbers roll back, threads pull out). There is no "Undone" toast: the numbers say it.
- **Home, "just changed".** When a patch becomes changed its seam is drawn once, as its number starts to roll: a gold dashed seam revealed left to right over 600 on the thread curve, then it is simply the patch's seam. A patch that was already changed when Home painted, or a return to Home, has the seam without the draw. The flat look draws a quiet ink seam that fades.
- **Bars creep.** A fill is the full track clipped to its value; a new value glides there in 350 with the number that rolls. A first paint never animates.
- **Reduced motion.** No travel, scale, clip draws or creep: the capsule fades in and out in 120, its stitch is static, the seam is just there.

**Clair's spool** (Spool board): one per screen at 30 (beside a status line), 44 (on cards, the sheet) or 96 (empty states). Hello and Stitched hop once (5 px, 420 ms) when the face changes; Working bobs 2 px every 560 ms and is the only face that blinks; Thinking pulses three thought stitches; Waiting is still (brows up, needle raised); Oops shakes once (±3 px, 3°) with a frayed tail; Sleepy breathes. Never on app switches, money warnings or dense lists. The Clair button's mark is faceless and never animates. Clair's status line is the only loading UI.

## 7. States: the stitch alphabet

| State | Looks like |
| --- | --- |
| Clair's idea | Chalk outline; nothing changed yet |
| Waiting for OK | Long basting stitch (dashed edge); not saved |
| Saved | The basting tightens to a solid seam |
| Just changed | "just changed" pill (in apps) / "just now" pill in the app's colour (on Home patches), held until the app is opened |
| Over / conflict | Ink cross-hatch on the excess |
| Error | Frayed edge, the reason and the fix in words |
| Undone | Stitches pull back; Undo re-stitches |

## 8. Words

- Clair builds **apps**; sections inside an app are **tabs**. "Patch" is how an app looks, never a button.
- Buttons say what happens: "Add to 3 apps", "Start pull day", "Log set 2", "Make it".
- Times "6 pm", "5:41 pm"; dates "Sun 22 Nov". Figures with units: "12,450 lb", "7 mi".
- No red; no streaks (a win is stated once); no judgement of a number (Calories shows "of 2,200", never "under"). No health, diet, training or medical advice from Clair.
- Status sentences: one or two clauses from live data, the most useful fact first, figures in bold.
- UI copy never uses a pronoun for Clair; Clair's own lines may say "I".

## 9. Screens and their boards

| Screen | Board | Notes |
| --- | --- | --- |
| Home | Main ("Home: the evening check-in waits in the queue") | Logo and avatar, "Evening, Sam.", status sentence, Needs your OK · N with "Show 3 more", Next up thread (time column, dashed line), "See the week in Calendar ›", Your apps quilt |
| Your apps | Tabs | Just used row, find field, All apps quilt "Most used first", New app |
| Search | Search | Pull down anywhere; scoped chips |
| You / Settings | You | What Clair changed (Undo each), credits meter, what Clair can read, notes, your data |
| Clair sheet | ClairSheet, ClairTalk, ClairResult, ClairAsk, ClairPhoto, ClairShare | Section 5 |
| Clair chat | Clair | Header with spool 44, "Answers from your apps only", credits link |
| Groceries | Groceries | Status sentence; list chips with counts, New list, Usuals; "Weekly shop · 4 to buy … Default list"; checklist; "Bought at Corner Market · 8" with "usual" marks; Add a photo |
| Budget | Budget | Hero "$376 left of $1,200" + bar + "Was $412 · 11 days to go"; "Where it went" bars; Subscriptions; Recent |
| Calendar | Calendar | "This week", the day strip, the agenda by day; Day and Month views are added (section 10) |
| Edit an item | EditItem | Section 5 |
| Workout | Workout | Five tabs; Today: Next up card with "Start pull day", two figure tiles, "Sessions this week 3 of 4" bar |
| Log a set | Session | Focused screen; section 10 |
| To-dos | Todos | "3 left today."; Today · Fri 20 Nov; Overdue tag; This week; pinned add field |
| New app 1 to 5 | Build, Preview, Arrange, Connect, Empty | Describe → (questions → plan, no board) → Preview → ready. DevDay builds Describe with its pattern tiles, one Preview layout with Make it pinned, and the ready landing; the layout pager, Arrange and the Connect step are Beta |
| Rule | Rule | When / Only if / Then cards and the switch |
| Laptop | Laptop | Section 4 |

**Where a board disagrees with a later rule**, the rule wins: Workout's chalk line "Try 125 today" is training advice, so the app shows only what Sam logged ("Last week: 10 × 120 on lat pulldown"); and "Clair noticed" insights stay off until FR-H6 says how they are computed.

## 10. Apps without a board: their instruments

Each app opens on the thing you do in it. These are block kinds any app can use, so an app Clair builds gets them too (contract: `spec/ui-tech-plan.md` §3).

| App | Opens on | Tabs |
| --- | --- | --- |
| Meditation | **Timer**: kind chips (Breathing, Body scan, Sleep, Walking), length presets 5 / 10 / 15 / 20, a ring that counts down, Start / Pause / End; "How do you feel?" 1–5 before and after; the screen stays awake; a soft chime at the end; it logs the session. Below: **this week** as seven day cells | Sit, Sessions |
| Running | **Countdown** to the race ("Winter 10K · 22 days to go · Sat 12 Dec"), this week's day cells with miles, **Start a run** (a stopwatch that asks for the distance and kind at the end and logs the run), this week's runs | This week, Log, Races |
| Calories | A **ring** ("1,140 of 2,200 today"), **Again** chips for saved foods (one tap logs it), today's meals | Today, Log, Foods |
| Cycle | A **month** of days: logged days marked by flow, start days marked; tap a day to log flow, energy 1–5 and symptoms. No predictions in the app. "Private" and Clair's read switch in the menu | Month, Cycles |
| Workout (Log a set) | **Guided log**: "Pull day · 18:42" running clock with Finish; "Exercise 2 of 5" and a bar; the exercise card with its plan and best, done sets with ticks, reps and weight steppers filled from the plan, "Rest 1:30" after each set; "New best" with the proud spool when a set beats the best; Up next; Skip | Log set N | (focused screen, no bar) |
| Calendar | **Day** (an hour timeline with a now-line and Google events as outlines), **Week** (the board), **Month** (a grid with dots in the apps' colours; tap a day for its list), switched by a segmented control | none |
| Classes | This week's classes and due dates as an agenda; **Due** as a checklist with "in 3 days" tags | This week, Due, Exams |
| Subscriptions | A hero "$38.46 a month · 4 subscriptions" and renewals with "in 2 days" tags | none |
| Notes | Notebooks and notes | Notebooks, All notes |

## 11. Look: Cloth (proposal, Nov 20; opt-in, not the default)

One stylesheet, `web/src/styles/theme-cloth.css`, scoped under `[data-look='cloth']`. `?look=cloth` turns it on (remembered), `?look=default` goes back, `?scheme=dark|light` forces a scheme; the demo menu on mock data has a Look and Colours switch. The default theme is untouched until the owner chooses. The side-by-side render and the measured contrast are in the artifact "Quilt Cloth Theme"; the running app with the switch is "Quilt Look Preview".

- **App bodies are cloth.** `.screen[data-dye]` takes `--cloth` (the ground's lightness, the dye's hue and a little of its chroma); cards inside take the same hue, so a card is always a lighter cloth than its page, in light and in dark. The app's hero card (gauge, ring, countdown, next, timer) carries a seam in the app's deep tone.
- **Patches are padded cloth.** A lit top edge (`--hi`), soft inner shade, an offset tinted shadow (`--shade`), and the running stitch in the patch's own deep tone. Light dyes are .035 deeper than the default pastel; dark dyes gain lightness and chroma.
- **Woven ground.** A 4 px thread grid at 2.2% on the ground and on sheets.
- **Gold thread = state, never decoration.** `--gold` is the "just changed" tag and the notch, `--gold-line` the changed patch's seam and the basting around a card waiting for OK (3:1 on a card in light, 8:1 in dark).
- **Stitch grammar, one meaning each.** Tack stitch (2/4, 1 px, 46%) between list rows; running stitch (1.5 px, 66%) for a patch seam; basting (12/8, gold) = waiting for OK; chalk (dotted, teal) = Clair's idea; frayed (2/5, ink) = a failed save. Never red.
- **Night cloth.** Ground `oklch(.205 .036 215)`, card .262, raised .305; text 13:1 or better; patch text 7.2:1 or better.
- Browser surfaces are themed too: selection (gold at 60%), caret, `accent-color`, thin scrollbars.

## 12. Moments and voice (Nov 20, evening)

Found by an animation-opportunities sweep with the frequency rule: ticking, tab and view switches, sidebar and pane picks, steppers and typing stay instant; only occasional and rare moments move. Every duration is on the tokens (120 / 220 / 350 / 600, exits 140 / 220 / 360); reduced motion keeps the 120 ms fade and drops movement.

| Moment | Motion | Where |
| --- | --- | --- |
| A new row arrives in a list already on screen | Height 0 → natural plus opacity, 220 ms (the one small layout animation). Not on first paint, tab or list switches, or rows that were already there. A first row in an empty list rises 8 px as the empty card fades. | `lib/enter.ts`, `Checklist`, `List`, `EmptyState` |
| Timer phases (Meditation, Running) | Controls crossfade 120 out / 220 in; the ring and clock do not move. The chips above the ring fold (140) when a sit starts and open (220) after. | `Timer.tsx` |
| Timer finish (30 s or longer) | The ring closes (about 300 ms) and its stroke eases to gold thread; the stitched spool beside "Done" hops once. | `Timer.tsx` |
| Log a set: New best | Banner in 220 ms (up 6 px, scale .97 → 1), the proud spool hops once, one 10 ms buzz; it fades in 140 if the value drops. A logged set's check draws in 120. | `Session.tsx` |
| Disclosures ("Add how you feel ›", "More details ›") | Grid rows 0fr → 1fr plus opacity, 220 in / 140 out; closed content is inert. | `Disclosure.tsx` |
| Confirm | The receipt (see §6): no toast while the Clair card shows its own Undo; otherwise the peek tiles fold into a capsule docked on the bar, with a gold stitch that unthreads over the 8 s undo window. | `Toast.tsx`, `Peek.tsx`, `ProposalCard.tsx` |
| A patch becomes "just changed" | Its gold seam draws once, 600 ms on the thread curve, as the number rolls. Fills (Budget bar) creep with their numbers, 350 ms. | `Home.tsx`, `theme-cloth.css`, `app.css` |

**Hold to talk** (spec `clair-agent.md` §4, board ClairTalk). Hold the Clair button 450 ms: a light fill sweeps in after 120 ms (330 ms linear), `vibrate(10)` fires, and the sheet opens straight into Talk. Spool, "Listening", a running-stitch waveform whose stitch lengths follow the voice (a still dashed line under reduced motion), the live transcript at 20 px (heard words ink, interim words secondary), and the hint "↑ Release to send · slide up to cancel". Release sends a normal Clair turn (`transcript`, `voice: true`); sliding up 60 px or more switches the hint to "Release to cancel" and release discards. A tap still opens the sheet. The laptop sidebar button holds the same way; a Talk button in the sheet's start state talks without holding. In mock builds and the published artifact (no microphone) a scripted line types in, word by word. Speech out: one spoken line after a voice turn, with a mute toggle.
