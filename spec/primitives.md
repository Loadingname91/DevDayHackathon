# Primitives: building any app from a few composable parts

Nov 20, 2026 · decision in [ADR-014](adr/014-composable-primitives-and-custom-blocks.md) · extends `backend.md` §6 (formulas) and `ui-tech-plan.md` §3 (blocks). Where this file and those disagree on something it defines, this file wins; everything else there stands.

The worked example throughout is StrengthLog, a workout logger the owner uses (`https://github.com/Loadingname91/StrengthLog`). Two more apps check that nothing here is workout-specific: a recipe and meal-prep app, and a chores app (§7).

---

## 1. Principles

- **Data and logic in the spec, drawing in the client.** An app is collections + formulas + blocks. A new kind of app should need new data and configuration, not new code.
- **The server computes every figure.** The client lays out what arrives in `values[block.id]` (unchanged from the instruments rule). Clair arranges and words; it never does arithmetic.
- **Few primitives, many presets.** Each primitive must serve at least three unrelated apps. A shape that serves one app is a preset (a template of a primitive) or a custom block.
- **Old specs keep working.** Every existing formula, block and instrument stays valid. New shapes are additive.
- **Unknown kinds degrade.** The client shows "Can't show this block yet" for a kind it doesn't know, so the server can ship ahead of the client.

---

## 2. Expressions (formulas v2)

A closed, non-recursive-in-time JSON language: no loops, no user functions, no network, no clock except the workspace clock. Evaluated in Python (`api/logic/formula.py`), with the same null and error semantics as `backend.md` §6 (null propagates, aggregates skip nulls, errors are `{error: "#ERR", reason}` values and never fail a request).

### 2.1 Expr

```ts
type Expr =
  | number | string | boolean | null
  | { setting: string }                          // app settings (unchanged)
  | { field: string }                            // a field of the current row (row formulas, `per`, filters)
  | { record: true }                             // the id of the record a record page is showing (§4.4)
  | Query                                        // §2.2
  | { op: 'add'|'sub'|'mul'|'div'|'min'|'max'|'avg', args: Expr[] }    // n-ary, 2 to 8 args
  | { op: 'round', args: [Expr, number?] }       // digits, default 0
  | { op: 'abs'|'neg'|'floor'|'ceil', args: [Expr] }
  | { op: 'coalesce', args: Expr[] }             // first non-null
  | { op: 'if', args: [Cond, Expr, Expr] }
  | { op: 'convert', args: [Expr, 'kg'|'lb'|'km'|'mi'|'c'|'f', 'kg'|'lb'|'km'|'mi'|'c'|'f'] }
  | { op: 'days_between', args: [Expr, Expr] }   // dates or datetimes, in the workspace zone
  | { op: 'shift', args: [Expr, string] }        // a date or datetime moved by '-2d', '3h', '1w', in wall time (DST-safe)
  | { op: 'next', args: [string, string?] }      // the next 'sun' / 'mon'… (and an optional '19:00') after now, in the workspace zone
  | { op: 'text', args: [string, ...Expr[]] };   // "Study for {0}": a template filled from the args
type Cond = { field: string; op: 'eq'|'ne'|'lt'|'gt'|'lte'|'gte'|'within'|'empty'|'in'; value: Expr | Expr[] }
          | { all: Cond[] } | { any: Cond[] };
```

- **Depth limit 6, size limit 64 nodes**, checked at validation; cycles through fields or stitches are rejected (as today).
- **Old shapes map in place.** `{minus: [a, b]}` is `{op: 'sub', args: [a, b]}`; a row formula `{op, a, b}` is `{op, args: [a, b]}`. Both stay accepted.
- **Row formulas** become `{type: 'formula', expr: Expr, output: Format}`. Estimated 1RM (Epley): `{op: 'round', args: [{op: 'mul', args: [{field: 'weight'}, {op: 'add', args: [1, {op: 'div', args: [{field: 'reps'}, 30]}]}]}, 1]}`.

### 2.2 Query

