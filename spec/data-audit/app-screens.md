# Board data audit A

Boards: Main, Tabs, Search, Calendar, Groceries, Receipt, Workout, Session, Budget, Todos, EditItem, Laptop, You, Rule (`design/canvas/*.dc.html`, markup + script data).
Specs: `spec/backend.md` §2.2, §3, §5, §6, §10 (Starter templates); `spec/clair-agent.md` §8 snapshot, §10 tools, §14 credits; `spec/prd.md`; `spec/ui-tech-plan.md` (contracts, demo table).

Provenance: U user gesture · C Clair (basted, confirmed) · F formula/derived · T template · S seed-only · X system.
Verdicts: OK · GAP-FIELD · GAP-INPUT · GAP-FORMULA · CONFLICT · SEED-MISSING.

Template collections referenced below (backend §10):
- budget: `spend {note, amount, category[Groceries, Eating out, Rent, Fun, Transport], at}`, `subscriptions {name, amount, renews date, repeat}` ●; face `limit − sum(spend.amount, month)` "left"
- groceries: `items {name, list, status, qty, price, bought_on, trip, usual}`, `trips {store, total, at}` ● label "Grocery trip"; face count to_buy on default list
- classes: `classes {name, title, room, time, repeat}` ●, `due {title, kind, at, class, done}` ●; face "due this week"
- workout: `sessions {name, at, repeat, done}` ●; face count done this week, "this week"
- todos: `todos {title, due, done, repeat}` ●; face count done = false, "open"
- calendar: `events {title, at, ends, repeat}` ●; face count `*dated` today

---

## Main (Home)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting name | "Evening, Sam." | X | none | none | GAP-FIELD | No user display-name field anywhere (workspaces has `name` 'My quilt'; auth is anonymous/email). `GET /home` returns `greeting` but its source is undefined |
| Status money | "$412" / "$376 left this month" | F | budget face | `limit − sum(spend.amount, month)` | OK | Matches canonical |
| Status next thing | "Pull day at 6 pm" | F | `*dated` first item | Next up composer | OK | FR-H2 |
| Needs your OK count | "4" (receipt, check-in, Hulu, scan) | F | change_sets basted + card kinds | `GET /home needsOk` | CONFLICT | backend §10: on DevDay `/home` returns only `change_set` cards, so the count would be 1. Check-in/Hulu/noticed are Proto fixtures |
| Receipt card source | "From your receipt photo · 5:41 pm" | C | change_sets.source {kind, at} | photo → `propose_changes` | OK | |
| Receipt store/total | "Corner Market", "$35.83" | C | groceries/trips.store, .total | photo → `propose_changes` | OK | Canonical |
| Receipt item count | "8 items" | F | change set lines | `expand`/`dry_run` | OK | |
| Receipt targets | "Groceries, Budget and Calendar", "Add to 3 apps" | F | change set targets | `affected` | OK | |
| Budget delta on card | "$412 → $376 left" | F | dry_run deltas | dry_run | OK | |
| Check-in title | "3 things from today" | F/S | Card kind `checkin` | Proto fixture (ui-tech-plan §318) | GAP-FORMULA | No rule defined for which items a check-in picks; seeded fixture only |
| Check-in item 1 | "Pull day at 6 pm. Log it after?" / "Logs the session in Workout" | F | workout/sessions | `POST /records/{id}/complete` on confirm | OK | Data exists in Quilt |
| Check-in item 2 | "Return library books" / "Due today · done already?" | F | todos/todos | complete | CONFLICT | Todos board shows it "Overdue · 2 days"; Main Next up/Calendar say 9 pm today |
| Check-in item 3 | "Spotify renews Sun 22 Nov · $11.99" / "Remind you the night before?" | F | budget/subscriptions | — | GAP-FIELD | No reminder/notification field or record type to store "remind the night before" |
| Check-in button | "Update 3 apps" | F | count of ticked items | client | OK | UI tally |
| Hulu suggestion | "Hulu hasn't been opened in 45 days" | none | none | none | GAP-FIELD | Quilt has no way to know third-party app usage. Mock data the app can never produce |
| Hulu saving | "$120 a year" | F | subscriptions.amount ($9.99) ×12 | none | GAP-FORMULA | 9.99×12 = 119.88; no annualise formula/card defined |
| Hulu "Remind me to cancel" | action | U/C | none | none | GAP-FIELD | Reminder storage undefined. You/Budget boards already show the reminder set (see CONFLICT under You) |
| Noticed insight | "Clair noticed · Budget × Groceries", "you spend $41 less eating out" | F | none | none | GAP-FORMULA | No cross-app pattern formula; ui-tech-plan says seeded fixture. FR-H6 |
| Next up 1 | "6 pm · Pull day · Workout · 5 exercises" | F | workout/sessions.at | `*dated` | GAP-FIELD | "5 exercises": sessions has no exercises field/collection |
| Next up 2 | "9 pm · Return library books · To-dos · due today" | F | todos/todos.due | `*dated` | CONFLICT | backend §2.2 seeds "Take out recycling" due 8 pm today (calendar: true), so Next up's 2nd item must be recycling, not library books. Also conflicts with Todos "Overdue · 2 days" |
| Next up 3 | "Sun 22 Nov · Spotify renews · Subscriptions · $11.99" | F | budget/subscriptions.renews, amount | `*dated` | CONFLICT | With seed rows from other boards, earlier items exist within 72 h: recycling 8 pm, "Coffee with Maya" Sat 21 Nov 10 am (Search), "Call home" Sun 22 Nov (Todos). Next 3 would not include Spotify |
| Your apps count | "7" | F | page blocks | — | CONFLICT | backend T2 "Sam's 7 apps from the templates table", but the table has 6 templates; Subscriptions is a collection inside budget there, a separate app here (and on You: "Built the Subscriptions app") |
| Ordering | "Most used first" | X | none | none | GAP-FIELD | Backend orders apps by page `position`; ui-tech-plan Patch `lastOpened` has no backend storage (no open events table) |
| Budget face | "$412 left" → "$376 left" | F | budget face | §6 | OK | |
| Groceries face | "12 to buy" → "4 to buy" | F | groceries face | count | OK | |
| Calendar face | "3 today" → "4 today" | F | calendar face | count `*dated` today | CONFLICT | With the seed as written, `*dated` today also holds MATH 1210 (MWF 11:50 am, classes ● with repeat) and Take out recycling; plus Todos board's "DevDay demo at 3 pm". Count would be ≥4 before receipt |
| To-dos face | "3 today" | F | todos | template face is "count where done = false, 'open'" | CONFLICT | Label and window differ from template face; open count across Todos board is ≥5 |
| Classes face | "2 due" | F | classes/due | count done=false within 7d | OK | Label shortened from "2 due this week" |
| Workout face | "Pull day 6 pm" | F | sessions | template face is "count done this week, 'this week'" | CONFLICT | Face shown is next session, not the template formula ("3 this week") |
| Subscriptions face | "$38 a month" | F | subscriptions.amount | none | GAP-FORMULA | No face defined for Subscriptions (not an app in the template table). 38.46 rounds to $38 |
| Toast | "Added 8 items to Groceries, Budget and Calendar." | F | confirm result | confirm | OK | |

