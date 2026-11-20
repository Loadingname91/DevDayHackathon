# Audit C: onboarding boards, Spool, DesignSystem, Home and Flows prototypes

Sources: `spec/backend.md` §2.2, §3, §6, §8, §10 (templates table, line 671 dry-run table), `spec/clair-agent.md` §8 snapshot, `spec/prd.md` FR-O*, FR-H*, FR-C9, FR-T5, `spec/ui-tech-plan.md` §5 seed/fixtures table (lines 228-245), `docs/onboarding.md`, `CLAUDE.md`.

Provenance: U user gesture · C Clair (lands after confirm) · F formula/derived · T template · S seed-only · X system.
Verdicts: OK · GAP-FIELD · GAP-INPUT · GAP-FORMULA · CONFLICT · SEED-MISSING.

Spec facts used throughout:
- Template faces (backend §10): Budget `limit − sum(spend.amount, month)` "left" (unset limit → "Set a monthly amount"); Groceries count to-buy on default list "to buy"; Classes count due open within 7 d "due this week"; Workout count sessions this week where done "this week"; To-dos count done=false "open"; Calendar count `*dated` today "today". Only Budget's empty text is defined.
- Money and Subscriptions chips make ONE app, "Budget & subscriptions" (subscriptions is a tab). No template defines a face for subscriptions.
- backend §2.2 line 671: Calendar "3 today" = Pull day 6 pm, Take out recycling 8 pm, Return library books 9 pm; after receipt 4 today.
- No field anywhere for: user display name, app last-opened / use count, grocery use-by date, external app usage, reminders, "planned" spend, per-category budget limits, workout exercises or duration. Credit grant size: `workspaces.settings.credits_monthly`, no value given.

---

## Welcome (`Welcome.dc.html`, "Day one, skipped picks")

| Data point | Value shown | Provenance | Stored in (app/collection.field) | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting | "Afternoon." | X | `GET /home` `greeting` | server composer | GAP-FORMULA | No rule for time-of-day bands (Morning/Afternoon/Evening) in any spec |
| Status line | "Nothing logged yet. Add a receipt or tell Clair something." | F (empty state) | `GET /home` `status` | composer, FR-O4 | OK | Matches FR-O4 |
| Apps count/state | "No apps yet" | F | page blocks (none) | Skip on "What slips?" | OK | FR-H8 skip path |
| Starter tile | Subscriptions · "the money you forget" | T | template `budget` | tile → Preview/Build | CONFLICT | Templates have no standalone Subscriptions app; Money+Subscriptions = one "Budget & subscriptions" app (onboarding §2.2) |
| Starter tile | Groceries · "from a receipt photo" | T | template `groceries` | tile | OK | |
| Starter tile | Classes · "every due date" | T | template `classes` | tile | OK | |
| Starter tile | Workout · "sets, reps, PRs" | T | template `workout` `sessions {name, at, repeat, done}` | tile | GAP-FIELD | Template has no sets, reps or PR fields |
| Pinned bar | "Your most-used apps get pinned here" | X | `workspaces.settings.pins` (empty) | | OK | |

## OnWelcome

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| (no data points) | Copy only: "Hi. I'm Clair…", "No account needed to start", "I have a quilt · Sign in" | X | auth | anonymous sign-in | OK | Matches FR-O1/O2 |

## OnSlips

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Chips | Money, Groceries, Classes, Workouts, Subscriptions, To-dos | T | client state → `POST /templates/apply {templates}` | user taps | OK | Matches FR-O2 |
| "Clair makes …" line | e.g. "Budget & subscriptions, Groceries and Calendar" | F (chip→template map) | — | client mapping | OK | Matches onboarding §2.2 mapping; Calendar always added. (Copy says "Clair makes" though no Clair call happens; copy only) |

## OnMaking

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| App list | "Budget & subscriptions, Groceries, To-dos and Calendar" | T | page blocks from `api/templates/*.json` | `POST /templates/apply` | OK | Consistent with picks Money+Groceries+To-dos |
| Budget patch face | "Set a monthly amount" | T/F | budget `settings.limit` (unset) | face formula → null → empty text | OK | backend §6, §10 |
| Groceries patch face | "Weekly shop" | T | groceries page `face` | — | GAP-FORMULA | Face is a count ("0 to buy"); no empty-state text defined, and showing the list name is not a face. FR-H7 "face number on every patch" |
| To-dos patch face | "Nothing yet" | T | todos `face` | — | GAP-FORMULA | Face = count open → "0 open"; "Nothing yet" empty text undefined |
| Calendar patch face | "Nothing yet" | T | calendar `face` | — | GAP-FORMULA | Same: "0 today" vs undefined empty text |
| Pins | Budget, Groceries, To-dos, Calendar | T | `settings.pins` | templates apply | OK | Up to 4, Calendar last (onboarding 2.3) |
| Pin label vs app name | "Budget" vs "Budget & subscriptions" | T | page `name` | | CONFLICT | Which is the stored app name? Template table names the app "Budget & subscriptions"; pins/patches say "Budget" |

