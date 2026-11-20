# Workflows and triggers (engine v1 is the DevDay feature)

Status (late Nov 19, owner decision, ADR-010): the core app is built tonight and **the workflow engine is built on Nov 20 as the judged feature**. This page has two parts. "Engine v1" is what gets built on the day, as a ladder cut from the top. Everything from "Why" down is the full design; the parts v1 doesn't cover stay parked for the paid plans.

## Engine v1: what is built on the day

**Rule.** Stored on the app it belongs to, in `AppSpec.workflows[]`, validated like stitches, changed only through the command service (so every rule change has Undo and syncs to both devices):

```json
{ "id": "w_…", "sentence": "Every Sunday at 7:00 pm, plan next week's training", "on": true,
  "trigger": { "kind": "schedule", "rule": "FREQ=WEEKLY;BYDAY=SU", "at": "19:00" },
  "action":  { "kind": "ask_clair", "text": "Plan my training for next week" } }

{ "id": "w_…", "sentence": "When an exam is added to Classes, add a study to-do two days before", "on": true,
  "trigger": { "kind": "row_added", "collection": "classes/due",
               "where": [{ "field": "kind", "op": "eq", "value": "exam" }] },
  "action":  { "kind": "write_row", "collection": "todos/todos",
               "map": { "title": "Study for {title}", "due": { "from": "at", "offset": "-2d" } } } }
```

