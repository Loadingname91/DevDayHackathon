# Screens CSS: every component on the canvas boards, with its exact declarations

Captured Fri 20 Nov 2026 from the design canvas (https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P, version `1795159780-3894`, page "Screens", 40 boards, already in the Mint colours of ADR-013). The full machine inventory (every inline style with counts, every state style, every colour) is `design/board-css-inventory.md`, written by `design/tools/board_css.py`; rerun it when the canvas changes. `design/DESIGN.md` says why; this file says exactly what.

Values below are as the boards write them. In code, use the token in the right-hand column, never the hex: the tokens in `web/src/styles/tokens.css` produce these colours in light mode and the matching dark ones.

## 1. Colours as the boards render them

| Board value | Role | Token |
| --- | --- | --- |
| `#EAF8F2` | Ground (plain, no gradient), sheet ground | `--ground` |
| `#0F241E` | Ink: text, primary button, "just changed" pill, Clair tile, overdue tag | `--ink`, `--cta` |
| `#475E56` | Meta text, section labels, unchecked ring, thread line | `--sec` |
| `#A5B5AF` | Stitch line: row separators, secondary button and chip edges, grabber, waveform rest | `--line` |
| `#00665D` | Accent: selected chip edge, tab underline, focus ring, switch on, credits meter, chalk edge | `--focus` |
| `#005652` | Link text, chalk text | `--focus` (text use) |
| `#FFFFFF` | Inputs, chips, secondary surfaces, the "+" patch | `--card` |
| `rgba(255,255,255,.78)` + inset `rgba(255,255,255,.95)` | Card (`.st`) | `--card` + `--card-line` |
| `0 12px 28px -16px rgba(10,40,34,.32)` | Card shadow | `--shadow` |
| `#E4EEEA` | Pressed row (`.rw:active`), Talk/Photo/File grounds | `--hair` |
| `#DCE8E3` | Bar and meter track, your words in Clair (bubble) | `--hair` (track), `--said` (bubble) |
| `#E6ECF7` | Selected chip ground | `color-mix(in oklch, var(--focus) 12%, transparent)` |
| `#BFE8DF` | Text selection | `--said` |
| `rgba(15,36,30,.07)` | Pressed pin cell | `color-mix(in oklch, var(--ink) 7%, transparent)` |
| `rgba(15,36,30,.42)` dashed | Basted card edge | `--thread` |
| `rgba(15,36,30,.45)` | Dye-dot ring, patch stitch | `color-mix(in oklch, var(--ink) 45%, transparent)` |
| `rgba(15,36,30,.32)` | Scrim | `--scrim` |
| `#D9B98F`, `#C9CCD1` | Spool flanges, needle | spool only (fixed) |
| `#5B7DB1`, `#8DB580`, `#9C6BA8` + ink | The "quilt" logo squares | logo only (fixed) |

**App fills (patch / pin tile) and deep tones (pin icon, progress, done):** Budget `#ADE2CA` / `#006344` · Groceries `#D3F5DB` / `#1B6236` · Calendar `#BBE6F6` / `#005D7A` · To-dos `#E0F7D5` / `#395E21` · Workout `#C5F6FB` · Classes `#AED7F5` · Subscriptions `#B2E2E2`. In code: `[data-dye] --fill / --deep`.

## 2. The shared stylesheet (every board but Home's older copy)

