# Audit B: Clair and Build boards, data provenance

Scope: `design/canvas/` Clair, ClairSheet, ClairTalk, ClairResult, ClairShare, ClairAsk, ClairPhoto, ClairFridge, ClairNotes, Build, Preview, Arrange, Connect, Empty. Values read from the markup and the `<script>` data of each board. Specs: `spec/backend.md` (§2.2, §3, §6, §10), `spec/clair-agent.md` (§8, §10, §12, §14), `spec/prd.md` FR-*, `spec/ui-tech-plan.md` §5 seed table, `design/notes/fixspec.md`.

Provenance: U user gesture · C Clair (tool, lands after confirm) · F formula/derived · T template · S seed-only · X system.

## Shared chrome (counted once)

### Home backdrop (behind ClairSheet, ClairTalk, ClairResult, ClairShare, ClairAsk, ClairPhoto, ClairFridge)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting name | "Evening, Sam." | X (greeting) | none | `GET /home` `greeting` | GAP-FIELD | No user/display-name field in the DDL (`workspaces.name` defaults "My quilt"; auth is anonymous or email). Onboarding never asks a name. |
| Money left | "$412 left this month" | F | budget face `{minus:[{setting:"limit"}, sum(spend.amount, month)]}` | formula §6 over seed spend $788.00, limit 120000 | OK | Canonical pre-receipt value. |
| Next dated thing | "Pull day at 6 pm" | F over S | workout/sessions.{name,at} via `*dated` | Next up / status composer (FR-H2) | OK | Seed row Pull day, Fri 20 Nov 6 pm (snapshot §8). |
| Queue count | "Needs your OK · 4" | S | change_sets (basted) | seed | CONFLICT | ui-tech-plan §5 queue = receipt, evening check-in, Hulu suggestion ($120 a year), scan insight ($41 less eating out). backend §10 says DevDay `/home` returns only `change_set` cards (check-in is Beta); Hulu suggestion needs "not opened" data nothing collects (GAP-INPUT). |
| Receipt card | "From your receipt photo · 5:41 pm · Corner Market · $35.83 · 8 items. Adding updates Groceries, Budget and Calendar." | C (photo, `report_understanding` + `propose_changes`), queued by S | groceries/trips + 8 items; budget/spend via stitch | receipt flow §12.1 | OK | Matches canonical receipt. |
| State of the backdrop | receipt still pending, $412 | S | | | CONFLICT | ClairResult ($376 → $364), ClairFridge (Weekly shop 4 → 6, spec §12.2 runs after the receipt) and ClairPhoto assume the receipt is confirmed, but the backdrop shows it pending and $412. |

### Pinned bar (Clair, ClairSheet, ClairTalk, ClairResult, ClairShare, ClairAsk, ClairPhoto, ClairFridge, ClairNotes, Empty)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Pins | Budget, Groceries, Calendar, To-dos, Clair | S | `workspaces.settings.pins` | seed (FR-P1 fixed pins) | CONFLICT | FR-P1: fixed demo pins are Groceries, Budget, Calendar, **Workout**. ClairResult targets Workout, which then has no pin for the thread (FR-S2). |

