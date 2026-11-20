# Workflows and triggers (PARKED, Nov 19)

Status: design only. Not in the DevDay build. Owner decides when to unpark (see `docs/start-here.md`, Parked).
Purpose: the premium layer (Plus and Pro), and a post-recording showcase app ("Internship hunt").

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
- Clair tool: `propose_app` and a new `propose_workflow(sentence → rule)`; both basted.

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