## OnHome

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting | "Afternoon." | X | `/home.greeting` | composer | GAP-FORMULA | As Welcome |
| Status line | "Nothing logged yet. Add a receipt or tell Clair something." | F | `/home.status` | composer | OK | FR-O4 |
| Your apps count | "Your apps · 4" · "Made from your picks" | F | page blocks | templates apply | OK | |
| Faces | Budget "Set a monthly amount"; Groceries "Weekly shop"; To-dos "Nothing yet"; Calendar "Nothing yet" | T/F | faces | | GAP-FORMULA | Budget OK; other three as OnMaking |
| Pins | Budget, Groceries, To-dos, Calendar | T | `settings.pins` | | OK | |

## OnSheet

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Home behind sheet | same as OnHome | — | — | — | GAP-FORMULA | Same three empty faces |
| Sheet chips | Photo, File; "Hold the Clair button to talk" | X | — | — | OK | Matches onboarding 3.2 |

## OnCamera

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Home behind dialog | same as OnHome | — | — | — | GAP-FORMULA | Same three empty faces |
| Permission state | "Use your camera?" / "Camera is off" | X | OS permission | Capacitor Camera | OK | Matches onboarding permissions table |

## OnCheckin (day-1 evening, guest)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting | "Evening." | X | `/home.greeting` | composer | GAP-FORMULA | No band rule |
| Status line clause 1 | "$35.83 on groceries today." | F | budget/spend or groceries/trips today | composer | GAP-FORMULA | FR-H2 says status always carries "money left this month"; with `limit` unset there is none. No composer rule for an unset limit (spend today instead) |
| Status line clause 2 | "Library books due tomorrow." | F | todos/todos.due | composer (next dated) | CONFLICT | To-dos patch on the same screen says "Nothing yet" (would be "1 open"); no screen shows Sam creating this to-do |
| Needs your OK count | "Needs your OK · 2" (check-in + keep) → 1 | F | `/home.needsOk` | Card kinds `checkin`, `keep` | OK | Both kinds exist in `Card` type (Proto/Beta) |
| Check-in title | "3 things from today" | C (seeded fixture for DevDay per ui-tech-plan line 318) | `Card.checkin.items` | no tool defined | GAP-FORMULA | No server/Clair procedure builds check-in items; FR-C9 only states the rule |
| Check-in item 1 | "Corner Market · $35.83 added" · Budget | C | budget/spend {note Corner Market, amount 3583} | receipt change set, stitch groceries/trips→budget/spend | OK | Only valid if this guest captured that receipt today; Groceries patch should then not read "Weekly shop" and Calendar not "Nothing yet" (trip is `calendar: true` → "1 today") |
| Check-in item 2 | "Return library books · due tomorrow" · To-dos | U/C | todos/todos {title, due} | not shown | CONFLICT | To-dos face "Nothing yet" on the same screen; no on-screen creation that day |
| Check-in item 3 | "Use the chicken and spinach by Tue" · Calendar | C | none | — | GAP-FIELD | No use-by field on groceries/items; not "data already in Quilt" (FR-C9); Calendar face "Nothing yet" contradicts a Calendar item → also CONFLICT |
| Reminder offer | "Want a reminder at 8 pm for these?" / "Reminders at 8 pm" | U | device local notifications (Beta) | "Remind me" | GAP-FIELD | Reminder time not stored anywhere in spec (no table/setting) |
| Keep card | "Keep your quilt · Right now your apps live only on this phone" | X | `is_anonymous` | `Card.keep` | OK | FR-O5 |
| Faces | Budget "Set a monthly amount"; Groceries "Weekly shop"; To-dos "Nothing yet"; Calendar "Nothing yet" | F | faces | | CONFLICT | After a confirmed receipt: Groceries would hold 8 bought rows (face "0 to buy"), Calendar "1 today" (trip), To-dos "1 open". Budget "Set a monthly amount" is consistent (limit unset) |

