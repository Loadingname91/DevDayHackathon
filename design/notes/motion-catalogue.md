# Quilt motion catalogue

Every animation Quilt defines, named with its industry term. Sources (line numbers as of Nov 19 07:00; quilt-home.html was still being edited): `quilt-flows.html` (QF), `workbench-motion.html` (WM), `quilt-home.html` (QH), boards in `artifact-files/.../project/` and `polish/fixspec.md` sections A and D. Live demos of every row: `SP/motion-catalogue.html`.

Status: **built** = running code in a prototype · **spec** = specified (fixspec or a still board) but not running anywhere · **new** = proposed in this pass (Part 1 below), with exact values.

Tokens (fixspec A): `EASE cubic-bezier(.16,1,.3,1)` · `EASE_THREAD cubic-bezier(.45,0,.15,1)` (thread draw only) · fb 120 · state 220 · layout 350 · focal 600 · exits 140 / 220 / 360. Gesture releases use a critically damped `spring(from,to,v0,response)` (no overshoot) carrying finger speed; `project(v)` adds momentum; `rubberband(o,d,.55)` past bounds. RM = reduced motion: no movement, 120 ms opacity only, springs jump, threads and rolls off, spool face only.

---

## Part 1. New opportunities on the surfaces the last pass skipped (find-animation-opportunities)

Scope: the Clair button and sheet (tap, hold-to-talk, listening, send, thinking, proposals, confirm, ask answer, photo + fork, share, dismiss), Clair building an app, and the layout preview. Most of it is already right. The gate: frequency, purpose, budget, function. Quilt's rule is feedback and continuity only, with one focal motion (thread pull).

| # | Location | Today | Purpose | Frequency | Suggested motion |
|---|---|---|---|---|---|
| N1 | QF:196 `.sheet.clairs` vs QH:136 `.sheet` | The two prototypes open the Clair sheet differently. Flows inherits `translateY(105%)` (flies up a full sheet height); Home uses `translateY(48px)`. Both set `transform-origin:100% 100%`, but nothing scales, so the origin does nothing. | Spatial consistency (it comes from the Clair cell) | Several times a day | Closed `transform:translateY(16px) scale(.96); opacity:0`, open `none; 1`, origin `100% 100%`, T.layout EASE in, T.layoutOut EASE out. Use the same rule in both files. RM: opacity only, 120 ms. |
| N2 | QH:697 `talkRelease`, QF:1396 tSend | When you release to send, the stitch waveform freezes mid-level and the sheet crossfades to "Reading that". Nothing confirms the release was heard. | Feedback | Every talk | On release, each stitch animates to its rest length (`x1/x2` to ±4.5) over T.fb EASE, and the hint reads "Sending". Swap to thinking after 120 ms. RM: the line is already static, so only the hint swaps. |
| N3 | QH:619 `view('result')`, QF:1407 | Proposal cards arrive inside the whole-sheet crossfade, so two destinations read as one block. | State indication (each card is a separate landing) | Every capture | After the swap, cards enter `opacity 0, translateY(8px)` → settled, T.state EASE, 40 ms stagger, cap 3. The buttons don't move. RM: opacity only, 120 ms, no stagger. |
| N4 | QH:731 `shutter` | The viewfinder disappears, then "Reading the receipt…" appears. The photo just vanishes. | Spatial consistency | Occasional | Shared element: the viewfinder frame scales (uniformly) and translates into a 44 px thumb in the attachment row, T.layout EASE. The rest of the sheet crossfades. RM: crossfade, 120 ms. |
| N5 | QH:741 `readSyllabus` (1.4 s), ClairShare board | Reading a shared file shows a static working spool and a title for 1.4 s or more. There's no sign of progress. | State indication (long wait) | Occasional | Reuse the built "seam lead" from WM:827: under the attachment row, two stitches per page (4 pages = 8 stitches), each fading in over T.fb, with one 220 ms stitch-dip of the spool per page. RM: stitches appear and the status line counts pages. |
| N6 | QF:604 b1 → b2 "Build it" | The Build screen replaces the Describe screen, and the user's sentence reappears in a chalk card with no link to the textarea it came from. | Spatial consistency (your words become the brief) | Rare (building an app) | Shared element: the sentence's box moves from the textarea rect to the chalk card rect (translate only, T.layout EASE), then the chalk outline wipes (built, 350 ms). RM: crossfade, 120 ms. |