## Tabs (Your apps)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Just used recency | Groceries "2 min", Budget "20 min", Workout "1 hour", To-dos "3 hours", Calendar "Today", Classes "Yesterday" | X | none | none | GAP-FIELD | `lastOpened` in ui-tech-plan Patch; no open-event storage in backend DDL. FR-P3 is Proto/Beta |
| All apps count | "All apps · 7" | F | page blocks | | CONFLICT | Same 6-template vs 7-app issue as Main |
| Order | "Most used first": Budget, Groceries, Calendar, To-dos, Workout, Classes, Subscriptions | X | none | none | CONFLICT | Main's order puts Classes before Workout; no usage data to rank by (GAP-FIELD) |
| Faces | "$376 left", "4 to buy", "4 today", "3 today", "Pull day 6 pm", "2 due", "$38 a month" | F | | | CONFLICT | Same face issues as Main (To-dos, Workout, Calendar count, Subscriptions) |

## Search

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Query | "coffee" | U | — | search box | OK | |
| Answer line | "$16.60 on coffee in October" | F/C | budget/spend | none | GAP-FORMULA | `GET /search` returns `{hits, elsewhere, ask}`; no aggregate. 5.25+5.25+6.10 = 16.60 ✓ |
| Answer detail | "3 visits: Blue Copper twice, Starbucks once. From Budget." | F/C | budget/spend.note | none | GAP-FORMULA | Needs Clair (`query_records`); search alone can't |
| Hits match "coffee" | Blue Copper, Starbucks rows | F | budget/spend.note | text match | CONFLICT | Text search for "coffee" can't match notes "Blue Copper"/"Starbucks"; no field holds "coffee" (category is Eating out). Needs a note like "Blue Copper coffee" or semantic search |
| Spend rows | Blue Copper · Eating out · Oct 3 · $5.25; Blue Copper · Oct 11 · $5.25; Starbucks · Oct 19 · $6.10; Blue Copper · Nov 6 · $5.25 | S | budget/spend {note, category, at, amount} | U add row / C capture | SEED-MISSING | Seed doesn't list Oct/Nov spends |
| Filter chips | "Oct", "Nov", "Eating out" | F | spend.at month, category | client filter of hits | OK | |
| Count | "Budget · 3" | F | | | OK | |
| Elsewhere count | "Everywhere else (3)" | F | | `elsewhere` | OK | |
| Elsewhere 1 | "Coffee beans · Groceries · bought today" | F | groceries/items status/bought_on | receipt confirm | OK | Post-receipt state |
| Elsewhere 2 | "Buy coffee filters · To-dos · this week" | S | todos/todos | | CONFLICT | Todos board doesn't list it; Groceries shows "Coffee filters · from To-dos" (an undefined todos→groceries stitch) |
| Elsewhere 3 | "Coffee with Maya · Calendar · Sat 21 Nov, 10 am" | S | calendar/events {title, at} | U / C | CONFLICT | Calendar board shows nothing on Sat 21 (week dots 0). Seed must add it and Calendar must show it |