```css
:root{--ease:cubic-bezier(.16,1,.3,1);--ease-thread:cubic-bezier(.45,0,.15,1);--t-fb:120ms;--t-state:220ms;--t-layout:350ms;--t-focal:600ms;--t-state-out:140ms;--t-layout-out:220ms;--t-focal-out:360ms}
html{-webkit-tap-highlight-color:transparent;-webkit-text-size-adjust:100%}
html,body{overscroll-behavior:none}
a{color:#0F241E;text-decoration:none}
@media (hover:hover) and (pointer:fine){a:hover{color:#475E56}a.lk:hover{color:#00665D}}
button,a,[role="button"]{touch-action:manipulation}
input,textarea,select{font-size:16px}
.pb,.qp,.chip,.grip,.swrow{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
.chips{overscroll-behavior-x:contain;scroll-snap-type:x proximity;scroll-padding-inline:16px}
.chips>*{scroll-snap-align:start}
.btn,.chip,.qp{transition:transform var(--t-fb) var(--ease)}
.btn:active,.chip:active{transform:scale(.97)}
.qp:active{transform:scale(.98)}
.pb{transition:box-shadow var(--t-fb) var(--ease)}
.pb:active{box-shadow:inset 0 0 0 100px rgba(15,36,30,.07)!important}
.rw{transition:background-color var(--t-fb) var(--ease)}
.rw:active{background-color:#E4EEEA!important}
.scr{mask-image:linear-gradient(to bottom,#000 calc(100% - 24px),transparent)}
.lk{font:600 15px 'Figtree',system-ui,sans-serif;color:#005652;min-height:44px;min-width:44px;justify-content:center;display:inline-flex;align-items:center;gap:4px}
.num{font-variant-numeric:tabular-nums}
.qp{border-radius:22px;box-shadow:0 12px 28px -18px rgba(10,40,34,.4)}
body{font-variant-numeric:tabular-nums}
::selection{background:#BFE8DF;color:#0F241E}
a:focus-visible,button:focus-visible{outline:3px solid #00665D;outline-offset:3px}
.st{background-color:rgba(255,255,255,.78);border-radius:22px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.95),0 12px 28px -16px rgba(10,40,34,.32);transition:outline-color var(--t-state) var(--ease);outline:1.5px solid transparent;outline-offset:-7px}
.st.basted{outline:1.5px dashed rgba(15,36,30,.42)}
.chalk{position:relative;background:rgba(0,102,93,0.06);border-radius:22px;outline:2px dotted rgba(0,102,93,0.7);outline-offset:-3px}
@media (prefers-reduced-motion:reduce){.btn,.chip,.qp,.pb,.rw,.btn:active,.chip:active,.qp:active{transform:none}}
```

Class meanings: `.st` card (stitched surface) · `.st.basted` waiting for OK · `.chalk` Clair's idea · `.pb` pinned-bar cell · `.qp` quilt patch · `.rw` tappable row · `.btn` button · `.chip` chip · `.lk` link · `.scr` the scrolling column (fades its last 24 px) · `.num` tabular figures.

Two boards add their own: **ClairTalk** `.wave` (the listening line: 3 px stitches in ink, `scaleX(.4 → 1)` over 760 ms alternate, the two end stitches still in `#A5B5AF`), **OnMaking** `.mk` (a starter app appears: `opacity 0, scale(.92)` → 1 over 350).

## 3. Page frame

| Part | Declarations | Boards |
| --- | --- | --- |
| Screen | `width: 390px; height: 844px; position: relative; overflow: hidden; background-color: #EAF8F2; color: #0F241E; font-family: 'Figtree', system-ui, sans-serif` | all 38 phone boards |
| Scrolling column (`.scr`) | `position: absolute; inset: 0 0 96px 0; overflow-y: auto; padding: 44px 16px 24px; box-sizing: border-box; display: grid; grid-template-columns: minmax(0, 1fr); align-content: start; gap: 16px` (bottom inset 110 / 150 / 160 when an action row or add field is pinned) | 15 |
| Laptop | `grid-template-columns: 240px minmax(0, 1fr) 320px`; left column has a dashed right edge (`linear-gradient(0deg, #A5B5AF 58%, transparent 0)` 1.5 × 8 px, repeat-y); main `padding: 26px 30px; gap: 16px`; detail column `background: #FFFFFF; padding: 26px 24px` | Laptop |

## 4. Headers