Rejected:
- QF:1388 / QH:681, fade-in on each transcript word. **Rejected (Function):** the live transcript must be readable the instant a word lands, and a fade per word adds lag at roughly 4 updates a second.
- QH:622 "answer", rolling the numbers in the answer ($376, $316, $26). **Rejected (Function):** nothing changed, the user is reading data, and a roll would imply a change.
- Clair button mark (QH:412), animating the faceless spool while Clair works. **Rejected (Frequency + rule):** the bar is chrome you see 100+ times a day, and spec D says the mark never animates except for press feedback.
- QF:639 / WM:587, re-tracing the chalk outline as a stroke (`stroke-dashoffset` around the rect) instead of the clip-path wipe. **Rejected (Purpose):** it carries the same information at a higher cost, and the left-to-right wipe already reads as drawing.
- ClairPhoto board, morphing the chosen "Log items / Just answer" chip into the next header. **Rejected (Purpose):** decoration. The standard state swap (crossfade + height) already connects the before and after.
- Pager dots (QF:675), sliding the active dot between positions. **Rejected (Frequency/Function):** the content already enters from the swipe side, so a second moving part would only compete with it.

Verdict: The Clair and build surfaces mostly do the right thing already: tokens, crossfade-plus-height swaps, the hold fill, the drag spring and the thread pull on confirm. What's missing is continuity at three handoffs (N4 photo, N6 brief, N1 sheet origin), plus two small feedback beats (N2 release, N3 proposals). N1 has the most leverage: it's the most frequent surface, and right now the two prototypes disagree on it. N5 reuses a built pattern rather than adding a new one. Handoff: `improve-animations plan <row>`.

---

## Part 2. Inventory

Columns: industry term · Quilt name · trigger · what moves · duration + easing · interruption · RM fallback · where · status.

### Foundations

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Cubic-bezier (ease-out) | Quilt ease | Every transition / WAAPI | n/a | `cubic-bezier(.16,1,.3,1)`; no linear, no `ease`, no ease-in | CSS transitions retarget | same curve, 120 ms | QF:15, WM:17, QH :root | built |
| Asymmetric easing | Thread curve | Thread draw only | stroke-dashoffset | `cubic-bezier(.45,0,.15,1)` 600 | runId guard | threads off | QF:15, WM:18 | built |
| Duration | Four beats | n/a | n/a | 120 feedback · 220 state · 350 layout · 600 focal; exits 140/220/360 (0.5–0.7×) | n/a | all → 120 | fixspec A | built |
| Press / Tap feedback | Press | :active on buttons, chips, patches | transform scale .97 (patches .98) | 120 EASE | CSS retarget | none | QF:87, WM:103/108, QH:80/105/149 | built |
| Press feedback (no scale) | Cell press · row tint | :active on pinned-bar cells / full-width rows | inset box-shadow darken / bg #F7F1E6 | 120 EASE | CSS | same (colour only) | QF:129, QF:168, QH:121/152 | built |
| Hold to confirm | Hold fill | pointerdown held 450 ms (Clair button, rows) | `::after` clip-path inset(0 100% 0 0)→inset(0) | 330 linear after 120 delay; vibrate 10 on fire | release <450 clears, no fill on quick taps | fill shows at once (no sweep), hold still works | QF:135, QH:132, QH:417 | built |
| Spring (critically damped) + Momentum | Release spring | Any gesture release | the dragged value | response .25–.35 s, carries velocity of last 3 samples, `project(v)` decides commit | pointerdown cancels and grabs from live DOMMatrix | jumps to end | QF:341, QH:745 | built |
| Rubber-banding | Overpull | Drag past a bound (sheet up, row past 130, pull) | translate with `rubberband(o,d,.55)` | follows finger | live | n/a (no drag motion) | QF:353 | built |
| Reduced motion | Fallback rule | `prefers-reduced-motion` | opacity only | 120 EASE | n/a | n/a | QF:251, WM:239, QH:207 | built |

