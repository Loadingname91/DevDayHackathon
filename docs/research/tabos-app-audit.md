# Which apps Quilt needs: an audit of tabOS

Sources: `sultanakisana/tabOS` at commit `705a087` (41 tab files, 95 local database tables), and the private `TabOSOrg/TabOSDocumentationSpace` at `288f618` (read over SSH).

## The short answer

tabOS builds every app from scratch, so the same few building blocks get rebuilt again and again with slightly different fields. Quilt builds apps from shared blocks, lists, repeat rules and dates, so most of those 39 user-facing tabs collapse into a handful of apps plus features every app already has.

- **For DevDay (updated Nov 19, evening):** Notes with a folder per class was added as the 8th seeded app and opens the demo (`spec/backend.md` §2.3). The other 7 stay as they are.
- **After DevDay:** add the templates in the "Later" table, about 9 apps instead of 30. Notes moved into the DevDay seed.
- **Never build as apps:** Reminders, Habit Alarm, Catch-Up and Timeline (every Quilt app gets these from repeat rules, dates and Calendar), plus Passwords and Accounts (they store passwords in plain text).

## What the docs repo says

The docs repo doesn't list apps either. It names three default templates in passing (Subscriptions, Grocery, Goals, in `research/TabOS Master Document.md`). Otherwise it leaves "the default template set" undefined (`docs/arch/idea-1/TabOS_Architecture_Design.md` §16, step 4).

It does settle the question behind this audit. The architecture doc and `TabOS_Session_Record.md` §1 call the first design's per-use-case blocks (`subscription_card`, `budget_row`) the one mistake that can't be fixed late. They replace them with twelve generic primitives: page, section, text, metric, progress, collection, record, view, form, chart, file and embed. The tabOS code repo predates that correction and has 41 hand-coded tabs. So the code is the thing the architecture argues against, and the repetition below is the evidence.

The architecture also gates the build on templates: hand-build every default template from the twelve primitives, and stop if one can't be expressed. Quilt's version of that check is the 8 seeded apps for DevDay and the "Later" list below after it.

`docs/arch/idea-1/features/features.md` adds things that aren't apps: a marketplace, sharing, B2B workspaces, export, data retention, MCP and other models per app. None of them changes the app list.

## What tabOS rebuilds

| Building block | Times tabOS rebuilds it | Where | In Quilt |
| --- | --- | --- | --- |
| A thing with a title and a done box | 15 | Task, CarTodo, BusinessTodo, ProjectTodo, MoveTask, BabyTask, CatchUpItem, EndOfLifeChecklistItem, RoadmapTask, Milestone, ChecklistItem, NoteChecklistItem, CatchUpPlanStep, BodyAreaImprovementStep, packing list | A list block over any collection with a `done` field |
| A reminder or repeat | 13 | Reminder, HabitAlarm, MaintenanceTask interval, RelationshipReminder, DebtReminder, AccountReminder, ReceiptReminder, BabyReminder, StudyReminder, Medication reminders, Subscription review, Bill reminder, car registration | One repeat rule on the record (`spec/backend.md` §3) plus a check-in. Any dated record can remind |
| A dated event or appointment | 8 | DoctorAppointment, BabyAppointment, BusinessMeeting, TimelineEvent, WorkItem meeting, SchoolItem class/exam, ItineraryItem, WorkSchedule | Records with `calendar: true`. Calendar reads all of them through `*dated` |
| A note | 9 | Note (with folders), JournalEntry, CarNote, BusinessNote, ProjectNote, RoadmapNote, WorkingNote, SchoolItem note, WorkItem note | One Notes app with notebooks, plus a text field on any record |
| Money in or out | 9 | Expense, TravelExpense, Receipt, Bill, BillPayment, Subscription, Debt, BusinessInvoice, SavingsGoal | Budget's `spend`, with stitches from Groceries, Trips and others |
| A shopping list | 4 | GroceryItem, ShoppingItem, BabyShoppingItem, packing list | Groceries with more lists (Weekly shop, Target, Baby) |
| A contact | 3 | Relationship, SchoolContact, BusinessContact | One People app |
| A saved link | 5 | Resource, SchoolResource, ProjectResource, RoadmapResource, LearningResource | One Saved app, or a link field |
| Stuff you own | 5 | ClothingItem, StorageBox, MoveBox, BabyInventory, Vehicle | One Stuff app with lists (boxes, closet) |
| Goals and roadmaps | 5 | Goal, EndGoal, EndOfLifeGoal, Project milestones, LearningRoadmap | One Goals app |

