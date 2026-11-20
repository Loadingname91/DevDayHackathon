# Quilt: full product, MVP and DevDay pitch

Nov 15, 2026 · @VendorSpace

Quilt stitches your life together: describe any need and Clair sews a new patch, an app made to fit you, into one quilt where every patch connects. This doc starts with everything Quilt can become, then picks the slice we build for Lassonde DevDay on Nov 20. After that come the business model, the technical risks, why people can trust it, the pitch and the application.

Taglines to pick from: "Your life, stitched together." · "Every app you need, stitched into one." · "Say what you need. Clair stitches it in."

Mock app from Claude Design: https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P (the design system and every screen in the Quilter's Workbench style, clickable; updated Nov 19)
Design book, with all screens, decisions and prototypes in one place: https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq

## Focus: what wins the pitch

Judged the way YC judges, the pitch wins on one painful problem, one starting user, one demo moment that never fails, and proof that people want it. The rest of this doc is backup for questions and stays out of the pitch itself.

1. The problem everyone feels: "You pay for five apps that don't talk to each other." Subscription overload plus scattered data.
2. Who it's for first: U of U students, because we can survey them and get sign-ups before Friday.
3. One magic moment, rehearsed until it can't fail: a receipt photo becomes grocery rows, the budget drops and the calendar updates, live on phone and laptop.
4. Proof of demand: 20 or more survey answers and a real waitlist number by Thursday. "40 students signed up in 3 days" beats any roadmap slide.
5. Say the hard thing first: "Why not Notion? Notion makes you build it. Quilt fills itself from a photo."
6. The bigger vision in one line: students first, but parents, caregivers, athletes and freelancers have the same problem (next section).

Cut from the pitch but kept in this doc for Q&A: the marketplace, teams, MCP, pricing tiers and most of the 19 catalogue features.

## Who Quilt is for

Every persona has the same three pains in different clothes: too many paid apps, data that doesn't connect, and the one app they need that nobody built. Quilt starts with students and adds one persona at a time, each with its own set of patches.

| Persona | Their pain | First apps | How the stitching helps |
| --- | --- | --- | --- |
| Student (first user) | Forgotten subscriptions, tight budget, gym, classes and deadlines in separate apps | Budget and subscriptions, grocery from photo, gym log, assignments | A receipt updates groceries and budget; renewals, workouts and due dates share one calendar |
| Busy parent or household | Bills, chores, meals, kids' schedules spread across apps and group chats | Bills, chore rota, meal plan and pantry, family calendar | The pantry feeds the shopping list, bills land on the family calendar, a chore form roommates or kids can fill |
| Caregiver | Tracking someone else's medication, appointments and symptoms, often on paper | Medication log, appointments, symptom diary, contacts | Doses and symptoms line up on one timeline to show a doctor; reminders from the same data |
| Athlete or hobbyist | Specialist apps for training, diet and gear that never share data, some only on one platform | Training log, meals, gear or collection tracker, race calendar | Training load and meals in one chart; works on any device with a browser |
| Side hustler or freelancer | Clients, invoices, hours and expenses across spreadsheets and paid tools | Clients, hours, invoices, expenses from receipt photos | Hours flow into invoices; receipts flow into expenses and a monthly profit metric |

One vision line covers all of them: "Everyone has a life no app was built for. Quilt lets you describe the apps you need and stitches them into one." Quilt grows beyond students because of platform gaps (an app that's iOS-only or has no web version) and the long tail of niche needs.

## The full product: where Quilt goes

The full vision is one quilt for your whole life. Every need becomes a patch (an app made to fit you), the stitching between patches is shared data, and Clair does the sewing, filling patches and reasoning across them. The hackathon demo is the first few patches. The pitch should show the whole quilt on one slide.

The metaphor, for use in both the pitch and the UI:

- **Patch** = an app's tile on your Home, each app cut to fit your life.
- **Stitching** = data flowing between apps: a receipt patch tugs the budget and calendar patches with it.
- **Clair** = the quilter. You say what you need; Clair sews it in.
- **Patterns** = templates and the marketplace: patches others designed that you can sew into your own quilt.
- **Quilting circle** = shared apps, roommates and teams working on one quilt.

The tone is warm rather than technical. A quilt is personal and handmade, and it grows over time; Quilt should feel the same way, never like a cold "system".

**Five product pillars**

| Pillar | What the user gets | Full-scale features |
| --- | --- | --- |
| Build | Any app you can describe, in seconds | Clair builder from plain words, ready-made templates, full styling (fonts, colours, layout), edit, duplicate and link any component |
| Capture | Logging that takes no effort | Photo, voice and chat entry; Clair fills any app; later live bank and health feeds and outside AI agents writing in through MCP |
| Connect | Your life, joined up | Data linked across apps, a calendar of everything, and questions across all of it ("if I cut entertainment subscriptions, how much do I save this year?"), plus proactive nudges |
| Everywhere | One app on every device | Phone, web and desktop from one codebase; real-time sync with offline use; encryption per account; export and import of all your data; your own data-retention settings |
| Share and earn | Apps as a creator economy | A marketplace where anyone publishes an app, free, one-time or by subscription; live collaboration on shared apps; team workspaces for companies |

**Flywheel.** More users build apps, the best become marketplace templates, templates bring new users with zero blank-canvas problem, and creators earn, so they build more. Meanwhile each user's data gets more connected, so Clair's answers get better and switching away gets harder.

**Roadmap**

1. **Hackathon (Nov 20):** the build-and-connect core, eight seeded demo apps (Notes among them), Clair filling any app from a photo or a sentence, the same app live on phone and laptop.
2. **Private beta (next 3 months):** U of U students; templates first, Clair for customizing; sync and offline; measure whether people still log after 30 days.
3. **Public launch:** paid tier, styling, voice capture, cross-app questions and nudges, data export.
4. **Marketplace:** creators publish and sell apps; live sharing with friends and roommates.
5. **Teams:** company workspaces, shared apps, admin controls, MCP so other AI agents can use Quilt.

**What to measure (north star and guardrails).** North star: apps with a new entry in the last 7 days per user. Guardrails from the architecture plan: time to first useful app, share of Clair-built apps kept without manual fixes, and Clair cost per successful task.

**Hard calls a PM would make now.**

- **Win one life area first.** Money (subscriptions, groceries, budget) is the wedge with the most pain and the clearest saving. Gym and to-dos follow.
- **Templates before blank canvas.** The marketplace is the long-term answer; until then ship 10 strong first-party apps.
- **Don't fight specialists on depth.** Quilt wins on breadth and connection, and lets power users link out where needed.
- **Be honest on privacy.** Encrypted at rest with per-account keys, never claim end-to-end, and say clearly what goes to the AI provider.
- **Workspace-level sharing only.** No per-block permissions, which keeps sharing simple and the system fast at scale.

## Feature catalogue (roadmap, for Q&A)

The full catalogue takes the best feature from each category leader and makes it work across every app. None of these need building for DevDay; the top eight go on the roadmap slide.

| Area | Feature | Seen in | How it looks in Quilt | Tier |
| --- | --- | --- | --- | --- |
| Build | Describe an app, Clair builds it | Notion AI, Taskade | "Track my subscriptions" becomes a working app | Free |
| Build | Templates and remix | Notion "Duplicate as template", Wabi | Start from a ready app, or copy one a friend shared | Free |
| Capture | Photo to rows | Glide AI columns, Notion Autofill | Receipt photo becomes grocery and expense rows | Free with a cap |
| Capture | Voice brain-dump | Todoist Ramble | Say a messy update; Clair splits it across apps | Free with a cap |
| Capture | Siri, Shortcuts, Control Center | Apple App Intents | "Hey Siri, log 2 coffees in Quilt" | Free |
| Automate | Scheduled Clair runs | ChatGPT Tasks, Claude scheduled tasks | "Every Sunday 8 pm, review my spending and set next week's budget" | Paid |
| Automate | Event triggers | Airtable automations, Zapier | "When a workout is logged, update my streak; nudge me after 3 missed days" | Paid |
| Automate | Buttons that run a saved prompt | Notion buttons with agents | A "Plan meals from pantry" button on the grocery app | Free |
| Connect | Bank feed with subscription detection | Plaid, Rocket Money | The subscriptions app fills itself and flags duplicates | Paid |
| Connect | Health data | Apple Health, Health Connect | Steps and sleep feed progress and chart blocks | Free |
| Connect | Live sync tables | Coda Packs | A table that mirrors Google Calendar, Strava or GitHub | Power |
| Connect | Inbound webhooks and MCP | Zapier, Make, Raycast | Any service or outside AI agent can read and write apps | Power |
| Glance | Widgets and Live Activities | Widgetsmith, Hevy | Rest timer or budget left on the lock screen; widget changes by time of day | Free (basic), Paid (smart) |
| Insight | Records and anomaly banners | Hevy Live PR | "New bench record" or "spending spike" on any metric | Free |
| Insight | Questions across all apps | (Quilt's own) | "If I cut entertainment subscriptions, what do I save this year?" | Paid |
| Insight | Forgiving streaks | Streaks, Loop | Streak block with freeze days | Free |
| Share | Public app pages and forms | Notion Sites, Notion Forms | RSVP or chore sign-up form that writes into your app | Free |
| Share | Marketplace | Wabi, Notion templates | Creators sell apps once or by subscription | Revenue share |
| Share | Live collaboration and team workspaces | Notion, Airtable | Roommates share a bills app; companies share apps with staff | Teams |

Top eight for the roadmap slide: scheduled and triggered Clair runs; widgets and Live Activities; voice brain-dump; bank feed with subscription detection; Apple Health and Health Connect; marketplace with remix; shareable forms; MCP so outside agents can use Quilt.

Sources: [Notion releases](https://www.notion.com/releases/2026-04-14), [Airtable automations](https://support.airtable.com/docs/creating-an-automation), [Coda Packs](https://coda.io/packs/build/latest/guides/overview), [Todoist Ramble](https://www.todoist.com/help/articles/use-ramble-to-add-tasks-by-voice-P1Raq7vVF), [Hevy Live Activity](https://www.hevyapp.com/features/live-activity/), [Hevy Live PR](https://www.hevyapp.com/features/live-pr/), [Plaid Transactions](https://plaid.com/docs/transactions/), [Rocket Money subscriptions](https://rocketmoney.com/feature/manage-subscriptions), [Raycast AI extensions](https://manual.raycast.com/ai/ai-extensions), [Notion Sites](https://www.notion.com/en-gb/help/public-pages-and-web-publishing).

## Business model and pricing

Quilt should charge one simple subscription with a monthly allowance of Clair credits, because AI is what each user really costs us. Everything you build keeps working when the credits run out. The market has settled on the same pattern: seats or plans, plus metered AI and automation.

**How others charge (Nov 2026)**

| App | Plans | What's metered | What makes people upgrade |
| --- | --- | --- | --- |
| [Notion](https://www.notion.com/pricing) | Free, Plus $10, Business $20 per member | AI credits on Business; Custom Agents at $10 per 1,000 credits; database automations need Plus; premium connectors need Business | AI is only a trial below Business; free has button-only automations |
| [Zapier](https://zapier.com/pricing) | Free 100 tasks, Pro from $19.99 for 750 tasks | Tasks (each action); AI steps cost 1 to 5 tasks; faster polling on paid | Free allows only two-step Zaps; going over switches to pay-per-task |
| [Make](https://www.make.com/en/pricing) | Free 1,000 credits, paid from about $9 | Credits per action; extra credits cost 25% more | Free allows 2 scenarios and a 15-minute interval |
| [Airtable](https://www.airtable.com/pricing) | Free, Team $20, Business $45 per seat | Automation runs (100 a month on free), records per base, AI credits with $20 packs | Hitting record or automation caps |
| [Taskade](https://www.taskade.com/pricing) | Free to Max $100 | AI credits, automation runs, agents, storage | Credit packs never expire; published apps keep running at zero credits |
| [Todoist](https://www.todoist.com/pricing) | Free, Pro $5 | Counts: 5 projects, 3 filters; limited AI voice sessions | Running out of projects or AI sessions |
| [Rocket Money](https://help.rocketmoney.com/en/articles/2217739-how-much-does-rocket-money-cost) | Free, Premium pay-what-you-want, Premium+ $15 | Features, not usage; dropped its 35 to 60% bill-negotiation fee for a flat tier | Budgets, live sync, bill negotiation |
| [Glide](https://www.glideapps.com/os/pricing) | Free to Pro $125 | Credits as standard LLM tokens; number of published apps and workflows | Publishing an app at all |

What the market shows: free tiers convert on structural limits (number of projects, scenarios or automations) as well as on volume. AI is usually only a trial on free plans. Plan credits don't roll over, but bought packs often do. Yearly billing gets 15 to 50% off. The Make and Zapier prices come partly from third-party breakdowns.

**Quilt's plans (proposal)**

| Plan | Price | What you get |
| --- | --- | --- |
| Free | $0 | 5 apps, every block, templates, sync on all your devices, 50 Clair credits a month, button automations, basic widgets |
| Plus | $6 a month ($48 a year) | Unlimited apps, 1,000 Clair credits, voice capture, 10 scheduled or triggered automations, smart widgets, questions across apps, full export |
| Pro | $12 a month ($96 a year) | 4,000 credits, unlimited automations, connectors (bank feed, health data, live sync tables), webhooks and MCP, option to bring your own AI key |
| Teams | $10 per seat a month | Shared workspaces, pooled credits, roles and admin, shared templates |

- Credits: a Clair chat step costs 1, building an app 10, a photo fill 5 and a scheduled run 2. Extra packs are $5 for 500 and never expire.
- No surprise bills: alerts go out at 80% and 100%, then Clair pauses until next month or a top-up. Apps, logging, sync and widgets never stop.
- Marketplace: creators keep 80% of what their apps earn, and Quilt takes 20%.
- Price anchor: Plus at $6 costs less than Rocket Money Premium+ ($15) and Todoist Pro ($5) together, before counting gym or habit apps.
- Student Plus: $4 a month, or $15 a semester, with a school email (Nov 19, from the founder pack: `founder/pricing.md`).
- Import from Notion, Apple Notes, Google Docs, Obsidian and Goodnotes, and full export to Markdown and CSV, are free on every plan. Switching cost was the main reason simulated buyers passed.
- In the pitch, say only "Free to start, $6 a month, $4 for students." The marketplace and teams are the expansion line.

All Quilt prices are a starting proposal to test with the survey and waitlist. None of them is decided.

## The MVP: what we build for DevDay

The MVP takes a thin slice of every pillar except Share, so the demo shows the whole idea working end to end: capture, connect, confirm, and live on two devices. Two people build it. This section was updated Nov 19 to match the build docs: `spec/backend.md`, `spec/clair-agent.md`, `docs/onboarding.md` and `spec/ui-tech-plan.md`.

| Pillar | Built before Friday | Built live on Nov 20 (judged) | Faked or cut |
| --- | --- | --- | --- |
| Build | App specs drawn from 9 blocks: page, text, metric, progress, collection, list/table/calendar view, form, chart; five starter apps from templates | Clair proposes a new app from a sentence (stretch) | Styling controls, editing blocks by hand |
| Capture | Quick-add, reorder and lists (Weekly shop, Taco night, Costco run) in every app | **Clair reads any photo or file:** says what it sees, asks a menu question when unsure, and shows one card to OK. Receipt first, then a fridge photo checked against your usual groceries | Bank feeds, Siri |
| Connect | Calendar shows dates from every app; Budget reads grocery spend | One OK updates Groceries, Budget and Calendar together, with Undo | Questions across apps, nudges, automations |
| Everywhere | Android app (React + Capacitor) on the phone, the same build as a website on the laptop, data on the server, live sync between them | | Offline edits, iOS, encryption, export |
| Share and earn | | | Marketplace, collaboration, teams (roadmap slide only) |

Demo apps, pre-seeded with realistic data: Budget, Groceries, Calendar, Classes, Workout, To-dos and Subscriptions. The scripted demo uses Budget, Groceries and Calendar.

**Stack:** React + Vite web app wrapped with Capacitor for Android; a Python (FastAPI) API on Vercel that alone holds the Claude key; Supabase for Postgres, guest sign-in and live updates; Claude (`claude-opus-5-5`, vision and tools) for Clair through the Anthropic Python SDK tool runner. All formulas run in Python on the server. DevDay has no stack rules.

**Split for two people**

- **Person A, API and Clair:** database schema and seed, change sets with confirm and undo, Python formulas, the Clair agent loop and its tools, join codes.
- **Person B, app and demo:** the app in the design book's look (warm ground, Hanken Grotesk and DM Mono, app dyes, no red), Home, the Clair sheet, the thread pull, live refresh across devices, the Android build, pitch slides.

**Plan.** Before Nov 20: schema, seed, API skeleton, the app shell and the Android build. Nov 20: confirm and undo, the Clair loop (receipt, then fridge), the Clair sheet, two-device sync, onboarding, three rehearsals. Hour by hour: `spec/backend.md` §13.

## Technical quirks and risks

The biggest technical risk is the AI misbehaving. Quilt's design handles it: Clair never writes code. It writes a small spec, and that spec is checked before anything changes. The other risks are known problems with known fixes, and the architecture doc already plans for most of them.

| Risk | Why it bites | MVP answer | Full-product answer |
| --- | --- | --- | --- |
| Clair returns a broken or odd app or change | AI output varies | Clair only proposes; the server checks every change against the app's fields before the card shows; nothing saves before OK, and every OK can be undone | A test set of about 100 prompts with expected apps, run on every change; features ship only when it passes |
| Builds feel slow | A multi-step AI build takes seconds | Show placeholder blocks filling in as Clair works | Stream each step live as it happens |
| Clair misreads a photo | Blurry photos, store abbreviations | Clair says what it sees first, then shows items on one card to review before OK; "Use sample" (marked as a sample) if a live read is slow | Learn the user's stores and items over time |
| AI cost per user | Every Clair action costs money | Small demo, one model | Credits per plan, cheaper models for easy steps, a usage ledger from day one |
| Malicious text in data | A receipt or shared template could contain instructions aimed at Clair | Treat all data as data, never as instructions | Approval step before deletes or big changes; attack cases in the test set |
| Two devices edit at once | Phone and laptop both open | Writes go to the server, which orders every change; a second confirm of the same card is refused; each device keeps a local copy only for fast loading | Server-ordered changes with per-field versions; a two-device conflict test must pass with zero lost edits |
| Changing an app breaks linked apps | The budget reads the grocery app's fields | Fixed demo schemas | Link checks on every change and versioned block types with migrations |
| Generic blocks hit a ceiling | Some needs don't fit 9 blocks | Pick demos that fit | Grow the block library deliberately; every first-party template must be buildable from blocks alone |
| Encryption limits search | Encrypted data is hard to filter and compute on | Not in MVP | Per-account keys plus a minimal search index; never claim end-to-end encryption |
| Widgets, Siri, Live Activities need native apps | A web app can't reach the lock screen | Android app built with Capacitor around the same React code | Capacitor plugins for widgets and shortcuts; iOS from the same code |
| Bank data brings compliance work | Security audits, Plaid costs | Not in MVP | Pro tier only, after a security review |
| Stage demo fails | Wi-Fi, AI outage | Phone hotspot, functions warmed before the pitch, "Use sample" marked as a sample, recorded backup video |  |

## Why people can trust Quilt

People will put their money, health and plans into Quilt only if it feels safe and lasting, so we design for trust from the start and say so out loud.

**Advantages people feel**

- **A new app with no install.** Every app in Quilt is self-contained. Describe it and it exists: no app store, no download, no new login.
- **Everywhere, in real time.** Build on your phone and it's already on your laptop, live, on any platform.
- **One subscription, not five.** Quilt replaces the budget, gym and to-do apps you pay for separately, and new apps never cost a new subscription.
- **Your life, joined up.** One receipt updates groceries, budget and calendar, which no single-purpose app can do.
- **It doesn't break.** Clair builds from tested blocks, not generated code, so apps behave the same every day.

**Promises that build confidence**

- **Your data is yours.** Export any app, or everything, at any time; delete your account and your data and keys are destroyed.
- **Encrypted with your own account key.** Each account's data is stored encrypted with its own key. We never claim end-to-end encryption, because Clair has to read data to help you.
- **Clear about AI.** We say plainly what goes to the AI provider, and you choose: full help, field names only, or none.
- **Clair asks before big changes.** Deleting an app or editing many records shows a preview and waits for your yes. Every change can be undone.
- **No bank login needed.** Receipts and manual entries work out of the box; bank linking is optional and comes later.
- **No surprise bills.** When credits run out, Clair pauses instead of charging you, and your apps keep working at zero credits.
- **No lock-in to us.** Apps export as a readable spec plus data, the same format the marketplace uses.

## What makes or breaks Quilt

Notion, Airtable and Taskade can already build an app with AI, so that alone won't set Quilt apart. Quilt's strength is that your apps are joined up and fill themselves: one receipt photo updates groceries, budget and calendar at once. That is what to pitch and what the demo should lead with.

**Hero line (YC two-sentence test):** Quilt is one app for your money, workouts and to-dos that builds the apps you describe and stitches them together. Photograph a grocery receipt and your grocery list, budget and calendar all update.

**Our insight (what others miss):** personal tracking fails at the logging, not the building. Day-30 retention for productivity and fitness apps is around 8 to 9%. Quilt wins on capture (photo, chat) and on data that flows between apps, which single-purpose apps can't do and Notion only does with manual setup.

| Competitor | What it does | Why Quilt is different |
| --- | --- | --- |
| [Notion AI](https://news.lavx.hu/article/notion-s-ai-agents-now-build-over-half-of-databases-as-custom-tools-launch) | AI agents build databases in a desktop workspace | Quilt is phone-first, quick to log into, and apps share data without manual relations |
| [Airtable Omni](https://www.maginative.com/article/airtable-bets-big-on-ai-agents-with-omni-reboots-as-an-ai-native-app-platform/) | Chat builds apps from tested components | Same safe-block idea, but for teams and business. Quilt is for one person's life |
| [Taskade AI Trackers](https://www.taskade.com/ai/trackers) | Prompt becomes a tracker with list, calendar and chart views | Closest on features. Each tracker stands alone; Quilt's apps feed each other |
| [Wabi](https://techcrunch.com/2025/11/05/replika-founder-raises-20m-pre-seed-for-wabi-the-youtube-of-apps) | $20M pre-seed; prompt-made mini-apps you share and remix | Social discovery. Quilt is private and connected |
| [Emergent](https://techcrunch.com/2025/09/24/emergent-raises-23m-from-lightspeed-to-let-consumers-build-apps/), Lovable, Bolt | Generate code for whole apps | Can build anything but breaks easily. Quilt's validated blocks don't break and keep your data stable |
| Rocket Money, Hevy, Todoist | Best-in-class single-purpose apps | Better at their one job, but they don't talk to each other. Quilt shouldn't fight them on depth |

**What could break it, and our answer:**

- **"Notion already does this."** Name it first, as YC advises. Answer: Notion is a desktop doc you set up; Quilt is a phone app that fills itself and joins your apps.
- **Blank canvas.** "What do you want to track?" stalls people. Start every user with 3 to 4 ready apps and use Clair to customize them.
- **Generic blocks feel worse than Hevy mid-set.** Don't claim to beat specialists. Claim the connections.
- **Logging is a chore.** Photo and chat capture is the answer, which is why the photo fill is the live feature.
- **Trust with money data.** No bank logins in the MVP; receipts and manual entries only. That is also a selling point for privacy-minded students.
- **Apple or Google could ship this.** Answer with speed and focus on joined-up personal data, and don't dwell on it in a 90-second pitch.

**Sharpest first user:** a budget-conscious student who juggles subscriptions, groceries and spending and won't hand a bank login to Rocket Money. Several "no bank linking" subscription apps show this demand exists.

**YC rules applied to our pitch:**

1. Say what Quilt does in the first breath, in plain words. The hook can come before it, but within 20 seconds.
2. Show progress over genius: a working demo, survey numbers and waitlist sign-ups (Seibel).
3. One business model only: free for a few apps, then a monthly plan.
4. Slides of 7 words or fewer, one idea each, one presenter speaking slowly (Ralston, Hale).
5. Avoid "platform", "AI-powered" and "better UX". Say what it does (Graham).

Sources: [Seibel, How to pitch your company](https://www.ycombinator.com/blog/how-to-pitch-your-company/), [Hale, pitch deck design](https://www.ycombinator.com/blog/how-to-design-a-better-pitch-deck/), [Ralston, Demo Day guide](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/), [Graham, How to apply](https://www.ycombinator.com/howtoapply), [Dropbox's YC application](https://www.ycombinator.com/apply/dropbox), [Airbnb 2008 deck](https://alexanderjarvis.com/airbnb-seed-pitch-deck/), [retention benchmarks](https://www.appalize.com/blog/mobile-trends/app-retention-rate-benchmarks-by-category-in-2026).

## 90-second pitch and demo

The pitch has one problem, one user, one magic moment and real numbers. Open with a show of hands, say what Quilt is within 30 seconds, spend the most time on the demo (a whiteboard into a course note, then a receipt), and end on the bigger vision in one line.

1. **Hook, 10 s.** "Hands up if you pay for more than three apps to manage your money, workouts or to-dos. Keep it up if they don't talk to each other."
2. **Problem with our numbers, 10 s.** "We surveyed \[N\] U students this week. They pay for \[X\] apps, about $\[Y\] a month, and none of them share data."
3. **What it is, then who we are, 10 s.** "Describe any app and Clair builds it: notes for each class, a workout log, a car tracker. Then fill it from anywhere: type it, say it, snap it, drop a file. It's on your laptop before you sit down. I'm \[name\], this is \[name\]."
4. **The magic moment, 25 s.** "I have a car; Quilt has no car app." Photograph the car's maintenance card and say "make this an app". Clair builds a Car app with the three services, puts the next oil change on the calendar and wires service costs to the budget. One tap, and it's on the laptop too. Then photograph an oil-change receipt: the service is logged, the budget drops from $412 to $367, and the next oil change moves to May. Any app you can describe, built and connected in seconds.
5. **Why not Notion, 10 s.** "Notion makes you build it. AI app builders build apps that sit alone. Quilt's apps arrive connected to your calendar, your budget and each other, and nothing changes without your OK."
6. **Traction and model, 10 s.** "\[N\] students joined our waitlist in \[D\] days. Free to start, $6 a month, $4 for students."
7. **Bigger vision, 10 s.** "Students first. But parents, caregivers, athletes and freelancers all pay for apps that don't talk, or need one nobody built."
8. **Close, 5 s.** "Quilt: your life, stitched together."

Demo safety: pre-seed every app with realistic data, warm the server before going on, keep a recorded backup video, and use "Use sample" (it says "sample" on screen) if Clair or the Wi-Fi is slow. Checklist: `docs/demo-day.md`.

**Before Friday, to earn steps 2 and 6:** put up a one-page landing site with a waitlist, and run a 2-minute survey in U of U student groups (how many tracking apps, what they pay, what they wish they could track). Even 50 sign-ups is a credible number for a pitch.

## Draft application answers

These cover the questions hackathon applications usually ask. The real form's questions are still unknown, so these answers need fitting to each one once we have them. Bracketed items are yours to fill in.

**Name, email, major, year, U of U ID.** \[You fill in. The team lead must be an enrolled U of U student.\]

**Team members.** \[Two people: names, schools, emails, roles.\]

**Project name.** Quilt

**One-line description.** Quilt is one app for your money, workouts and to-dos that builds the apps you describe and stitches them together. Photograph a grocery receipt and your grocery list, budget and calendar all update.

**What problem are you solving?** People pay for five apps that don't talk to each other: a budget app, a gym tracker, a to-do list, a calendar, and a notes file for everything else. Each has its own login and subscription, some don't exist on every platform, and the one tracker you actually need often doesn't exist at all.

**What does it do?** You tell Clair "track my subscriptions and warn me before renewals" or "log my lifts and show my bench progress", and Quilt builds a working app: lists, tables, forms, metrics, progress bars and charts, wired to your data. Every app is made from the same small set of blocks, so apps can see each other. The calendar app shows dates from every other app, and Clair can fill an app from a photo, such as turning a grocery receipt into logged items.

**Who is it for?** First, University of Utah students juggling paid apps for budgeting, fitness and tasks that don't share data. The same problem hits parents running a household, caregivers tracking someone's medication, athletes and hobbyists, and freelancers, so each becomes a next set of templates.

**What will you build during DevDay?** Clair, the agent that turns a photo of anything into changes across your apps. You photograph a grocery receipt and Clair says what it sees, then shows one card: tick off 8 items, take $35.83 off the budget, put the trip on the calendar. Nothing saves until you tap OK, and Undo puts it back. Point it at your fridge and it compares what it sees with what you usually buy, asks which ones you're out of with a quick menu, and remembers your answer. We arrive with the apps, the data model and the two-device sync working, so the day goes into Clair and a polished demo.

**How does it work?** Clair (Claude, with vision and tools) never writes code and never saves on its own. It reads your apps through tools, then proposes a small structured change that Quilt checks against each app's fields and holds until you OK it. Every app is a spec made from the same 9 blocks, stored in one table, and one renderer draws every app. This makes it reliable enough to demo live, and a new kind of app takes one sentence instead of a sprint.

**Business model.** Free for a few apps, then a low monthly plan for unlimited apps and photo fills, priced below the stack of single-purpose apps it replaces. Next, a marketplace where anyone can publish apps for free or for sale (we take a cut), then team workspaces billed per seat.

**Tech stack.** React + Vite, wrapped with Capacitor as an Android app (the same build is the website); Python FastAPI API; Supabase (Postgres, sign-in, live updates); Claude Opus through the Anthropic Python SDK tool runner for Clair.

**Prior work.** Architecture and backend design, and a clickable design canvas of every screen, already exist; the apps and data model will be built before the event, and Clair during it.

**Experience level.** \[Yours and your teammates'.\]

**Links.** \[GitHub repo, any live URL.\]

## DevDay: the event

DevDay is a one-day vibe-code hackathon plus business pitch on Nov 20, 2026. The posted application deadline was Nov 10, so we need to ask the organizers whether they accept late applications.

| Item | What the site says |
| --- | --- |
| Date and place | Fri Nov 20, 2026, Lassonde Studios, 1710 Student Life Way, Salt Lake City. No start or end times posted |
| Application deadline | Nov 10, 2026 (passed). Apply link is a Qualtrics form |
| Hosts and sponsors | Lassonde Entrepreneur Institute and Lassonde DevLab; sponsors Samir Patel, Eccles School of Business, Lovable |
| Eligibility | University of Utah students only (undergrad, master's, PhD) and recent U of U grads. Team lead must be an enrolled U of U student; other members may be from other schools. No high school students |
| Team size | Solo or up to 4 |
| Existing projects | Allowed, but you must build a new, constrained feature during the event, and that feature is what gets judged |
| Tools | Any AI tool or traditional coding. Judged on quality of results, not method. No stack rules |
| Judging | Two parts: a high-speed pitch of the business and software, plus the technical work done during the event. Exact format announced on the day; no published rubric or weights |
| Prizes | Cash (amounts not listed), recognition, and admission to the Lassonde DevLab student software incubator |
| Bring | Laptop, charger, notebook. Breakfast and lunch provided, free entry |
| Organizer tips | Set up AI coding accounts and student verification early (can take days), do one practice run prompt to GitHub to live URL, have a backup tool if free credits run out |

Not published: schedule, tracks or sponsor challenges, submission format (video, Devpost, repo), and the application questions themselves (the form only loads in a browser and could not be opened when this was written). Sources: [DevDay page](https://lassonde.utah.edu/devday/), [application form](https://eccles.qualtrics.com/jfe/form/SV_0voa2jlZwVBqpP8).

## What this means for Quilt

The best play is to arrive with Quilt's core already working (describe a need, Clair writes an AppSpec, blocks render) and build one showpiece feature live on the day: Clair filling an app from a photo, starting with a grocery receipt.

- **Pre-existing work is fine, but only the event-day feature is judged.** So the core engine (validator, compiler, block renderer, the seven demo apps) should be built before Nov 20, and the application should name the one feature we will build there.
- **Why the photo feature.** It is visual, takes under 10 seconds to show, and proves Clair's main promise, that you never fill in forms. It also reuses everything else, because the photo becomes rows checked against the app's own schema. Backup live feature if the photo path is done early: the calendar app that pulls dates from every other app.
- **Pitch counts as much as code.** Judging includes a fast business pitch, so the application and the demo need a one-line market, a user and a way to make money alongside the tech.
- **Deadline.** The posted deadline was Nov 10. Email the organizers about a late application; the site has a Request Information form.
- **Team size.** We are a team of 2 (the limit is 4). The team lead must be an enrolled University of Utah student (or recent U of U grad); teammates can be from anywhere.
- **Stack.** DevDay has no stack rules, and AI coding tools are encouraged (Lovable is a sponsor). Our stack: React + Capacitor (Android), a Python API, Supabase and Claude (see the MVP section). Set up accounts and any student verification now, since the organizers warn it can take days.

## Open items for you

Nothing gets submitted until you approve the final answers.

- [ ] Confirm you (or a teammate) are an enrolled University of Utah student or recent U of U grad, since the team lead must be
- [ ] Ask the organizers whether late applications are accepted (deadline was Nov 10)
- [ ] Open the application form in your browser and paste its questions here or in the thread
- [ ] Send team names, schools, emails and roles (up to 4 people)
- [x] Stack confirmed Nov 19: React + Capacitor, Python API, Supabase, Claude (`spec/backend.md`)
- [ ] Set up AI tool accounts and student verification this week