## OnKeep

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting, status line | "Evening." · "$35.83 on groceries today. Library books due tomorrow." | X/F | `/home` | composer | CONFLICT | Same issues as OnCheckin (to-do vs "Nothing yet") |
| Needs your OK count | "1" → "0" | F | `/home.needsOk` | | OK | |
| Kept line (Google) | "Kept. Your quilt is saved to sam@gmail.com." | U | auth.users.email (linked identity) | `linkIdentity` | OK | onboarding shows "sam@…" |
| Kept line (email) | "Kept. We sent a link to your email to finish." + "Add a device ›" link | U | `email_confirmed_at` null | `updateUser` | CONFLICT | backend §8 / onboarding 6.4: until email confirmed Add a device stays off and the line is "Check your email to finish keeping your quilt." The board shows Add a device in the `kept` branch for email too |
| Retry rule | "Clair asks once more after a few more adds" | X | not stored | — | GAP-FIELD | FR-O5 "after 3 more confirms": no field records Not-now or the confirm count since |
| Faces | 4 empty faces | F | | | CONFLICT | As OnCheckin |

## OnDevice

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Join code | "482 913" (then "730 155" on Get a new code) | X | `join_codes.code_hash` (5 min, single use) | `POST /join-codes` (`secrets.randbelow`) | OK | Matches onboarding 6.4 example |
| Expiry | "expires soon" | X | `join_codes.expires_at` | | OK | Copy is vaguer than onboarding's "expires in 5 minutes" |
| Pins | Budget, Groceries, To-dos, Calendar | T | `settings.pins` | | OK | |

## OnLaptop

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Accepted code | "482913" | X | `join_codes` | `POST /join-codes/redeem` | OK | |
| Result | "Joined. Same quilt as your phone." | X | session swap | `verifyOtp` | OK | |
| Guest workspace claim | "The laptop's own empty guest quilt is gone." | X | workspaces | — | CONFLICT | backend §8: it is orphaned and purged later, not gone |

## OnOffline

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| (no data points) | "Quilt needs a connection to set up." | X | — | — | OK | Matches onboarding error table |

## Spool

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| (no data points) | Expressions, sizes and timings only | — | — | — | OK | No record data shown |

## DesignSystem

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Display sample | "$376 left" | F | budget face | | OK | Canonical post-receipt |
| Title sample | "Evening, Sam." | X | none | — | GAP-FIELD | No user display-name field (auth user, workspace `name` default "My quilt"); demo seed sets no name |
| Heading sample | "Corner Market" | C | groceries/trips.store | receipt | OK | |
| Patch face sample | "$38 a month" | F | subscriptions | — | GAP-FORMULA | No face defined for subscriptions (template has one Budget face); value = Spotify+Hulu+Adobe+iCloud $38.46 |
| Row title sample | "Return library books" | S | todos/todos.title | seed | SEED-MISSING | In ui-tech-plan/snapshot/line 671, not in backend §2.2 seed rows |
| Body sample | "Hulu: 45 days unopened." | C | none | — | GAP-FIELD | Quilt cannot know external app usage; no field |
| Clair line sample | "I read 8 items." | C | understanding event | `report_understanding` | OK | |
| Section label | "Needs your OK · 3" | F | `/home.needsOk` | | OK | Seed queue is 4 (receipt, check-in, Hulu, scan) → 3 after receipt |
| Meta sample | "To-dos · due today" | F | todos.due | | OK | |
| Numbers sample | "$35.83 · 5:41 pm" | C | trips.total, trips.at | receipt | OK | |
| Date format | "6 pm · Sun 22 Nov" | — | — | — | OK | format only |
| App dyes | To-dos butter, Groceries sage, Budget sea glass, Workout apricot, Calendar chambray, Subscriptions lavender, Classes pear, Meals blush | T | page `dye` | | CONFLICT | backend §2.2 Groceries page has `"dye": "pear"`; this board gives Groceries sage and Classes pear. "Meals" has no template |
| Buttons | "Add to 3 apps" | F | ChangeSet.targets | | OK | |

---

