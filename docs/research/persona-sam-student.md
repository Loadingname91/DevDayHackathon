# Sam, the Forgetting-Tax Student

A U of U undergrad who runs their whole life from a phone and pays a "forgetting tax": renewals they forgot to cancel, late fees, groceries that go off, deadlines that sneak up. They will log something only if it takes less time than the checkout line.

| Field | Value |
| --- | --- |
| Persona ID | PU-001 |
| Type | Primary |
| Product scope | Home, app view (budget, groceries, gym, to-dos, calendar), Clair build, Clair photo fill, the Quilt design system |
| Valid for | Full-time undergrads (18 to 24) at the University of Utah on a tight monthly budget, phone-first, managing their own money for the first time |
| Not valid for | Parents, caregivers, freelancers (later personas); grad students with a stipend and family; power users who already live in Notion or spreadsheets |
| Confidence | Proto: derived from the founders' pitch doc and category benchmarks; no interviews or survey yet |
| Last validated | 2026-11-18 (not validated; drafted) |
| Owner | Quilt founding team (product + design) |

The Persona Card is the daily-use reference. Sections 1 to 4 cover context and motivation, sections 5 to 8 cover behavior, and sections 9 to 11 turn the persona into product and design decisions. Evidence & Confidence says how far to trust it.

---

## Persona Card

**Sam, the Forgetting-Tax Student**
Sam is a second-year student who pays for Spotify, Hulu, Adobe CC and iCloud, tracks lifts in one app, to-dos in another and money in their head. Nothing connects, so the budget is always a guess and renewals arrive as surprises. Sam is the person Quilt's DevDay demo has to convince in 90 seconds.

**Key quote (assumed, to validate in survey):** "I'd track my spending if it didn't mean typing every receipt in."

**Goals.** Know how much is left this month without doing math; stop paying for things they don't use; keep the gym streak and the deadlines from colliding; feel like they have it together.

**Frustrations.** Logging takes longer than the purchase; apps that each want a login and a subscription; finance apps that demand a bank login; trackers that look like accounting software or a cold dashboard.

**Design rules: always.** Capture in one tap or one photo, from the bottom third of the screen. Show the effect of an entry on other apps immediately. Show what Clair will change before it changes it, with undo.

**Design rules: never.** Never use red or alarm styling for money, because it reads as shame. Never require setup before the first useful screen. Never make Sam read jargon (no "workspace", "database", "schema").

---

## 1. Demographics & Identity

| Attribute | Detail |
| --- | --- |
| Age | 18 to 24 (assumed; most likely 19 to 21) |
| Location | Salt Lake City, on or near campus |
| Education | Undergraduate, University of Utah |
| Role | Student; part-time job *(assumed)* |
| Company size | n/a (personal use) |
| Team | Solo; shares some costs with 1 to 3 roommates |
| Reports to | n/a; parents may cover part of rent or phone plan *(assumed)* |
| Stakeholders | Roommates (split bills), parents (asks "where does the money go"), professors (deadlines) |
| Purchasing role | Decision-maker and end user; price-sensitive, pays monthly by card |
| Accessibility | Uses the phone one-handed while walking or in a line; bright store and gym lighting; often glancing, not reading |

Sam is managing money alone for the first time and building habits that will last, like budgeting, cancelling and planning. Tools that feel grown-up without feeling corporate win. Tools that feel like homework lose.

Small amounts matter. A forgotten $13 renewal is a week of lunches, so trust is earned through small, visible savings.

---

## 2. Technology & Environment Context

| Tool | Role |
| --- | --- |
| iPhone or Android, Notes app | Catch-all for lists, grocery notes, random ideas |
| Banking app | Checks balance; does not categorize well; no subscriptions view |
| Gym tracker *(assumed, e.g. Hevy)* | Logs sets; data trapped in that app |
| Canvas, Google Calendar *(assumed)* | Classes and due dates |
| Spotify, Hulu, Adobe, iCloud | Paid subscriptions, renewal dates scattered across emails |

Sam is fluent with apps. They install and drop apps in minutes, use widgets and share sheets, and take photos of everything. They do not want to build relations, formulas or templates, and a blank canvas stalls them.

Sam tries apps fast and drops them fast. Day-30 retention for productivity and fitness apps sits around 8 to 9% (pitch doc benchmark). Sam stays if the app pays back in the first session and logging stays effortless.

Most use happens on the move, in 10 to 60 second bursts: in the checkout line, between sets, walking to class. The laptop comes out for planning at night or on Sunday.

---

## 3. Jobs to Be Done

**Functional.** When I've just bought something or finished a workout, I need to log it in seconds so that my budget, lists and progress stay true without a weekly catch-up session.

**Emotional.** When I open my money stuff, I want to feel calm and in control without feeling judged, so that I keep looking and don't start avoiding it.

**Social.** Sam wants to be the roommate who knows who owes what and the friend who "has their life together", and might share a screenshot of a good month the way people share a Spotify Wrapped.

**Underlying.** Sam wants to stop paying for what they forget and to have one place that is theirs and grows with them, in place of five rented apps built for someone else.

---

## 4. Goals & Motivations

**Life goal.** Graduate without debt surprises, stay healthy, and feel like an adult who runs their own life.

**Know what's left.** One number for "left this month" that updates itself. The product must compute across groceries, eating out and subscriptions without manual entry.

**Cut waste.** Spot unused subscriptions before renewal. The product must surface renewals and usage, and make cancelling a one-tap decision.

**Keep the week from colliding.** See workouts, deadlines and renewals on one calendar. The product must pull dates from every app.

**How it should feel.** Personal and handmade, like something Sam owns; a bank or an enterprise tool is the look to avoid. Quick, so every capture finishes before the moment passes. Safe, so nothing changes behind their back and every change can be undone.

