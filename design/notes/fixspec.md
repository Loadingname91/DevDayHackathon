# Quilt polish: fix spec (merged from 6 audits: taste, improve-animations, review-animations, find-animation-opportunities, mobile-native, apple-design)

Read brief.md (same folder) for context. This file is the single source of truth for shared values. Where an audit and this spec disagree, this spec wins. Each fix agent owns ONLY its listed files; never edit another agent's files. Never edit support.js.

## A. Shared values (every agent uses exactly these)

### Motion tokens (put in :root of every file you own that has motion)
```css
--ease: cubic-bezier(.16,1,.3,1);
--ease-thread: cubic-bezier(.45,0,.15,1);   /* thread draw ONLY (signature) */
--t-fb:120ms; --t-state:220ms; --t-layout:350ms; --t-focal:600ms;
--t-state-out:140ms; --t-layout-out:220ms; --t-focal-out:360ms;
```
```js
const EASE='cubic-bezier(.16,1,.3,1)', EASE_THREAD='cubic-bezier(.45,0,.15,1)';
const T={fb:120,state:220,layout:350,focal:600,stateOut:140,layoutOut:220,focalOut:360};
let RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>RM=e.matches);
```
- Every CSS transition and WAAPI call names an easing (EASE unless stated). No linear defaults, no `ease`, no ease-in curves.
- Exits use the *-out duration: put the exit duration on the base rule, the entrance duration on the active state (.toast/.toast.on, .sheet/.sheet.on, .scrim/.scrim.on, .st.basted gets --t-state-out).
- Mascot loops (bob, blink, breathe, think dots) are character motion and keep their own timings.

### Gesture release spring (gesture releases ONLY; everything else uses EASE)
Critically damped (damping 1.0 = no overshoot, so "no bounce" holds). Velocity from last 3 pointermove samples.
```js
function spring(from,to,v0,response,onUpdate,onDone){const w=2*Math.PI/response,x0=from-to,t0=performance.now();let id;
 const step=n=>{const t=(n-t0)/1000,e=Math.exp(-w*t),x=(x0+(v0+w*x0)*t)*e,v=(v0-w*(v0+w*x0)*t)*e;
  if(Math.abs(x)<.5&&Math.abs(v)<5){onUpdate(to,0);onDone&&onDone();}else{onUpdate(to+x,v);id=requestAnimationFrame(step);}};
 id=requestAnimationFrame(step);return()=>cancelAnimationFrame(id);}
const project=(v,d=.995)=>(v/1000)*d/(1-d); // v in px/s → projected extra distance
const rubberband=(o,d,c=.55)=>(o*d*c)/(d+c*Math.abs(o));
```
Responses: sheet .35 (close if y+project(v) > .35*h); row swipe .25 to ±width / .3 back (commit if |x+project(v)| > .4*w OR |x|>90); Arrange drop .3; pull-down cancel .35; layout pager .3 (commit if |dx+project(v)| > .3*w). On pointerdown cancel any running spring/WAAPI and start from the live value (read DOMMatrix m41/m42). Under RM springs jump straight to the end value.

### Signature thread pull (the one focal motion; same recipe everywhere)
- Sequence on confirm: remove `.basted` (stitch tightens, 220ms) → at +220ms append `<svg class="threads" aria-hidden="true">` inside the phone frame (`position:absolute;inset:0;pointer-events:none;overflow:visible;z-index:16;contain:layout paint`; path `fill:none;stroke:#E3A72F;stroke-width:2.4;stroke-linecap:round`).
- Per target i (stagger 120ms): path `M a C a.x,a.y+dy b.x,b.y-dy b` with `dy=max(40,(b.y-a.y)*.55)`, coordinates relative to the phone frame rect; `strokeDasharray=L`; animate strokeDashoffset L→0, T.focal, EASE_THREAD, fill forwards.
- LAND at 70% of the draw (await sleep(T.focal*.7)), not at .finished: target gets its mustard notch / "just changed" tag (opacity 0→1, scale .95→1, 220ms EASE, transform-origin left center), numbers roll.
- Last landing + 400ms: threads fade opacity 1→0 over T.layoutOut EASE, then remove.
- Guard with a `busy` flag + runId so double taps / Undo mid-run don't stack. Disable the confirm button during the run.
- Undo: re-add .basted (140ms), roll back, notches fade out 140ms; retract threads strokeDashoffset 0→L (toward the source), T.focalOut, EASE.
- RM: no threads, no roll; values swap, notches/tags fade in 120ms opacity only.
- Keep the card/button area height fixed during the run (min-height 44px on the button row) so targets don't jump.