| Component | Declarations | Boards |
| --- | --- | --- |
| Top row | `display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 44px` | 12 |
| Back chevron | `width: 44px; height: 44px; margin-left: -12px; display: grid; place-items: center`; icon 22 px, stroke 1.8, ink | 20 |
| Right action | `···` 44 × 44 bold, letter-spacing 2px (app menu) · or `.lk` ("Finish", "Cancel") · or a 44 px spacer `width: 44px` to keep the title centred | Workout, Session, Search, You |
| Focused-screen title (centred in the top row) | `margin: 0; font-weight: 700; font-size: 17px; letter-spacing: -0.005em` | Settings, Log a set, New reminder, What Clair remembers, Preview |
| App identity row | `display: flex; align-items: center; gap: 12px; flex-wrap: wrap` | 8 |
| App icon tile | `width: 36px; height: 36px; border-radius: 12px; background: <app fill>; display: grid; place-items: center; flex: none`; icon 18 px in ink | Workout, Groceries, Budget, Calendar, To-dos, Empty, Preview |
| App title (h1) | `margin: 0; font-weight: 700; font-size: 28px; letter-spacing: -0.025em; line-height: 1.05` | 12 |
| Status sentence | `margin: 0; font-size: 16px` with figures in `<b class="num">`; Home's is `font-size: 17px; line-height: 1.35` | Groceries, To-dos, Calendar, Home |
| "new" next to the title | the pill tag (section 9) | Empty |
| "Connected to" line | `13px #475E56`, then each app as a 10 px dye dot + name | Empty |
| Home top | logo `display: flex; gap: 8px; align-items: center; font-weight: 700; font-size: 17px; letter-spacing: -0.005em` (22 px four-square mark + "quilt"); avatar `width: 44px; height: 44px; border-radius: 50%; background: #C5F6FB; display: grid; place-items: center` | Home, Clair boards |
| Greeting | `margin: 0; font-weight: 700; font-size: 30px; letter-spacing: -0.025em; line-height: 1.05` | 7 |
| Clair chat header | fixed top, `padding: 40px 16px 12px; background: #EAF8F2` with a dashed bottom edge; spool 44 + title 17 / 700 + "Answers from your apps only" 13; credits as `.lk` | Clair |

## 5. Tabs

| Component | Declarations | Boards |
| --- | --- | --- |
| Tab list | `display: flex; gap: 2px; overflow-x: auto; margin: 0 -16px; padding: 0 12px; scrollbar-width: none; background-image: linear-gradient(90deg, #A5B5AF 58%, transparent 0); background-size: 8px 1.5px; background-repeat: repeat-x; background-position: 0 100%` | Workout |
| Tab | `flex: none; min-height: 44px; min-width: 44px; padding: 0 12px; border: 0; border-radius: 0; background: transparent; font-size: 15px; color: #475E56` | Workout |
| Selected tab | `color: #0F241E; font-weight: 600; box-shadow: inset 0 -2.5px 0 #00665D` | Workout |

Apps with one page have no tab list (Groceries, Budget, Calendar, To-dos).

## 6. Cards and sections

| Component | Declarations | Boards |
| --- | --- | --- |
| Section label | `display: flex; justify-content: space-between; gap: 8px; font-size: 13px; font-weight: 600; letter-spacing: 0; color: #475E56`; right-hand meta in `font-weight: 500` (or 400) | 28 |
| Card of rows | `.st` + `padding: 4px 16px` (rows inset) or `padding: 4px 0` (full-width row buttons with their own `padding: 8px 16px`) | 10 |
| Content card | `.st` + `padding: 16px; display: flex; flex-direction: column; gap: 8px` | Workout, Budget, Session |
| Compact card | `.st` + `padding: 12px 16px; display: flex; flex-direction: column; gap: 8px` (or `align-items: center; gap: 12px` in a row) | Rule, You, Preview |
| Basted card | `.st.basted` + `padding: 12px 16px; display: flex; flex-direction: column; gap: 8px` | 15 |
| Card line on a basted card | eyebrow `13px / 600 #475E56` ("From your receipt photo · 5:41 pm") · title `<b style="font-size: 16px">` with the amount right in `15px` tabular · meta `13px #475E56` · delta line "Budget ~~$412~~ → **$376** left" 16 px | Home, Clair result |
| Chalk card | `.chalk` + `padding: 12px 16px; display: flex; flex-direction: column; gap: 8px`; first line: 16 px chalk-triangle mark (`fill rgba(0,102,93,.16)`, stroke `#00665D` 1.8) + 13 / 600 label; then `font-size: 15px; font-weight: 500; color: #005652` | Rule, Search, Workout, Clair ask |
| Empty state card | `.st` centred, `padding: 24px 16px`: spool 96 hello, "<App> is ready" 20 / 700, one 16 px sentence; then a stack of secondary buttons with icons | Empty |
| Paragraph | `margin: 0; font-size: 16px; line-height: 1.45` | 7 |

## 7. Rows