### Clair: button and sheet

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Press feedback | Clair cell press | tap Clair | inset paper .1 darken; mark never moves | 120 EASE | CSS | same | QH:129, QF:136 | built |
| Hold to confirm | Hold to talk | hold Clair 450 ms | fill → vibrate 10 → sheet opens in Talk | 120 delay + 330 linear | early release = tap (sheet) | fill at once, no sweep | QH:417, QF:405 | built |
| Drag (threshold) | Slide up to cancel | while held, finger up ≥60 px | waveform opacity .3 (QH) / stitches → #BFAE90 (QF); hint "Release to cancel"; vibrate 8 | 120 EASE | toggles both ways | colour/text only | QH:692, QF:414, QH:162 | built |
| Slide in + Fade (sheet) | Clair sheet rise | tap Clair | sheet translateY(48px)+opacity; scrim opacity | in 350 EASE, out 220 | close mid-open retargets; drag spring cancelled on reopen | opacity 120 | QH:136-137, QH:134; QF:196 (105%) | built |
| Origin-aware animation | Rise from the button | same | translateY(16px) scale(.96), origin bottom-right | 350 / 220 EASE | CSS retarget | opacity 120 | Part 1 N1 | new |
| Fade out | Dismiss | scrim tap, Esc, Clair re-tap, drag | sheet + scrim out | 220 EASE | reopen during exit is clean | 120 | QH:662, QF:459 | built |
| Crossfade + Layout animation | State swap | any sheet state change | content opacity, sheet height | fade 120 → height 220 → fade 120 | swapId drops stale swaps | instant swap | QH:640, QF:445 (also chained sheets) | built |
| Swipe to dismiss + Rubber-banding | Pull the sheet down | drag grab / top 48px / body at top | translateY 1:1, scrim follows; up = rubberband | spring .35; close if y+proj > .35h | grab mid-spring | close fades 120 | QH:745-807, QF:466 | built |
| Waveform (level meter) | Stitch waveform | Talk mode | 19 stitches' length follows voice level | rAF; decay .035/frame (QH) / 90 ms steps (QF); board: scaleX .4↔1 760 alternate | stops on release/cancel | static line + "Listening" | QH:677, QF:1391, ClairTalk.dc:46 | built |
| Typewriter (word by word) | Live transcript | words arrive | text | 260 ms/word (QH), 220 (QF), no fade | n/a | same | QH:681, QF:1388 | built |
| Interpolation | Stitches settle | release to send | stitches → rest length | 120 EASE, then swap | n/a | hint only | Part 1 N2 | new |
| Pulse | Clair thinking | after send / ask | thought dots opacity .25↔1, staggered .2 s; 700–900 ms dwell | 1.2 s ease-in-out loop | new state replaces | face only | QH:674, QF:1403 | built |
| Stagger | Proposals arrive | result state | cards opacity + translateY 8 | 220 EASE, 40 ms apart, cap 3 | n/a | opacity 120 | Part 1 N3 | new |
| Line drawing (orchestrated) | Capture confirm | "Add to N apps" | cards un-baste → threads card dots → pins → notches → sheet closes → toast | 220 + 600 (stagger 120, land 70%) + 400 + 220 | busy + runId; buttons disabled | no threads; notches fade 120 | QH:705, QF:1416 | built |
| Scale in | Pin notch | thread lands on pin | notch scale .95→1 + opacity | 220 EASE; undo fade 140 | n/a | opacity 120 | QH:503, QF:1347 | built |
| Crossfade | Answer arrives | ask resolved | state swap; spool stitched hop once | 220 + 420 hop | n/a | swap + face | QH:622, QF:1433 | built |
| Press feedback | Shutter | press shutter | scale .94 | 120 EASE | CSS | none | QH:179 | built |
| Shared element transition | Photo drop-in | shutter fires | viewfinder → 44 px thumb | 350 EASE | n/a | crossfade 120 | Part 1 N4 | new |
| Crossfade | Log or answer fork | photo + question | unchosen chip fades 140, state swap | 140 + swap | n/a | swap | ClairPhoto.dc:58 (still) | spec |
| Stepped animation (determinate progress) | Reading seam | file shared in | 2 stitches/page fade in, spool dips per page | 120 per stitch, 220 dip | n/a | stitches appear, text counts | Part 1 N5 (QH:741 today: static) | new |
| Translate | Seam lead | reading a receipt photo | spool slides along the seam; stitches appear | 350 EASE; stitches 120 | n/a | jumps per row | WM:179, WM:827 | built |

Mascot (Clair spool, `spool(expr,size,play)`, sizes 30/44/96, one per screen; motion on the outer svg):

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Keyframes (one-shot) | Hop (hello, stitched, proud) | expression newly entered (`play`) | translateY −5 px | 420, up cubic-bezier(.2,.8,.3,1), down (.6,0,.9,.5) | plays once | face only | WM:202, QF:215, QH:197 | built |
| Shake / Wiggle | Oops shake | piece frayed / save failed | translateX ±3, rotate ±3° | 360 ease-in-out, once | once | face only | WM:204 | built |
| Alternate (yoyo) | Working bob | working (status spool only) | translateY −2 | 560 ease-in-out infinite alternate | loop | still | WM:205 | built |
| Idle animation | Blink | while working only | eyes scaleY .1 | 4.3 s, irregular double blink | loop | none | WM:207 | built |
| Pulse | Thought stitches | thinking | 3 dots opacity | 1.2 s, .2 s stagger | loop | none | WM:210 | built |
| Pulse (scale) | Sleepy breathe | sleepy | body scale 1.035 | 2.6 s ease-in-out | loop | none | WM:209 | built |
| Translate | Stitch dip | one row sewn | translateY 2 px and back | 220 ease-in-out | per row | none | WM:857 | built |
| n/a (still) | Waiting | basted, needs OK | nothing; brows up, needle raised | none | n/a | n/a | WM:772 | built |
| Loop (rotate) | Chalk rock (presence option D) | working, chalk-only option | rotate ±8° | 900 ease-in-out alternate | loop | none | WM:148 | built (exploration) |
| Loop | Needle dip (presence option A) | working, needle option | translate + rotate | 520 ease-in-out | loop | rests | WM:181 | built (exploration) |