```ts
type Query = {
  agg: 'sum'|'count'|'avg'|'min'|'max'|'last'|'first'|'count_distinct';
  from: CollectionRef | '*dated';
  value?: string | Expr;         // field key (old `field`) or a per-row expression, e.g. volume = weight × reps
  where?: Cond[];
  window?: 'today'|'week'|'month'|'all'|{ days: number }|{ range: 'param' };   // `param`: the block's range control (§4.2)
  by?: GroupBy;                  // turns the result into groups (§2.3)
  per?: 'record';                // evaluated once per row of the block's source; see §4.4
};
type GroupBy =
  | { field: string }                              // a select, multi-select, text or relation field
  | { path: string }                               // through a relation: "exercise.muscle"
  | { time: 'day'|'week'|'month' }                 // buckets on the collection's dateField
  | { buckets: { field: string; edges: number[] } }// numeric ranges: reps 1-5, 6-8, 9-12, 13+
  ;
```

- **`path`** follows one relation hop (`sets.exercise → exercises.muscle`); two hops at most. A multi-select at the end counts the row once per value; a weighted multi-select (`{value, weight}` options, §5.1) contributes its weight, so a secondary muscle counts half a set.
- **Grouped results** are `[{key, label, value, text}]`, sorted by `value` descending unless the block says otherwise. Charts, bars, regions and ranked lists all read this one shape.
- **`last` / `first`** use the dateField (ties by position). "Last time" for a ghost value is `{agg: 'last', from: 'strength/sets', value: 'weight', where: [{field: 'exercise', op: 'eq', value: {field: 'id'}}], per: 'record'}`.

---

## 3. What stays and what becomes a preset