## All 39 tabs, mapped

| tabOS tab | Becomes | When |
| --- | --- | --- |
| Budget, Bills, Subscriptions, Receipts | **Budget** (spends, subscriptions, bills as repeating spends; a receipt is a photo that makes a spend) | DevDay |
| Debts | Budget, a "Debts" tab | Later |
| Grocery, Shopping | **Groceries** (Shopping is another list) | DevDay |
| To-Do, Reminders, Habit Alarm, Catch-Up | **To-dos** (a reminder is a to-do with a time; a habit is a repeating to-do with a streak; Catch-Up is the overdue view) | DevDay |
| Timeline | **Calendar** (past and future of `*dated`) | DevDay |
| School | **Classes** | DevDay |
| (none in tabOS) | **Workout** | DevDay |
| Notes, Journal, Brainstorm | **Notes** with notebooks (Journal is a dated notebook) | First after DevDay |
| Menu | **Meals** (recipes and a week plan; stitches ingredients to Groceries) | Later |
| Health, Baby Care | **Health** (a person field covers a baby; medications are repeating to-dos) | Later |
| Goals, Improvements | **Goals** | Later |
| Projects, Business, Work | **Projects** (invoices stitch to Budget as income) | Later |
| Relationships | **People** (also holds class and work contacts) | Later |
| Car, Vehicle Inventory | **Car** (Vehicle Inventory is a dealership lot tool; drop it unless someone asks) | Later |
| Travel | **Trips** (itinerary is dated, expenses stitch to Budget, packing is a to-do list) | Later |
| Resources | **Saved** | Later |
| Wardrobe, Storage Management, Move-In/Move-Out | **Stuff** (boxes, closet; the move checklist is a To-dos list) | Later |
| Maintenance | A To-dos list named Home, with repeat rules | Later |
| Language Learning | **Flashcards** (could also be a notebook in Notes) | Later |
| Grammar, Boredom | Ask Clair. These are prompts with no data to keep | Drop |
| Passwords, Accounts | Drop. Both store passwords in plain text, and a password manager does this better | Drop |
| End-of-Life | A Goals template if someone asks; too sensitive for a default | Drop for now |

Home, Available Tabs and Custom Tabs are app shell screens. In Quilt they're Home, the template gallery and Clair building an app.

## Notes per course

Notes come up as a separate app in tabOS, inside School as a note type, and inside Projects, Business and Car. In Quilt they should be one app.

- **Notes** holds two collections: `notebooks {name, class}` and `notes {title, body, notebook, at, photo}`. A notebook can link to a class.
- The notebook switch works like the Groceries list switch: ECON 1010, MATH 1210, CS 3500, Personal.
- The ECON 1010 class page shows its notebook's notes next to its due dates, through the link. The notes aren't copied there.
- When a class is added (by hand or from a syllabus), Clair offers a matching notebook in the same card.
- Clair can file a photo of a whiteboard or slide into the right notebook, because it knows which class is on now (ECON 1010, Kendall 104).

The same pattern fixes the one overlap in our own seed. Classes' `due` and To-dos' `todos` are both "a thing with a date and a done box". For DevDay that stays as it is, because the canonical numbers depend on it (Classes 2 → 3 due this week). After DevDay, class work could live in To-dos with a class link, and the Classes page would show it the way it shows notes.

## Open questions for you

1. Is Notes the first app after DevDay, or does Meals come first (it stitches to Groceries, which the demo already shows)?
2. Should a habit be a To-dos feature (a streak on a repeating to-do) or its own Habits app? Workout is already close to a habits app.
3. The docs repo names Goals as a default template. Should Goals join the "Later" list early, ahead of Health or Car?