## Calendar

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Today heading | "Today · Fri 20 Nov" | X | DEMO_NOW | | OK | |
| Grocery trip | "Grocery trip, Corner Market" · From Groceries · 5:41 pm · just changed | F | groceries/trips (label) | `*dated` | CONFLICT | Spec title format is "Grocery trip · Corner Market" (label · title) |
| Pull day | "Pull day · From Workout · 6 pm" | F | workout/sessions | `*dated` | OK | |
| Library books | "Return library books · From To-dos · 9 pm" | F | todos/todos.due | `*dated` | CONFLICT | Todos board: "Overdue · 2 days" |
| Today count | 3 rows after receipt (week dot count 3) | F | `*dated` today | | CONFLICT | Canonical is 4 today after receipt: backend §5 lists Pull day, Take out recycling 8 pm, Library books 9 pm + trip. Recycling missing; MATH 1210 11:50 am class (●, repeat MWF) and To-dos "DevDay demo at 3 pm" would also land today |
| Sun 22 Nov | "Spotify renews · $11.99 · From Subscriptions" | F | budget/subscriptions.renews | `*dated` | CONFLICT | Todos board "Call home · Sun 22 Nov" (calendar ●) not shown |
| Mon 23 Nov | "CS 3500 project due · From Classes · 11:59 pm" | F | classes/due | `*dated` | CONFLICT | Seed d01 title is "Start CS 3500 project"; `*dated` shows record title. MATH 1210 11:50 am and CS 3500 3:00 pm class occurrences (MW) also missing |
| Tue 24 Nov | "Use the chicken and spinach · From Groceries · just changed" | C | none | none | GAP-FIELD | Items have no use-by field and items aren't ●; Receipt board puts this as the Calendar effect, but backend §5 says the Calendar line is the trip. Also missing: Homework 11 (d02, Tue 24 Nov 11:59 pm) and ECON 1010 9:10 am |
| Week strip dots | F3, S0, S0, M1, T1, W0, T0 | F | `*dated` per day | | CONFLICT | Sat has Coffee with Maya; Sun has Spotify (1, shown 0) and Call home; Mon–Thu have class occurrences; Tue has Homework 11 |
| Header | "This week" (Fri 20–Thu 26) | X | | | OK | UI copy; week window in spec is Mon–Mon, but this is a 7-day strip |