| Part | v1 kinds | Not in v1 |
| --- | --- | --- |
| Trigger | `schedule` (weekly or daily, one time of day) · `row_added` (collection + `where`) · `field_changed` (collection, field, `to` value, + `where`) | `date` (N days before or after a date field), `form_submitted`, `connector_event`, thresholds |
| Condition | the existing `Filter[]` grammar (`where`) | |
| Action | `ask_clair` (a turn text; the result is a basted card in Needs your OK; costs credits like typing it) · `write_row` (insert into any app's collection; `map` takes fixed text, `{field}` from the triggering row, and a date with an offset in days or hours) | `remind`, `send`, updating an existing row |
| Surface | a `workflows` block the server adds as a last tab named Workflows on any app with rules: sentence, switch, Run now, "ran N times this week · last run" | Settings → Automations, plan limits |

**How it runs.**

- `row_added` and `field_changed` run in the command service's `expand` step, after stitches, in the same change set as the change that fired them. So the proposal card already lists what the rule will add ("To-dos: Study for Midterm 2 · by rule"), nothing is written before OK, and one Undo reverses both. Written rows carry `_via: {workflow: id}` and show "by rule ›".
- `schedule` and Run now start a Clair run with `action.text` as the turn text and `source.kind = "workflow"`. A rule never writes app data directly through `ask_clair`; the result waits for OK.
- Guards, all at validation or expand time: a rule can't write into the collection that triggers it; rules don't fire on rows written by a rule in the same chain beyond depth 3; rows from a connector (`source` set) never fire rules; a rule that is off does nothing; an idempotency key (rule id, triggering record id, occurrence or date) stops a rerun writing twice.
- A rule whose target app or field no longer exists is kept, shown as "needs fixing", and skipped.

**The ladder.** Build in this order. Each step ends in something that can be shown; if the day runs short, stop at the last finished step.

| Step | Built | What can be shown |
| --- | --- | --- |
| 1 | `workflows[]` on the spec with the v1 grammar and validation; `POST /apps/{id}/workflows`, the switch, the `workflows` block and tab | A rule on Workout's Workflows tab, on both devices |
| 2 | `schedule` + `ask_clair` through **Run now**; Clair's `offer` event after a confirmed plan ("Do this every Sunday at 7 pm?" → Turn on) | The demo beat: plan, confirm, Turn on, the rule appears; Run now gives a card in Needs your OK (`spec/clair-agent.md` §12.9) |
| 2b | The appointment check as a second scheduled rule: Calendar events get a `kind`, Clair's `get_gaps` read, the prompt section (`spec/clair-agent.md` §12.10). No new engine code | Ask "Am I due for any appointments?" → "Haircut is due. You go about every 5 weeks" → Add to Calendar → Turn on "Every Sunday at 7:00 pm, check for appointments that are due" |
| 3 | `row_added` and `field_changed` + `write_row` inside `expand`; guards; "by rule ›"; run counts | Add an exam in Classes → the card shows the study to-do it will also add → one OK, both apps, one Undo |
| 4 | `propose_workflow`: a rule described to Clair in words becomes a basted rule card; Turn on saves it | Type "When I add an exam, add a study to-do two days before" → "Add this rule to Classes?" → Turn on → then step 3's demo |
| 5 | Scheduled firing: `/cron/sweep` on a Vercel cron reads `schedule` rules that are due; "Next run" on the rule row | "Next run Sun 22 Nov, 7:00 pm"; a rule set a minute ahead fires on stage only if rehearsed |

Steps 1 and 2 are the must-run (PRD row 12). Step 2b comes next and is cut before the planner is ever touched. Steps 3 to 5 are cut from the top down. "Next run" is shown only when step 5 is deployed.

**`propose_workflow` (step 4).**

```python
def propose_workflow(app: str, sentence: str, trigger: Trigger, action: Action) -> str: ...
# Validates against the v1 grammar and the apps' specs; stores a basted change set that
# patches the app's workflows[]; streams a rule card. Nothing is saved before Turn on.
# → {change_set_id, preview: "rule", targets}
```

Added to Clair's prompt with it: write only rules made of the v1 triggers and actions; if Sam asks for something v1 can't run (send an email, remind me, react to my bank), say plainly that rules can't do that yet and propose nothing; restate the rule as one sentence Sam would recognise. Evals: three supported sentences produce a valid rule each; one unsupported sentence produces none.

**Seed.** The demo account starts with no rules. The Sunday rule is made on stage (step 2). The exam rule is made live only if step 4 is built; if only step 3 is built it is made through the endpoint in rehearsal and shown as already there, and it is not shown at all if it isn't one Sam could have made in the app (`spec/prd-data-provenance.md`).

**What to say on stage.** "Rules are described, not configured: Clair writes them, they run across my apps, and anything Clair decides still waits for my OK." Say only what the finished steps do.

**Plans (unchanged, not built).** Free keeps stitches. Plus gets 10 rules and Clair steps paid from credits, including Clair's own pattern runs with a monthly cap. Pro gets unlimited rules, connector triggers and sending.

## Why (evidence)

- Competitors charge for automation, not for apps (`docs/pitch.md` price table, Nov 2026): Notion database automations need Plus $10, Custom Agents $10 per 1,000 credits; Airtable free caps at 100 automation runs a month; Taskade and Glide meter automation runs, agents, number of workflows; Zapier from $19.99 for 750 tasks.
- Quilt plans already promise it (Plus: 10 scheduled or triggered automations; Pro: unlimited, connectors, webhooks), but no engine exists. Today's only trigger is a stitch (row added in A, row written in B; `spec/backend.md` §5) plus occurrence stitches run by the sweep.
- Angle: workflows are described, not configured. Clair writes the rule from a sentence; rules cross the user's own apps with no Zapier; AI steps still land as basted cards (nothing changes without OK).

## Model

Rule stored on the app spec (`AppSpec.workflows[]`), validated like stitches, executed by the command service.

| Part | Kinds | Exists today |
| --- | --- | --- |
| Trigger | `row_added` (collection) · `field_changed` (field, to value, or crosses threshold) · `date` (date field ± N days, with condition) · `schedule` (RRULE subset, e.g. weekly SU 19:00) · `form_submitted`, `connector_event` (Pro) | `row_added` = stitch; date via sweep for occurrences only |
| Condition | existing `Filter[]` grammar (`where`) | yes |
| Action | `write_row` (insert or update in any app, field mapping as stitch maps) · `remind` (FR-D5 `remind` field) · `ask_clair` (prompt + target app; output is a basted change set in Needs your OK; charges credits) · `send` (email or Slack via connector; Pro) | write_row = stitch expand; others new |
| Surface | `workflows` block: one sentence per rule, on/off toggle, "ran N times this week", last run; global list in Settings → Automations | no |

Execution:
- `row_added`, `field_changed`: in `commands.py` expand step, same transaction as the triggering change set; writes join that change set (one Undo) unless the action is `ask_clair`.
- `date`, `schedule`: `/cron/sweep` (exists for occurrence stitches). Writes as `origin sweep` change sets, stitched directly; `ask_clair` writes basted.
- Loop guard: a workflow can't trigger itself, directly or through another workflow; cycles rejected at validation (same rule as formulas and stitches). Max chain depth 3.
- Idempotency: key (workflow id, triggering record id, occurrence/date) so a sweep rerun writes once.
- Clair tool: `propose_app` and a new `propose_workflow(sentence → rule)`; both basted. (DevDay uses the `offer` event and a plain endpoint instead; see the cut above.)

Tiers: Free = stitches (connected on arrival stays free). Plus = 10 workflows, `ask_clair` paid from credits. Pro = unlimited, `schedule`, `connector_event`, `send`, webhooks.

## Missing pieces besides the engine

- Formula division: add `{div: [Term, Term]}` next to `minus` (response rate, MPG). One line in the grammar (`spec/backend.md` §6).
- Status change by tap: a status chip on list rows (update gesture). Drag between `group` columns later.
- Phone notifications: FR-D5 (Beta).
- Already enough: `list/table/calendar` with `group` and `where`, `chart` bar/line, `metric`, `progress`, `form`, relations, `*dated`.

## Showcase app: Internship hunt (post-recording, opened pre-built)

Seed would say Made by: Clair build (weeks ago) + gestures. Not seeded yet.

| Tab | Blocks |
| --- | --- |
| Pipeline | list `group: status` (Saved, Applied, Interview, Offer, No) |
| This week | metric applications this week; progress 6 of 10 goal; metric response rate (needs `div`); chart bar applications per week |
| Interviews | calendar (feeds main Calendar via `*dated`) |
| People | table of recruiters and referrals, relation to applications |
| Workflows | the 5 rules below |

| # | Trigger type | Rule | On stage |
| --- | --- | --- | --- |
| 1 | row_added | New application → deadline on Calendar | already visible |
| 2 | field_changed | Status → Interview → Calendar event + prep note in Notes → Prep | fire live; laptop shows both |
| 3 | date | 7 days after Applied, no reply → To-dos "Follow up with the recruiter" | show the to-do the sweep made |
| 4 | ask_clair | On Interview → Clair drafts 5 likely questions as a card | show the earlier card |
| 5 | schedule | Sundays 7 pm → Clair digest "6 applied, 2 replied, 1 interview Thursday" | show last Sunday's digest |

Minimum to show it on stage: `field_changed` + `write_row`, a read-only Workflows block, `div`, status chip, seed rows for 3 to 5 (with provenance per `spec/prd-data-provenance.md`). Alternatives considered: Car app a month later (fuel log, MPG chart, mileage triggers); tutoring side hustle (sessions → invoices → Budget income, unpaid 7 days → reminder).