### Building an app

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Shared element transition | Brief lifts into chalk | "Build it" | sentence box textarea → chalk card | 350 EASE translate | n/a | crossfade 120 | Part 1 N6 | new |
| Reveal (clip-path) | Chalk outline | each piece starts | dotted outline clip-path inset(0 100% 0 0)→0 | 350 EASE | runId stops | fade 120 | QF:639, WM:587 | built |
| Fade + Translate | Proposed title | name picked | opacity + translateY 4 | 220 EASE | n/a | appears | WM:595 | built |
| Enter (fade + rise) | Basting a piece | piece passes checker | body opacity + translateY 4; stitch becomes basted | 220 EASE | runId | appears | QF:652, WM:617 | built |
| Shake + state change | Fray and re-cut | piece fails | frayed edge, spool oops shake, chalk redraws | 360 shake, 1.3 s hold, 350 chalk | runId | face + text | WM:602-611 | built |
| Orchestration + Scroll | Clair builds (sequence) | after describe | title → pieces one by one; scroller follows (smooth, nearest); status line sticky | ~0.7 s + 0.75 s/piece | runId restart | narrated, fades 120 | WM:589, QF:621 | built |
| Drag + Direction-aware transition | Layout pager | swipe / arrows on preview | #pv translateX 1:1, opacity 1−|dx|/w·.4; new layout enters ±24 px | commit \|dx+proj\|>.3w; spring .3; enter 220 EASE | grab mid-spring | instant swap | QF:662-709 | built |
| Drag to reorder | Arrange | drag grip | picked piece scale 1.02, siblings translate ±(h+gap) | lift 120, shift 220, settle spring .3 from drop | pointerdown cancels FLIP/spring | no lift, instant | QF:738-800 | built |
| Exit (scale + fade) + Layout animation | Rip out a piece | seam-ripper icon | piece opacity → 0, scale .96; gap closes (FLIP) | 220 EASE + 350 | n/a | instant | QF:760-765 | built |
| Pulse (ring) | Block flash | piece added / moved by Clair | mustard ring box-shadow 3px → 0 | 600 EASE | n/a | none | QF:758 | built |
| Toggle | Connection toggle | tap connection | knob translateX 20, track colour | 220 EASE | CSS | colour 120 | QF:153-155 | built |
| Line drawing | Connect pull | "Add to my apps" | draft un-bastes; a thread from each ticked connection into the new patch; notch lands | 220 + 600 (land 70%) | busy + runId | notch fades | QF:832-846 | built |
| Stagger | Stitch-in | "Stitch it in" | pieces basted → running, 40 ms apart | 220 each | runId | 120 | WM:627 | built |
| Reveal (clip-path circle) | Dye sweep | after stitch-in | title dye circle(0%→150%) from the chalk mark | 350 EASE | runId | set instantly | WM:633 | built |
| Scale in (from larger) | Label stamp | finale beat 1 | "pieced by clair" label rotate(−6°) scale(1.15) → rotate(−1.5°) | 220 EASE | n/a | fade 120 | WM:637 | built |
| Slide in | Dock insert | finale beat 3 | new patch translateX(−24) + opacity, "new" tag scales in | 350 EASE + 220 | n/a | appears | WM:642-645 | built |
| Orchestration | Sew finale | "Stitch it in" | stitch-in → dye → stamp → face +60 → dock +120 → toast +250 | ~1.1 s total | runId | same order, fades | WM:625-646 | built |
| Enter | Landed | arriving in the new app | header translateY 8 + opacity; "new" tag .96→1 (+60) | 220 EASE | n/a | none | QF:872-876 | built |