## Groceries

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Header total | "{14} to buy across 3 lists" | F | items status/list | none | GAP-FORMULA | Face counts default list only; "across lists" count not defined as a face or block |
| Grocery spend | "$177.83 of $200 spent this month" | F | trips.total, block target 20000 | progress block `b_spend` | OK | Canonical |
| List chips | Weekly shop 4, Taco night 5, Costco run 5 | F/T | items.list options | list switch | OK | Counts per option via switch (assumed); seed matches |
| List notes | "Default list", "Sat 21 Nov", "Once a month" | T | option `hint` | New list / rename | OK | |
| New list | "New list" chip | U | options | `POST /collections/{id}/options` | OK | |
| Coffee filters | "from To-dos" | C/stitch | `_via` | none | GAP-FIELD | No todos→groceries stitch declared anywhere |
| Tortillas | "1 pack" | S | items.qty | U edit | OK | |
| Olive oil | "running low" | S | items.qty? | | GAP-FIELD | Not a quantity; no note/state field on items |
| Dish soap | "1 bottle" | S | items.qty | | OK | |
| Oat milk | "1 carton", usual "every week" | S/F | qty; usuals | get_usuals | GAP-FORMULA | Usual rhythm "every N days" is only a Clair tool (`get_usuals`); no endpoint/formula for the app view |
| Eggs | qty "12", usual "every 6 days" | S | qty | | CONFLICT | backend §2.2 seed: qty "1 dozen" |
| Bananas | "1 bunch", "every 5 days" | S/F | | | OK | Rhythm: see GAP-FORMULA above |
| Chicken thighs | "2 lb · use by Tue", not marked usual | S | qty | | GAP-FIELD | No use-by field. Not usual on board, but snapshot lists Chicken thighs every ~10 d as a usual (CONFLICT) |
| Rice | "5 lb bag" | S | qty | | OK | |
| Spinach | "1 bag · use by Tue", "every week" | S | qty | | GAP-FIELD | use-by |
| Greek yogurt | "32 oz", not usual | S | qty | | CONFLICT | Snapshot: Greek yogurt every ~7 d usual |
| Coffee beans | "12 oz", "every 2 weeks" | S | qty | | OK | |
| Usual tag | "usual" on 5 items | F | items.usual / auto | | OK | |
| Usuals filter | "Usuals · N", "What you buy on a rhythm" | F | | | GAP-FORMULA | Same as rhythm |
| Off-list usuals | Butter "every 2 weeks · last 15 days ago"; Cheddar "every week · last 9 days ago"; Orange juice "every 10 days · last 6 days ago" | F/S | bought items history | get_usuals | OK | Matches seed; Hummus (~7 d, last 5 d) in seed but not shown (board omission) |
| Bought section | "Bought at Corner Market · 8" | F | items.trip relation | receipt confirm | OK | |
| Last trip | "Corner Market", "Today 5:41 pm", "$35.83" | C | trips | receipt | OK | |
| Last trip items | "8 items" | F | count items where trip = this | none | GAP-FORMULA | Reverse-relation count not in formula grammar |
| Last trip source | "from your receipt photo" | X | change_sets.source | | OK | |

## Receipt (review)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Source/time | "Receipt photo · today 5:41 pm" | C | change set source, trips.at | photo | OK | |
| Store | "Corner Market" | C | trips.store | `propose_changes` | OK | |
| Count/total | "8 of 8 items · $35.83" | F | sum of line prices | dry_run | OK | Sum checks: 35.83 |
| Line: Oat milk | "1 carton" $3.49 | C | items.qty, price | | OK | |
| Line: Eggs | "Eggs, dozen" "12" $4.29 | C | items.name/qty/price | | CONFLICT | Stored name is "Eggs" (matched open item), seed qty "1 dozen" |
| Line: Bananas | "1 bunch" $1.87 | C | | | OK | |
| Line: Chicken thighs | "2 lb · use by Tue" $8.62 | C | qty | | GAP-FIELD | use-by not storable |
| Line: Rice | "Rice, 5 lb" "1 bag" $6.99 | C | | | CONFLICT | List item is "Rice" qty "5 lb bag" |
| Line: Spinach | "1 bag · use by Tue" $3.29 | C | | | GAP-FIELD | use-by |
| Line: Greek yogurt | "32 oz" $4.29 | C | | | OK | |
| Line: Coffee beans | "12 oz" $2.99 | C | | | OK | (low price, but consistent) |
| Effect Groceries | "Check off 8 items on your list" | F | dry_run lines | | OK | |
| Effect Budget | "$412 → $376 left this month" | F | dry_run | | OK | |
| Effect Calendar | "Use the chicken and spinach by Tue 24 Nov" | C | none | none | CONFLICT | backend §5: Calendar effect is "Grocery trip · Corner Market 5:41 pm" (trip ●). Use-by reminder has no field (GAP-FIELD) |
| Targets | "Adding updates 3 apps", "Add to 3 apps" | F | affected | | OK | |

