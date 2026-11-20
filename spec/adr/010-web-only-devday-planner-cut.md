# ADR-010: Web only for DevDay, and the workflow engine as the event-day feature

## Status

Accepted · 2026-11-19 (late evening) · Deciders: Quilt team · Narrows ADR-005 for DevDay; changes the Nov 19 demo order

## Context

Three things changed on the night before DevDay.

1. No application code exists yet. The base (schema, seed, renderer, write path, sync, a first Clair loop) has to be built tonight, and the Capacitor Android build adds an APK, a camera plugin and a web-view sign-in problem on top of it.
2. The demo we want shows apps working together: Clair reads several apps and an outside calendar, proposes one plan, and can keep doing it by rule. The Car build showed building; it didn't show connection across apps as well.
3. Google sign-in inside an embedded web view is blocked by Google. On a website it is an ordinary redirect.

## Decision

**Client.** For DevDay the client is the React + Vite website only. The phone runs it in the browser (Chrome on Android), added to the Home screen through a web app manifest (`display: standalone`) so it opens full screen. The laptop runs the same site. No Capacitor project, no APK. Camera is the file input with `capture`; speech, if built, is the Web Speech API.

**After DevDay.** A native phone app is still planned (health data, notifications, widgets, share sheet). Whether that is the Capacitor shell of ADR-005 or a React Native or fully native client is undecided and gets its own ADR. On stage we say "native apps next" and name no framework.

**Build split.** Tonight is the base: the app working end to end with a typed sentence to Clair, a basted proposal, confirm, undo and two-device sync. The event day builds the judged feature:

1. Google Calendar, read-only, through Google sign-in on the web (`spec/backend.md` §8a).
2. The training planner (`spec/clair-agent.md` §12.9; broadened in the third cut below).
3. The workflow engine, version 1 (owner decision, late Nov 19: the core is tonight, the engine is the day). Rules live on an app, Clair writes them, and they run across apps. It is built as a ladder so each step is demoable on its own (`spec/workflows.md`, "Engine v1"). The first rule is the planner on a schedule: "Every Sunday at 7:00 pm, plan next week's training".

**Demo order.** See the third cut below. The Car photo build, the 5-second fill, the whiteboard and the fridge are not built for DevDay; their worked examples stay in `spec/clair-agent.md` as the product's reference.

## Third cut (later the same night, owner decision)

The owner set the demo's shape and asked for all of it to be built.

- **Pitch:** Shark Tank style, eight beats in 90 seconds (`docs/demo-day.md`).
- **Beat 4, recorded:** Clair builds three apps from three sentences: Calories, Running (with a 10K on Sat 12 Dec that lands on Calendar) and Cycle (private). The build path (`propose_app`, the Build flow, Make it) is back in the DevDay build for exactly these sentences. The clip is a screen recording of the real app, made on the day on a second, 8-app seed state, and is announced as a recording. If its eval doesn't pass, it isn't shown and the Flows prototype is shown as a prototype.
- **Beat 5, live:** "Plan my training for next week". The planner builds the week instead of only rescheduling it: four lifts kept or moved, two runs toward the race, one recovery to-do, one grocery item, and a sentence of calorie figures. It reads nine apps and changes five. A brief built in Python gives the model the facts; the model arranges and words. Four rungs, each a complete plan; the demo runs the highest that passes 10 of 10.
- **The account:** 12 apps (the 8, plus Calories, Running, Cycle, Meditation). Cycle's read switch is on in the demo account so the planner can use Sam's logged energy; a new Cycle app always starts with it off, and nothing is encrypted.
- **Scope:** the builder, the broad planner, Google Calendar and the whole engine ladder are all in the plan of record. This is more than two people are likely to finish in a day. The build order and cut order in `spec/backend.md` §13 are therefore part of the decision: a safe point (planner rung 1 and the Sunday rule on seeded Google events) is reached first and never cut.

Added consequences: two seed states to keep in step; the planner is a health-adjacent feature, so its copy rules matter (own figures and logs only, an expected range for the cycle, no diet, training or medical advice); a 9-app plan that must come out the same every run is the riskiest piece, which is why the rungs exist.

## Consequences

- One build target tonight instead of two; the Google redirect works with no plugin.
- The phone demo has browser limits: no offline shell beyond the read cache, and the venue network matters more. Test on the hotspot.
- The pitch still says "describe any app and Clair builds it", but the live demo no longer shows a build. If a judge asks, show the Flows prototype and say it is a prototype.
- The DevDay application described the receipt as the event-day feature. The planner is a different feature; say so if asked, and keep the git history as the record of what was built on the day.
- Google's calendar scope is a sensitive scope. Unreviewed, the connection works only for accounts listed as test users, shows an "unverified app" screen, and its tokens are short-lived. Fine for the demo; a launch needs Google's review.
- The refresh token is stored unencrypted in a server-only table. Encryption is deferred with the rest (`spec/backend.md` §12).
- Every "Capacitor" or "APK" mention left in older sections of the specs reads as "the website in the phone's browser" for DevDay.

## Alternatives considered

- **Keep the APK and add native Google sign-in:** a few hours of client ID and signing-fingerprint setup the night before, for no gain on stage.
- **Google Calendar by secret iCal link:** an hour or two, but no sign-in and no path to writing back; kept as the fallback if the OAuth spike fails.
- **One hardcoded rule instead of an engine:** safest, and it was the first plan. The owner chose to build the engine on the day; the ladder in `spec/workflows.md` keeps that honest, because its first two steps are exactly that one rule, and everything above them is cut from the top if the day runs short.
- **The whole parked design in a day** (every trigger and action, connectors, sending email): not feasible. Version 1 is three triggers and two actions.

## References

`spec/prd.md` (must-run table), `spec/backend.md` §8a and §13, `spec/clair-agent.md` §12.9, `spec/workflows.md`, `docs/demo-day.md`.