| Component | Declarations | Boards |
| --- | --- | --- |
| Row | `display: flex; align-items: center; gap: 12px; min-height: 56px` (agenda 58, activity 62, notes 64, receipt lines 52) | 16 |
| Separator (every row after the first) | `background-image: linear-gradient(90deg, #A5B5AF 58%, transparent 0); background-size: 8px 1px; background-repeat: repeat-x` | 13 (state style) |
| Row text block | `flex: 1; display: flex; flex-direction: column; min-width: 0` | many |
| Row title | `font-size: 16px; font-weight: 500; color: #0F241E` | 16 |
| Row meta | `font-size: 13px; color: #475E56` | 28 |
| Row amount | `font-size: 14px; font-variant-numeric: tabular-nums` (15 on cards) | Budget, Search |
| Row chevron | 18 px `M9 6l6 6-6 6`, stroke 1.8 | You |
| Row delete | `flex: none; width: 44px; height: 44px; margin-right: -8px; border: 0; border-radius: 16px; background: transparent; display: grid; place-items: center`; trash 20 px | What Clair remembers |
| Dye dot ("From Workout") | `flex: none; width: 10px; height: 10px; border-radius: 50%; background: <app fill>; box-shadow: inset 0 0 0 1.5px rgba(15,36,30,0.45)` then `font-size: 13px; color: #475E56` | Calendar, Home, Clair ask, Laptop |
| Check circle | `flex: none; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center` + off `box-shadow: inset 0 0 0 1.5px #475E56` / on `background: #006344` with a 14 px white tick (stroke 2.4) | To-dos, Groceries, Home check-in |
| Done title | `font-size: 16px; font-weight: 500; text-decoration: line-through; color: #475E56` | To-dos, Groceries, You |
| "usual" mark | `display: inline-flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600; color: #475E56` with a 14 px repeat icon | Groceries |

## 8. Buttons, links, fields, chips

| Component | Declarations | Boards |
| --- | --- | --- |
| Primary | `.btn` + `min-height: 48px; padding: 0 20px; border-radius: 99px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-weight: 600; font-size: 16px; border: 0; background: #0F241E; color: #FFFFFF` | 15 |
| Secondary | the same with `background: transparent; box-shadow: inset 0 0 0 1.5px #A5B5AF; color: #0F241E` | 15 |
| Button pair | grid `1fr 2fr` (Skip · Log set 2), `1fr 1.6fr` (Cancel · Save reminder), or flex with `flex: 1.6` on the primary (Add to 3 apps · Review items) | Session, Rule, Home |
| Pinned action row | `position: absolute; left: 16px; right: 16px; bottom: 30px` (no bar on that screen) | Session, Rule, Preview |
| Link (`.lk`) | `600 15px #005652; min-height: 44px`; `›` only when it goes somewhere; on its own line `align-self: flex-start; margin: -8px 0` | Home, Budget, Clair |
| Field | `min-height: 44px` (48 in Clair and search); `border: 0; border-radius: 16px; background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #A5B5AF; padding: 0 12px; font-size: 16px; color: #0F241E` | EditItem, Clair, Search |
| Focused field | `box-shadow: inset 0 0 0 2px #00665D` | Search |
| Field label | `display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #475E56` | EditItem |
| Add field, pinned | `position: absolute; left: 16px; right: 16px; bottom: 96px; display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 4px 0 16px; border-radius: 16px; background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #A5B5AF; font-size: 16px; color: #475E56` + a 40 px round ink + | To-dos |
| Find field | `display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 12px; border-radius: 16px; background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #A5B5AF; font-size: 16px; color: #475E56` with a 16 px magnifier | Home, Your apps |
| Chip | `flex: none; min-height: 44px; padding: 0 12px; border-radius: 16px; border: 0; font-size: 13px–14px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px` + `background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #A5B5AF; color: #0F241E` | Groceries, Search, Clair |
| Selected chip | `background: #E6ECF7; box-shadow: inset 0 0 0 1.5px #00665D; color: #005652` | Groceries, Search, Fridge, Slips |
| Chip count | `<span class="num" style="font-weight: 600">4</span>` after the name | Groceries |
| "New list" chip | chip with `color: #005652` and a + icon | Groceries |
| Icon button (Talk) | chip at `width: 48px; min-height: 48px; padding: 0` | Clair ask |
| Talk / Photo / File | `flex: 1; min-height: 44px; border-radius: 16px; font-size: 15px; font-weight: 600` + secondary edge, icon 20 | ClairSheet, ClairPhoto |
| Stepper | frame `display: flex; align-items: center; justify-content: space-between; border-radius: 16px; box-shadow: inset 0 0 0 1.5px #A5B5AF; padding: 2px`; − / + `.btn` `width: 44px; height: 44px; border: 0; border-radius: 12px; background: #E4EEEA; font-size: 18px`; value `font-size: 18px; font-weight: 700; tabular`; label above `13px #475E56` | Log a set |
| Switch (large, Rule / Connect) | `flex: none; width: 60px; height: 44px; padding: 9px 4px; border: 0; background: transparent; display: flex; align-items: center; border-radius: 22px; background-clip: content-box; box-shadow: inset 0 0 0 50px <#00665D on / #A5B5AF off>`; knob 26 px white; `justify-content: flex-end` when on | Rule, Connect |
| Switch (small, settings) | track `width: 48px; height: 28px; border-radius: 22px; padding: 2px; display: flex` on `background: #00665D; justify-content: flex-end` / off `background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #475E56`; knob `24px; border-radius: 16px` on white / off `#475E56; transform: scale(.75)` | What Clair remembers |
| Radio card | `.st` + `padding: 12px 16px; display: flex; gap: 12px; align-items: flex-start`; radio `20px; accent-color: #00665D`; title `16 / 600`, sub `13 #475E56` | You |

