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
| Clair chat | Clair | `/chat`, behind "Open chat ›" (section 16): header with the Clair mark, "Ask Clair" over "Answers from your apps first", the credits link; the conversation; suggestions and the field pinned at the bottom; a history of chats beside it (rail) or in a drawer (phone) |
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

## 13. Links (Nov 20)

Records link to records, in any app, one mechanism for every app (Clair-built ones too). Contract: `spec/ui-tech-plan.md` §3 "Links", reserved keys `_links` and `_backlinks`, `GET /search`, `POST` and `DELETE /records/{id}/links`. Code: `components/Links.tsx`, `styles/links.css` (prefix `lc-`; `.lk` is the older text link). The client never counts or derives a link: backlinks, reverse counts and titles come from the server.

- **Chip.** A 28 px pill: `--hair` fill, 13 / 600, the title (ellipsis at 22ch), the target app's 8 px dye dot when it is in another app, then "· Classes" in `--sec` 500. A chip that opens something is a button, so it gets the 1.5 px `--edge` ring; a deleted target ("(deleted)") is struck through in `--sec`, has no ring and is not a button. The visible pill is 28 but its buttons are 44 tall (negative block margin, like `.tick`), so the reach is 44 and the row does not grow. With a remove, a 44 × 44 × follows inside the pill. No red.
- **On a row.** Under the title, outside the row's button (a button can't hold a button): the row's relations as chips (same-app target: filters the list to it; another app's: opens that record there), then the rows that point at it as a count with a chevron ("4 notes ›", opens that list filtered), then "N linked" with a link glyph (opens the record). A block that lists fields shows only those relations; one that lists none shows all. The relation is not repeated in the row's meta line.
- **Filter.** `?filter=<relationField>:<id>` on an app URL: lists of any collection with that relation field show only the rows holding that id, on the first tab that lists such a collection. A dismissible chip sits under the tab strip: "In notebook · MATH 1210 ×" (`--focus` 12% fill, `--focus` edge, 44 tall button around a 32 px pill). Clearing it clears the query. Adding a row while filtered starts with that relation set. A filter is a new list, not rows arriving: no row animation.
- **`?row=<id>`.** Opens that record: the edit sheet on a phone, the pane on a laptop (the row is picked and scrolled into view, past "Show all N" if it hid there). Said once, then the query is cleared.
- **Relation in the form.** The picked rows first as `--focus`-tinted chips with a ×, then the target's other rows as chips (a search field past six, thirty at most without a search); one picks one (a new pick replaces), `many` picks several. A target in another app carries its dye dot.
- **Linked / Linked from** (edit sheet, laptop pane), under the fields after a dashed rule. "Linked": what this record links to, chips with a ×, and **Link to…** (44 px outline button, link glyph). "Linked from": what links here, read-only, eight shown then "Show all N". Empty: one line, "Nothing linked yet. Link a note, a class, anything."
- **Link to…** is a sheet: a search field (autofocus on a fine pointer), results grouped by app with the app's dot, each a 56 px row (title, snippet 13 `--sec`), "Suggested" while empty; a result already linked shows "Linked" and is disabled. One tap is one link, then the sheet closes. Linking and unlinking are writes with the standard Undo toast, carrying both apps' dots.
- **`[[` in a long text** (`multiline`: a 4 row textarea that grows to 360 px). `[[` opens a listbox under the field (this app's rows first, then every app, eight at most); arrows and Enter or Tab choose, Escape closes only the list, a tap chooses on touch (the field keeps focus). The text keeps `[[Title]]`; the server links it on save. In read views (the laptop pane) a `[[Title]]` that resolves in `_links` is a chip that opens it; one that doesn't stays text.
- **Motion.** A chip that arrives after the list was drawn rises 8 px as it fades in (220 ms, `T.state`); a removed chip fades 140 ms before it goes; nothing moves on first paint. Reduced motion: 120 ms fades only. List navigation and filters never animate.
- **Words and access.** Sentence case, "app" not "tab", no pronoun for Clair. Every chip has a name ("Linked to Cafe Rio in Budget. Open", "In notebook MATH 1210. Show all notes in it", "Unlink Cafe Rio"); the suggestions are a real listbox with `aria-activedescendant` on the textarea; pickers are the existing `role=dialog` sheets.
- **Not built.** Linking from the Add sheet (a new record has no id yet: type `[[Title]]` in its text, or link after saving); "Add a notebook" inside the relation picker; Clair reading `_links`.

## 14. Notes workspace (Nov 20)

Notes is a workspace, not two lists: notebooks, each with any number of pages, and a page you write in. Contract: `spec/ui-tech-plan.md` §3 `notebook`. Code: `components/blocks/Notebook.tsx`, `components/Tree.tsx` (reusable outline), `lib/markdown.ts` (marked + DOMPurify, loaded when a preview first opens), `styles/notes.css` (prefixes `nb-`, `tr-`, `np-`, `.md`).

- **Laptop.** The detail pane gives way (the page and its preview are the detail): the screen widens to 1240, a 256 px tree on the left (a dashed stitch on its right edge), the page on the right. Tree: search field, "+ New page" (in the notebook you are in), each notebook a 44 px row (open/close chevron, name, count, ··· options, + add) over its pages (a dashed stitch down the indent); the open page is the selected-row treatment (`--focus` 10% fill, 1.5 px `--focus` edge). Arrow keys walk the rows, Right and Left open and close.
- **A page.** Status ("Saved", "Saving…", or "Not saved. Try again"), a Write | Split | Preview switch (the `.seg`), Delete; then the title (34 / 700, borderless, wraps, a 2 px `--focus` underline while typing), "In MATH 1210, ECON 1010" (a button that opens the notebooks picker), the writing area, "Linked" and "Linked from". The writing area is a `--card` surface (radius 22, `--card-line` edge, `--focus` edge while it has the cursor), 16 / 1.65, as tall as the text. Split puts the preview beside it on the ground, no card; below 600 px of room it stacks. `[[` opens the link list pinned to the bottom of the screen, not under the page-long field.
- **Preview.** 16 / 1.65, measure 72ch; headings 28, 22, 18 / 700; a quote is a `--hair` block (no side bar); code is a `--hair` block and the only monospace; a rule and table rows are dashed stitches; task items are the check circle; `[[Title]]` that resolves is a chip (`--hair` fill, 1.5 px `--edge`), one that does not is muted text with a dashed underline.
- **Phone.** A 48 px notebook switcher (opens a sheet: All pages, each notebook with its count and ···, New notebook) beside a filled + (the one primary), a search field, the page list as ordinary rows (title; date · notebook · first words). A page opens full screen: the app header and the pinned bar step aside, Back names the notebook, Write | Preview below it (the phone opens to Write; the laptop remembers its view).
- **Motion.** Only the chevron turns (120 ms). Switching pages, views and notebooks never animates (high frequency).
- **Saving.** Typing saves after a 0.9 s pause, on blur, when the tab hides and when you leave the page; one write at a time. A failure keeps the text and offers "Try again". Delete asks nothing and offers Undo.
- **Not built.** Pages inside pages, a graph view, tabs, covers and icons, tags, drag to reorder or move a page between notebooks (use "In …"), toggling a task from the preview.


## 15. Attachments (Nov 20)

A photo or a file goes to Clair the same way text does (spec `clair-agent.md` §3, FR-C3, FR-C6, FR-C12, FR-C13). Pieces: `web/src/components/attach/` (`AttachButtons`, `AttachTray`, `useAttachments`, `useDropPaste` with `DropHint`, `UnderstandingLine`), the logic in `web/src/lib/attachments.ts`, the styles in `web/src/styles/attach.css` (prefix `at-`). The ranked list of what Quilt reads, and why, is `scratchpad/fix-a/inputs.md`.

- **Buttons.** Photo (camera glyph) and File (paperclip). Where they go depends on room (`AttachButtons`, `variant`): in the Clair sheet's start state they are two **labelled chips** under the field (board ClairSheet's Photo and File chips: 48 tall, radius 16, `--card`, 1.5 px `--edge`, 15 / 600); in a pinned follow-up field and in the chat on a laptop (viewport 600 px or wider) two 44 px **icon squares** (the Talk button's family) sit in the field row; on a phone's pinned field and chat the row has room for **one** 44 px paperclip ("Attach a photo or file"), because two would squeeze the field to 178 px. The one button's file input accepts pictures too, so a phone's own sheet still offers "Take Photo". Real buttons that open a hidden file input. On a touch device the Photo chip has `capture="environment"` (the camera); on a laptop it is a plain picker. File accepts PDF, pictures, `.csv .txt .ics .md` and `text/*`, several at once, and reaches the photo library on a phone. Names: "Take a photo" or "Add a photo", "Attach a file", "Attach a photo or file".
- **Tray.** A strip above the field that scrolls sideways (`ul`, "Attachments"), 12 px of room above and right for the remove badge. A photo is a 56 px thumbnail (radius 12) of the picture that will be sent, never the 12 MP original. A PDF, CSV, ICS or text file is a typed tile, 56 tall, radius 16, `--card` with a 1 px card line: a 36 px glyph tile, the name at 14 / 600 (ellipsis, 208 px at most) over "PDF · 4 KB" at 13 `--sec`. Remove is a 20 px ink badge on the corner inside a 44 × 44 button ("Remove <file name>"). Working: a ring (2.4 px stroke, ink, 900 ms linear) over a 62% card veil on a photo, or in the glyph tile with "Preparing…" or "Uploading…" under the name; reduced motion keeps the ring still. Failed or refused: a **frayed edge** (2 / 5, ink, no gold, no red), the file name at 13 `--sec`, the reason in ink 13 / 500 (`role="alert"`), then **Retry** (an upload only) and **Remove** as 44 px text buttons in `--focus`. One plain line under the strip (`role="status"`): "Up to 5 per message".
- **Limits** (the device checks, the server checks again): 5 attachments, the sixth is refused with the line and no tile; photos 25 MB before the downscale, scaled so the long side is at most 1568 px (never up), JPEG 0.85, 5 MB after; PDF 10 MB (20 pages on the server); text 1 MB. A type Quilt cannot read gets a tile that says "Can't read this yet. A photo or PDF works." and does not stop the others.
- **Send.** The field's send waits while anything is preparing or uploading, and while an upload has failed and not been retried or removed (the text and the tiles stay; the tile says "Couldn't upload. Try again"). An attachment with no words sends "Read this and tell me what you find." as the text. Pictures upload as soon as they are ready, so they are usually in Storage before the sentence is typed.
- **Drop and paste.** Drop files anywhere on the sheet or the chat column, or paste a screenshot into the field (Ctrl or Cmd + V). While a file is over the host a chalk-dotted veil says "Drop to attach" (`--focus` 9% over the ground, 2 px dotted edge, 16 / 600 `--focus`; a 120 ms fade, nothing else moves). Never the only way in: the buttons do the same.
- **In a turn** (`TurnView`, shared by the sheet and the chat). What was sent sits right-aligned above the words (`SentTiles`: the same tiles as the tray, no Remove); an attachment alone sends the default sentence and shows no bubble. The turn keeps only names and thumbnails, never bytes: the chat archive saves the user line as "Spent $12 · Attached: receipt.jpg". A slow photo turn offers **Use sample** (the receipt fixture); a slow file turn offers **Try again** (the same Storage paths).
- **Understanding line** (FR-C13). Before any card: a 40 px rounded thumbnail (the photo; a glyph tile for a PDF, a CSV or a calendar file) then what Clair thinks it is, 16 / 500 ink: "Corner Market receipt · 8 items · $35.83". The words are the run's `understood` summary. It writes nothing.
- **Motion** (frequency: occasional). A tile arrives in 220 ms (opacity and 8 px of rise, `--t-state`) and leaves in 140 ms (opacity only, `--t-state-out`); the others close the gap at once. Reduced motion: 120 ms fades. Nothing animates on the buttons beyond the 120 ms press tint.
- **Words.** Sentence case, "photo" and "file", no pronoun for Clair, no gold (gold is waiting for OK).
- **Not built.** The OS share target (an installed Android PWA only; FR-C8), a crop or rotate step, PDF page previews, an upload progress percentage.

## 16. Bigger Clair, the Chat screen and saved chats (Nov 20)

The owner: "the chat screen for Clair is super small", then "chats should be saved, like ChatGPT or Claude". Code: `lib/turns.ts` (one turn engine for the sheet and the chat), `lib/chats.ts` (the archive), `components/ClairSheet.tsx`, `components/clair/` (`TurnView`, `Composer`, `ChatList`, `Drawer`, `Glyph`), `screens/Chat.tsx`, `styles/chat.css` (prefix `chat-`, `hx-` for the history list, `dr` for the drawer), a block at the end of `styles/clair.css`.

- **One engine.** The conversation lives outside React. A turn started in the sheet carries on in the chat (stream, cards, Undo) and the other way round. The sheet shows the last turn of the current chat (grown: every turn since it opened); the chat shows all of it. One turn runs at a time (a second is `409` on the server): the field and the chips wait; a slow turn ("Use sample") re-runs in place.
- **Big mode.** A 44 px header button (expand / collapse glyph, "Make Clair bigger / smaller"), shown once there is a turn (and while big). Phone: the sheet grows to 8 px below the safe-area inset, the bar still lit under it. Laptop (1024 px and up): a panel up to 760 px wide, 92 dvh tall, centred in the main column (past the sidebar, short of the pane). The sheet is anchored at its bottom edge and its height, width and left edge run 350 ms on the ease from the rect it had (the content reflows inside; reduced motion is a 120 ms fade). Remembered on the device (`localStorage` `quilt-clair-big`). Toggling never touches a turn. The marker is `.cs-big` inside the sheet; `.sheet:has(.cs-big)` carries the geometry, so `Sheet.tsx` is unchanged. A plan card of five apps fits without scrolling on a 1280 × 800 laptop.
- **Chat screen** (`/chat`; no bar, no detail pane). Header: back (phone), the faceless Clair mark, "Ask Clair" 17 / 700 beside the credits pill (a link to You), "Answers from your apps first" 13; on a phone, New chat (+) and History (list) buttons. The log is `role="log"`, `aria-live="polite"`: your words are right-aligned `.said` bubbles, Clair's lines carry the 30 px spool (the last turn only), answers are chalk cards with their "From" app chips (the contract gives apps, not a row count), cards are the same `ProposalCard`, still confirmable, with the same Undo (no receipt capsule: the card's own row is the Undo). Foot: the three suggestions as chips (hidden under 560 px of height, a keyboard is up), then the field row pinned at the bottom: field (grows to 5 lines, Enter sends, Shift+Enter a new line), the attachment slot, Talk. A chat opened read-only has "Continue" (only when it is still the server's latest thread, under 24 h) and "New chat" in place of the field. Switching chats is a 120 ms fade; the log follows new words only while it is at the bottom.
- **History.** Laptop: a 280 px rail inside the chat page, a running-stitch seam on its right. Top to bottom: **New chat** (48 px, the spool mark), a search over titles (44 px), the chats grouped **Today / Yesterday / Previous 7 days / Older**. A row: up to two dye dots (the apps it touched), the title (the first line you said, one line, ellipsis; no model call), "sample" for a seeded chat in a mock build. The chat you are in is 600 weight on `--hair` with a vertical tack stitch (no red, no gold). A "…" (44 px) shows on hover and focus, always on touch: **Rename** (inline field, Enter saves, Escape cancels) and **Delete** (two steps inline: "Delete this chat? Delete / Keep", 44 px targets). Arrow keys move through the search and the rows, Home and End jump, Enter opens. The current chat appears in Today the moment it has a turn. Empty: "No chats yet. Ask Clair something." with the spool, in the log. Phone: the same list in a drawer from the header's History button: slides in 350 ms (transform and opacity), the backdrop fades in 220, tap outside, Escape or a swipe left closes it (the panel follows the finger), focus is held inside and returns to the button, the chat behind is `inert`; opening a chat closes it; reduced motion is a 120 ms fade. The sheet needs no list: "Open chat ›" (start state), "Continue: <title>" (the chat in hand, or the server's latest) and "Open in chat ›" (beside "Waiting for your OK", else under the turn) lead to `/chat`.
- **Saved.** After each completed turn (and each confirm or Undo) the thread is written to a per-device archive in IndexedDB (`quilt-chats`): title, apps, and per message the words, the answer, the sources and one line per card (title, status, apps); never a card body. 30 chats, 90 days, memory only without IndexedDB. The server's latest thread (`GET /clair/threads/latest`, text only, within 24 h) is read when the sheet or the chat opens and added to the list; "Continue" sends its `thread_id`. A message that names a change set but not what was in it reads "Changes saved". Rename and Delete are local. Samples (eight, spread over the four groups) exist only in mock builds, marked "sample", never saved.
- **Words.** "Chat", "New chat", "Continue", "Open chat". No pronoun for Clair in the UI; sentence case.