---

## 5. Behavioral Patterns & Mental Models

Sam thinks in piles: "my gym stuff", "money stuff", "school stuff". They feel the links between piles ("groceries are part of my budget") but never set them up the way a database would. Sam already collects and displays personal artifacts: stickers on a laptop, patches on a jacket, screenshot receipts of their music taste. A design language that treats each app as a personal object they own, and that makes the links visible, matches how Sam already thinks (assumed; validate in survey).

Sam is mostly reactive. They log in the moment and review on Sunday night, so capture needs to take near-zero effort and review needs to be glanceable.

Sam accepts an imperfect receipt read if they can confirm or fix it in one tap. They will not tolerate wrong data they can't see.

If capture fails twice or takes more than a few taps, Sam goes back to the Notes app. This two-strikes rule is a proxy threshold and unvalidated.

---

## 6. Decision-Making & Trust Patterns

Trust comes from visible savings. One "you saved $120 a year" moment builds more trust than any feature list, and one wrong charge or silent change breaks it.

Before adopting an app, Sam asks: "Is it free to start? Does it want my bank login? Does it work on my phone right now? Will I have to set it up?"

Sam is risk-averse with money data and auto-charges, and risk-tolerant with trying new apps and AI features.

Sam learns features from a friend's screen or a 15-second video, rarely from settings, so discoverability has to live in the first screens.

---

## 7. Workflow & Collaboration Context

Classes, work shifts and the gym leave 10 to 60 second gaps, with one longer planning block on Sunday.

Sam creates and consumes alone, though roommates share bills and groceries (sharing is out of MVP scope).

Roommates pay late or forget, and Sam tracks split bills in a group chat. This is future "quilting circle" territory.

Sam depends on dates set by others, Canvas deadlines and subscription renewal emails, and can't control their timing.

---

## 8. Current Alternatives & Workarounds

Today Sam combines the Notes app and the bank app: a grocery list in Notes, a balance check in the bank app, mental math for the rest. The setup persists because it's free and instant.

Quilt enters at the receipt moment. A photo replaces typing, and the effect shows up across apps. That position is fragile until capture is faster than the Notes app.

Sam would fire Quilt over logging that takes longer than the purchase, a misread receipt saved without asking, or a surprise charge.

---

## 9. Pain Points & Unmet Needs

**Typing receipts.** Manual entry is the pitch doc's named reason logging fails ("personal tracking fails at the logging"). The week-two drop-off is a hypothesis to check in the survey.

**Invisible renewals.** Renewal dates live in emails, and Sam pays for unused services for months.

**Islands of data.** Gym, money and deadlines never meet, so Sam can't see that a heavy deadline week also wrecks the food budget.

**Apps that judge.** "No red" is a founder brand decision from the pitch doc. Our hypothesis is that red overspend warnings feel like scolding. If the survey disagrees, the rule still holds because urgency is carried by weight, position and texture.

**Blank-canvas paralysis.** "What do you want to track?" stalls them. They need a ready app to change.

---

## 10. Success Definition & Quality Bar

**Accuracy.** Money must be right to the cent once confirmed. Drafts may be rough if they are clearly marked as drafts.

**Timeliness.** A capture is "on time" if it's done before Sam leaves the checkout or starts the next set.

**Self-sufficiency.** Home alone should answer "how am I doing this week?" without opening an app.

**Quality bar by context.** In the checkout line: one photo, one confirm. In the gym: one-handed, key numbers at 28 px or larger and 7:1 contrast for arm's-length reading in bright light *(proposed)*. On Sunday on the laptop: the phone layout scaled up for the MVP; a denser planning view is post-MVP.

---

## 11. Design Principles & Tradeoff Heuristics

**Capture over configuration.** If a choice adds a setup step to save a capture step, cut the setup.

**Show the stitch, then settle.** Make cross-app effects visible (what changed where) until Sam has seen them, then return the screen to calm.

**Draft over silent save.** Anything Clair proposes looks unmistakably provisional until Sam confirms it.

**Warm over clinical (founder preference, untested for money trust).** Use the personal, handmade expression for chrome, navigation and Clair. Keep numbers in clean, high-contrast data type.

**Ink over red.** Urgency is carried by weight, position and texture, never by alarm colour.

**Ready apps over blank canvas.** Start from a filled example Sam edits.

---

## Evidence & Confidence

| Source | Type | Detail |
| --- | --- | --- |
| D1 | Founders' strategy doc | `docs/pitch.md`, Nov 15 2026: first user, pains, competitors, MVP scope |
| D2 | Category benchmark | Day-30 retention ~8 to 9% for productivity and fitness apps (cited in D1) |
| D3 | Design artifacts | Claude canvas "Quilt clickable mock" (17 screens) and Stitch "TabOS" prototype; show assumed behaviors, not evidence |

**Validated.** Nothing yet. Sections 3, 8 and 9 are consistent with the category benchmark and competitor positioning in D1.

**Assumed.** Everything else, especially the key quote, the "piles and personal artifacts" mental model (section 5), the no-red emotional response (section 9), and the Receiptify/Wrapped-style sharing behavior (section 3). Validate with the planned 2-minute U of U survey.

**Open questions.** (1) How many paid apps does a U of U student pay for, and how much a month? (2) Would they photograph a receipt to log it, or do they mostly pay by card with no paper receipt? (3) Does warm, handmade styling raise or lower trust for money data compared with a clean bank-like look?

**Governance.** Re-review after the survey closes (target Thu Nov 19, 2026; if fewer than 20 answers, keep the Proto label and say so in the pitch) and again after the first 20 beta users. Retire or split if the survey shows two distinct student segments.
