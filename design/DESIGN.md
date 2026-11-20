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

**Toast** (What Clair remembers): a white card, not a dark pill: radius 16, 1.5 px `--line` edge and a soft shadow, 52 tall, 16 above the bar; the message 15 px; **Undo** is a link on the right.

**Sheet**: on `--ground` (not white), radius 22, padding `8px 16px 16px`, gap 16, a 40 × 4 grabber in `--line`, then the header (spool 44 · 22 / 700 title over a 13 px line · close ×).

**Home quilt** (Home board, "Your apps · 7 … Most used first", then a find field): a 6-column grid of 58 px rows, gap 6, filled with no holes, most used first (Budget 4 × 2, Workout 2 × 2, the rest 2 or 3 wide). A patch is the app's fill, radius 22, padding `8px 12px`, an inner dashed stitch (inset 6, radius 11), the icon and name at the top (13 / 600) and the figure at the bottom (28 / 700 on the big patch, 14 / 700 on small ones), "just changed" in the corner. The last cell is a white "+" patch.

**Clair sheet** (Tap Clair): spool 44 "hello" + "Tell Clair anything" 22 / 700 + a 13 `--sec` line, a close ×; the field (radius 22, 1.5 px `--line`) with a round send; Talk | Photo | File as secondary buttons; "Try this evening" with three rows, each with an icon tile and a "Log it · Budget" meta; "Open chat ›".

**Question card** (New app, after Build it; Clair asks before building, `spec/clair-agent.md` §7 rule 7). Clair's line first (spool 30, "A few questions first, then I'll show you the plan."), then one white card (`.card`, padding 16, gap 16) with 1 to 3 questions split by a dashed `--line` rule. Each question: the header as a section label (13 / 600 `--sec`, "Pick any" on the right when it's multi-select), the question 17 / 700, then option rows like the fridge question (board ClairFridge): full width, min-height 56, radius 16, padding `8px 12px`, gap 12, `--card` with a 1.5 px `--line` edge; label 16 / 600 over a 13 `--sec` description. Single select is a 22 px circle with a 10 px `--focus` dot (`role="radio"`, arrow keys move); multi is a radius-7 square filled `--focus` with a tick (`role="checkbox"`). Selected = `--focus` 12% ground, 1.5 px `--focus` edge, label in `--focus`. Every question ends with an **Other** row; picking it, or an option that takes a value ("Set a number"), opens a field under it, indented to the label (46), with a 13 / 600 label ("Calories a day"). Then **Continue** (primary, full width, disabled until each question is answered; a 13 `--sec` line under it says how many are left) and the link "Skip, use your best guess". No option ever suggests a number.

**Plan card** ("Here's the plan"): chalk, because it is Clair's idea and nothing is made yet. The chalk-triangle mark + "Here's the plan" (13 / 600), the new app's 36 px tile and name (22 / 700) with a Private tag when private, one line per change (16 / 1.4) behind a 10 px dye dot of the app it touches, then **Build it** (primary) | **Change answers** (secondary, no wrap; back to the questions with the answers kept). Build it shows the Build preview; nothing is saved before Make it. Steps on New app crossfade (out 140, in 220, opacity only); each step is a history entry, so Back (and the phone's back) walks describe ← questions ← plan ← preview. Expired (the questions waited over 24 h): a white card "Still want to build this?" with **Build it** (re-sends the sentence) | Not now.

**Empty app** (New app 5 · ready): "new" tag beside the h1, "Connected to ● Calendar ● Budget", a card with spool 96 hello, "<App> is ready" and one sentence, then secondary buttons: "Tell Clair or add a photo", "Type one in", "Bring 4 in from Budget".

## 6. Motion

Tokens: feedback 120, state 220, layout 350, focal 600; exits 140, 220, 360. Ease `cubic-bezier(.16,1,.3,1)` for everything, no bounce; the thread curve `(.45,0,.15,1)` only for a stitch being drawn. Gesture releases use the critically damped `spring()` and keep the finger's speed (`design/notes/fixspec.md` §A, ported in `web/src/lib/motion.ts`).

| Moment | Motion |
| --- | --- |
| Press | Buttons and chips scale .97; patches .98; bar cells and full-width rows darken instead |
| Hold | 450 ms; the fill starts after 120 ms; a 10 ms buzz when it fires |
| Sheet | Grows from where it was opened (the Clair cell: origin bottom right), translateY 16 + scale .96 → 1 over 350; leaves in 220; drag down to close (spring .35, closes past .35 of its height with momentum) |
| Toast | A white card with an Undo link; rises 8 px in 220, leaves in 140; waits until raised tiles have sunk |
| Confirm a card | The basted edge closes (220). Then each target app you can see gets a running stitch sewn around its tile in its own colour (600, 120 apart, lands at 70%: the number rolls, "just now" scales in). Apps you can't see, or whose number changes but only a pin shows, creep up above the bar as small tiles, get the same stitch and roll, then sink. Owner's idea, Nov 20; the earlier thread pull stays behind `?motion=threads` until the owner confirms |
| Undo | The edge re-bastes (140), the stitches pull out (360), tags fade, numbers roll back |
| Number roll | Old and new share a grid cell; increases roll up, decreases roll down, 220 |
| Tags | Scale .95 → 1 from the left, 220; fade out 140 |
| Lists | A ticked row's circle fills (120), the title strikes, then the row folds away (220). Swipe right to complete, left to delete: the row follows the finger, arms at 90 px with a short buzz, commits past 90 or with a fling (spring .25), springs back otherwise (.3) |
| Queue on Home | The handled card leaves up 8 px (140), everything below FLIPs (350), the next card enters (220) |
| Build | The sentence lifts into the chalk card (350), chalk outlines wipe in left to right (350), each piece bastes (220, 240 + 380 apart), then the sew finale: stitch-in 40 ms apart, dye sweep (350), "pieced by clair" stamps (220), spool hops, the patch slides onto Home (350) with "new" |
| Reduced motion | No movement anywhere: 120 ms opacity fades (every duration token becomes 120), springs jump, no stitches drawn, no rolls, spool face only. One exception: the 3% press scale on buttons stays, it is the finger's own feedback, not movement on screen |

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
| New app 1 to 5 | Build, Preview, Arrange, Connect, Empty | Describe → pick a layout → arrange → connect and add → ready |
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
