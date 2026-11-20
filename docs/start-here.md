# Start here

Last updated late on Thu 19 Nov 2026, the night before DevDay. Open this first on any device: clone the repo, open Claude Code in it, and tell it which item you're picking up.

## Where things stand

Quilt is an app builder. You describe an app and Clair builds it from the shared blocks. Every app is connected to your calendar, your budget and your other apps, and Clair can read across all of them. Nothing changes until you tap OK, and everything is live on the phone and the laptop. The plain-words version is `docs/product.md`.

The plan changed three times tonight; this is the last version (`spec/adr/010-web-only-devday-planner-cut.md`):

- **It's a website for DevDay.** The phone opens it from its Home screen; the laptop uses the same site. There is no Android APK. A native app comes after.
- **The pitch is Shark Tank style,** with two pieces of screen work: a **recording** of Clair building three apps from three sentences (a calorie tracker, a running tracker, a private cycle tracker), then a **live** run of "Plan my training for next week".
- **The live planner is broad.** Clair reads nine apps and Google Calendar, moves the gym sessions that clash, adds two runs toward a 10K, a recovery to-do and one grocery item, and gives a reason for each. It's built in four steps so there is always a smaller version that works.
- **Tonight we build the core:** apps drawn from blocks, Home, a typed sentence to Clair, a card, OK, Undo, and sync between two devices. The demo account has 12 apps.
- **Tomorrow we build the workflow engine,** the feature the judges see, with the planner as its first rule, plus the app building needed for the recording, plus Google Calendar. You asked for all of it. It is more than two people are likely to finish, so the order below matters.
- The Car photo build, the whiteboard and the fridge are not built. The grocery receipt is last.

The script is `docs/demo-day.md`. The build order is `spec/backend.md` §13.

## Who builds what

Hitesh builds the frontend: everything in `web/`. His teammate builds the backend: the API in `api/`, the database, Google sign-in and Clair.

The frontend doesn't wait for the backend. It is built first against mock data, which is a set of saved answers copied from the demo seed, and each screen is switched over to the real API as that part of the API goes live. A screen that only works on mock data isn't finished, and mock data is never shown on stage.

The two halves meet at the contract: the list of API calls and the shape of each answer. If either side needs to change it, they change the spec and add a line to the log in `spec/split.md`, so the other person's Claude Code sees it on the next pull.

If you're picking this up on a new machine, tell Claude Code which side you're on. `spec/split.md` has the rest.

## Before the pitch, in order

1. **Tonight: the base.** Steps T1 to T4 in `spec/backend.md` §13. It's done when you can type "spent $12 on lunch" on the phone, tap Add, see $412 become $400 on the laptop, and Undo.
2. **Tonight: Google setup.** Create the Google Cloud project, turn on the Calendar API, set the consent screen to testing, add the demo Google account as a test user, and make the four demo events (`docs/demo-day.md` section 2). This is settings, not code.
3. **Go/no-go at 10:00 tomorrow.** If the base doesn't run on the phone's browser, the day goes to finishing it.
4. **Tomorrow, in this order** (`spec/backend.md` §13, D1 to D10):
   1. The safe point: the planner's first step (four lifts) and the Sunday rule, on seeded Google events.
   2. App building for the three sentences. Record the clip by early afternoon.
   3. The planner's other three steps: runs, the cycle and calorie lines, recovery and groceries.
   4. Google Calendar sign-in.
   5. The appointment check, then the rest of the engine (rules that write rows, rules described in words, the scheduled run), then the grocery receipt.
5. **Freeze two hours before the pitch.** Record the fallback run and rehearse.
6. **Put up the waitlist page** with a real price ($6 a month, $4 for students) and an "Import from Notion / Notes / Obsidian" button. Its sign-ups fill the [N] in pitch beats 2 and 6.
7. **Make the deck** for the slide beats, with real numbers only.

## Decided on Nov 19