## Workout

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Tabs | Today, Log, History, Progress, Routines | T | AppSpec tabs | | GAP-FIELD | Template has one collection (sessions); Log/Progress/Routines need sets/exercises/routines collections |
| Next up | "today 6 pm", "Pull day" | F | sessions.name, at | `*dated` | OK | |
| Plan | "5 exercises · about 45 min" | none | none | none | GAP-FIELD | No exercises, no duration field |
| Lifted this week | "12,450 lb" | F | none | none | GAP-FIELD | Needs sets {reps, weight} |
| New bests | "2" | F | none | none | GAP-FIELD | Needs sets + best formula |
| Sessions this week | "3 of 4" | F | sessions.done, week | count done (face) + progress target 4 | OK | Template face is this count; target 4 as a block constant. Repeating sessions: count over `repeat.log` not defined (see note) |
| Clair tip | "You did 10 × 120 on lat pulldown last week. Try 125 today." | C | none | none | GAP-FIELD | Sets data absent |
| History | "41 sessions since September." | F | sessions | count done all | SEED-MISSING | Seed must hold 41 done sessions (or occurrences in `log`) since Sep |
| Progress | "Lat pulldown: 100 → 120 lb in 8 weeks." | F | none | none | GAP-FIELD | |
| Routines | "Pull, push, legs; Clair can build a new one." | S | sessions.name | | GAP-FIELD | No routine/template collection; names alone could come from sessions |
| Log | "Every set you log, newest first." | | none | | GAP-FIELD | |

## Session (Log a set)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Session | "Pull day" | S | sessions.name | | OK | |
| Elapsed | "18:42" | X | none | none | GAP-FIELD | No start time; also a session 18 min in contradicts DEMO_NOW 5:45 pm before Pull day 6 pm (CONFLICT if shown in the same timeline) |
| Progress | "Exercise 2 of 5", "27%" | F | none | none | GAP-FIELD | |
| Exercise | "Lat pulldown" | S | none | | GAP-FIELD | |
| Rest timer | "Rest 0:47" | X | client | | OK | Client-only timer |
| Plan/best | "3 × 10 · best 120 lb × 10" | F | none | | GAP-FIELD | |
| Set 1 | "12 reps × 110 lb" | U | none | | GAP-FIELD | |
| Set 2 steppers | reps 10, weight 120 lb | U | none | | GAP-FIELD/GAP-INPUT | No sets collection; steppers have nothing to write to |
| New best | "New best on lat pulldown" | F | none | | GAP-FORMULA | |
| Up next | "Seated cable row 3 × 12 · 100 lb", "Face pulls 3 × 15 · 40 lb" | S | none | | GAP-FIELD | Exercises 1 and 5 unnamed anywhere |

## Budget

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Left | "$376" "left of $1,200" | F | face, settings.limit | §6 | OK | Canonical |
| Was | "Was $412" | F | change set deltas | confirm result | OK | |
| Days to go | "11 days to go" | F/X | month window | none | GAP-FORMULA | No days-left term (ui-tech-plan ask fixture also counts 11) |
| Change link | "Corner Market receipt, 5:41 pm ›" | X | change_sets | | OK | |
| Groceries category | "$177.83 of $200", "from your receipt today" | F | spend.amount by category | sum where category | GAP-FIELD | Per-category budgets ("of $200") have no field; only one `limit` setting |
| Eating out | "$165 of $150", "$15 over. Weeks you scan receipts, you spend less here." | F | spend | | GAP-FIELD | Per-category limit; insight is GAP-FORMULA |
| Transport | "$42 of $80" | F | spend | | GAP-FIELD | Per-category limit |
| Subscriptions category | "$38.46 of $40" | F | none | | GAP-FIELD | "Subscriptions" is not a spend category option; subscriptions rows aren't spend rows, so they don't count toward the $1,200 face |
| Spent reconciliation | 177.83+165+42+38.46 = 423.29 of 823.83 spent | F | spend | | SEED-MISSING | $400.54 must sit in Rent/Fun (not shown). Seed must define it |
| Subs header | "Subscriptions · $38.46 a month" | F | subscriptions.amount | sum | GAP-FORMULA | No formula/face declared for it |
| Spotify | "renews Sun 22 Nov" $11.99 | S | subscriptions {name, renews, amount, repeat} | U / C | SEED-MISSING | Seed lists Spotify only in snapshot "next dated", no rows spec |
| Hulu | "reminder set: cancel before Wed 2 Dec" $9.99 | S | subscriptions + ? | | GAP-FIELD | Reminder state not storable; also CONFLICT with Main (Hulu card still pending) |
| Adobe CC, student | "renews Thu 3 Dec" $13.49 | S | subscriptions | | SEED-MISSING | |
| iCloud 50 GB | "renews Wed 9 Dec" $2.99 | S | subscriptions | | SEED-MISSING | |
| Recent 1 | "Corner Market · Groceries · from your receipt · 5:41 pm · $35.83" | C/stitch | spend with `_via` | stitch | OK | |
| Recent 2 | "Union food court · Eating out · yesterday · $11.40" | S | spend | U / C | SEED-MISSING | Thu 19 Nov |
| Recent 3 | "Gas · Transport · Tuesday · $28.00" | S | spend | U / C | SEED-MISSING | Tue 17 Nov |