## Clair (chat)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Credits | "32 credits" | X | usage_ledger (grant − spends) | `GET /usage` / `GET /me` | SEED-MISSING | Spec only says the demo account is "seeded with enough for rehearsals"; no grant number. Meter in chat header is FR-T1 (Beta). |
| Header claim | "Answers from your apps only" | UI copy about data | | | CONFLICT | ClairAsk says "Your apps first; general answers say so" and shows a general (non-app) answer. |
| Question | "How much did I spend on food this week?" | U (typed) | clair_messages | | OK | |
| Week food total | "$71.20." | F via C (`query_records budget/spend window=week`, category Groceries + Eating out) | budget/spend.amount, category, at | Clair sums rows | SEED-MISSING | 35.83 + 35.37 = 71.20 checks. Needs seeded spend rows this week (Mon 16 Nov on). |
| Groceries this week | "$35.83 on groceries" | F over C (receipt → stitch) | budget/spend (category Groceries, `_via` groceries) | receipt confirm | OK | Only if the receipt is confirmed; consistent with usuals (last pre-receipt trip Sun 15 Nov, before the week window). |
| Eating out this week | "$35.37 eating out" | F over S | budget/spend category Eating out | seed | SEED-MISSING | 5 rows summing $35.37 this week are not in the seed spec. |
| Pace claim | "You're on pace for your $200 grocery budget." | F | groceries tab block `b_spend` target 20000 | Clair from get_app/snapshot | CONFLICT | Grocery spend after receipt is $177.83 of $200 on day 20 of 30, which projects to about $267: not on pace. Also the $200 lives in Groceries (progress block), not Budget. |
| Source chip | "From Budget · 6 rows" | F (`done.sources` + row count) | | SSE `done {sources}` | CONFLICT | 6 rows = 1 receipt spend + 5 eating-out rows (implied). Chip omits Groceries though the $200 target comes from it. |
| Capture | "add oat milk to groceries" | U | | | OK | |
| Proposal | "Add Oat milk, 1 carton, to your list?" · "Waiting for your OK · Groceries" | C (`propose_changes` insert groceries/items {name, qty "1 carton", list Weekly shop, status to buy}) | groceries/items.name, qty, list, status | confirm | OK | Oat milk (i01) is already open on Weekly shop before the receipt; fine only after the receipt closes it. qty "1 carton" is Clair's guess. |
| Done line | "Added Oat milk to Groceries." | C | | | OK | |
| Suggestion chips | "build a classes app", "what's due this week?", "scan a receipt" | UI | | | OK | "build a classes app" when Classes already exists (snapshot §8) would build a duplicate; copy only. |

## ClairSheet

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Field placeholder | "Spent $12 on lunch, gym tomorrow 6 pm…" | UI | | | OK | Matches fixspec D. |
| Suggestion: capture | "Spent $12 on lunch · Log it · Budget" | UI (static, FR-C2c) | | | OK | Example prompt, not a claim about Sam's data. |
| Suggestion: ask | "Can I afford $60 concert tickets? · Ask · from Budget and Calendar" | UI | | | OK | |
| Suggestion: build | "Track my plants · Build · a new app" | UI | | | OK | Matches the Build fixture (ui-tech-plan §5); the Build flow boards use Subscriptions instead (see Build). |
| Section label | "Try this evening · Changes through the day" | X (time of day) | | client clock / server_now | OK | |

## ClairTalk

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Live transcript | "Spent $12 on lunch, gym tomorrow 6 pm…" | U (voice, on-device speech) | clair_messages (transcript) | FR-C17 | OK | |

## ClairResult

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Typed input | "spent $12 on lunch, gym tomorrow 6 pm" | U | | | OK | |
| Header | "2 things, 3 apps" → "Added to 3 apps" | F (change set targets) | change_sets.targets | dry_run `affected` | OK | Calendar counts via `*dated`. |
| Clair line | "I made that into 2 things. Nothing is saved until you OK it." / "Added. Budget, Calendar and Workout are up to date." | C | | | OK | |
| Budget line | "Budget · Eating out · Lunch · $12.00" | C (`propose_changes` insert budget/spend {note "Lunch", amount 1200, category Eating out, at}) | budget/spend.note, amount, category, at | confirm | OK | Matches capture fixture. |
| Budget delta | "$376 → $364 left this month" | F (dry_run) | budget face | dry_run deltas | CONFLICT | Correct post-receipt (376.17 − 12 = 364.17), but the board's own Home backdrop shows $412 with the receipt pending; from that state it would be $412 → $400. |
| Workout line | "Calendar + Workout · Gym · 6 pm · Sat 21 Nov · a planned session in Workout" | C (insert workout/sessions {name "Gym", at 2026-11-21T18:00-07:00, done false}) | workout/sessions.name, at | confirm; Calendar via `*dated` | OK | Matches ui-tech-plan capture fixture (prd-stories AC-1 still says Fri 20 Nov from Thu 19 Nov, different day, same rule). Workout isn't pinned (see pinned bar). |
| Ask | "Can I afford $60 concert tickets?" | U | | | OK | |
| Answer | "Yes. $376 left until 1 Dec; after $60 you'd have $316, about $29 a day." (after capture: $364 / $304 / $28) | F via C (`get_faces budget` + month window end) | budget face | Clair text; days to 1 Dec = 11 | OK | 316/11 = 28.7 → $29 matches ui-tech-plan. fixspec §D still says "about $26 a day" (CONFLICT in fixspec, board is right). Same backdrop issue: Home shows $412. |
| Source chips | "From Budget, Calendar" | F (`done.sources`) | | | OK | Calendar isn't used by the figure; acceptable per fixture. |
| Action | "Add to Budget as planned" → "Planned in Budget: concert tickets, $60" | C (propose_changes) | none | | GAP-FIELD | budget/spend has no planned/status field; inserting a spend would drop the face to $316 now. |

