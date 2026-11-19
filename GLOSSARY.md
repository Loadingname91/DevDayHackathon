# Quilt

Quilt is a phone-first workspace where Clair, an AI, builds small personal apps from a fixed set of blocks and stitches them together so one capture updates every app it touches. This glossary fixes the words we use for that, in the product and in the docs. The reference architecture (TabOS v3) uses some different words; they are listed under _Avoid_.

## Language

### Apps and their parts

**App**:
One thing Sam keeps track of (Budget, Groceries, Workout), made from blocks and shown as one patch on Home.
_Avoid_: Tab (TabOS v3 and the pitch doc), widget, mini-app

**Block**:
One piece of an app, from a fixed set: page, text, metric, progress, collection, list, table, calendar, form or chart.
_Avoid_: Component, module, primitive (in product copy)

**Collection**:
The kind of record an app holds, with named fields (Groceries has items and trips).
_Avoid_: Table, schema, database

**Record**:
One entry in a collection: one grocery item, one set, one due date. The app shows it as a row.
_Avoid_: Item (except in Groceries copy), entry, object

**Field**:
One named value on every record of a collection (name, amount, due date, list).
_Avoid_: Property (in product copy), column, attribute

**List**:
A named group of records inside one collection, picked with chips (Weekly shop, Taco night). It is a value of the record's list field, not a separate collection.
_Avoid_: Using "list" for the list block's layout (call that the list view)

**View**:
How a block shows a collection: as a list, a table or a calendar.
_Avoid_: Layout, mode

**Face**:
The one headline value an app shows on its patch and in the status line ("$376 left", "4 to buy").
_Avoid_: Summary, badge, KPI

**Usual**:
A grocery item Sam buys again and again, marked on the item itself (yes, no or worked out by Clair).
_Avoid_: Staple, favourite, regular

### Dates and repeats

**Due date**:
The one main date a record sits on in Calendar and Next up. A thing with several dates becomes several records.
_Avoid_: Deadline (in copy), timestamp

**Repeat rule**:
How often a record comes back (every Saturday, every month on the 22nd), stored on the record.
_Avoid_: Recurrence, schedule, cron

**Occurrence**:
One date produced by a repeat rule. Completing it moves the record to the next occurrence.
_Avoid_: Instance, copy

### Clair and changes

**Clair**:
Quilt's AI. It reads what Sam gives it (words, voice, photos, files) and Sam's apps, then answers, asks or proposes changes.
_Avoid_: Assistant, bot, the AI, agent (in product copy)

**Proposal**:
A set of changes Clair wants to make, shown as a card and saved only when Sam says OK.
_Avoid_: Suggestion, draft, recommendation

**Basted**:
The state of a proposal that is shown but not saved; nothing in any app has changed yet.
_Avoid_: Pending, draft, unconfirmed

**Stitched**:
The state of a change set that is saved into every app it touches.
_Avoid_: Applied, committed, confirmed

**Change set**:
Everything one gesture, one confirm or one undo changes, saved or undone together.
_Avoid_: Command group (TabOS v3), transaction, batch

**Stitch**:
A link that carries records from one app into another (a grocery trip becomes Budget spending).
_Avoid_: Connection, integration, sync, relation

**Clair note**:
Something Clair keeps about how Sam likes things done ("stopped buying Greek yogurt"), listed in Settings and deletable. Facts about Sam's things live in the apps, not in notes.
_Avoid_: Memory, preference, profile

**Menu question**:
A question Clair asks with tap-to-pick options before it proposes anything.
_Avoid_: Prompt, survey, clarification

**Check-in**:
Clair's short evening card listing what to log or decide today.
_Avoid_: Notification, digest, reminder

### Home and the bar

**Home**:
The first screen: status line, Needs your OK, Next up, Clair noticed and Your apps.
_Avoid_: Dashboard, feed

**Patch**:
An app's tile on Home, in its dye, showing its face.
_Avoid_: Card, tile, icon

**Bar**:
The strip at the bottom of every screen with four pinned apps and the Clair button.
_Avoid_: Dock, tab bar, nav bar

**Pin**:
An app's place on the bar.
_Avoid_: Shortcut, favourite

### Accounts

**Workspace**:
Everything one person owns in Quilt: their apps, records, notes and history.
_Avoid_: Account (for the data), space, quilt (in technical docs)

**Guest account**:
The account made the moment someone first opens Quilt, before they add an email or Google. It lives on that device until they keep their quilt.
_Avoid_: Anonymous user, trial

**Join code**:
A six-digit code that opens the same workspace on a second device.
_Avoid_: Pairing code, PIN

## Flagged ambiguities

- The pitch doc says "tab" where the product now says **app**. TabOS v3 also says "Tab". Use **app** everywhere a person reads it.
- "Row" is how a **record** looks in a list; use "record" in docs and "row" only when describing the UI.
- "List" means a group of records (Weekly shop). The list-shaped layout is the **list view**.
- "Memory" was used for both Clair notes and data in apps. Facts about Sam's things are **records** (or the usual mark); how Sam likes Clair to behave is a **Clair note**.