## 9. Tags, bars, figures

| Component | Declarations | Boards |
| --- | --- | --- |
| "just changed" | `font-size: 13px; font-weight: 600; padding: 2px 8px; background: #0F241E; color: #FFFFFF; border-radius: 99px; white-space: nowrap` | 8 |
| Status tag ("Overdue · 2 days") | the same with `border-radius: 4px` | To-dos |
| Timer tag ("Rest 0:47") | `font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: <app fill>; tabular` | Log a set |
| "example" tag | `font-size: 13px; padding: 2px 8px; border-radius: 6px; box-shadow: inset 0 0 0 1.5px #A5B5AF; color: #475E56` | Preview |
| Bar | `height: 8px; border-radius: 4px; background: #DCE8E3; overflow: hidden` (7 in Budget's list, 6 on laptop and in Log a set, 10 for the credits meter); fill `height: 100%; background: <app deep>; border-radius: 4px` | Budget, Workout, You |
| Over a limit | fill `position: absolute; inset: 0 auto 0 0; width: <limit share>%` + excess `position: absolute; inset: 0 0 0 auto; width: <excess>%; background: repeating-linear-gradient(45deg, #0F241E 0 1.3px, transparent 1.3px 4px), repeating-linear-gradient(-45deg, #0F241E 0 1.3px, transparent 1.3px 4px)`; note `13px #475E56` ("$15 over.") | Budget, Clair ask |
| Hero figure | `font-weight: 700; font-size: 44px; letter-spacing: -0.035em; line-height: 1; tabular` (46 on laptop) + `font-size: 14px; color: #475E56` ("left of $1,200") | Budget, Laptop |
| Figure tile | `.st` + `padding: 12px 16px; display: flex; flex-direction: column; gap: 4px`; label `13px #475E56`; value `font-size: 18px; font-weight: 600; white-space: nowrap; tabular` | Workout |
| Credits figure | `font-weight: 700; font-size: 30px; letter-spacing: -0.025em` + `13px #475E56` | You |
| Large card title | `font-weight: 700; font-size: 30px; letter-spacing: -0.025em` ("Pull day") · `22px / -0.015em` ("Lat pulldown") | Workout, Log a set |
| Progress line ("Exercise 2 of 5 … 27%") | `display: flex; justify-content: space-between; font-size: 13px; color: #475E56` over a 6 px bar | Log a set |

## 10. Calendar

| Component | Declarations | Boards |
| --- | --- | --- |
| Day strip | `display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px` | Calendar |
| Day cell | `display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 8px 0; border-radius: 12px`; day initial `13px`; date `<b>` `15px` tabular; dots `13px; min-height: 12px` ("•••", one per item) | Calendar |
| Today / selected cell | `background: #0F241E; color: #FFFFFF` | Calendar, Preview |
| Other cell | `background: #FFFFFF; color: #0F241E; box-shadow: inset 0 0 0 1px #E6DCC8` (use `--line`) | Calendar |
| Agenda day | section label ("Today · Fri 20 Nov") over a card of rows (`padding: 4px 16px`) | Calendar |
| Agenda row | row at `min-height: 58px`: title `16 / 500` (+ "just changed"), `From <App>` with its dye dot, time right `font-weight: 600; font-size: 13px; color: #475E56; tabular` | Calendar |
| Small week (renewals) | cells `padding: 8px 0; border-radius: 12px; font-size: 13px; tabular`, off `background: #E4EEEA; color: #475E56`, marked `background: #0F241E; color: #FFFFFF`; 7 px dot | Preview |

## 11. Home

| Component | Declarations | Boards |
| --- | --- | --- |
| Queue | section label "Needs your OK · 4" → one basted card → `.lk` "Show 3 more" | Home |
| Next up | list `position: relative; display: flex; flex-direction: column; padding-left: 22px`; thread `position: absolute; left: 6px; top: 14px; bottom: 14px; width: 2px; background: linear-gradient(0deg, #475E56 55%, transparent 0) 0 0 / 2px 8px repeat-y`; item `display: grid; grid-template-columns: 80px minmax(0, 1fr); gap: 8px; align-items: center; min-height: 56px`; dot `position: absolute; left: 1px; top: 50%; width: 12px; height: 12px; margin-top: -6px; border-radius: 50%; background: <app fill>` with an ink ring; time column 16 px; title 16 / 500 over `<App> · meta` 13 | Home |
| Your apps label | "Your apps · 7" … "Most used first" (right, 400) | Home, Your apps |
| Quilt | `display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); grid-template-rows: repeat(4, 58px); gap: 6px`; placement fills the 6 × 4 with no holes, most used first (Budget `1/5 × 1/3`, Workout `5/7 × 3/5`, the rest 2 or 3 columns by 1 row) | Home |
| Patch (`.qp`) | `position: relative; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-start; padding: 8px 12px; box-sizing: border-box; overflow: hidden; background: <app fill>`; radius 22 and the patch shadow from `.qp` | Home, Your apps |
| Patch stitch | `position: absolute; inset: 6px; border: 1.5px dashed rgba(15,36,30,0.45); border-radius: 11px` | 9 |
| Patch name | `position: relative; display: flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600; line-height: 1.2; white-space: nowrap` with a 14 px icon | Home |
| Patch face | `font-weight: 700; line-height: 1.05; tabular` + big `font-size: 28px; letter-spacing: -0.025em` / small `font-size: 14px; letter-spacing: -0.005em` | Home |
| Patch tag | "just changed" at `position: absolute; top: 8px; right: 8px` on the big patch; a notch on small ones | Home |
| New app patch | white patch, centred +, `aria-label="New app: tell Clair what to track"` | Home |
| Just used row (Your apps) | patches 2 min / 20 min / 1 hour… in a scrolling row | Your apps |

## 12. Clair

| Component | Declarations | Boards |
| --- | --- | --- |
| Scrim | `position: absolute; inset: 0; background: rgba(15,36,30,0.32)` | 10 |
| Sheet | `position: absolute; z-index: 2; left: 12px; right: 12px; bottom: calc(92px + env(safe-area-inset-bottom, 0px)); max-height: calc(100% - 148px)` (or `top: 56px` for a full one); `background: #EAF8F2; border-radius: 22px; padding: 8px 16px 16px; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 12px 32px -16px rgba(15,36,30,0.6); transform-origin: 100% 100%` | 9 |
| Grabber | `flex: none; width: 40px; height: 4px; border-radius: 4px; background: #A5B5AF; align-self: center` | 9 |
| Sheet header | `flex: none; display: flex; align-items: center; gap: 12px`: spool 44 · `flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px` with the title `margin: 0; font-weight: 700; font-size: 22px; letter-spacing: -0.015em; line-height: 1.1` and a `13px #475E56` line · close × `flex: none; width: 44px; height: 44px; margin-right: -8px` | 9 |
| Sheet scroller | `flex: 1; min-height: 0; overflow-y: auto; margin: 0 -16px; padding: 0 16px 24px; display: flex; flex-direction: column; gap: 12px` | 4 |
| Your words | `align-self: flex-end; max-width: 85%; padding: 8px 12px; border-radius: 22px 22px 4px 22px; background: #DCE8E3; font-size: 16px; line-height: 1.4` | 3 |
| Data answer | `.chalk` card: answer `16 / 1.45` with the figure bold, a bar if it's money against a limit, "From" + source chips (dye dot + app name), a `.lk` to the app | Clair ask |
| General answer | `padding: 12px 16px; border-radius: 22px; background: #FFFFFF`; first line "General answer · not from your apps" with a book icon, 13 `#475E56` | Clair ask |
| Bottom input row | field `flex: 1; min-height: 48px` + a 48 px Talk icon chip | Clair ask |
| Listening | title "Listening" + "Hold the Clair button while you talk"; the `.wave`; transcript `font-weight: 700; font-size: 20px; letter-spacing: -0.015em; line-height: 1.3; min-height: 52px` with the unconfirmed tail in `#475E56`; hint row `min-height: 44px; 13 / 600 #475E56` "Release to send · slide up to cancel" | ClairTalk |
| Clair cell pressed (Talk) | an overlay `position: absolute; inset: 0; background: rgba(255,255,255,0.28)` on the Clair tile, `aria-pressed="true"` | ClairTalk |
| Toast | `position: absolute; left: 16px; right: 16px; bottom: 92px; z-index: 2; min-height: 52px; padding: 0 8px 0 16px; box-sizing: border-box; border-radius: 16px; background: #FFFFFF; box-shadow: inset 0 0 0 1.5px #A5B5AF, 0 8px 22px -14px rgba(15,36,30,0.55); display: flex; align-items: center; gap: 8px`; text `flex: 1; font-size: 15px; ellipsis`; Undo is a `.lk` | What Clair remembers |

## 13. Pinned bar

| Component | Declarations | Boards |
| --- | --- | --- |
| Bar | `position: absolute; left: 12px; right: 12px; bottom: max(18px, env(safe-area-inset-bottom, 0px)); height: 64px; display: flex; padding-block: 5px; padding-inline: 6px; box-sizing: border-box; border-radius: 26px; background: rgba(255,255,255,0.74); border: 1px solid rgba(255,255,255,0.95); backdrop-filter: blur(18px) saturate(1.4); box-shadow: 0 14px 30px -12px rgba(10,40,34,0.4)` (`z-index: 3` over a sheet) | 26 |
| Cell (`.pb`) | `flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border-radius: 20px` | 27 |
| Pin tile | `position: relative; overflow: hidden; width: 46px; height: 30px; border-radius: 13px; display: grid; place-items: center; background: <app fill>; color: <app deep>`; icon 19, stroke 1.8 | 27 |
| Current app | tile adds `box-shadow: inset 0 0 0 2px #0F241E`; label `font-weight: 700`; `aria-current="page"` | Search, To-dos, Calendar, Groceries, Budget |
| Clair cell | tile `background: #0F241E` with the faceless spool mark in white; label 700 | 27 |
| Label | `font-size: 13px; font-weight: 600; line-height: 16px; letter-spacing: 0; white-space: nowrap` | 26 |

## 14. Workout: Log a set (the guided screen)

| Part | Declarations |
| --- | --- |
| Column | `.scr` with `inset: 0 0 110px 0`; no bar on this screen |
| Top row | back · `Pull day <span class="num">· 18:42</span>` (17 / 700) · `.lk` "Finish" |
| Progress | "Exercise 2 of 5" … "27%" (13 `#475E56`) over a 6 px bar |
| Exercise card | `.st` + `padding: 16px; display: flex; flex-direction: column; gap: 12px`: name 22 / 700 / -0.015em with the timer tag right; "3 × 10 · best 120 lb × 10" 13 `#475E56`; done sets as `display: flex; gap: 8px; align-items: center; font-size: 15px` with an 18 px tick in `#006344`; "Set 2" 13; a 2-column grid (`1fr 1fr; gap: 12px`) of steppers |
| New best | `display: flex; gap: 12px; align-items: center; font-size: 15px`: spool 30 "proud" + "**New best** on lat pulldown. Logged when you finish the set." |
| Up next | section label + a card of rows (title 16 / 500, plan 13) |
| Actions | pinned pair `grid-template-columns: 1fr 2fr; gap: 8px`: Skip (secondary) · "Log set 2" (primary) |