## ClairShare

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| File chip | "Syllabus · ECON 1010.pdf · 4 pages · shared from Files" | U (attach) + X (page count) | Storage clair-uploads | FR-C6 / FR-C8 | OK | "shared from Files" implies OS share (FR-C8, Proto/Later); the File chip path (FR-C6) is the Live+ route. |
| Status | "Reading 4 pages…" | X (`status` event) | | SSE | OK | |
| Head / line | "6 due dates, 2 exams" · "Found 6 due dates and 2 exams. Add to Classes and Calendar?" | C (`report_understanding kind=syllabus`, `propose_changes` 8 × insert classes/due) | classes/due | §12.5 | OK | |
| Rows (8) | Problem set 7 "Due Mon 23 Nov, 11:59 pm"; Midterm 2 "Tue 1 Dec, 9:10 am · Kendall 104" (Exam); Problem set 8 "Due Fri 4 Dec, 11:59 pm"; Reading response "Due Mon 7 Dec, 9 am"; Problem set 9 "Due Wed 9 Dec, 11:59 pm"; Term paper "Due Fri 11 Dec, 5 pm"; Review sheet "Due Mon 14 Dec, 9 am"; Final exam "Wed 16 Dec, 8 am · Kendall 104" (Exam) | C | classes/due.title, kind, at, class | confirm | OK | Exact match with backend §2.2 table; weekdays check out. |
| Room on exams | "Kendall 104" | F (relation lookup) | classes/classes.room via due.class | card line | GAP-FORMULA | `due` has no room field; showing the related class's room on a card line isn't specified (spec card §12.5 shows it too). Also assumes exams are in the class room. |
| More | "Show 5 more" | F (8 − 3) | | | OK | |
| Done line | "Added 8 dates to Classes and Calendar. Each one warns you 3 days ahead." | C | none | | GAP-FIELD | No reminder/warning field or notification job on DevDay (notifications are Beta, FR-O4). |
| Button | "Add to 2 apps" | F (targets) | | | OK | |

## ClairAsk

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Header | "Your apps first; general answers say so" | UI | | | OK | Conflicts with Clair board header (logged there). |
| Question | "How much did I spend on eating out this month?" | U | | | OK | |
| Answer | "$165 of $150." | F via C (`query_records budget/spend category=Eating out window=month`) | spend.amount; **limit: none** | | GAP-FIELD | Budget has one app-level `settings.limit`; no per-category budget. The "$150" has nowhere to live. $165 itself needs seed rows (SEED-MISSING). |
| Over | "$15 over" (also aria "Eating out: $165 of $150, $15 over") | F | | Clair arithmetic | GAP-FIELD | Depends on the $150 above. |
| Breakdown | "mostly Blue Copper (4 visits)" | F via C (group spend.note) | budget/spend.note | query_records | SEED-MISSING | Needs 4 November spend rows with note "Blue Copper", category Eating out. |
| Chip | "Eating out · November" | F | | | GAP-FORMULA | No per-category progress block or face is defined in the budget template. |
| Link | "See Eating out ›" | UI | | | GAP-FORMULA | No filtered category view specified in Budget. |
| Source | "From Budget" | F (`done.sources`) | | | OK | |
| Question 2 | "How much protein should I eat a day?" | U | | | OK | |
| General answer | "1.2 to 1.6 g per kg … At 70 kg that is about 85 to 110 g a day." | C (general knowledge, labelled "General answer · not from your apps") | none | | OK | 70 kg is a worked example, not Sam's data; no weight field exists. Math: 84 to 112 g. Medical caveat present (AB-6). |
| Action | "Track protein in Workout ›" | C | none | | GAP-FIELD | workout/sessions has no food/protein field, and no tool edits an existing app's spec (`propose_app` makes new apps; `propose_changes` has no ops on apps). |