## quilt-home.html (Home prototype)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Greeting (evening) | "Evening, Sam." | X | none for name | composer | GAP-FIELD | No display name stored; band rule undefined (GAP-FORMULA too) |
| Greeting (morning/caught) | "Morning, Sam." / "Afternoon, Sam." | X | | | GAP-FIELD | same |
| Status line | "$412 left this month. Pull day at 6 pm." | F | budget face + first Next up | composer | OK | FR-H2/AC-2 exact |
| Status (morning) | "MATH 2270 quiz at 9:40 am" | S | classes | | CONFLICT | Seed classes are ECON 1010, MATH 1210, CS 3500; no MATH 2270 or quiz |
| Status (caught) | "DevDay demo at 3 pm" + "You added a receipt and set a reminder to cancel Hulu today." | S | calendar/events | | CONFLICT | Receipt is 5:41 pm; a 3 pm event still upcoming after it is impossible on the same day. DevDay demo event not seeded |
| Needs your OK (evening) | 4 cards: receipt, check-in, Hulu, scan | S | `/home.needsOk` | | OK | Matches ui-tech-plan queue |
| Receipt card | "From your receipt photo · 5:41 pm", "Corner Market", "$35.83", "8 items. Adding updates 3 apps", Budget "$412 → $376 left", "Add to 3 apps" | C | basted change set | receipt photo / fixture | OK | Canonical |
| Toast after confirm | "Added 8 items to Groceries, Budget and Calendar." | F | change set | | CONFLICT | 8 items go to Groceries only; Budget gets 1 spend, Calendar 1 trip |
| Faces after confirm | Budget $376, Groceries "4 to buy", Calendar "4 today" | F | faces | dry_run | OK | |
| Hulu card | "Hulu hasn't been opened in 45 days. Cancelling it would keep $120 a year." | C | none | — | GAP-FIELD | No field for external app usage; $120 = $9.99×12 (≈$119.88) needs a seeded Hulu row (SEED-MISSING) |
| Hulu actions | "Reminder set: cancel Hulu before it renews on Wed 2 Dec." / "Clair won't ask again for 30 days." | C | none | — | CONFLICT | Flows SUBS gives Hulu renewal day 28 (28 Nov), not 2 Dec. Reminder and 30-day mute have no field (GAP-FIELD) |
| Scan insight | "Weeks you scan grocery receipts, you spend $41 less eating out." | C (seeded fixture) | none | — | GAP-FORMULA | No insight computation defined; needs weeks of eating-out spends in seed (not specified) |
| Check-in card | "3 things from today": "Pull day at 6 pm. Log it after?", "Return library books · due today", "Spotify renews Sun 22 Nov · $11.99" | C (seeded) | `Card.checkin` | — | OK | Matches prd risk row; all items exist in seed (via ui-tech-plan). Builder undefined (see OnCheckin) |
| Check-in review | Pull day "Was at 6 pm. Log it?"; Library books → "Done"; Spotify "remind me Sat" | C | workout/sessions.done, todos.done | | CONFLICT | At DEMO_NOW 5:45 pm Pull day hasn't happened ("Was at 6 pm"); "remind me Sat" has no field (GAP-FIELD) |
| Next up | 6 pm Pull day "Workout · 5 exercises"; 9 pm Return library books "To-dos · due today"; Sun Spotify renews "Subscriptions · $11.99" | F | `*dated` next 3 within 72 h | | CONFLICT | backend line 671 seeds Take out recycling 8 pm today, so next 3 = Pull day, recycling, library books; Spotify drops out. "5 exercises": no field (GAP-FIELD) |
| Next up (morning) | 9:40 am MATH 2270 quiz "Classes · JWB 335"; 3 pm DevDay demo "Lassonde Studios"; 6 pm Pull day | S | | | CONFLICT | JWB 335 is MATH 1210's room (MWF 11:50 am); no quiz record; DevDay demo not seeded |
| Budget face | "$412 left" | F | budget face | | OK | |
| Groceries face | "12 to buy" | F | | | OK | |
| Calendar face | "3 today" | F | `*dated` today | | CONFLICT | Spec-internal: seed class c02 MATH 1210 is MWF 11:50 am; Fri 20 Nov has an occurrence in `*dated` today, so the count is 4 with Pull day, recycling, library books |
| To-dos face | "3 today" | F | todos | | CONFLICT | Template face is count open, label "open", not "today" |
| Workout face | "Pull day 6 pm" | F | workout/sessions | | CONFLICT | Template face is count done this week, "this week" |
| Subscriptions patch | "$38 a month" | F | subscriptions | | CONFLICT | Separate Subscriptions app contradicts template (one Budget & subscriptions app); no face formula (GAP-FORMULA) |
| Classes face | "2 due" → "3 due" after syllabus | F | classes/due | | OK | Label shortened from "due this week" |
| Filler patches (23) | Runs "12 mi wk", Meals "4 planned", Chores "2 left", Savings jar "$140", Journal "6 entries", Assignments "4 open", Sleep "7.1 h", Rent split "$0 owed", Reading list "3 books", Plants "2 to water", Textbooks "$214", Internship apps "6 sent", Water "5 cups", Movies "9 seen", Laundry "Sat", Recipes "14 saved", Side gig "$85 wk", Climbing "3 sends", Exams "Wed 9 Dec", Packing list "0 / 18", Birthdays "Maya Sat", Coffee count "$16 Oct", CS 3500 "Mon" | S | none | — | SEED-MISSING | "Patch stubs" (ui-tech-plan l.318) with literal face strings; a face is a formula over rows, so a stub can't produce these. Seed spec lists none. Exams/CS 3500/Assignments duplicate Classes data |
| Your apps count | "Your apps · 14" (30 in many) | F | page blocks | | SEED-MISSING | Seed spec says 7 apps "+ filler"; count not fixed |
| Patch order / staleness | "Most used first", "not opened in N wk" | F | none | — | GAP-FIELD | No last-opened or use-count field (FR-H7b Beta) |
| Day-one greeting | "Hi, Sam. Let's build your first app." | X | none | | CONFLICT | Guest has no name (onboarding §1.3 note); also GAP-FIELD |
| Day-one tiles | Subscriptions, Groceries, Classes, Workout "sets, reps, PRs" | T | | | CONFLICT | Same as Welcome board |
| Try chips (evening) | "Spent $12 on lunch, gym tomorrow 6 pm" → Budget Eating out $12 "Lunch · today"; Calendar+Workout Gym "Sat 21 Nov, 6 pm" | C | budget/spend, workout/sessions | `propose_changes` | OK | Matches capture fixture |
| Try (morning) | "Spent $5 on coffee" → Eating out $5 | C | budget/spend | | OK | |
| Ask answer | "$412 left until 1 Dec; after $60 you'd have $352, about $32 a day." | C | budget face | `get_faces` | OK | Before-receipt numbers; ui-tech-plan fixture is after-receipt $376/$316/$29 |
| Ask action | "Add to Budget as planned" / "Planned $60 for concert tickets in Budget." | C | none | | GAP-FIELD | No planned/actual field on budget/spend; a spend would lower $ left now |
| Syllabus share | "Found 6 due dates and 2 exams"; "Problem set 1 · Fri 27 Nov", "Midterm 1 · exam · Wed 9 Dec", "Essay draft · Mon 14 Dec"; "3 more due dates and 1 more exam"; "Syllabus · ECON 1010.pdf · 4 pages" | C | classes/due | `propose_changes` | CONFLICT | backend §2.2 canonical syllabus: Problem set 7 Mon 23 Nov, Midterm 2 Tue 1 Dec, … Final exam Wed 16 Dec. Titles and dates differ |
| Syllabus toast | "Added 6 due dates and 2 exams to Classes and Calendar." | C | | | OK | Counts match |