### Stitching

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Morph (dash length) | Basted → stitched | confirm | `.st` background-size dash 20 → 7 px, colour ink2 → stitch | 220 EASE in; 140 back | CSS | 120 | QF:78-82, WM:84-90, QH:73-74 | built |
| Line drawing | Thread pull (the one focal) | confirm on a basted card | per target svg path stroke-dashoffset L→0; stagger 120; land at 70%; fade +400 | 600 EASE_THREAD; fade 220 | busy + runId; Undo retracts | no threads; values swap, tags fade 120 | WM:483, QH:535, QF:520 | built |
| Number ticker + Tabular numbers | Odometer roll | value changes on landing | old/new stacked, translateY ±100% + opacity, direction follows value | 220 EASE | settles any roll in flight | swap | WM:412, QH:492 | built |
| Scale in | Just changed tag | landing | tag opacity + scale .95→1, origin left | 220 in / 140 out EASE | n/a | fade 120 | WM:421-428, QH:503-512 | built |
| Colour transition | Fed dot | landing | selvedge dot → mustard | 220 in / 140 out | CSS | 120 | WM:110-111 | built |
| Line drawing (reverse) | Seam-ripper undo | Undo | threads retract toward source, tags fade, numbers roll back, card re-bastes | 360 EASE; 140 | busy guard | swap + fade 120 | WM:514, QH:566 | built |

### Lists and sheets

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Swipe actions (drag + spring) | Swipe row | horizontal drag ≥10 px | row translateX 1:1 to ±130 then rubberband; armed at 90 (moss / ink), vibrate 8 | commit if \|x\|>90 or \|x+proj\|>.4w; fly to −w spring .25; back spring .3 | grab mid-spring from live x | no slide; opacity 120 then collapse | QF:1107-1168, QF:158-167 | built |
| Accordion / Collapse | Row delete + Undo | delete commit / Undo | height → 0; re-insert 0 → h + opacity | 220 out / 220 in EASE | n/a | opacity 120 | QF:1099-1106 | built |
| Colour transition | Check fill | "Got it" | check background → moss | 120 EASE | n/a | same | QF:170 | built |
| Hold (long-press) | Select by hold | hold a row 450 ms | row tint #E6ECF7, vibrate 10 | 120 EASE | move cancels | same | QF:1125-1128 | built |
| Slide in (bottom sheet) | Edit sheet | tap a row | sheet translateY(105%) → 0; scrim | 350 in / 220 out EASE | drag to dismiss (spring .35) | opacity 120 | QF:142-143, QF:1170 | built |
| Rubber-banding (pull to refresh pattern) | Pull to search | pull down at scrollTop 0 | content translateY rubberband; arms at 64 (hint ink, "Release to search", vibrate 8) | release ≥64 → search; else spring .35 | grab mid-spring | no translate | QF:1003-1037 | built |
| Slide in + Fade | Search opens | pull released / button | search content translateY(−16) → 0 + opacity | 220 EASE | n/a | appears | QF:1001 | built |
| Slide in + Fade | Toast | any undoable result | translateY 10 → 0 + opacity | 220 in / 140 out EASE | re-trigger retargets | opacity 120 | QF:137-138, QH:183 | built |
| Layout animation (FLIP) | Many apps reflow | app count crosses 8 / 20, fold | translate only; size change >2% → crossfade 220; new patches .96 → 1, stagger 12 cap 240 | 350 EASE | n/a | instant | WM:703-721 | built |
| Fade out | Fold offer | "Leave them" | chalk offer opacity | 140 EASE | n/a | 120 | WM:732 | built |
| Fade in | Basted placeholder → data | slow tab data arrives | values fade in; basting disappears | 220 EASE | swId | 120 | WM:916 | built |

### Home

| Industry term | Quilt name | Trigger | What moves | Duration · easing | Interruption | RM | Where | Status |
|---|---|---|---|---|---|---|---|---|
| Layout animation (FLIP) | Queue advance | a Needs-your-OK card is handled | card exits translateY −8 + fade; everything below FLIPs; next card enters 8 → 0 | 140 out, 350 FLIP, 220 in (40 ms stagger, max 2) | busy + runId | opacity 120 | QH:472-490 | built |
| Accordion + Stagger | N more | "N more waiting" | extra cards enter, rest FLIP | 220, 40 ms stagger max 2; FLIP 350 | busy | opacity 120 | QH:829 | built |
| Line drawing + Number ticker | Add to 3 apps (Home) | basted receipt card | threads from the card's dye dots to the pinned-bar pins; money line $412 → $376 rolls down; notches | 600 thread, 220 roll | busy + runId; Undo retracts 360 | swap + fade | QH:550-582 | built |
| Scroll + Enter | Receipt arrives | photo taken from the Clair sheet | screen smooth-scrolls to top; receipt card enters the queue | smooth scroll; 220 enter | busy | instant scroll | QH:731-740 | built |