### Number roll
Wrap value in `display:inline-grid;overflow:hidden;vertical-align:bottom`; old and new stacked in the same grid cell. Increase: old → translateY(-100%), new from 100%. Decrease (e.g. $412→$376): old → translateY(100%), new from -100%. Both with opacity, T.state, EASE. Changing/animated numbers get `font-variant-numeric:tabular-nums` (Bricolage supports it).

### Spool mascot (Clair)
- Signature: `spool(expr, size, play=false)`. One-shot classes (sp-hop, sp-shake) are emitted only when `play` is true; pass play=true only when that expression is newly entered (track lastFace per screen). Loop classes (sp-bob, sp-think, sp-breathe) unconditional.
- Motion lives on the OUTER svg (CSS px, same amplitude at every size); delete `.sp-hop .body`, `.sp-shake .body`, `.sp-bob .body` rules:
```css
.sp{transform-origin:50% 100%}
.sp-hop{animation:hop 420ms 1}
@keyframes hop{0%{transform:none;animation-timing-function:cubic-bezier(.2,.8,.3,1)}40%{transform:translateY(-5px);animation-timing-function:cubic-bezier(.6,0,.9,.5)}75%,100%{transform:none}}
.sp-shake{animation:shake 360ms ease-in-out 1}
@keyframes shake{0%,100%{transform:none}20%{transform:translateX(-3px) rotate(-3deg)}45%{transform:translateX(3px) rotate(2deg)}70%{transform:translateX(-1.5px)}}
.sp-bob{animation:bob 560ms ease-in-out infinite alternate}
@keyframes bob{to{transform:translateY(-2px)}}
.sp-bob .eyes{animation:blink 4.3s infinite;animation-delay:-1.7s}   /* blink ONLY while working */
@keyframes blink{0%,90%,94%,96%,100%{transform:scaleY(1)}92%,95%{transform:scaleY(.1)}}
@media (prefers-reduced-motion:reduce){.sp,.sp .body,.sp .eyes,.sp .dots circle{animation:none!important}}
```
  (Keep the eyes' existing transform-box/origin so scaleY blinks in place.)
- Small-size drawing branch inside spool(): `const sm=size<=44; const o=sm?2.6:1.6, fw=sm?2.6:1.8, er=sm?3.2:2.3;` o = every ink outline stroke-width, fw = face strokes, er = eye radius; when sm drop the barrel band path (`M14 18.5h28M14 38h28`). Small-size cues outside the barrel: proud = mustard spark `<path d="M50 -1v10M45 4h10" stroke="#E3A72F" stroke-width="2.4" stroke-linecap="round"/>`; stitched = tick `<path d="M46 2l3 3 6-7" fill="none" stroke="#2A2119" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`. (Make sure the svg viewBox/overflow:visible lets these show.)
- Props on-model: waiting needle `<path d="M41 9 L55 -5 L57 -7 L55 -3 Z" fill="#C9CCD1" stroke="#2A2119" stroke-width="1.2" stroke-linejoin="round"/>`; sleepy z's as paths `<path d="M47 1h5l-5 6h5M55 -7h4l-4 5h4" fill="none" stroke="#2A2119" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`; oops frayed tail visible below the flange `M14 40 l-4 1.5 l2 3 l-4.5 1 l2 3 l-5 1`.
- Sizes only 30 / 44 / 96. One spool per screen. Small "from Clair" marks on cards use the chalk icon, not a spool.

### Mobile baseline (every phone page you own)
```html
<meta charset="utf-8">  <!-- first in head -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<meta name="theme-color" content="#F4EEE1"><meta name="color-scheme" content="light">
```
```css
html{-webkit-tap-highlight-color:transparent;-webkit-text-size-adjust:100%}
html,body{overscroll-behavior:none}
button,a,[role="button"]{touch-action:manipulation}
input,textarea,select{font-size:16px}           /* no iOS focus zoom; never maximum-scale */
/* long-press targets: */ .pb,.qp,.chip,.grip,.swrow{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
.chips{overscroll-behavior-x:contain;scroll-snap-type:x proximity;scroll-padding-inline:16px}
.chips>*{scroll-snap-align:start}
```
- Every `:hover` rule wrapped in `@media (hover:hover) and (pointer:fine){…}`.
- `document.addEventListener('touchstart',()=>{},{passive:true})` so iOS applies :active.
- Pinned bar: `bottom:max(18px, env(safe-area-inset-bottom,0px))`; sheets `padding-bottom:calc(16px + env(safe-area-inset-bottom,0px))`; toast `bottom:calc(92px + env(safe-area-inset-bottom,0px))`.
- Press feedback (120ms EASE): buttons and chips `:active{transform:scale(.97)}`; patches `.qp:active{transform:scale(.98)}`; pinned-bar cells darken instead of scale (`box-shadow:inset 0 0 0 100px rgba(42,33,25,.07)`); full-width rows (swipe rows, Next-up rows) get `:active{background-color:#F7F1E6}`, no scale.
- Hold (Snap/Ask and rows): one hold time 450ms. On pointerdown add `.holding`; Snap/Ask shows a light fill `::after` (rgba(251,246,236,.22), clip-path inset(0 100% 0 0) → inset(0), 330ms linear after a 120ms delay, so quick taps never show it). On fire: `navigator.vibrate?.(10)`, remove .holding; navigation happens on pointerup (not mid-hold), focus the search input synchronously in that handler. Clear on pointerup/leave/cancel. Prevent `contextmenu` on hold targets. Snap/Ask should be a <button>.
- Scroller ends: `mask-image:linear-gradient(to bottom,#000 calc(100% - 24px),transparent)` on the main scroller, padding-bottom ≥ 24px beyond the bar clearance. (No blur anywhere.)

### Reduced motion (everywhere)
No movement; 120ms opacity fades only. Sheets: `transform:none; opacity 0↔1 120ms; visibility hidden when closed`. Toasts: no translate. Springs jump. Threads/rolls off. Spool: face only.

### Visual system (taste)
- Section labels: Hanken Grotesk 13px/600, letter-spacing 0, #665847, sentence case written in the source ("Needs your OK · 3", "Next up", "Your apps · 7", "To buy · 12", "Today · Fri 20 Nov", "Adding updates 3 apps", "What Clair can read"). Counts may be DM Mono. No tracked caps anywhere.
- Text floor 13px everywhere (meta, tags, captions, patch names, "stale/why" lines). Row meta 13px #665847. "Just changed" tag 13px, padding 2px 8px, radius 4px.
- Pinned-bar labels 13px/600 letter-spacing 0, no ellipsis, nowrap; Snap/Ask cell `flex:0 0 64px`, pins `flex:1`. If any label still clips at 390, drop to 12px/600 +.01em and say so.
- Row titles 16px/500 #2A2119. Clair chat bubbles 16px. Sentences people read in ink #2A2119; ink2 only for meta.
- DM Mono ONLY for numbers/figures. Clair's lines ("I read 8 items…") in Hanken 15px/500 #22396F.
- One link look: `font:600 15px 'Hanken Grotesk'; color:#22396F; text-decoration:none; min-height:44px; display:inline-flex; align-items:center`; trailing › only for navigation.
- Buttons: primary/secondary `min-height:48px; padding:0 20px; border-radius:12px; font-size:16px; font-weight:600`. Secondary always `background:transparent; box-shadow:inset 0 0 0 1.5px #BFAE90`. One filled primary per view (the pinned bar's Snap/Ask is chrome and doesn't count, but an inline denim "Scan a receipt" right above it becomes a secondary).
- Radius scale 4 (tags, bars) / 8 (day cells, swatches, small tiles) / 12 (buttons, inputs, chips, search) / 16 (cards, dock, tiles) / 22 (sheet top only).
- Spacing on a 4px scale: 3,5→4; 6→8; 10→12; 13,14→12 or 16; 18→16; 22→24. Card padding 12px 16px; screen column gap 16.
- Bricolage tracking: ≥40px -.035em; 28-36px -.025em; 20-24px -.015em; ≤17px -.005em.
- App dyes by NAME: Budget #D3ECE7, Groceries #DDEBD2, Calendar #DCE4F3, To-dos #FBEBC4, Workout #F8DCC2, Classes #E7EBC2, Subscriptions #EADCF0, Meals #F3DCE0.
- Times "6 pm", "5:41 pm" (nbsp between number and unit); dates "Sun 22 Nov".
- Sentence case for tabs/tiles/notes ("Today", "Log", "This week", "Most used first", "From every app").
- No streaks: Workout's tiles become "12,450 lb lifted this week · 2 new bests" (or two tiles without streak).
- Each screen's title is an <h1>; screens with no visible title get one ("Settings" on You, "Ask Clair" on Clair).

## B. Work split

### F1 · workbench-motion.html (owner: motion study + canonical mascot)
Tokens + easing everywhere (remap: roll 280→T.state; dropTag 150→T.stateOut+EASE; thread fade 400→T.layoutOut; chalk outline 300→T.layout; title 300→T.state; piece body 250→T.state; dye sweep 500→T.layout; .lead 420→--t-layout; fold offer 150→T.stateOut; data fade 150→T.state; all missing easings → EASE). `[hidden]{display:none!important}` (Stitch all 8 / Fix a row and control segments currently visible too early). Thread pull to section-A recipe (new curve, land at 70%, undo retracts toward source with T.focalOut EASE, not ease-in). `#rbtns{min-height:44px;align-items:center}`. Roll direction + tabular-nums on .odo. Spool CSS + drawing per section A (this file's spool() becomes canonical; keep signature spool(expr,size,play)). Build: `el.scrollIntoView({block:'nearest',behavior:RM?'auto':'smooth'})` before drawChalk; `#cstat` sticky (top:0; z-index:2; background muslin; padding 6px 0). Sew finale: stamp 0 → happy face +60ms → sleep 120 → dock insert → sleep 250 → toast. Working: drop infinite bob in the wait scenario, one 220ms stitch-dip (translateY 2px and back, ease-in-out, on outer svg) per row; keep bob only on the stationary 30px status spool. Many-apps FLIP: translate only (no non-uniform scale; if size changes >2% crossfade opacity T.state instead); new patches scale .96→1; the "Jump to a patch" input filters instantly (no flip per keystroke). Mobile baseline + RM (all RM durations 120, toast no translate). `.jump input` 16px, type=search enterkeyhint=search.

### F2 · quilt-home.html (owner: Home prototype)
Thread pull on "Add to 3 apps" (section A; sources = the 3 dye dots in the card's "Adding updates…" line; targets = pinned-bar pins Groceries/Budget/Calendar, top-centre of the icon; notch on landing; roll the status-line money $412→$376 downward-direction). Then card exits (opacity, translateY -8px, T.stateOut), measure-before/after FLIP of everything below (translate only, T.layout), next queue card enters (opacity, translateY 8px→0, T.state). Never a full render() mid-sequence. "N more" expand/collapse: FLIP the rest, new cards enter with 40ms stagger (max 2). Dyes by name (section A). Labels/type/buttons/links per section A (`.sect`, `.from`, `.tn .what b` 16px, `.morebtn` as the link look, pin labels, patch names 13px, `.qp .stale/.why` 13px). Spool: 44 caught-up, 96 day-one, chalk icon (14px) replaces the 18px card spools, play only on first entry. Snap/Ask hold → search (port from flows behaviour, section A). Press feedback, toast exit faster, mobile baseline, safe area, tabular-nums on `.qp .face` and status money, tracking tokens, scroller mask, `.find input` 16px type=search enterkeyhint=search, charset. Read workbench-motion.html's existing thread/roll code for reference only (F1 is editing it concurrently: do not edit it).

### F3 · quilt-flows.html (owner: build flow, search, rows, sheets)
- Row tap: open sheet from `click` (suppress if moved or long-press selected); scrim closes only on a pointerdown that starts on the scrim. (P0, currently opens-then-closes on touch.)
- Pull-down search (P0, broken on touch): touchstart records y when scrollTop<=0; touchmove (passive:false) preventDefault only while pulling down from the top, translate content by rubberband(dy), `.armed` at ≥64px (hint turns ink, label "Release to search"); touchend ≥64 → open search (content enters translateY(-16px)→0 + opacity, T.state); else spring back (.35). Keep the mouse pointer path and the visible "Pull down to search" button.
- Sheets: drag-to-dismiss from .grab (44px hit area via ::before) and the top 48px, and from the body when its scrollTop===0 moving down; 1:1 track, upward rubberband, scrim opacity follows; release by spring rule. `.sheet{overscroll-behavior:contain}`, `.scrim{touch-action:none}`. Closed sheets `visibility:hidden` (delay T.layoutOut) + `inert`. Exit T.layoutOut, enter T.layout; scrim same pattern with EASE. Chained sheets (tab menu → Stitches/History): swap content inside the open sheet (fade old 120, FLIP height 220, fade new) instead of close/reopen. On (pointer:coarse) focus the sheet heading (tabindex=-1), not the first input. max-height 82dvh where applicable.
- Swipe rows: start at 10px; 1:1 up to ±130 then rubberband; `.armed` at |dx|≥90 (right: moss bg white text; left: ink bg #FBF6EC text; inactive label opacity 0; vibrate 8 once); release via spring rule. Delete: fly to -width (spring .25 with release velocity), then collapse height to 0 over T.layoutOut, then splice+draw; Undo re-inserts height 0→h + opacity, T.state. Got it: spring back to 0 (.3), check fills moss (bg-color 120), then draw. pointercancel → animated return. pointerdown cancels running animation and grabs from live position. Long-press = 450ms, `.sel` bg transition 120. RM: no slide; opacity 120 then collapse.
- Snap/Ask hold per section A (fix: currently pointerup lands on re-rendered button and shows the camera toast; navigation on pointerup; focus #sq synchronously; add pointercancel).
- Arrange: read drop rect before clearing transform and seed FLIP with it; pick-up `.dragging` scale(1.02) 120ms; siblings shift live (translateY ±(h+gap), 220ms EASE) toward the target index; settle with spring .3; pointerdown cancels running FLIP.
- Layout preview pager: track #pv 1:1 (translateX(dx), opacity 1-|dx|/w*.4), release by pager rule; new layout enters from the side the swipe came from (translateX(±24px)→0 + opacity, T.state); re-render only #pv.
- b5 "Add to my apps": render the draft card `.st.basted` from the start; tap → remove .basted (220) → threads from each ticked connection row to #pdye (section A recipe) → goStep(5); b6 header enters (translateY 8→0 + opacity, T.state), "new" tag scale .96→1 + opacity. No 60ms basted flicker.
- Search: spool hop only on entering (not per keystroke). All spools via section-A spool CSS/signature.
- Tokens/easing remap (preview entrance 300→T.state, chalk 300→T.layout, piece 250→T.state, FLIP 350→T.layout, flash 900→T.focal+EASE, rip exit 200→T.layoutOut, snap-back T.state); toast exit; RM reactive; hover gating; inputs 16px; input hints (#tellIn enterkeyhint=send; #sq enterkeyhint=search autocapitalize=none; #dc autocapitalize=characters autocorrect=off spellcheck=false; #tname autocapitalize=words enterkeyhint=done); tabular-nums on `.big`; mobile baseline; safe area; chips scroller; scroller mask; type/buttons/links per section A where the flows file has its own copies.

### F4 · canvas generators: SP/tools/gen_all.py and SP/tools/gen_demo.py → regenerate the 19 generated boards
Section A visual system in the helpers (sect(), btn(), row(), bar(), patch(), card(), the shared CSS), so it lands everywhere: labels, 13px floor, row titles 16, chat 16, mono only on numbers, one link look (Budget "Corner Market receipt" gets the 44px box), buttons 48/r12/16/600 with secondary transparent+inset stitch (delete per-call height/radius/size overrides), radii scale, spacing scale, tracking tokens, tabular-nums on changing figures, dyes by name, time/date formats, sentence case (Workout tabs, tiles), no streak tile, h1 on every screen (add "Settings" on You, "Ask Clair" on Clair, etc.), Groceries/Empty inline camera button → secondary. Shared board CSS: hover gated, inputs 16px, tap highlight transparent, user-select/touch-callout on bar/patches, pinned bar bottom max(18px, env(safe-area-inset-bottom)), bar Snap/Ask as <button> (pins may stay links), press feedback :active rules (120ms EASE) and `.st{transition:background-size 220ms var(--ease)}`, scroller mask at the bottom, sheet (EditItem) padding-bottom with safe-area calc. Spool drawings in boards: apply section-A small-size branch + props to the board spool() helper. Then regenerate (check how gen scripts are invoked: read their __main__/argv) and re-apply SP/tools/fix_all.py ONLY if regeneration would undo its dye swap (it edits gen_all.py's DYE dict already, so likely not needed; Main/Calendar are not yours). Do NOT touch Main.dc.html, DesignSystem.dc.html, Spool.dc.html, canvas.json, support.js.

### F5 · hand-written boards: Main.dc.html, DesignSystem.dc.html, Spool.dc.html (project folder)
- Main: section A visual system (labels, type, buttons, links, radii, tracking, tabular-nums on faces/status money, dyes by name, times), `justAdded` toast absolute (left:12px; right:12px; bottom:92px), bar like F4's bar (Snap/Ask <button>, safe-area bottom), hover gating, h1.
- DesignSystem: make it the source of truth for everything in section A. Add a "Motion" block after "States: the stitch alphabet" (copy the Spool board's 70px/1fr grid markup): 120 feedback (press scale .97) · 220 state · 350 layout (FLIP translate only) · 600 thread pull, the one focal (its own curve .45,0,.15,1; lands at 70%) · exits 140/220/360 · ease cubic-bezier(.16,1,.3,1), no bounce · gesture release: critically damped spring, no overshoot, carries finger speed · hold 450ms with fill · reduced motion: no movement, 120ms fades, spool face only. Update "Pieces"/type/radius/spacing specs to section A (button 48/r12/16/600, link look, label style, 13px floor, radius scale 4/8/12/16/22, 4px spacing, tracking tokens, tabular nums for changing figures). Its own labels follow the new label style.
- Spool: redraw per section A (small-size branch, cues, props), relabel per section A type rules (captions 13px, no mono prose), motion captions match the new hop/shake/bob/blink values (hop 5px on the outer svg, shake ±3px, bob 2px, blink only while working, irregular). Show all 8 at 30/44/96.
- Do NOT touch generated boards, canvas.json or support.js.

## C. Done = verified
Each agent: render its files locally (own port: F1 8781, F2 8782, F3 8783, F4 8784, F5 8785; scripts/shots under SP/polish/fix-<Fn>/), one batched check + at most one confirm round:
- No console errors; no horizontal overflow at 390; all controls ≥44px (except edge-bleed chip scrollers and text links inside a sentence);
- For prototypes: replay the changed interactions with Playwright (touch context: isMobile, hasTouch, 390x844, CDP touch events for gestures), and once with reducedMotion:'reduce'; capture a few frames of the thread pull.
- Report back: what changed (by spec item), what you verified and how, anything you skipped or couldn't apply and why. Keep it under 40 lines.

## D. Decision Nov 19: Snap/Ask becomes the Clair button (supersedes every Snap/Ask item above)

Why: a camera button says "Quilt is for receipts". The main button is Clair: one place to put anything in or ask anything, and it can land in several apps. The receipt is one example of that, not the product.

### The button (pinned bar, right cell, everywhere)
- Same 64px ink cell (#2A2119, paper text #FBF6EC, radius 0 16px 16px 0). Glyph: a FACELESS spool outline (barrel + two flanges + a thread tail), 20px, paper stroke 1.8. Label "Clair" 13px/600. It is a mark, not the character: it does not count against "one spool per screen" and never animates except press feedback.
- aria-label "Clair: type, talk or add a photo. Hold to talk".
- Tap: the Clair sheet rises from the bar (transform-origin bottom right; translateY + opacity, T.layout EASE; exit T.layoutOut). Hold 450ms (same fill + vibrate as before): opens the sheet straight in Talk mode, listening while held; release = send; slide up 60px+ while holding = cancel ("Release to cancel").
- On canvas boards (stills) the cell is `<a class="pb" href="ClairSheet.dc.html" role="button">` (support.js only routes <a>).
- Search no longer lives on the hold. Search = pull-down (unchanged) + the Search board. Questions go to Clair.

### The Clair sheet (states)
1. Start: 44px spool "hello" (the screen's one spool) + h2 "Tell Clair anything". Text field (16px, placeholder "Spent $12 on lunch, gym tomorrow 6 pm…", enterkeyhint send; NOT auto-focused on touch). Row of three 48px chips: Talk (mic), Photo (camera), File (paperclip). "Try" list, three suggestions that change by time of day, one of each kind: capture ("Spent $12 on lunch"), ask ("Can I afford $60 concert tickets?"), build ("Track my plants"). Footer link "Open chat ›" (Clair board).
2. Talk: spool "waiting"; a running-stitch line whose stitch lengths pulse with voice level (the waveform IS stitches; under RM a static line + "Listening" text); live transcript in 20px Bricolage; hint "Release to send · slide up to cancel".
3. Capture result (from type/talk "spent $12 on lunch, gym tomorrow 6 pm"): spool "thinking" → then a basted proposal card per destination: "Budget · Eating out · $12" and "Calendar + Workout · Gym · Fri 21 Nov, 6 pm". Primary "Add to 3 apps" (count = apps touched), secondary "Edit". Confirm = the signature thread pull from the cards to the pins, then sheet closes and Home shows tags. Nothing saves before OK.
4. Ask result ("Can I afford $60 concert tickets?"): answer card in ink 16px: "Yes. $376 left until 1 Dec; after $60 you'd have $316, about $26 a day." + source chips (dye dot + app name: Budget, Calendar) + action "Add to Budget as planned".
5. Photo: camera → existing Receipt flow (Review receipt). File/Share: attachment preview row.
### Share into Quilt
OS share sheet → Quilt → Clair sheet opens with the item attached (e.g. "Syllabus · ECON 1010.pdf, 4 pages"), spool "working" while reading, then: "Found 6 due dates and 2 exams. Add to Classes and Calendar?" with a basted list preview (3 rows + "3 more"), primary "Add to 2 apps".
### Clair asks you first (check-in)
In Home's "Needs your OK" queue, an evening card: "3 things from today" (e.g. "Lunch $12 from Apple Pay", "Gym logged? 6 pm passed", "Hulu renews Fri") with "Review" primary. Same one-card-at-a-time rule.
### Copy
Replace "Snap/Ask", "snap anything", "Hold to ask Clair or search" everywhere with Clair wording: Welcome/day one "Tell Clair anything: type, talk or add a photo". No pronoun for Clair in UI copy except Clair's own first-person lines.

### Work split for this round
- G1 (boards): gen_all.py/gen_demo.py: bar() SNAP cell → Clair button; new generated boards ClairSheet (state 1), ClairTalk (state 2), ClairResult (state 3 on top, state 4 below in the same scroll or as a toggle in the board's DCLogic), ClairShare (share state); Welcome/Search/any copy. Main.dc.html: bar cell + check-in card as a queued item. DesignSystem.dc.html + Spool.dc.html: rules text for the button (faceless spool mark, tap/hold), the "talk" stitch waveform. canvas.json: add the 4 boards as a new row "Clair: tell, talk, ask, share" (follow the layout pattern in SP/tools/layout_canvas.py: 470px x-step, 390x844, row title note 300px above; put the row after row 1, shift later rows + Laptop + their title notes down 1300px), update the "screens"/"flows" notes (Demo path: Home > Clair > Photo > Review receipt…). Section A rules apply. Verify as section C.
- G2 (prototypes): quilt-home.html and workbench-motion.html: Clair button, sheet with states 1-5 interactive (typing a capture or tapping a suggestion runs the result; capture confirm = thread pull to pins; Photo → existing receipt card in the queue / receipt path), hold-to-talk with a simulated transcript, check-in card in Home queue, share demo reachable from the Home demo-state switcher. workbench-motion: dock cell only.
- G3 (after F3 finishes): quilt-flows.html: replace Snap/Ask with the Clair button + sheet (states 1-3 minimum), keep pull-down search.