## quilt-flows.html (Flows prototype)

| Data point | Value shown | Provenance | Stored in | Produced by | Verdict | Note |
|---|---|---|---|---|---|---|
| Build: example rows | Spotify "renews Sun 22 Nov" $11.99; Hulu "not opened in 45 days" $9.99; Adobe CC, student "renews Thu 3 Dec" $13.49; iCloud 50 GB "renews Wed 9 Dec" $2.99 | C (Build preview, labelled "example") | preview only, "cleared when you add it" | `propose_app` | OK | As examples. But Home/Budget/Calendar treat these as Sam's real rows → see seed section. Hulu "not opened" GAP-FIELD |
| Build: metric | "$38.46 a month · 4 subscriptions" | F | sum(subscriptions.amount) | built app's face | OK | Built app can define this face |
| Build: progress | "Under your $40 cap", "$38.46 of $40 · 96%" | F | built app progress target 4000 | `propose_app` | OK | Target on the block, like Groceries' 20000 |
| Build: chart | Aug–Nov bars "example" | C | example | | OK | |
| Build: notes | "Cancel anything I haven't opened in a month." | C | example | | GAP-FIELD | Implies usage tracking |
| Build: question | "How early should I warn you before a renewal? 3 days before" | C | none | `ask_user` | GAP-FIELD | No reminder/warning field or mechanism |
| Connections (Subscriptions) | Out Calendar "renewal dates"; Out Budget "monthly cost"; Out Home nudges "unused 30 days" | T/C | stitches | | GAP-FIELD | Subscriptions → budget/spend stitch not declared anywhere; "Home nudges" is not a stitch target; "unused" needs usage data |
| Connections (Calendar) | In Subscriptions, In Workout, In Groceries "use-by dates", Out Home nudges "tomorrow's first event" | F | `*dated` | | GAP-FIELD | No use-by field; Home nudges target undefined |
| Calendar history | "5:41 pm Spotify renewal added from Subscriptions · Clair"; "12:20 pm Subscriptions connected to this app · You"; "Tue Leg day moved to 7 am · You" | C/U | change_sets | | CONFLICT | 5:41 pm is the receipt; nothing adds a Spotify renewal then. Leg day not seeded; moving one session is "Edit this one only" (Later) |
| Calendar "This week" today | "Today · Fri 20 Nov": DevDay demo 3 pm Lassonde Studios; Grocery trip Corner Market 5:41 pm; Pull day 6 pm | F | `*dated` | | CONFLICT | backend l.671: today after receipt = Grocery trip, Pull day, Take out recycling 8 pm, Return library books 9 pm (4). Board omits recycling and library books, adds unseeded DevDay demo; also omits MATH 1210 11:50 am occurrence |
| Calendar Sun 22 Nov | Spotify renews $11.99 "just changed" "from Subscriptions" | S | subscriptions.renews | | SEED-MISSING | Not in backend §2.2; "just changed" with no change in the flow |
| Calendar Mon 23 Nov | "CS 3500 project due · 11:59 pm" | S | classes/due d01 | | CONFLICT | Seed title is "Start CS 3500 project" |
| Calendar Tue 24 Nov | "Spinach use by · from Groceries" | C | none | | GAP-FIELD | No use-by field. Also missing d02 Homework 11 Tue 24 Nov 11:59 pm (CONFLICT) |
| Search data (Budget) | Blue Copper $5.25 Sat 3 Oct; Blue Copper $5.25 Sun 11 Oct; Starbucks $6.10 Mon 19 Oct; Blue Copper $5.25 Fri 6 Nov; Corner Market $35.83 Fri 20 Nov (Groceries); Spotify $11.99 Sun 22 Nov (Subscriptions) | S | budget/spend | | CONFLICT | "Subscriptions" is not a spend category (options: Groceries, Eating out, Rent, Fun, Transport); no stitch makes a spend from a subscription; a spend dated Sun 22 Nov is in the future. Rest SEED-MISSING |
| Search answer | "$16.60 on coffee in October · 3 visits: Blue Copper twice, Starbucks once. From Budget." | F/C | budget/spend | `query_records` | OK | Sums seeded rows (5.25+5.25+6.10) |
| Search data (other) | Groceries Coffee beans, Oat milk "bought · Fri 20 Nov"; To-dos "Buy coffee filters · this week"; Calendar "Coffee with Maya · Sat 21 Nov · 10 am"; Workout "Pull day · today 6 pm" | S | | | SEED-MISSING | Coffee with Maya and Buy coffee filters not seeded; "Buy coffee filters" duplicates the Weekly shop item |
| Budget app header | "$376 left of $800", bar 53% | F | budget settings.limit | | CONFLICT | Canonical limit $1,200 (120000). 53% matches $800 |
| Budget rows | Blue Copper Fri 6 Nov $5.25; Corner Market Fri 20 Nov $35.83; Spotify Sun 22 Nov $11.99 | S | budget/spend | | CONFLICT | Spotify row as above |
| Groceries lists | Weekly shop "4 to buy" "Fri 20 Nov"; Taco night 5 "Sat 21 Nov"; Costco run 5 "once a month" | F/S | items.list options + hint | | CONFLICT | Counts OK; seed has no hint on Weekly shop ("Fri 20 Nov") |
| Groceries open rows | Coffee filters "1 box", Tortillas "1 pack", Olive oil "1 bottle", Dish soap "1 bottle" | S | items.qty | | SEED-MISSING | Names match seed; qty not in seed |
| Groceries bought rows | Oat milk "1 carton", Eggs "12", Bananas "1 bunch", Chicken thighs "2 lb", Rice "2 lb bag", Spinach "1 bag · use by Tue", Greek yogurt "32 oz", Coffee beans "1 bag", all "from receipt" | C | items.qty, trip | receipt | CONFLICT | Seed Eggs qty "1 dozen" (not "12"); receipt line "Rice 5 lb" (not "2 lb bag"); "use by Tue" GAP-FIELD |
| Bought section | "Bought at Corner Market · 8 · Fri 20 Nov" | F | items.trip, trips.at | | OK | |
| Taco night rows | Ground beef 1 lb, Avocados 3, Limes 4, Salsa 1 jar, Shredded cheese 8 oz | S | items | | SEED-MISSING | Names match; qty not in seed (Limes seed has no qty) |
| Costco run rows | Paper towels 12 rolls, Laundry pods 1 tub, Frozen berries 3 lb, Almonds 2 lb, Toilet paper 24 rolls | S | items | | SEED-MISSING | Names match; qty not in seed |
| Settings Home | "Evening, Sam." "3 things to look at today"; "Clair added a receipt · 8 rows into Groceries, Budget and Calendar · 5:41 pm" | C | change_sets | | CONFLICT | Receipt writes 10 blocks (1 trip, 8 items, 1 spend), not 8 rows across 3 apps. Name GAP-FIELD |
| Activity | "Added 8 items from your Corner Market receipt · 5:41 pm"; "Built the Subscriptions app … 12:20 pm"; "Set a reminder to cancel Hulu · Subscriptions · yesterday"; "Moved Leg day to 7 am · Workout · Tuesday" | C/U | change_sets | | CONFLICT | Hulu reminder "yesterday" predates the Subscriptions app built today 12:20 pm; quilt-home says the reminder was set "today" and still shows the Hulu card. A built Subscriptions app also contradicts the template's single Budget & subscriptions app. Leg day not seeded |
| Credits | "32 of 50 left · resets Tue 1 Dec"; laptop "Sam · 32 credits", chat header "32 credits" | X | usage_ledger, `settings.credits_monthly` | `GET /usage` | SEED-MISSING | Grant size (50) and the seeded spend (18) are in no spec |
| Credit costs | chat step 1, photo 5, build 10; "See Plus · $6 a month" | X | usage_ledger.kind | | OK | FR-T5 / pitch proposal |
| Read level | Full help / Field names only / Nothing | X | workspaces.read_level | `PATCH /settings` | OK | |
| Laptop Budget | "$376 left of $800" "was $412 · Corner Market receipt from your phone, 5:41 pm" | F | | | CONFLICT | $800 vs $1,200 |
| Laptop categories | Groceries "$177.83 / $200"; Eating out "$165 / $150" (over); Transport "$42 / $80"; Subscriptions "$38.46 / $40" | F | none for limits | | GAP-FIELD | No per-category limit field in Budget template. Also spends total $423.29, but canonical month spend is $823.83 (CONFLICT) |
| Laptop recent | Corner Market Groceries just now $35.83; Union food court Eating out yesterday $11.40; Gas Transport Tue $28.00; Spotify Subscriptions Sun 22 Nov $11.99 | S/C | budget/spend | | CONFLICT | Spotify row as above; others SEED-MISSING |
| Laptop receipt detail | Oat milk $3.49, Eggs, dozen $4.29, Bananas $1.87, Chicken thighs $8.62, + 4 more; also in Groceries, Calendar | C | items.price | receipt | OK | Matches AB-2 |
| Laptop app list | Budget, Groceries, Calendar, To-dos, Workout, Subscriptions | S | pages | | CONFLICT | Classes missing from Sam's 7 apps; Subscriptions separate app |
| Capture fixtures | "Coffee $4.50, study group 2 pm" → Eating out $4.50, Study group Fri 20 Nov 2 pm; "Groceries $23, gym done 45 min" → Budget+Groceries $23, Workout Gym 45 min | C | budget/spend, calendar/events, workout/sessions | | GAP-FIELD | Workout sessions have no duration field ("45 min") |
| Ask fixtures | "Yes. $376 left until 1 Dec; after $60 you'd have $316, about $29 a day."; "How much did I spend today? $35.83, all at Corner Market. $376 left until 1 Dec." | C | | `get_faces`, `query_records` | OK | Matches ui-tech-plan fixture |
| Ask fixture | "What's due this week? CS 3500 project, Mon 23 Nov at 11:59 pm. Spotify renews Sun 22 Nov ($11.99)." | C | classes/due, subscriptions | | CONFLICT | Omits d02 Homework 11 (MATH 1210) Tue 24 Nov 11:59 pm, which the "2 due this week" face counts |

