# Board brief: Quilt

## The idea (founder/idea.md)

**What it is:** a personal app builder for students. You describe the app you need and Clair, an AI assistant built on Claude, builds it from shared building blocks (pages, lists, tables, calendars, charts, forms). Examples:
- Course notes with a folder per class (CS 6717, ECON 1010).
- A journal.
- A workout log, a car maintenance tracker, a plant tracker.
- A budget, subscriptions, groceries, to-dos.

All the apps live in one place and can share data: a workout lands on the calendar, a grocery trip lands in the budget.

**How data gets in:** from anywhere. Type it; say a sentence to Clair; give Clair a photo of a whiteboard, a page of handwritten notes, a receipt or a syllabus; drop in a file; or, on the paid plan, connect an outside service. Clair puts it in the right app, in the right folder, and shows a draft you approve with one tap. Nothing changes without that OK.

**Example:** in the Notes app, open the CS 6717 folder, start a new note, take a photo with Clair, and the note is written up there. Open the laptop and it's already there. A journal entry works the same way.

**Everywhere:** Android app and the same build as a website on the laptop; iPhone later. Everything syncs live between devices.

**Who it is for:** University of Utah students, undergrad and grad. They juggle classes, notes, money, workouts and life admin across separate apps that don't share data (Notes, Notion, Google Docs, a lift tracker, a bank app), switch between phone and laptop all day, and drop apps that need a lot of setup.

**What it sells (proposal, not decided):**
- Free: 5 apps, 50 Clair credits a month.
- Plus: $6 a month or $48 a year. Unlimited apps, 1,000 credits, voice, 10 automations.
- Pro: $12 a month or $96 a year. 4,000 credits, connectors to outside services, webhooks, bring your own AI key.
- Teams: $10 per seat a month.
- Credits: a chat step costs 1, a photo or file fill 5, building an app 10. Extra packs are $5 for 500. Apps and typing keep working when credits run out; only Clair pauses.
- Later: a marketplace where anyone sells the apps they built; creators keep 80%.

**Where and how:** online. Users come from U of U student groups through a survey and a waitlist page. Hosted API on Vercel, database on Supabase, AI on Anthropic's API (every Clair action costs the company money).

**Budget and constraints:** two founders building for a university hackathon demo on Fri 20 Nov 2026. No funding, budget, survey results or waitlist numbers yet. AI cost per user not measured yet.

## Competitors the founders know of

Notion (Free, Plus $10, Business $20 per member; AI mainly on Business), Obsidian (free; paid sync), Base44 (an AI app builder with connectors), Glide, Taskade, Todoist, and the phone's own Notes app. Their answer to "why not Notion?": "Notion makes you build it. Quilt builds it for you and fills itself."

## What is not known yet

Market size, conversion from free to paid, AI cost per active user per month, how many apps a student keeps using after a month, and whether students will pay at all.