## ClairPhoto

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Photo label | "Fridge photo" | U (photo) | Storage | | CONFLICT | spec §12.6 (the case this board illustrates) is a **pantry shelf** photo with "can I make pasta?". |
| Question | "What can I make tonight?" | U | | | OK | Differs from spec wording "can I make pasta?"; fine as input. |
| Status | "Looking at your photo and Groceries…" | X | | SSE status | OK | |
| Log path | "I see 9 items. Review them before anything goes into Groceries." | C (`report_understanding`) | none | | CONFLICT / GAP-FIELD | ClairFridge says the fridge has "14 things" (spec §12.2 "14 items"); 9 is the pantry count from §12.6. Logging seen items into Groceries has no target: Groceries has no on-hand/inventory field. |
| Answer | "Spinach and egg pasta." | C | | Clair text | OK | |
| Count | "You have 4 of 5 things" | F via C | | | CONFLICT | Counts Pasta and Olive oil as owned (below). |
| Pasta | "Pasta · from your Groceries" | C (`query_records groceries/items`) | groceries/items | | GAP-FIELD | Groceries tracks to-buy and bought, not what's on hand; Pasta is in no seed list or usual. |
| Olive oil | "Olive oil · from your Groceries" | C | groceries/items | | CONFLICT | Olive oil (i11) is **open on Weekly shop** (still to buy after the receipt); spec §12.6 says "Olive oil is on Weekly shop, so you're likely out". |
| Spinach, Eggs | "from your photo" | C (`report_understanding` items) | | | OK | Both bought today on the receipt, consistent post-receipt (backdrop says pre-receipt, see chrome). |
| Missing item | "missing parmesan ($4.29 at Corner Market)" | F via C (last price of bought "Parmesan" + trip store) | groceries/items.price + trip relation → trips.store | query_records | SEED-MISSING | No Parmesan in the 6-week history. Spec §12.6 gives no price. $4.29 equals the receipt's Eggs and Greek yogurt prices. |
| Sources | "From Your photo · Groceries" | F | | | OK | |
| Action | "Add parmesan to Groceries" → "Parmesan added to Groceries · just changed" | C (insert groceries/items {name Parmesan, list Weekly shop, status to buy}) | groceries/items | confirm | OK | Matches §12.6 step 3. Card doesn't show the face delta (Weekly shop +1). |

## ClairFridge

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Understanding | "Your fridge. I can see 14 things." | C (`report_understanding kind=fridge`) | | `understood` event | OK | Matches §12.2 / FR-C13. |
| Status | "Checking it against what you usually buy…" | X | | SSE status | OK | |
| Question | "Looks like you're low on these. Add to Weekly shop?" | C (`ask_user`, multi) | clair_questions | | OK | |
| Butter | "you buy every 2 weeks · last 15 days ago" | F via C (`get_usuals`) | groceries/items history (usual auto) | get_usuals | OK | Seed: every ~14 d, last 15 d ago. |
| Cheddar | "usually every week · last 9 days ago" | F via C | same | get_usuals | OK | Seed: every ~7 d, last 9 d. Spec description adds "none visible". |
| Orange juice | "every 10 days" | F via C | same | get_usuals | OK | Seed: every ~10 d, last 6 d ago; the board drops "last 6 days ago" (spec option text has it). |
| Hummus | "almost empty" | C (`report_understanding` state low) | | | OK | Seed: every ~7 d, last 5 d ago. |
| Other field | placeholder "e.g. stopped buying juice" | U | clair_questions answer | | OK | |
| Note | "Noted: you stopped buying orange juice" | C (`save_note` kind fact, app groceries) | clair_notes.text | Sam's Other text | OK | Matches §12.2. Board uses a regex for juice (ponytail comment), fine for a board. |
| Proposal title | "Add 2 to Weekly shop · mark orange juice not usual" | C (`propose_changes` 2 inserts + update usual "no") | groceries/items.name, list, status, usual | confirm | OK | |
| Proposal sub | "Butter, Cheddar · orange juice stops showing as low" | C | | | OK | |
| Card | "Groceries · Weekly shop" · "Add to Groceries" → "Saved to Groceries" · pin "Groceries, just changed" | F | | | OK | Board shows no "4 → 6" delta line that §12.2 specifies ("Weekly shop 4 → 6 to buy"); add it. Backdrop pre-receipt conflict logged in chrome. |