---

## Seed rows the boards imply

Exact values as shown. "Spec" = whether `spec/backend.md` §2.2 lists it.

**Budget (`budget/spend`, `settings.limit`)**
| Row | Values | Spec | Disagreement |
|---|---|---|---|
| limit | $800 (flows Budget, laptop) | §2.2: 120000 ($1,200) | CONFLICT |
| Blue Copper | $5.25, Eating out, Sat 3 Oct | no | |
| Blue Copper | $5.25, Eating out, Sun 11 Oct | no | |
| Starbucks | $6.10, Eating out, Mon 19 Oct | no | |
| Blue Copper | $5.25, Eating out, Fri 6 Nov | no | |
| Gas | $28.00, Transport, Tue (17 Nov) | no | |
| Union food court | $11.40, Eating out, yesterday (Thu 19 Nov) | no | |
| Corner Market | $35.83, Groceries, Fri 20 Nov 5:41 pm | yes (via stitch) | |
| Spotify | $11.99, "Subscriptions", Sun 22 Nov | no | Category not an option; future date; no stitch |
| Nov category totals | Groceries $177.83, Eating out $165, Transport $42, Subscriptions $38.46 | no | Sum $423.29 vs canonical $823.83 after receipt ($788 before) |
| Coffee count | "$16 Oct" (filler patch) | no | consistent with $16.60 |