| Decision | Answer |
| --- | --- |
| Demo | A recorded clip of Clair building three apps, then the live training planner as the first rule of the workflow engine |
| The planner | A full week: lifts, runs, recovery and a grocery item, from Calendar, Google Calendar, Classes, To-dos, Running, Calories and Cycle |
| Scope tomorrow | All of it, in the order above, cutting from the end |
| Client for DevDay | Website only, on phone and laptop |
| Where it runs | The website's files on Vercel. The API is one ordinary Python server on Railway, not Vercel functions (`spec/adr/012-api-on-railway-long-running-server.md`) |
| Who builds what | Hitesh the frontend, on mock data first; his teammate the backend (`spec/split.md`) |
| Google Calendar | Read-only, through Google sign-in; writing back to Google is later |
| Encryption | None for the hackathon; planned later |
| Which AI model does what, after DevDay | Haiku 5.5 for photos and chat, Sonnet 5.5 for building. Opus 5.5 for everything at DevDay |
| Import and export | Free on every plan |
| Student price | $4 a month or $15 a semester, next to Plus at $6 |
| Calories, Running, Cycle, Meditation | In the hackathon build as simple apps (12 apps in the demo account). No photo meals, pace, timer, charts or predictions yet. Clair reads Cycle only when its switch is on; it is on in the demo account |
| Appointment reminders | In the hackathon build as the engine's second rule; the reminder is stored, no notification is sent |
| Appointments | A kind on Calendar events, not a separate app |
| Clair's pattern checks | On Plus, with a monthly cap |
| Health data | In the plan after DevDay: read-only, Android first, on Plus |
| Cycle app | Only with its own switch for what Clair can read |
| Tab names for the starter apps | Set; listed in `docs/product.md` |

## Decisions waiting on you

| Decision | Options | Where to look |
| --- | --- | --- |
| What to tell the DevDay organisers | The application said the feature built on the day is the receipt. It's now the workflow engine. Tell them, or be ready to say so if asked | `spec/prd.md`, "Event boundary" |
| The native app after DevDay | Capacitor (keeps this code), React Native (rewrites the screens) or fully native | `spec/adr/010-web-only-devday-planner-cut.md` |
| Does Calories set a daily target | The big calorie apps work one out at setup. Suggested: offer it, with a clear "Just log" option | `docs/product.md` |
| Dark mode for DevDay | The look is picked (Soft Quilt in the Mint colours, light and dark, ADR-013). Decide whether the build ships dark mode or just light | `spec/adr/009-soft-quilt-look-pickable-grounds.md` |
| The first job new users see | The business review's three reviewers chose a class job: notes and syllabi filed into the right course | The review was removed from the repo; see the note at the end |
| Pitch timing | The pitch doc says to say what Quilt is within 30 seconds; the YC advice it quotes says 20 | `docs/pitch.md` |
| Smaller calls | A guest can't add a second device until they add an email. How long guest accounts, guest credits and photos are kept | `spec/prd.md` open questions |

## Parked for after DevDay

- The rest of the workflow engine. Version 1 is tomorrow's build. Date triggers, reminders, sending email, outside triggers and plan limits wait, along with the "Internship hunt" showcase app (`spec/workflows.md`).
- The deeper versions of the new apps: meals from a photo, charts, a meditation timer, cycle predictions, the planner reading Calories or Cycle, phone notifications, health data from the phone (`docs/product.md`).
- Building an app from a photo, or from any sentence other than the three in the clip. The Car build from a photo is specified (`spec/clair-agent.md` §12.0) and not built.
- Fixing old numbers on the boards. The boards now wear the Soft Quilt look, but some still show old numbers; the fixes are listed in `spec/prd-data-provenance.md` (epic E5). The design-system board still describes the old look and needs a Soft Quilt version.
- Data fields the boards assumed. Category limits, reminders, Workout sets, your name and recently opened apps are epics E3 and E4 of `spec/prd-data-provenance.md`.

## Docs that are behind

These still lean on the receipt, the Car build or the old look. They're fine to read but shouldn't be copied from until they're updated:

- `.impeccable/surfaces/app.md` describes the old Quilter's Workbench look.
- In `docs/pitch.md`, the application answer "What will you build during DevDay?" still describes the receipt. If the application is already submitted, leave it. The pitch script, the MVP section and the plans table are up to date.
- The design boards and prototypes show the receipt flow. There are no boards for the planner card, "from Google" rows or the Workflows tab.
- Older sections of the specs still say "APK" or "Capacitor" in places; read them as the website on the phone.

## Where everything lives

| Folder | What's in it |
| --- | --- |
| `docs/` | Written for people: this page, the product in plain words, the pitch, the demo-day script and the Home research |
| `spec/` | Written for building: requirements, the backend and seed, Clair's agent, the UI plan, the data provenance PRD and its audit, parked workflows, and decision records in `spec/adr/` |
| `design/` | The Home, Flows and motion prototypes, the design notes and the generators. The boards are on the design canvas: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P, which links to every other Quilt page |
| `setup/` | Claude Code settings, hook and skills list to copy onto a new machine |

`README.md` is the repo map, and `CLAUDE.md` is the map Claude Code reads first.

## Removed on Nov 19

To clear the decks before building, these were taken out of the repo: the business review (`founder/`), the generated canvas boards, the design book, the board tests, the early design explorations, the onboarding journey, the Sam persona and the tabOS app audit. Nothing is lost: they are in git at commit `ee70002`, and `git checkout ee70002 -- founder` (or any other path) brings one back. Some older sections of the specs still mention those paths.