| Today (Nov 20) | Becomes | Kept as |
| --- | --- | --- |
| `metric`, `progress`, `gauge`, `ring` | one `stat` family (a figure, an optional target, a shape) | presets `metric`, `progress`, `gauge`, `ring` |
| `strip`, `bars` | `chart` v2 | presets `strip` (week, by day), `bars` (by option) |
| `next`, `timer`, `picks` | `flow` | presets `next` (a flow's preview card), `timer` (a one-step flow), `picks` (a one-step flow choosing from a list) |
| `list`, `table`, `calendar`, `checklist`, `days`, `month` | `views` | all kept as view kinds |
| `countdown` | `stat` with a date target | preset `countdown` |

The client may keep drawing presets with their current components; the change is in the spec grammar and the server values, so Clair learns one primitive per row instead of eleven instruments.

---

## 4. The primitives

Each primitive: its spec shape, what the server sends in `values[block.id]`, and three apps that use it.

### 4.1 `flow`: run steps one at a time, logging each

```ts
{ kind: 'flow'; id: string; label: string;
  source: CollectionRef;               // the thing being run: a session, a recipe, a routine
  steps: { from: CollectionRef;        // exercises of the routine, recipe steps, chores of a room
           link: string;               // the relation field from a step to the source (or its parent)
           order: string;              // sort field
           repeat?: string;            // a number field: sets per exercise
           group?: string;             // steps with the same value interleave (supersets: A1 B1 rest A2 B2 rest)
           rest?: string | number;     // seconds after each step or round; a field, or a number, or {setting}
           fields: string[] };         // what the user logs per step (weight, reps, rir) or confirms
  log: CollectionRef;                  // where each logged step goes (sets, cooked, done chores)
  ghost?: 'last' | 'target' | 'none';  // placeholder per field: last logged value, or the step's target
  finish?: { set: Record<string, Scalar>; minutesField?: string } }  // what completing the run writes
```

**Values:** the preview card (`eyebrow`, `title`, `meta`, `action`, as `next` today) and the run plan: `steps: [{id, name, round, group?, rest_after?, fields: [{key, ghost, best?}]}]`, plus `live` if a run is in progress (§5.3).

**Client:** a full-screen runner that survives navigation (a bar on every screen while live), auto-advances within a group, starts the rest countdown after each step or round, fills a field from its ghost on one tap, and marks a step done when every field is valid. Each logged step is `POST /records` to `log`; finishing is `POST /records/{source}/complete {occurrence, minutes}`. Undo works per step.

**Used by:** a workout (StrengthLog's active session, supersets, rest rows), a recipe while cooking (steps with timers, nothing logged but done), a study session (Pomodoro rounds), a morning routine.

### 4.2 `chart` v2

```ts
{ kind: 'chart'; id: string; label: string;
  type: 'line'|'bar'|'area'|'spark';
  series: { label: string; value: Query }[];       // each Query has `by: {time}` or `by: {field}`
  metrics?: { label: string; series: number[] }[]; // a toggle: weight / est. 1RM / volume / reps
  range?: { default: '7d'|'30d'|'90d'|'all'; options: ('7d'|'30d'|'90d'|'all')[] };
  tap?: 'record' }                                  // tapping a point opens that record
```

**Values:** `{range, metric, series: [{label, points: [{x, y, text, record_id?}]}], empty?}` for the default range and metric. Another range or metric is `GET /apps/{id}/blocks/{block_id}?range=90d&metric=1` (same shape). A `spark` has no axes and fits inside a list row.

**Used by:** exercise progress, spending by month, sleep hours, grades over a term, weight trend.

### 4.3 `regions`: an asset of named regions, coloured by a grouped query

```ts
{ kind: 'regions'; id: string; label: string;
  map: 'body' | 'week' | 'house' | 'campus-utah';  // a shipped asset with named region ids
  value: Query;                                     // with `by` resolving to region ids
  levels?: number;                                  // colour steps, default 5
  tap?: 'filter' }                                  // tapping a region filters the page's other blocks
```

**Values:** `{regions: {<region id>: {level: 0..levels-1, text}}, legend: [{level, text}], unmapped?: [labels]}`. Colours come from the app's dye (light to deep), never red. Region ids are fixed per asset (`body`: `chest`, `front_delts`, `biceps`, `abs`, `quads`, … front and back; listed with the asset). A group key that matches no region is listed in `unmapped`.

**Used by:** a muscle heatmap, chores per room, where classes are on campus, a symptom body map. A map that isn't shipped is a custom block (§6).

### 4.4 Record page

A collection may declare a page for one of its records:

```ts
type Collection = { …; page?: { title?: string; tabs: PageBlock[] } };
```

Blocks on a record page may use `{record: true}` in filters and `per: 'record'`. Route: `GET /apps/{id}/records/{record_id}` → `{record, spec_page, data, values, seq}`. The client opens it from any row of that collection (the edit sheet becomes "Edit" on the page).

**Used by:** an exercise (its chart, best set per rep range, every session's sets, notes), a class (assignments, notes, the next lecture), a recipe (ingredients, steps, the times it was cooked), a car.

### 4.5 `views`

The existing `list`, `table`, `calendar`, `checklist`, `days`, `month`, plus:

- `grid`: cards in columns (exercise library, recipe box). Optional `image` field.
- `board`: columns by a select field, drag between columns (`PATCH` the field). Chores by status, applications by stage.
- `ranked`: a grouped query as a ranked list with bars ("Most trained exercises", "Top spending").
- `search`: a field-backed filter bar on any view, with chips from select fields ("OHP" finds "Overhead press" through an `aliases` field).

---

## 5. Data model additions

### 5.1 Fields

- `multiselect`, with options that may carry a `weight` (primary muscle 1, secondary 0.5).
- `duration` (seconds), shown as "1:30".
- `unit` on number fields already exists; add `units: {setting: 'units'}` so an app setting (kg or lb) converts on display and on input (`convert`).
- `image` (a Storage path), for grid cards and recipe photos.

### 5.2 Repeats: rotation

```ts
repeat: { rotation: { order: string[] /* record ids */, after: 'done' } }
```

"Next" is the record after the last one completed, regardless of weekday (Upper A → Lower A → Upper B). `*dated` shows only the next one, on today, unless it has a time. The planner brief lists a rotation's next session as movable.

### 5.3 Live state

A record is **live** when its collection declares `live: {started: 'started_at', done: 'done'}` and the record has `started_at` set and isn't done. `GET /home` and `/sync` return `live: [{app, record_id, title, started_at, block_id}]`; the client shows a bar on every screen with a clock from `started_at` and `server_now`, and tapping it reopens the flow. Starting is `PATCH started_at`; finishing is the flow's `finish`.

### 5.4 Import

A CSV or file goes to Clair (`clair-agent.md` §3, attachments). Clair answers with a question card mapping each column to a field (auto-filled, editable), then proposes one bulk change set, flagged as bulk past 5 rows. A mapping can be saved as a Clair note so the next import from the same source skips the question.

---

## 6. Custom blocks (the safety valve)

```ts
{ kind: 'custom'; id: string; label: string;
  code: string;                    // Storage path of one ES module, at most 64 KB
  reads: CollectionRef[];          // the only collections it may read
  values?: Record<string, Expr>;   // server-computed inputs, sent as values[block.id]
  height?: number }                // initial height; the block can resize itself
```

**Runtime.** A sandboxed iframe: `sandbox="allow-scripts"` (no same-origin, no forms, no popups), CSP `default-src 'none'; script-src 'self' blob:; style-src 'unsafe-inline'`, no network. The host injects the design tokens (CSS variables for the ground, ink, dyes) and a tiny SDK over `postMessage`:

```ts
quilt.data(ref)          // rows of a declared collection (respects read level and Cycle's switch)
quilt.values             // this block's server-computed values
quilt.propose(ops, text) // a basted change set; the host shows the card; nothing saves before Sam confirms
quilt.open(record_id)    // open a record page
quilt.resize(height)
quilt.theme              // light or dark, the app's dye
```

**Making one.** Clair's `propose_app` (or `PATCH /apps/{id}`) may include a custom block with its code. Before the card shows **Make it**, the server checks the module (size, no `fetch`, `XMLHttpRequest`, `WebSocket`, `import()` of a URL, `eval`, or `Function`), and the client renders it once in a hidden frame; an exception or a blank render fails the build with a tool error so Clair can fix it. The code is part of the app spec change set, so Undo removes it.

**Promotion.** The server counts custom blocks by a normalized description. A shape built for three different apps is a candidate primitive.

**Cost.** Writing code is a build turn (Sonnet, 10 credits). A custom block costs nothing to run.

---

## 7. The litmus test: three apps, no new kinds

| Need | StrengthLog | Recipes and meal prep | Chores |
| --- | --- | --- | --- |
| Main action | `flow` over a routine's exercises, supersets by `group`, rest rows, ghost = last | `flow` over a recipe's steps with timers | `flow` over tonight's chores (one-tap done) |
| Plan | `rotation` repeat on routines; planner moves sessions | meals on `days` week view; shopping via the Groceries stitch | `rotation` across housemates |
| Progress | `chart` v2: weight / est. 1RM / volume by week, range 30d/90d/all | times cooked per recipe (`ranked`) | done per person (`chart`, by person) |
| Map | `regions` `body`: sets per muscle over 7 days | — | `regions` `house`: overdue per room |
| Detail | exercise record page: chart, best per rep bucket (`by: buckets`), sessions | recipe record page: ingredients, steps, cooked log | room record page |
| Library | `grid` + `search` on exercises (aliases) | `grid` with photos | — |
| Measurements | a collection + `chart` small multiples + `stat` target | — | — |
| Import | CSV through Clair with a mapping card | a recipe link or photo through Clair | — |
| Alerts | rest done, ongoing session: native app | a timer while cooking: native app | reminders: native app |

**Pass:** every row is expressible with §2 to §5. Alerts are the known exception and wait for the native app.

---

## 8. Plan

Owners follow `spec/split.md`: **A** = backend (`api/`), **B** = frontend (`web/`). Each step ships behind the rule that existing specs render the same.

### Built together with the workflow engine (owner, Nov 20)

The owner chose to build the workflow engine (`spec/workflows.md`, engine v1) and layer 1 of this file in the same piece of work, so rules and apps share one expression language from the start:

- **Rule actions** (`write_row.map`) take `Expr` values. The v1 shorthand stays accepted and maps in place: `"{title}"` → `{op: 'text', args: ['{0}', {field: 'title'}]}`; `{from: 'at', offset: '-2d'}` → `{op: 'shift', args: [{field: 'at'}, '-2d']}`.
- **Trigger conditions** (`field_changed`, and a `row_added` filter) are `Cond` (§2.1), the same filters blocks use.
- **The rule's own figures** (its run line, "Next run Sun 6 Dec 7:00 pm") come from `next` and `shift`, computed by the server.
- One evaluator (`api/logic/formula.py`) and one validator serve formulas, blocks and rules; Clair's `propose_workflow` and `propose_app` are checked against the same grammar.

So the engine's steps 3 and 4 (`row_added` / `field_changed` + `write_row`, `propose_workflow`) and T-2 / T-3 below are one milestone. The judged demo beat (the Sunday planning rule, steps 1 and 2) needs no expressions beyond `next`, and stays first.

### Today (Fri 20 Nov), only if the day's ladder allows

Order of the day stays `backend.md` §13: D1, D2 (the workflow engine, the judged feature), the safe point, D3. This work starts only after the safe point is reached, and stops at the freeze.

| # | What | Owner | Done when |
| --- | --- | --- | --- |
| T-1 | ADR-014 and this file; a line in `split.md` §7 | A | written (this file) |
| T-2 | Expressions §2.1 and queries §2.2 (`by` field, path, time, buckets; `per: record`; `value` as an expression) in `api/logic/formula.py`, old shapes mapped in place | A | unit tests for estimated 1RM, sets per muscle through `exercise.muscle` with weights, best per rep bucket, volume by week; **every existing test and the 12 canonical faces unchanged**; `smoke.py --full` passes |
| T-3 | Contract: the new block kinds and fields as additive members in `api/models.py`, `api/openapi.json` regenerated | A | model tests pass; the client is unaffected (it doesn't send these) |
| T-4 | Client: an unknown block kind renders "Can't show this block yet" instead of failing | B | one test with a fake kind |

Nothing in the demo seed, templates or Clair's prompt changes today.

### Week 1 after DevDay

| # | What | Owner |
| --- | --- | --- |
| W1-1 | `chart` v2 values and `GET /apps/{id}/blocks/{block_id}`; client chart with range and metric toggles, `spark` | A, B |
| W1-2 | Record pages: `Collection.page`, `GET /apps/{id}/records/{id}`; client page and row → page navigation | A, B |
| W1-3 | `grid`, `board`, `ranked`, `search` views | B (A: `ranked` values) |
| W1-4 | Instruments re-expressed as presets in the templates; Clair's prompt teaches primitives instead of instruments | A |

### Week 2

| # | What | Owner |
| --- | --- | --- |
| W2-1 | `flow` values (run plan, ghosts, groups, rest) and live state (§5.3) | A |
| W2-2 | The flow runner, the live bar on every screen | B |
| W2-3 | `rotation` repeat in `repeats.py`, `*dated` and the planner brief | A |
| W2-4 | `regions` with the `body` asset (front and back, named muscle ids) | B (asset), A (values) |
| W2-5 | **Litmus:** Clair builds StrengthLog from one paragraph; then Recipes and Chores. Each gap found becomes a ticket, not a new kind | A, B |

### Week 3

| # | What | Owner |
| --- | --- | --- |
| W3-1 | Custom blocks: sandbox host, SDK, static checks, hidden-frame render check, Undo | B (host), A (checks, storage) |
| W3-2 | Clair writes custom blocks inside `propose_app`; eval: 5 prompts that need one | A |
| W3-3 | Import through Clair: attachments (D10 work), the mapping card, saved mappings | A, B |

### Later

Native app: notifications (rest done, an ongoing session, reminders), background timers, health data (`prd.md` Future Considerations).

---

## 9. Open questions

1. **Region assets:** which maps ship first (`body` surely; `house` and `week` are cheap; a campus map is per school).
2. **Custom block review:** is a hidden-frame render check enough, or should a custom block's first run on a device ask "Allow this block?"
3. **Presets in the client:** keep the current instrument components (fast, already built) or redraw them as primitives (one code path)? Recommendation: keep them until W1-4 proves the primitive renders identically.
4. **Pricing:** do custom blocks and record pages sit in the free plan or Plus?