**Groceries** – names, lists and counts agree with §2.2 (12/5/5, 12 → 4). Additions: qty values (Coffee filters 1 box, Tortillas 1 pack, Olive oil 1 bottle, Dish soap 1 bottle, Ground beef 1 lb, Avocados 3, Limes 4, Salsa 1 jar, Shredded cheese 8 oz, Paper towels 12 rolls, Laundry pods 1 tub, Frozen berries 3 lb, Almonds 2 lb, Toilet paper 24 rolls); receipt items Oat milk 1 carton, Eggs "12" (seed "1 dozen"), Bananas 1 bunch, Chicken thighs 2 lb, Rice "2 lb bag" (receipt "5 lb"), Spinach 1 bag "use by Tue" (no field), Greek yogurt 32 oz, Coffee beans 1 bag. Weekly shop hint "Fri 20 Nov" (seed: none).

**To-dos (`todos/todos`)**
| Row | Values | Spec |
|---|---|---|
| Return library books | due Fri 20 Nov 9 pm, open | ui-tech-plan/snapshot/l.671 only, not §2.2 rows |
| Take out recycling | due Fri 20 Nov 8 pm, weekly Fri | §2.2 worked example + l.671; missing from every board's Next up / check-in / Calendar |
| Buy coffee filters | "this week" | no; duplicates grocery item |
| (guest) Return library books | "due tomorrow" (OnCheckin) | guest-only; never created on screen |
| To-dos face | "3 today" | Template says count open "open" |