## To-dos

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Face | "{3} left today." | F | todos | none | CONFLICT | Template face is open count "open"; "today" window not the template's |
| Heading | "Today · Fri 20 Nov" | X | | | OK | |
| Return library books | sub "Marriott Library", "Overdue · 2 days" | S | todos.title, due | | CONFLICT | Overdue (due Wed 18 Nov) vs Main/Calendar "9 pm today" / "due today". Location "Marriott Library": no field (GAP-FIELD) |
| DevDay demo at 3 pm | sub "Lassonde Studios" | S | todos.title (time in title) | | GAP-FIELD | Location field missing; a 3 pm due would also appear in Calendar today (CONFLICT with Calendar's count) |
| Book flu shot | "Student health", done (ticked) | S | todos.done | U tick | GAP-FIELD | Location; done today fine |
| Pay Sam back for pizza | "$14 · Budget" | S | todos.title | | CONFLICT | The user is Sam ("Evening, Sam."). "$14 · Budget" implies amount field + todos→budget link: neither exists (GAP-FIELD) |
| Start CS 3500 project | "Due Mon 23 Nov · from Classes" | stitch | `_via` classes/due | none | GAP-FIELD | No classes/due → todos stitch; would also double in Calendar |
| Call home | "Sun 22 Nov" | S | todos.due | U / C | CONFLICT | Not on Calendar Sun 22 |
| Missing | Take out recycling 8 pm (backend §2.2) | S | todos | | CONFLICT | Seeded in spec; absent from board |

## EditItem

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Section | "Bought at Corner Market · 8" | F | items.trip | | OK | |
| Oat milk row | "1 carton · from receipt" | C | qty, change set source | | OK | |
| Eggs row | "12" | S | qty | | CONFLICT | Seed "1 dozen" |
| Bananas row | "1 bunch" | S | qty | | OK | |
| Chicken thighs row | "2 lb · use by Tue" | S | qty | | GAP-FIELD | use-by |
| Field Name | "Oat milk" | U | items.name | edit sheet | OK | |
| Field Amount | "1 carton" | U | items.qty (label "Qty") | edit sheet | CONFLICT | Template label is "Qty"; "Amount" is the money field name elsewhere. Price (money) not editable here |
| Field Category | "Dairy" | U | none | | GAP-FIELD | Items have no category field |
| Link | "From your Corner Market receipt · also in Budget" | F | `_via` | | CONFLICT | Items aren't in Budget; only the trip total is stitched to a spend |

## Laptop

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| App list | Budget, Groceries, Calendar, To-dos, Workout, Classes, Subscriptions | F | pages | | CONFLICT | 7 apps vs 6 templates (see Main) |
| Account | "Sam · 32 credits" | X | name: none; credits: usage_ledger | | GAP-FIELD | Name has no field; credits OK (matches You) |
| Month | "November" | X | | | OK | |
| Left | "$376 left of $1,200", "Was $412 · Corner Market receipt from your phone, 5:41 pm" | F | | | OK | "from your phone": device of origin not stored (minor, change_sets.user_id only) |
| Categories | Groceries $177.83 / $200; Eating out $165 / $150; Transport $42 / $80; Subscriptions $38.46 / $40 | F | | | GAP-FIELD | Per-category limits; Subscriptions not a category (same as Budget) |
| Recent | Corner Market $35.83; Union food court $11.40; Gas $28.00 | S | spend | | SEED-MISSING | Same as Budget |
| Recent: Spotify | "Subscriptions · Sun 22 Nov · $11.99" | S | subscriptions | | CONFLICT | A future renewal listed under Recent spends; phone Budget board doesn't list it |
| Detail lines | "Oat milk $3.49", "Eggs, dozen $4.29", "Bananas $1.87", "Chicken thighs $8.62", "+ 4 more" | F | spend `_via` trip → items.trip | none | GAP-FORMULA | Reverse lookup spend→trip→items undefined. "Eggs, dozen" vs stored "Eggs" (CONFLICT) |
| also in | Groceries, Calendar | F | `_via` | | OK | |

## You (activity and settings)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Activity 1 | "Added 8 items from your Corner Market receipt · Groceries, Budget, Calendar · 5:41 pm" | X | change_sets | | CONFLICT | Confirm happens after DEMO_NOW 5:45; 5:41 is the receipt time, not the change time |
| Activity 2 | "Built the Subscriptions app · and connected it to Calendar and Budget · 12:20 pm" | C | change_sets (propose_app) | | CONFLICT | Contradicts template table (subscriptions is in budget template) and backend T2 seed (apps from templates). If built today at 12:20, activity 3 "yesterday" is impossible |
| Activity 3 | "Set a reminder to cancel Hulu · Subscriptions · yesterday" | C | none | | CONFLICT | Main still offers "Remind me to cancel"; reminder has no storage (GAP-FIELD) |
| Activity 4 | "Moved Leg day to 7 am · Workout · Tue 17 Nov" | C | sessions.at | `propose_changes` | SEED-MISSING | Seed needs a Leg day session + a stitched Clair change set dated Tue 17 Nov |
| Credits | "32 of 50 left · resets Tue 1 Dec", "Free plan" | X | usage_ledger, settings.credits_monthly | | SEED-MISSING | Monthly grant 50 not stated in spec; seed must set 50 and 18 spent |
| Credit costs | chat 1, photo fill 5, build 10 | T | clair-agent §14 | | OK | |
| Read level | Full help / Field names only / Nothing | U | workspaces.read_level | `PATCH /settings` | OK | |
| Notes | "3 notes" | F | clair_notes | count | CONFLICT | Snapshot seeds 1 note (n1 Costco); fridge beat adds 1 → 2 |

## Rule (reminder from an insight)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Insight | "$41 less eating out" | F | none | none | GAP-FORMULA | Seeded fixture only |
| When | "After a grocery trip shows up", "A purchase at a grocery store in Budget, or a trip in Calendar" | U | none | none | GAP-FIELD | No rules/automations table or engine anywhere in spec |
| Only if | "No receipt was scanned that day", "Groceries has no new items from a photo" | U | none | none | GAP-FIELD | |
| Then | "Remind me to scan the receipt", "Shows in Needs your OK on Home, once, by 9 pm" | U | none | none | GAP-FIELD | No reminder card kind in `Card` union |
| Toggle | "Reminder is on" | U | none | none | GAP-FIELD | |

---

## Seed rows the boards imply

Values quoted from boards. "⚠" marks a disagreement.

### Budget (`budget`)
- settings.limit 120000 (✓ canonical). Spent Nov before receipt $788.00; after $823.83.
- spend (Nov):
  - Corner Market · Groceries · 2026-11-20 17:41 · $35.83 (`_via` trip; created by receipt confirm, not seed)
  - Union food court · Eating out · Thu 19 Nov · $11.40
  - Gas · Transport · Tue 17 Nov · $28.00
  - Blue Copper · Eating out · Fri 6 Nov · $5.25
  - Groceries category total before receipt $142.00 (must equal Nov grocery trips, stitched)
  - Eating out total $165.00 (incl. $11.40 + $5.25; $148.35 more needed)
  - Transport total $42.00 (incl. $28.00; $14.00 more needed)
  - ⚠ "Subscriptions $38.46" category: not a spend category; either add the option + spend rows, or drop the row
  - ⚠ Remainder $400.54 (788.00 − 142 − 165 − 42 − 38.46) must be Rent/Fun, never shown; if Subscriptions isn't spend, remainder is $439.00
- spend (Oct): Blue Copper · Eating out · Oct 3 · $5.25; Blue Copper · Oct 11 · $5.25; Starbucks · Oct 19 · $6.10 (⚠ notes need "coffee" to be found by search "coffee")
- Per-category targets shown: Groceries $200, Eating out $150, Transport $80, Subscriptions $40 (⚠ no field)

### Subscriptions (`budget/subscriptions` or separate app ⚠)
- Spotify · $11.99 · renews 2026-11-22 (Sun) · monthly
- Hulu · $9.99 · renews 2026-12-02 (Wed, implied by "cancel before Wed 2 Dec") · monthly · ⚠ "not opened in 45 days" unproducible; reminder state unstorable
- Adobe CC, student · $13.49 · renews 2026-12-03 (Thu) · monthly
- iCloud 50 GB · $2.99 · renews 2026-12-09 (Wed) · monthly
- Total $38.46 a month (face "$38 a month")

### Workout (`workout/sessions {name, at, repeat, done}`)
- Pull day · 2026-11-20 18:00 · done false (today)
- Leg day · Tue 17 Nov · moved to 7 am by Clair (activity) · done true (implied)
- 3 sessions done Mon 16–Thu 19 Nov ("3 of 4"); names implied Push/Leg/(one more) from "Pull, push, legs" ⚠ not named
- 41 done sessions since September (History)
- ⚠ Unstorable with current fields: Pull day has 5 exercises, ~45 min; Lat pulldown 3 × 10, best 120 lb × 10, last week 10 × 120, 100 → 120 lb in 8 weeks; Set 1 today 12 × 110 lb; Seated cable row 3 × 12 · 100 lb; Face pulls 3 × 15 · 40 lb; 12,450 lb lifted this week; 2 new bests

### To-dos (`todos/todos {title, due, done, repeat}`)
- Return library books · ⚠ due 2026-11-20 21:00 (Main, Calendar, check-in) vs overdue 2 days = Wed 18 Nov (Todos board) · "Marriott Library" (no field)
- DevDay demo at 3 pm · due today 15:00 (implied) · "Lassonde Studios" (no field)
- Book flu shot · today · done true · "Student health" (no field)
- Pay Sam back for pizza · today · "$14 · Budget" (no field) · ⚠ name clash with user Sam
- Start CS 3500 project · Mon 23 Nov · "from Classes" ⚠ duplicates classes/due d01, no stitch
- Call home · Sun 22 Nov
- Buy coffee filters · this week (Search only) ⚠ not on Todos board
- Take out recycling · Fri 20:00 weekly (backend §2.2) ⚠ not on any board
- Face: "3 today" / "3 left today" (after Book flu shot done)

### Calendar (`calendar/events` + `*dated`)
- events: Coffee with Maya · Sat 21 Nov 10:00 (Search only ⚠ Calendar board shows Sat empty)
- `*dated` per Calendar board: Fri 20 Grocery trip Corner Market 5:41 pm (after receipt), Pull day 6 pm, Return library books 9 pm; Sun 22 Spotify renews $11.99; Mon 23 CS 3500 project due 11:59 pm; Tue 24 Use the chicken and spinach (⚠ no source collection)
- ⚠ Missing from board but implied by seed: Take out recycling Fri 8 pm; MATH 1210 Fri 11:50 am and Mon/Wed; CS 3500 Mon/Wed 3 pm; ECON 1010 Tue/Thu 9:10 am; Homework 11 Tue 24 Nov 11:59 pm; Call home Sun 22; DevDay demo Fri 3 pm; Workout sessions after today
- Face "3 today" → "4 today" holds only if class times, recycling or to-dos without times are excluded

### Groceries (consistent with backend §2.2 except)
- Weekly shop qty: Coffee filters "from To-dos" (⚠ stitch), Tortillas "1 pack", Olive oil "running low" (⚠), Dish soap "1 bottle", Oat milk "1 carton", Eggs "12" (⚠ seed "1 dozen"), Bananas "1 bunch", Chicken thighs "2 lb · use by Tue" (⚠), Rice "5 lb bag", Spinach "1 bag · use by Tue" (⚠), Greek yogurt "32 oz", Coffee beans "12 oz"
- Taco night: Ground beef 1 lb, Avocados 3, Limes 4, Salsa 1 jar, Shredded cheese 8 oz
- Costco run: Paper towels 12 rolls, Laundry pods 1 tub, Frozen berries 3 lb, Almonds 2 lb, Toilet paper 24 rolls
- Receipt prices: Oat milk 3.49, Eggs 4.29, Bananas 1.87, Chicken thighs 8.62, Rice 6.99, Spinach 3.29, Greek yogurt 4.29, Coffee beans 2.99 (= 35.83)
- Usuals shown: Oat milk weekly, Eggs 6 d, Bananas 5 d, Spinach weekly, Coffee beans 2 wk; ⚠ board omits Chicken thighs (~10 d) and Greek yogurt (~7 d) that the snapshot lists; omits Hummus
- Nov grocery trips before receipt must total $142.00

### Classes
- Calendar shows d01 as "CS 3500 project due" ⚠ seed title "Start CS 3500 project". Face "2 due" ✓.

### Clair / account
- clair_notes: 3 (You) ⚠ vs 1 in snapshot
- credits: 50 monthly, 32 left (18 spent), resets Tue 1 Dec
- change_sets (Clair, stitched): "Moved Leg day to 7 am" Tue 17 Nov; "Set a reminder to cancel Hulu" yesterday ⚠; "Built the Subscriptions app" today 12:20 pm ⚠
