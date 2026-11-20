# Board brief: Quilt

## The idea (founder/idea.md)

- **What it is:** a phone-first app where an AI assistant, Clair (built on Claude), builds small personal apps (Budget, Groceries, Classes, To-dos, Workout, Subscriptions, Calendar) and fills them from a photo, a file or a sentence. Every change waits as a draft until the user taps OK, and one confirm updates every app it touches. Example: a photo of a grocery receipt ticks 8 items off the grocery list, adds a $35.83 spend to Budget and a trip to Calendar in one tap. A fridge photo suggests what to rebuy from the user's buying history.
- **Who it is for:** full-time undergraduates (18 to 24) at the University of Utah, phone-first, managing their own money for the first time. They pay a "forgetting tax" (forgotten subscription renewals, late fees, groceries that go off, missed deadlines), use several separate apps that don't share data (a lift tracker, a to-do app, money tracked in their head), won't hand a bank login to a finance app, and drop apps that need setup or take longer to log than the purchase took. If capture fails twice they go back to their phone's Notes app.
- **What it sells (proposal, not decided):**
  - Free: 5 apps, 50 Clair credits a month.
  - Plus: $6 a month or $48 a year: unlimited apps, 1,000 credits, voice capture, 10 automations.
  - Pro: $12 a month or $96 a year: 4,000 credits, connectors (bank feed, health data), bring your own AI key.
  - Teams: $10 per seat a month.
  - Credits: a chat step costs 1, a photo fill 5, building an app 10. Extra packs are $5 for 500 and never expire. Apps keep working when credits run out; only the AI pauses.
  - Later: a marketplace where anyone sells apps; creators keep 80%.
- **Where and how:** online. Android app and the same build as a website. First users come from U of U student groups via a survey and a waitlist page. Hosted API on Vercel, database on Supabase, AI on Anthropic's API (each AI action costs the company money).
- **Budget and constraints:** two founders building for a university hackathon demo on Fri 20 Nov 2026. No funding, budget, survey results or waitlist numbers yet. AI cost per user not measured yet.

## What the founders have said about competitors (from their pitch doc, prices as of Nov 2026)

Notion (Free, Plus $10, Business $20 per member; AI mainly on Business), Todoist (Free, Pro $5), Rocket Money (Free, Premium+ $15; needs a bank login), Taskade (Free to $100; AI credits), Airtable (Free, Team $20 per seat), Glide (Free to $125), Zapier and Make (automation, credit-metered). Their answer to "why not Notion?": "Notion makes you build it. Quilt fills itself from a photo."

## What is not known yet

Market size, conversion from free to paid, the AI cost per active user per month, how many apps a student actually keeps using, and whether students will pay at all.