**Workout (`workout/sessions`)**
| Row | Values | Spec |
|---|---|---|
| Pull day | Fri 20 Nov 6 pm, "5 exercises" | no (exercises has no field) |
| Leg day | moved to 7 am Tue | no |
| Gym | Sat 21 Nov 6 pm (capture fixture, after confirm) | fixture only |

**Subscriptions (`budget/subscriptions` per template; a separate app on boards)**
| Row | Values | Spec |
|---|---|---|
| Spotify | $11.99, renews Sun 22 Nov | no |
| Hulu | $9.99, renews day 28 (flows) vs "Wed 2 Dec" (home); "not opened in 45 days" | no; renewal dates disagree; usage has no field |
| Adobe CC, student | $13.49, renews Thu 3 Dec | no |
| iCloud 50 GB | $2.99, renews Wed 9 Dec | no |
| Total | $38.46 / "$38 a month"; cap $40 | no face in template |

**Calendar (`calendar/events`)**
| Row | Values | Spec |
|---|---|---|
| DevDay demo | Fri 20 Nov 3 pm, Lassonde Studios | no; would make today 4 (5 with MATH 1210) |
| Coffee with Maya | Sat 21 Nov 10 am | no |
| Today count | "3 today" → "4 today" | l.671 lists Pull day, recycling, library books; but MATH 1210 MWF 11:50 am also falls on Fri 20 Nov |

**Classes**
| Row | Values | Spec |
|---|---|---|
| CS 3500 project | "CS 3500 project due", Mon 23 Nov 11:59 pm | seed title "Start CS 3500 project" |
| Homework 11 | (never shown) | seed d02 Tue 24 Nov; missing from flows Calendar and "What's due" answer |
| MATH 2270 quiz | 9:40 am, JWB 335 (home, morning) | not in seed (JWB 335 = MATH 1210) |
| Syllabus (home share) | Problem set 1 Fri 27 Nov; Midterm 1 Wed 9 Dec; Essay draft Mon 14 Dec | contradicts canonical PS7 Mon 23 Nov … Final exam Wed 16 Dec |

**Home queue / Clair**
| Item | Values | Spec |
|---|---|---|
| Queue | receipt, check-in, Hulu ($120 a year), scan ($41 less eating out) | ui-tech-plan yes; producers undefined |
| Check-in (Sam) | Pull day 6 pm; Return library books due today; Spotify renews Sun 22 Nov $11.99 | prd risk row yes |
| Check-in (guest, OnCheckin) | Corner Market $35.83 added; Return library books due tomorrow; Use the chicken and spinach by Tue | third item has no data source |
| Credits | 32 of 50, resets Tue 1 Dec | grant size not in spec |
| Join code | 482 913 (alt 730 155) | onboarding example |
| Kept email | sam@gmail.com | onboarding "sam@…" |
| Filler apps | 23 stub patches with literal faces (listed in quilt-home table) | "filler patches" only; no rows |
