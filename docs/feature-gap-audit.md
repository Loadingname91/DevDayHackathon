# Quilt mock: functional gap audit

Nov 19, 2026 · compares the 17-screen Claude canvas mock against what people expect from the apps Quilt replaces (Notion, Todoist, Hevy, Rocket Money, Apple Reminders, Google Calendar). Priority is for the DevDay demo (Nov 20), not the full product.

**Legend:** P0 = the demo or pitch breaks without it · P1 = a judge or first user will notice it's missing · P2 = expected soon after launch · P3 = later.

## What exists today

Home (insights, rule banner, pinned cards, tab grid, dock) · All tabs · Search and ask (global, from Home only) · Calendar of everything · Welcome · Empty states · Clair chat · Build a tab → Clair building · Insight to rule · Groceries · Receipt fill · Workout (5 sub-tabs, Inspect) · Log a set · Budget · To-dos.

## Gaps

| Area | Missing | Seen in | Priority | Why |
| --- | --- | --- | --- | --- |
| Cross-device | Laptop layout of the same tab | Notion, Todoist | **P0** | The demo shows phone and laptop side by side; there is no laptop screen |
| Build | Full preview before stitching, layout options, arrange mode, connection step | Notion AI, Taskade, Glide | **P0** | "Build a tab" is half the pitch; today it jumps from blocks to "add to my tabs" |
| Find | Find inside a tab (search, filter, sort) | Todoist, Hevy, Rocket Money | **P1** | No tab can be searched or filtered; lists will grow fast |
| Find | Global search reachable everywhere, with scopes and recent searches | Notion ⌘K, Spotlight | **P1** | Search exists but only from Home, and has no scope or recents |
| Find | Answers from search ("how much on coffee in October?") | Notion AI Q&A | P1 | Search already routes misses to Clair; show the answer card in results |
| Edit | Edit or delete a row, swipe actions, multi-select | Every list app | **P1** | Only checkboxes exist; no way to fix a wrong row |
| Trust | Activity: what Clair changed, with undo per change | Notion page history | **P1** | Pitch promises "every change can be undone" |
| Trust | Settings: what Clair can read (full / field names / none), export, delete account | — | **P1** | Pitch promises these; no screen shows them |
| Money | Clair credits meter and plan | Notion AI, Glide | P2 | Business model depends on credits; judges may ask |
| Manage | Tab settings: rename, re-dye, reorder, pin, fold, duplicate, delete | Notion, Todoist | P2 | Only Workout has "edit tabs" |
| Capture | Quick add from anywhere (global +, share sheet) | Todoist quick add | P2 | Every add is per tab today |
| Capture | Recurring items (renewals, chores) | Todoist, Reminders | P2 | Subscriptions and chores repeat |
| Notify | Inbox of nudges and rules that fired | Rocket Money alerts | P2 | Rules exist with no place to see what fired |
| Data | Recently deleted / trash | Notes, Reminders | P3 | Undo covers the demo |
| Data | Import (CSV, from another app) | Notion import | P3 | After beta |

## Search plan (proposed)

1. **Global search** opens from anywhere (pull down on Home, the dock, ⌘K on laptop). It searches tab names, every row and every Clair action; results are grouped by tab with the tab's patch dye; scope chips (all, a pile, a tab; rows, tabs, actions); recent searches.
2. **Find in a tab** sits in every tab's header. Its filter chips are generated from the tab's own fields (category, date, status), because every tab is a spec with typed fields. No other tracker gets this for free.
3. **Ask** when the query reads as a question: a Clair answer card on top, with the rows it used as sources.