## ClairNotes

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Count | "Notes · 3" | F (count) | clair_notes | `GET /clair/notes` | CONFLICT | Snapshot §8 has exactly 1 note: "n1 (preference) Receipts from Costco go on Costco run." None of the board's 3 is it. |
| Note 1 | "You stopped buying orange juice" · "from a fridge photo, today" | C (`save_note`, fridge beat) | clair_notes.text, source_run_id, created_at | §12.2 | OK | Created by the fridge beat; should not be in the seed before the beat. |
| Note 2 | "Gym is pull day on Saturdays" · "from Workout" | S | clair_notes.text, app_id | | CONFLICT | (a) Pull day is **today, Fri 20 Nov 6 pm** (status line, snapshot). (b) `save_note` accepts only Sam's own words; "from Workout" implies it was derived from app data. (c) FR-C15: facts about Sam's stuff live in apps, not notes. |
| Note 3 | "Don't suggest snacks" · "you said, Tue 17 Nov" | S | clair_notes.text, kind preference, created_at | save_note from a typed turn | SEED-MISSING | Valid preference; not in the snapshot or seed. |
| Toggle | "Turn off notes" · "Clair stops reading and adding notes" | U | none | | GAP-FIELD | No notes on/off setting (workspaces.settings holds pins, credits_monthly; read_level is separate). |
| Delete + Undo | "Deleted: …" · "Undo" | U | clair_notes.deleted_at | `DELETE /clair/notes/{id}` | GAP-INPUT | No restore endpoint for a deleted note. |
| Empty text | "Notes like “stopped buying orange juice” show up here." | UI | | | OK | |

## Build

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Sentence | "Track my subscriptions and warn me before they renew" | U (typed) | clair_messages | `POST /clair/turns` → `propose_app` | CONFLICT | The Build fixture is "Track my plants" (ui-tech-plan §5, prd demo step 8, ClairSheet). The seed already has a Subscriptions app (snapshot §8, ui-tech-plan seed: 7 apps incl. Subscriptions) and Budget's template has a subscriptions collection, so this builds a duplicate. |
| Suggestion chips | "log my lifts and PRs", "plan meals from my pantry", "track internship applications" | UI | | | OK | |
| Patterns | "Subscriptions · 4 blocks", "Lift log · 5 blocks", "Meal plan · 4 blocks", "Job hunt · 4 blocks" ("Skips to preview") | T | none | | GAP-INPUT | FR-B1 patterns (Beta) have no spec files; backend §10 templates are budget, groceries, classes, workout, todos, calendar only. Block counts unverifiable. |

