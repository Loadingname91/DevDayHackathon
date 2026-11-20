# Instruments: what changed and how they're handled

Before, every app was a list plus a form. Now each app opens on a block built for what it's for. All of it runs on mock data, and the contract for the backend is written into the specs.

## How they're handled

- **Same renderer, more block kinds.** Apps are still JSON specs of tabs and blocks. I added 11 block kinds beside the existing ones: `gauge`, `bars`, `ring`, `countdown`, `strip`, `picks`, `checklist`, `days`, `next`, `timer`, `month`. `blocks/index.tsx` picks the component for each kind.
- **The server computes, the client lays out.** Figures like "$412 left", "66%", "22 days to go" and "1,140 of 2,200" arrive in `values[blockId]`. The server also writes each app's status sentence (`status`, with `**bold**` figures). The client never does the maths or reads the device clock for "today"; it uses `server_now`.
- **What the client does measure:** gesture time (the meditation and run timers, the Workout session clock), the "New best" check while logging a set, and the row counts in section labels. It also filters the rows the server sends, using the `within` ops (`today`, `week`, `past`, `future`, `7d`, `-7d`) and the new `empty` op.

## What each app opens on

| App | Instrument |
|---|---|
| Budget | hero figure with bar, "Where it went" category bars with a cross-hatch for over-limit (no red), Subscriptions, Recent |
| Groceries | list switcher, sectioned checklist with swipe, "Bought in the last week", spend bar |
| To-dos | Overdue / Today / Coming up / Someday / Done sections, pinned add field |
| Calendar | Day timeline, Week and Month views |
| Workout | next-up card with Start, weekly strip, Log a set screen |
| Running | race countdown, stopwatch, week strip |
| Meditation | countdown timer with mood before and after |
| Calories | ring against the target, one-tap "Again" foods |
| Cycle | month grid of logged days, no predictions |

## Writes

All use the existing endpoints, with Undo through change-sets.

- **Timer and picks:** one `POST /records`. The server stamps the time.
- **Log a set:** a `POST /records` per set, then `POST /records/{id}/complete {occurrence, minutes}` at the end.
- **Checklist:** ticking uses `complete`, and swiping deletes with `DELETE`.
- **Edit sheet:** `PATCH` with `base_version`.
- **Month log:** `POST` or `PATCH` for a day.

## What the backend now has to build

- `spec/ui-tech-plan.md` §3 has the new types.
- `spec/backend.md` §10 lists what the server computes for each instrument, with worked values at the demo clock, plus which collections it must send.
- `spec/split.md` §7 has a log row and an "Open for the backend" list.

## Still open for the backend

- Which writes the server stamps with "now". Picks and timers send no time; To-dos' add field sends no due date and expects Someday.
- Setting `bought_on` when a grocery item is ticked, so it shows under "Bought in the last week".
- Where the minutes live for one occurrence of a repeating session.
- The rest-time default (90 s) has no seed field.
- The date window for Calendar's month view.
- **Decision needed:** may Clair use these instruments when it builds a new app, or only the six base blocks? CLAUDE.md still says the six base blocks.
