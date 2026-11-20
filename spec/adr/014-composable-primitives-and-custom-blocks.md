# ADR-014: Composable primitives, a full expression language, and custom blocks

Date: Fri 20 Nov 2026. Status: accepted (owner, "lets write this for today, lets plan on the changes"). Spec: [`spec/primitives.md`](../primitives.md).

## Context

Quilt promises "describe any app, Clair builds it". Today an app is a spec of tabs and blocks drawn from a fixed vocabulary: six base blocks plus the eleven instruments added on Nov 20 (`gauge`, `bars`, `ring`, `countdown`, `strip`, `picks`, `checklist`, `days`, `next`, `timer`, `month`). Each instrument was made for one starter app.

The owner asked whether Quilt could replicate a real app, StrengthLog (a workout logger: routines, supersets, a live session with rest timers, PRs, a muscle heatmap, progress charts, measurements, CSV import, Android notifications). About 60% of it fits today. The rest needs a live session, a body heatmap, richer charts, per-record pages, and formulas the grammar can't express (estimated 1RM, sets per muscle through a relation, best set per rep range, a rotation instead of weekdays).

Adding one more block kind for every new kind of app would never end, and Clair would have to learn each one.

## Decision

Three layers, so new kinds of app need data and configuration, not new code:

1. **Logic is fully declarative on the server.** The formula grammar of `backend.md` §6 grows into a small, closed expression language: arithmetic and functions over fields and queries, queries that group by a field, a path through a relation or a numeric bucket, and queries scoped to one record. Every number is still computed in Python on the server; Clair still never does arithmetic. Old formulas keep working unchanged.
2. **A few composable primitives replace one-off instruments.** `flow` (run a sequence of steps one at a time, logging each: a workout, a recipe, a study session), `chart` v2 (any query, any series, a range control, sparklines), `regions` (an asset of named regions coloured by a grouped query: a body, a house, a campus), `record page` (tabs and blocks scoped to one record), and more `views` (grid, board). The eleven instruments become presets of these and keep working.
3. **Custom blocks are the safety valve.** When no primitive fits, Clair writes a small component that runs in a sandboxed iframe with no network. It reads only the collections it declares, and it writes only by proposing changes, which stay basted until Sam confirms, with Undo. A custom block that keeps being written becomes a primitive.

Cross-cutting: a **live state** for a record that is in progress (shown as a bar on every screen), import through Clair with a mapping question card, and native notifications later.

**The test that this works:** three very different apps (StrengthLog, a recipe and meal-prep app, a chores app) are expressible in the spec with no new block kinds. One that isn't names the next primitive.

## Consequences

- Clair builds from about a dozen primitives plus an escape hatch, so "any app" is literally true without the core growing forever.
- The renderer must show a placeholder ("Can't show this block yet") for an unknown kind, so the server can ship a primitive before the client draws it.
- Custom blocks bring code from the model into the product. They run sandboxed (no network, no same-origin, a strict CSP), they can't write except through proposals, they're checked before **Make it**, and they're versioned with the app spec, so Undo removes them.
- **Today (DevDay) only the backend part of layer 1 lands, and only if the day's ladder allows it** (`spec/primitives.md` §8). Nothing about the demo changes: templates, seed, faces and every `check.py` item stay identical. The judged feature (the workflow engine, `backend.md` §13 D2) comes first.
- Native notifications and background timers wait for the native app (ADR-010).