## Preview

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Summary | "Built 4 pieces. Here are 3 layouts." | C (`propose_app`) | change_sets (basted app) | | CONFLICT | Preview's 4 pieces are Renewals, Monthly total, Renewal dates, Under your $40 cap; Arrange's 4 are Renewals, Monthly total, Renewal dates, Add a subscription. `propose_app` returns one spec; how 3 layouts are made isn't specified. |
| Layout names | "List first", "Calendar first", "Summary first" | UI (FR-B4) | | | OK | |
| Name | "Subscriptions" | C | AppSpec.name | propose_app | CONFLICT | Duplicate of the seeded Subscriptions app (see Build). |
| Sample label | "Example rows · cleared when you add it, unless you keep them" + per-row "example" | C | none | | GAP-FIELD | Labelled (good), but `propose_app(name, purpose, spec)` has no slot for example records, so nothing carries them to Connect's "Keep the example rows". |
| Row | "Spotify · renews Sun 22 Nov · $11.99" | C (example) | subscriptions.name, amount, renews | | CONFLICT | Identical to Sam's real seed row (snapshot: "Spotify renews Sun 22 Nov $11.99"), so it is real data, not an example. |
| Row | "Hulu · not opened in 45 days · $9.99" | C (example) | none for "not opened" | | GAP-FIELD | No last-opened field and no way for Quilt to know app usage. Same data behind the seeded "Hulu suggestion ($120 a year)" card. |
| Row | "Adobe CC, student · renews Thu 3 Dec · $13.49" | C (example) | subscriptions.* | | SEED-MISSING | If these are Sam's (Empty: "Bring 4 in from Budget"), the seed must list them. |
| Row | "iCloud 50 GB · renews Wed 9 Dec · $2.99" | C (example) | subscriptions.* | | SEED-MISSING | As above. (Real-world 50 GB price is lower; check realism.) |
| Monthly total | "$38.46 · a month · 4 subscriptions" | F (sum amount, count) | | face/metric | OK | 11.99 + 9.99 + 13.49 + 2.99 = 38.46. Assumes all monthly; needs repeat to normalise. |
| Cap piece | "Under your $40 cap" · "$38.46 of $40 · 96%" | F | none ($40) | | GAP-INPUT | The sentence never gives $40, Budget has no per-category cap; an app `settings` value could hold it, but nothing supplies it. 38.46/40 = 96%. |
| Day strip | F 20 … T 26, 22 highlighted | X (server_now) + F (renews) | | | OK | Weekdays correct. |

## Arrange

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Hint | "Drag the grip to reorder. The rows are examples." | UI | | | OK | |
| Piece | "Renewals · Shown as list · Spotify, Hulu, Adobe, iCloud" | C | AppSpec view | | OK | Same names as Preview. |
| Piece | "Monthly total · $38.46 a month" | F | | | OK | |
| Piece | "Renewal dates · Sun 22: Spotify" | F | | | OK | |
| Piece | "Add a subscription · name, price, renews on" | C | AppSpec form | | CONFLICT | Field names differ from the budget template's subscriptions (`name, amount, renews, repeat`); no field for "not opened" or a cap. Also replaces Preview's cap piece. |
| Views | List / Table / Calendar | U | AppSpec view kind | FR-B5 | OK | |
| Clair hint | "Tell Clair: put the total on top" | U → C | | | GAP-INPUT | Layout tools (`update_block`, `move_block`) are cut; only re-calling `propose_app` during the build could do it, not specified. |

## Connect

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Name | "Subscriptions" | C, editable U | AppSpec.name | FR-B6 | CONFLICT | Duplicate app name (see Build). |
| Dye | lavender selected (of butter, sage, sea glass, apricot, chambray, lavender, pear, blush) | C, editable U | AppSpec.dye | | OK | Matches the `Dye` type in ui-tech-plan. |
| Connection 1 | "Renewal dates → Calendar · Each renewal shows on its day, 3 days warning" (on) | C | collection `calendar: true` | `*dated` | GAP-FIELD | Showing on Calendar is OK; "3 days warning" has no reminder field or job. |
| Connection 2 | "Cost → Budget · Counts in Subscriptions ($40 cap)" (on) | C (stitch) | budget/spend.category | stitch | GAP-FIELD | Budget categories are Groceries, Eating out, Rent, Fun, Transport: no "Subscriptions" option, no per-category cap. A stitch fires on insert, not on each monthly renewal. |
| Connection 3 | "Unused 30 days → Home · Clair suggests cancelling what you don't open" (off) | C | none | | GAP-INPUT | No usage data; off by default, yet Preview already shows "not opened in 45 days". |
| Keep examples | "Keep the example rows" (unchecked) | U | none | | GAP-FIELD | Default matches FR-B6; no carrier for example rows (see Preview). |

## Empty

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| App | "Subscriptions · new" | C (confirmed `propose_app`) | page block | "Add to my apps" | CONFLICT | Duplicate of the seeded Subscriptions app. |
| Connected | "Connected to Calendar, Budget" | F (spec stitches) | AppSpec.stitches / calendar flag | | OK | Matches Connect defaults (1 and 2 on). |
| Ready | "Subscriptions is ready · Add your first one. The fastest way is usually a photo of the bill or email." | UI | | | OK | |
| Import | "Bring 4 in from Budget" | F (count budget/subscriptions) | budget/subscriptions | C (insert + delete) | CONFLICT | Implies 4 subscriptions live in Budget; the snapshot puts them in a separate Subscriptions app. No move-between-apps op (Clair could insert + delete). If the 4 are Spotify/Hulu/Adobe/iCloud, Preview's "example" rows are Sam's real rows. |