## 17. Remove app (Nov 20)

The app menu (`···` in an app's header, phone and laptop) ends with **Remove app**: a running-stitch seam (1.5 px, 66% dashes in `--thread`), then a 44 px row, ink text and a trash icon, never red. Contract: `spec/backend.md` §11 row 21 and FR-S8. Code: `components/RemoveApp.tsx`, `styles/remove.css` (prefix `rm-`), `removeApp` and `previewRemoveApp` in `lib/store.ts`, `DELETE /apps/:key` in the mock.

- **One sheet, two steps.** Tapping the row fades the menu out (140), then the confirm step arrives in the same sheet (220, up 8 px and in); the sheet's label becomes "Remove <App>?". No second sheet. Reduced motion: both are 120 ms fades with no travel. The sheet's own rise, drag and exit are unchanged.
- **The step** is `role="alertdialog"` labelled by its heading (22 / 700, "Remove Groceries?") and described by its body. Body: what goes with the app ("Its 42 rows go with it." plus "and 1 rule" when it has rules, from the app's own data), then what else reads it, one line per thing with the other app's dye dot and bold name, in plain words from the server's preview ("**Budget** reads Groceries trips and will stop getting new ones. Rows it already has stay."; five lines at most, then "and N more"), or "Nothing else uses it."; then "You can undo this right after." (13 `--sec`). Buttons, 48 tall, one filled primary: **Keep** (outline) | **Remove** (filled ink, never red), equal columns.
- **Preview first.** The step asks `DELETE /apps/{id}` without `confirm` (a 409 `{error: 'dependents', dependents: [{app, what}]}`); Remove stays disabled until it has answered ("Checking what uses it…", `role="status"`). A failed check says so in ink with a "Try again" link and nothing changes. A failed Remove says why in ink and the buttons come back.
- **Focus.** Focus lands on **Keep** (the safe button) when the step opens. Keep, Escape, the scrim, the × and a drag down all just close the sheet; the sheet returns focus to `···`. Nothing is sent.
- **Remove.** `DELETE /apps/{id}?confirm=true` is one change set. The button reads "Removing…", the sheet leaves (220), Home arrives with the receipt capsule ("Removed Groceries." and **Undo**, the standard 8 s gold thread, the app's dye dot); the patch, its sidebar row and its pin are gone, and Home and `me` reload. Undo is `POST /change-sets/{id}/undo`: the patch comes back where it was. There is no "Undone" toast.
- **Every app.** Calendar and the pinned apps can be removed (the server tombstones them and the pin drops); a private app (Cycle) shows the same step. The client holds no rule about which apps may go: the server's answer decides.

- **The trash (Nov 20).** Remove no longer deletes: the app waits 3 days. The confirm step adds one note, "Kept for 3 days in You → Recently removed." (13 `--sec`, a 14 px trash glyph). **You** gets a **Recently removed** section under Another device (`components/RemovedApps.tsx`, styles at the end of `styles/remove.css`): a `.sec` label, then one card with a row per app: its dye tile, the name, "Deleted in 3 days" (13 `--sec`, rounded up from the server's `purge_at`; "Deleted today" under a day), **Restore** (outline, 44) and a 44 px trash button, "Delete <App> now". Empty: one card, "Nothing here. An app you remove waits here for 3 days before it is deleted." **Restore** sends `POST /apps/{id}/restore`; the patch sews onto Home (the standard slide-in, `sewing`) and reads "just changed", and a 5 s capsule says "Restored Groceries." (no Undo: Remove is the way back). **Delete now** opens the same alertdialog sheet as Remove ("Delete Groceries now?", "Its rows, rules and links are deleted for good.", "This can't be undone. Restore it instead if you might want it back."), **Keep** (outline, takes focus) | **Delete now** (filled ink, never red); a capsule says "Deleted Groceries for good." Reduced motion: as Remove.