## Seed rows the boards imply

Values exactly as shown. ✓ = already in the seed spec; ✗ = missing; ⚠ = conflicts.

**Workout**
- ✓ Pull day, Fri 20 Nov 2026 6:00 pm (status line). ⚠ ClairNotes note says pull day is Saturdays.
- (created by capture, not seed) Gym, Sat 21 Nov 2026 6 pm.

**Budget / spend (November)**
- ✓ month total $788.00 pre-receipt, limit 120000.
- ✗ Eating out rows this week (Mon 16 to Fri 20 Nov) summing **$35.37** across 5 rows (Clair: "From Budget · 6 rows", the 6th is the receipt).
- ✗ Eating out for November totalling **$165**, including **4 rows with note "Blue Copper"**.
- ✗ Groceries spend rows totalling $142.00 (mirroring the trips via stitch) with no grocery spend Mon 16 to Fri 20 Nov before the receipt.
- ✗ Remaining Rent/Fun/Transport rows must make $788.00 − $142 − $165 = $481.00. (Check: plausible rent won't fit; consider lowering or explaining.)
- ✗ "$150" Eating out budget: no field to seed it in.

**Groceries**
- ✓ Weekly shop 12 (incl. Oat milk, Spinach, Eggs, Olive oil), Taco night 5, Costco run 5; usuals Butter/Cheddar/Orange juice/Hummus.
- ✗ Parmesan bought at Corner Market for **$4.29** in the 6-week history (ClairPhoto).
- ✗ Pasta (ClairPhoto "from your Groceries"): not seeded, and Groceries can't express "on hand".
- ⚠ Olive oil shown as owned (ClairPhoto) but is open on Weekly shop.

**Subscriptions** (Preview/Arrange rows; Empty "Bring 4 in from Budget")
- ✓ Spotify, renews Sun 22 Nov 2026, $11.99.
- ✗ Hulu, $9.99, "not opened in 45 days" (no field for the last part; ui-tech-plan Hulu suggestion "$120 a year").
- ✗ Adobe CC, student, renews Thu 3 Dec 2026, $13.49.
- ✗ iCloud 50 GB, renews Wed 9 Dec 2026, $2.99.
- ⚠ Location: Empty says Budget; snapshot §8 / ui-tech-plan say a separate Subscriptions app; templates say Budget & subscriptions is one app (prd-stories AC-4).

**Classes** (created by the ClairShare flow, not seed): 8 ECON 1010 due records, exact match with backend §2.2.

**Clair notes**
- ⚠ Snapshot seed: "Receipts from Costco go on Costco run." (not shown on ClairNotes).
- ✗ "Don't suggest snacks" (you said, Tue 17 Nov).
- ⚠ "Gym is pull day on Saturdays" (from Workout).
- (created by fridge beat) "You stopped buying orange juice" (from a fridge photo, today).

**Queue (Needs your OK · 4)**: receipt ✓; evening check-in, Hulu suggestion ($120 a year), scan insight ($41 less eating out) per ui-tech-plan, but backend §10 says DevDay returns only change_set cards.

**Account**: user name "Sam" (no field); credits "32" (no grant value in spec).

**Cross-board disagreements**
1. Home backdrop pre-receipt ($412, receipt pending) vs ClairResult/ClairFridge/ClairPhoto post-receipt values.
2. Fridge item count: ClairPhoto "9 items" vs ClairFridge "14 things".
3. Pins: boards To-dos vs FR-P1 Workout.
4. Clair header "Answers from your apps only" vs ClairAsk general answer.
5. Build pieces: Preview cap piece vs Arrange form piece.
6. Concert per-day: board/ui-tech-plan "$29" vs fixspec §D "$26".
7. Pull day Friday (status line) vs note "on Saturdays".
