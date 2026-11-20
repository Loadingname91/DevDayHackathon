# Quilt · Business plan

**Verdict: Not yet**

- ✓ Each paying user-month earns $3.24 before fixed costs (54% contribution).
- ✓ Year 1 operating profit: $6,671.
- ✗ 0 of 20 simulated buyers buy (0%, the bar is 25%).

| key number | |
| --- | ---: |
| Price | $6.00 a paying user-month |
| Profit margin at plan | 51% per paying user-month |
| Break-even | 26 paying user-months a day |
| Year 1 operating profit | $6,671 |
| Startup spend | $325 |
| Cash needed before it pays for itself | $374 |
| Startup money earned back | month 5 |
| Buyer panel | 0 buy · 20 pass |

## The idea

- What it is: a personal app builder. You describe the app you need (course notes with a folder per class, a journal, a workout log, a car maintenance tracker, a budget) and Clair, an AI assistant built on Claude, builds it from shared building blocks into one place where the apps can share data. Clair also fills any app from anywhere: a photo, a sentence, a file, or a connector to another service. Every change waits for one tap of OK, and everything syncs between phone and laptop.
- Who it is for: University of Utah students, undergrads and grad students, who juggle classes, notes, money, workouts and life admin across several apps that don't talk to each other, and who switch between phone and laptop all day.
- What it sells, at what price (proposal, not decided): Free (5 apps, 50 Clair credits a month); Plus $6 a month or $48 a year (unlimited apps, 1,000 credits, voice, 10 automations); Pro $12 a month or $96 a year (4,000 credits, connectors to outside services, webhooks, bring your own AI key); Teams $10 per seat a month. Credits: a chat step costs 1, a photo or file fill 5, building an app 10. Extra packs are $5 for 500. Later, a marketplace where creators sell apps they built and keep 80%.
- Where and how: online. An Android app and the same build as a website on the laptop; iPhone later. First users come from U of U student groups through a survey and a waitlist page. Hosted API on Vercel, database on Supabase, AI on Anthropic's API.
- Budget and constraints: a two-person founding team building for a hackathon demo (Lassonde DevDay, Fri 20 Nov 2026). No funding, budget, survey results or waitlist numbers yet. The AI cost per user isn't measured yet.

## Summary

**What has to change first is the switching cost.** In the second panel, $6 sat inside the acceptable range ($1.02 to $6.99), yet 0 of 20 bought. 15 of the 20 passed because their notes and trackers already live in Apple Notes, Google Docs, Notion, Obsidian or Goodnotes and moving them "sounds like a weekend of work". Free import and export, a privacy promise and one job that clearly beats their current setup come before any pricing change (`/founder-offer`, then a waitlist test from `/founder-launch`).

Quilt is a personal app builder. You describe the app you need (course notes with a folder per class, a journal, a workout log, a car maintenance tracker) and Clair builds it. Clair then fills any app from anywhere (typing, voice, a photo, a file or a connector), with one tap of OK, and it all syncs between phone and laptop. It's for people 18 to 35 who juggle notes and life admin across apps that don't talk to each other, students first.

**Verdict: Not yet.**
- **Margin:** at $6 a month each paying user-month leaves $3.24 (54%), but only with the model split: Haiku 5.5 for capture and chat, Sonnet 5.5 for builds, a build cap on free. With Opus 5.5 on everything, as the spec says now, each one loses $19.58.
- **Break-even:** 26 paying users.
- **Year 1:** $6,671 operating profit if 500 are paying by month 12. That ramp is untested: neither panel bought, and the bar is 25%.

**Where the board and the panel agree:** pick one hero job and win it before the platform. The board's candidate is the class-notes job: a photo or syllabus filed into the right course, on the laptop by the time you sit down. The panel adds the price of entry: import, export, and replacing something people already pay for.

**Where they disagree:** the board worries about Notion copying the AI; the panel mostly worried about leaving Notion.

**The biggest risk:** Notion is free for students and its AI already builds databases on the $20 tier. If it moves that down to the free student plan, Quilt's core job is matched at $0. The answer is the hero job done much better on a phone (the competitor scan found phone apps worse than desktop in about 100 reviews), plus import from Notion itself.

**To start:** about $374 of cash and the founders' time. The first test is two waitlist pages ($6 against $4) with an "Import from Notion / Notes / Obsidian" button whose clicks are counted.

**This week:** put the waitlist page up before the DevDay pitch.

These are simulated buyers and projected numbers. The first run, on the photo-capture framing, is kept in `run-1-photo-wedge/` for comparison.

## What the board said

**Vote: 3 fund if, 0 pass. Average score 4.7 / 10** (Offers 5, Monopoly 4, Product 5). The memos are in `founder/board/`. The first run, on the photo-wedge framing, is in `founder/run-1-photo-wedge/board.md`. It scored the same average with different reasons.

### Risks more than one member raised

1. **Breadth without a hero job.** Notes, journal, workouts, cars, budget, connectors, Teams and a marketplace read as a list of products. A blank "describe your app" box is still setup (all three).
2. **No edge the AI supplier doesn't also sell.** Notion, Base44, Taskade and Glide already build from prompts; the model is rented (Monopoly, Offers).
3. **AI cost and the credit meter.** Each Clair action costs money, and 50 free credits ration the best moment (all three). AI cost per active user is unmeasured.
4. **Willingness to pay.** Free substitutes are everywhere, with no evidence yet that students pay (Offers, Monopoly).

Where they disagree: the Offers lens wants Quilt sold as an outcome ("your semester, organised") with the builder as delivery. The Monopoly lens wants one job won ten times better (syllabus and lecture photos into a class tracker and calendar). The Product lens wants one hero flow built into onboarding, and offers the class-notes photo filed on the laptop as the candidate. All three name a class-related job first; none names budget or groceries.

The board's best moat is **linked data across apps**: the switching cost grows as classes, notes, calendar and budget feed each other (Monopoly). It still needs proof that linked apps keep students longer.

### Conditions checklist

- [ ] One hero job picked and onboarding built around it (candidates from the board: class notes and syllabus photos into a course folder, a tracker and the calendar, on phone and laptop)
- [ ] Sold as an outcome ("your semester, organised"), with the builder as how it's delivered; outcomes on the pricing page, not credit counts
- [ ] Willingness to pay measured at a stated price before tiers are fixed (`/founder-consumer`)
- [ ] AI cost per active user below revenue at every tier, including free; credits never stop the hero job mid-task (`/founder-cfo`)
- [ ] The gap confirmed: no incumbent does photo-to-approved-draft across linked apps for students (`/founder-competitors`)
- [ ] Draft accuracy measured on real photos, and 30-day retention of linked versus standalone apps
- [ ] Marketplace, Teams, webhooks, bring-your-own-key and automations off the near-term plan
- [ ] A guarantee and a semester-start offer with a real deadline
- [ ] A first network effect named, such as classmates sharing a course app

### The strongest version the board can see

Quilt sold as "your semester, organised": on day one a student photographs or drops in each syllabus. Clair builds a folder and tracker per course and puts every due date on one calendar. All term, a photo of the whiteboard or a handwritten page becomes a filed note in the right course, there on the laptop by the time they sit down. The builder stays: when the student wants a workout log or a car tracker, they describe it and it joins the same quilt and the same calendar. That's what makes leaving expensive later. Classmates sharing a course app is the first network effect to try. This keeps your build-anything product. It changes the order: one class-shaped job first, everything else after.

## The competition

Checked 2026-11-19, public sources only. Raw rows: `founder/competitors.csv`. App Store ratings come from Apple's public lookup API (US). Google Play ratings come from the US listing pages. Both were read on 2026-11-19.

The job: a University of Utah student describes an app (class notes with a folder per course, a journal, a workout log, a car tracker, a budget). The AI builds it and fills any app from a photo, a sentence, a file or a connector. Every draft waits for one tap of OK, and the apps sync between phone and laptop. Android and web come first. Budgeting apps were covered in `run-1-photo-wedge/competitors.md` and aren't redone here.

### 1. The table, most direct first

| # | Name | Type | Platforms | Comparable paid plan | Student price | AI builds from a description? | AI fills from photo/file? | Rating (reviews) |
|---|---|---|---|---|---|---|---|---|
| 1 | [Taskade Genesis](https://www.taskade.com/genesis) | direct | iOS, Android, web, desktop ([pricing](https://www.taskade.com/pricing)) | Starter $6/mo billed yearly ($72) | none published | **yes**: "One Prompt. One App." | page doesn't say; 100+ integrations | iOS 4.7 (6,409); Android 3.8 (28.5K) |
| 2 | [Base44](https://base44.com/pricing) | direct | web builder; [iOS app](https://apps.apple.com/us/app/id6757432427); no Android app found on Play | Starter $16/mo billed yearly; Free = 5 apps, 25 message credits | case by case with a student email | **yes** (full-stack web apps) | **yes**: built-in extraction from "PNG, JPG, JPEG, and PDF files" plus OAuth connectors to Google Workspace, Notion, Slack ([docs](https://docs.base44.com/Integrations/Using-integrations)) | iOS 3.0 (84); [Trustpilot](https://www.trustpilot.com/review/base44.com) 2.7 (939) |
| 3 | [Notion + Notion AI](https://www.notion.com/pricing) | direct (DIY) | iOS, Android, web, desktop | Plus $10/mo; full AI only on Business $20 | **Plus free with a school email**, but AI is a "Trial" | partly: AI "can help you create databases, complete with views and properties" ([FAQ](https://www.notion.com/help/notion-ai-faqs)), Business+ | file upload in AI chat; autofill on Business+ | iOS 4.8 (90,737); Android 4.6 (408K) |
| 4 | [Capacities](https://capacities.io/pricing) | indirect | iOS, Android, web, desktop | Pro $9.99/mo billed yearly ($119.88) | none; Basic free is "intended for students" | no | **yes** on Pro: image, PDF and weblink analysis, autofill | iOS 4.3 (118); Android 3.1 (639) |
| 5 | [Anytype](https://anytype.io/pricing) | indirect | iOS, Android, desktop | Plus $4/mo (billing period of the shown price unclear) | education discount by application | no | not checked | iOS 4.5 (254); Android 4.0 (1.21K) |
| 6 | [Obsidian](https://obsidian.md/pricing) | indirect | iOS, Android, desktop | app free; Sync $4/mo yearly, $5 monthly; Publish $8/$10 | **40% off Sync and Publish** | no (no first-party AI) | no | iOS 4.5 (2,832); Android 4.4 (19.5K) |
| 7 | [Goodnotes](https://www.goodnotes.com/pricing) | indirect | iPad, iPhone, Mac; Android, Windows, web with core features | Pro $35.99/yr; AI Pass +$9.99/mo | none listed | no | imports PDF/images; AI Q&A, quizzes on notes | iOS 4.7 (470,488); Android 3.8 (38.8K) |
| 8 | [Notability](https://notability.com/pricing) | indirect | iPad, iPhone, Mac, Windows, Android | Plus $15.99/yr (limited AI); Pro $79.99/yr | none listed | no | AI quizzes, flashcards, transcription | iOS 4.8 (459,118); Android 4.3 (4.12K) |
| 9 | [Softr](https://www.softr.io/pricing) | indirect (no-code) | web, PWA | Basic $19/mo (billing toggle not resolved) | **50% education discount** | yes ("AI App Builder", business apps) | not checked | n/a |
| 10 | [Glide](https://www.glideapps.com/pricing) | indirect (no-code) | web | Basic $25/mo | not checked | not checked | not checked | n/a |
| 11 | [Lovable](https://lovable.dev/pricing) | indirect (AI builder) | web; iOS app | Pro $25/mo | **up to 50% off Pro** | yes (web apps) | not checked | iOS 4.8 (3,156) |
| 12 | [Tana](https://tana.inc/pricing) | indirect, **pivoted** | desktop on pricing page | Pro $15/member/mo yearly | none mentioned | no; now sold as AI meeting notes ("You'll spend 30,000 hours in meetings.") | n/a | iOS 4.0 (50) |
| 13 | [Mem](https://get.mem.ai/pricing) | indirect, **shutting down** | iOS, web | no new subscriptions; read-only Dec 18 2026, shuts Jan 15 2027 | n/a | n/a | n/a | iOS 4.3 (131) |
| 14 | [Apple Notes](https://apps.apple.com/us/app/notes/id1110145109) | substitute | iPhone, iPad, Mac | free | n/a | no | not checked | iOS 4.8 (671,492) |
| 15 | [Google Keep](https://keep.google.com/) | substitute | Android, iOS, web | free | n/a | no | not checked | iOS 4.6 (29,034); Android 4.7 (2.67M) |
| 16 | [Google Docs](https://apps.apple.com/us/app/google-docs/id842842640) / Sheets | substitute | Android, iOS, web | free | n/a | no | not checked | Docs iOS 4.8 (3.3M), Android 4.7 (3.02M) |
| 17 | ChatGPT / [Claude](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) chat | substitute | iOS, Android, web | free to download; paid plans not checked | not checked | makes one-off trackers in chat | reads photos and files in chat | ChatGPT iOS 4.8 (12.4M); Claude iOS 4.7 (308,929) |

Notes:
- Base44 has been owned by Wix since June 2025 ([Globes](https://en.globes.co.il/en/article-wix-acquires-israeli-vibe-coding-co-base44-1001513267)). It builds web apps for people to publish. It isn't a personal life hub.
- The AI-notes category is thinning out. Mem is shutting down, and Tana now leads with meetings. Neither is a live competitor for a student in 2027.
- Todoist and the budgeting apps are in run 1 and still apply as single-job alternatives.

### 2. Price range for the comparable paid plan

Comparable plan means the cheapest paid plan that unlocks the AI. For Obsidian and Anytype, which have no first-party AI, it's the plan that unlocks sync. Prices are per month, using the yearly rate where only that is shown.

| | Price | Who |
|---|---|---|
| Low | $1.33 ($15.99/yr) | Notability Plus (limited AI) |
| | $3.00 ($35.99/yr) | Goodnotes Pro |
| | $4 | Obsidian Sync, Anytype Plus |
| | $6 | Taskade Starter (builds apps) |
| Median (all 12 paid rows) | **about $12.50** | between Capacities $9.99 and Tana $15 |
| | $16 | Base44 Starter |
| | $19 to $20 | Softr Basic; Notion Business (the plan with full AI) |
| High | $25 | Glide Basic, Lovable Pro |

Split by kind: the note apps have a median of about $4/mo, and the AI app builders about $19/mo. Quilt Plus at $6/mo ($48/yr) is priced like a note app while doing a builder's job. Taskade Starter is the same $6.

**Student pricing worth knowing:**
- **Notion Plus is $0** with a school email, but AI stays a trial. The AI that makes databases sits on Business at $20.
- **Obsidian takes 40% off Sync**, which works out to about $2.40/mo (my arithmetic from $4).
- **Lovable gives up to 50% off Pro**, and **Softr gives 50%** to education users. **Base44** handles it case by case, and **Anytype** asks you to apply.
- **Goodnotes, Notability, Capacities and Taskade list no student price.** One Goodnotes reviewer: "It’s so much for a student especially for a one who lives in dorm" ([1★, Nov 2026](https://apps.apple.com/us/app/id1444383602?see-all=reviews)). One Capacities reviewer: "No student discount." ([1★, Jun 2025](https://apps.apple.com/us/app/id1670188548?see-all=reviews)).

### 3. Positioning map

Axis X: who builds the structure, you or the AI. Axis Y: where it works best, phone-first quick capture or laptop power.

```
Phone-first capture
  HIGH |  Apple Notes, Google Keep           [ EMPTY-ish: AI builds personal apps
       |  Goodnotes, Notability                and fills them from a photo, on the
       |   (tablet/handwriting first;           phone, at student price ]
       |   no app structure)                 ChatGPT / Claude chat (one-off, no
       |                                        lasting structured apps; inference)
   MID |  Anytype, Capacities                Taskade Genesis ($6; web-first,
       |   (mobile apps lag desktop)            Android 3.8)
       |  Obsidian (mobile slow; sync paid)
       |
   LOW |  Notion Free/Plus (you build it)    Notion Business AI ($20)
       |  Glide, Softr (business data apps)  Base44, Lovable, Softr AI
       |                                       (desktop web builders, credits)
       +-------------------------------------------------------------------
          You build the structure                 AI builds from a description
```

The top-right corner has no product that keeps structured, linked apps for a student on a phone. Taskade is the nearest, and it sits in the middle.

### 4. Complaints, ranked

Source: Apple's public review feed (`itunes.apple.com/us/rss/customerreviews/page=N/id=<id>/sortby=mostrecent/json`), up to the 500 most recent US reviews per app, filtered to 1 to 4 stars and to the 12 months before 2026-11-19. That gives 854 reviews: Notion 310 (Feb 22 to Nov 18, 2026), Goodnotes 363 (Aug 7 to Nov 18), Obsidian 102, Notability 38 (Oct 29 to Nov 18), Base44 33 (Apr to Nov), Capacities 8. I coded the themes by keyword and spot-checked them by hand, so the counts are approximate, and one review can count toward several themes. Every quote below was checked against the downloaded text. Reddit was not used because the search only returned mirror sites. For Trustpilot (Base44) I used only the score, because the page blocked a direct fetch to verify quotes.

| Rank | Theme | ~Count | Where | Quotes |
|---|---|---|---|---|
| 1 | **Paywalls and pricing changes**: paid-once apps turned into subscriptions, sync behind a fee, credits | ~196 | Goodnotes 138 (mostly the v5 to v6 subscription move), Notion 24, Base44 14, Notability 11, Obsidian 9 | "I BOUGHT this app back when I was in college, and then all of a sudden I’m locked out of my notebooks" ([Goodnotes 1★, Nov 2026](https://apps.apple.com/us/app/id1444383602?see-all=reviews)); "as long as I wanna sync, it will charge…" ([Obsidian 4★, Oct 2026](https://apps.apple.com/us/app/id1557175442?see-all=reviews)) |
| 2 | **Slow, laggy, won't load** | ~103 | Notion 55, Goodnotes 25, Obsidian 17 | "The amount of time this app takes to load is ridiculous if you are using iCloud sync to iPhone." ([Obsidian 3★, Oct 2026](https://apps.apple.com/us/app/id1557175442?see-all=reviews)) |
| 3 | **The phone app is worse than the desktop one** | ~100 name a phone or iPad plus a problem; ~45 compare it to desktop or web outright | Notion 75 / 27, Obsidian 24 / 6, Base44 4 / 3, Capacities (all-time: 4 of 26) | "Notion is such a formidable application to use on a desktop… so why does the mobile app feel so foreign?" ([Notion 2★, Oct 2026](https://apps.apple.com/us/app/id1232780281?see-all=reviews)); "Desktop is Lifechanging, iOS is Barely Functional" ([Capacities 3★, Dec 2025](https://apps.apple.com/us/app/id1670188548?see-all=reviews)) |
| 4 | **Lost notes and broken sync** | ~70 | Goodnotes 37, Notion 13, Notability 10, Obsidian 8 | "One random update later all of my notes for every single class were missing." ([Notion 1★, Oct 2026](https://apps.apple.com/us/app/id1232780281?see-all=reviews)); "Nearly 10 years of work is just gone." ([Notability 1★, Nov 2026](https://apps.apple.com/us/app/id360593530?see-all=reviews)) |
| 5 | **No reachable support** (noisy count) | ~65 | Goodnotes 30, Notion 23 | Base44 on the App Store: "There is no customer service. Except support tickets which take days to resolve." ([1★, Nov 2026](https://apps.apple.com/us/app/id6757432427?see-all=reviews)) |
| 6 | **Too much setup, confusing** | ~46 | Notion 28, Goodnotes 10, Obsidian 5 | "What should be a simple daily planning and logging system quickly turned into what felt like an IT database management project." ([Notion 1★, Jul 2026](https://apps.apple.com/us/app/id1232780281?see-all=reviews)); "You should build these things for people who arent that educated in setup and are too busy to really deep dive" ([Notion 1★, Jul 2026](https://apps.apple.com/us/app/id1232780281?see-all=reviews)) |
| 7 | **AI pushed on people who didn't ask for it** | ~45 | Notion 33, Goodnotes 8, Notability 3 | "It was great before they put all their AI features front and center." ([Notion 3★, Sep 2026](https://apps.apple.com/us/app/id1232780281?see-all=reviews)); "Goodnotes forces AI integration on you with zero ways to disable it." ([Goodnotes 1★, Oct 2026](https://apps.apple.com/us/app/id1444383602?see-all=reviews)) |
| 8 | **AI builders burn credits and build things that don't work** | 14 of 33 Base44 App Store reviews; Trustpilot 2.7 from 939 reviews | Base44 | "You will burn through credits and spend 3x or more trying to create something." ([1★, Nov 2026](https://apps.apple.com/us/app/id6757432427?see-all=reviews)); "You have to explain things 5 times so it understands" ([1★, May 2026](https://apps.apple.com/us/app/id6757432427?see-all=reviews)) |
| 9 | **Key features exist only on desktop** (thin) | 2 explicit | Capacities | "I have to get on my iPad or computer in order to create or edit an object" ([3★, Aug 2025](https://apps.apple.com/us/app/id1670188548?see-all=reviews)) |

### 5. The gap

**No product lets a student say "make me a class-notes app" on an Android phone, have the AI build it as a lasting, linked app, and fill it from a photo, at a student price, without the AI writing anything the student didn't approve.** The evidence:

- **The AI that builds structure is priced out of students' reach or pointed at business.** Notion's database-building AI is on Business at $20, while the plan students get free has only a trial. Base44 ($16), Softr ($19) and Lovable ($25) build business web apps. Base44's own reviews complain most about credits (theme 8).
- **The apps students already use are weakest on the phone** (theme 3, about 100 reviews). Notion, Obsidian and Capacities are all praised on desktop and panned on mobile. Base44 has no Android app on Play.
- **Photo and file fill exists, but scattered.** Capacities Pro reads images and PDFs, Base44 has an extraction integration, and Goodnotes and Notability make quizzes from notes. None of them turns a photo into rows across a student's own apps.
- **AI that acts without asking is a liability.** About 45 reviews revolt against AI pushed into the product (theme 7), and about 70 report lost notes (theme 4). One tap of OK before any change, and nothing lost, directly answers both. A note on this, though: the backlash means "AI" in the pitch will repel part of the market.

How strong the gap is: it's narrow. **Taskade Genesis already builds an app from one sentence for $6/mo, with iOS and Android apps.** What Quilt adds over Taskade is phone-first capture, filling from photos (not confirmed on Taskade's page), a student focus, and the consent step. Those are differences of degree, not a moat, so test them against Taskade by name in the survey.

### 6. The threat: who could copy fastest

1. **Notion, the biggest threat.** It already has student distribution (Plus is $0 with a school email) and an AI that "can help you create databases, complete with views and properties." If it moves AI to Plus or to the student plan, it covers "describe a class-notes app" at $0 overnight. Its weak spot is the mobile app (theme 3) and the anti-AI backlash in its own reviews (33 of 310). This is inference from the pricing page; Notion has announced no such move.
2. **Taskade, the closest product today.** Genesis does prompt-to-app at the same $6 price, on Android and iOS. Aiming it at students with a template gallery and photo capture is a marketing move more than a build. Limits: an Android rating of 3.8 (28.5K reviews) and positioning as a business "AI agents" tool.
3. **Base44 (Wix), the closest on capability.** It already has photo/PDF extraction, OAuth connectors and app generation. A "personal apps" mode would take little building. Limits: web-first, no Android app found, a 3.0 iOS rating and a 2.7 Trustpilot score with credit complaints, and Wix's business-website buyer.
4. Goodnotes and Notability own student handwriting on iPad and are adding AI fast, but they show no sign of building structured apps. ChatGPT and Claude can make a one-off tracker in chat today, and the student pays nothing extra for it. That's the substitute to beat in the demo.

Defence the evidence supports: phone-first with Android on day one, a visible OK before every AI change, no data loss (export and version history up front), and a student price published on the pricing page, where Goodnotes, Notability, Capacities and Taskade publish none.

## The buyer panel

**0 buy · 20 pass** (0% buy) out of 20 simulated buyers. Seed 13915, so the same cards can be dealt again.

These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the big ones with real people before you spend.

### By segment

| group | buyers | buy rate |
| --- | ---: | ---: |
| Young professional, early career | 8 | 0% |
| Freelancer or side hustler | 3 | 0%  (thin) |
| Undergrad | 6 | 0%  (thin) |
| Grad student on a stipend | 3 | 0%  (thin) |

### By buying behaviour

| group | buyers | buy rate |
| --- | ---: | ---: |
| Notes-app loyalist | 4 | 0%  (thin) |
| Handwritten notes on a tablet | 2 | 0%  (thin) |
| App hopper | 3 | 0%  (thin) |
| Overloaded juggler | 3 | 0%  (thin) |
| Free-tier only | 3 | 0%  (thin) |
| Reads every review | 2 | 0%  (thin) |
| Notion power user | 3 | 0%  (thin) |

### By income

| group | buyers | buy rate |
| --- | ---: | ---: |
| $63,000 and up | 7 | 0%  (thin) |
| under $18,000 | 6 | 0%  (thin) |
| $18,000 to $63,000 | 7 | 0%  (thin) |

### Why they pass

| reason | buyers | in their words |
| --- | ---: | --- |
| habit | 15 | "My notes live in Apple Notes and Google Docs, they already sync between my phone and laptop, and I can already snap a whiteboard into a note. I might poke at the free tier once, but I'm not paying $6 a month to rebuild a setup that already works." (P001) · "My notes live in Goodnotes on my iPad and I like writing by hand, and whatever else I track is already in Notion for free. I might poke at the free tier once out of curiosity, but I'm not paying another $6 a month to move my stuff somewhere new." (P002) |
| price | 3 | "Honestly, the mess of five apps is my actual problem, so I'd download the free version and poke at it. But I make about seven grand a year and I'm already paying for Spotify and a budgeting app, so another $6 a month isn't happening unless Quilt replaces something I already pay for." (P004) · "I don't pay for apps, period. If it's actually good I'd poke at the free tier, but 5 apps is probably enough for me, and my Notes app and Google Docs already do most of this for nothing." (P008) |
| trust | 2 | "It's brand new, so there are no Play ratings or Reddit threads for me to read, and I don't pay for apps nobody has reviewed. I might try the free tier, but 5 apps is enough for my lists and I make $14k a year, so I'm not paying $6 a month for this." (P006) · "It's brand new, so there are no Play Store ratings or Reddit threads for me to check, and I don't pay for apps I can't look up first. At most I'd poke at the free tier, and I already know I'd drop it after a week like every other tracker I've set up." (P013) |

### Why they buy

| reason | buyers | in their words |
| --- | ---: | --- |

### What would flip a no

- A one-tap import of my existing Notes and Google Docs that sorts them into folders for me, plus an easy full export so I'm never locked in.
- If I could snap a page of my handwritten Goodnotes notes and it reliably turned them into something searchable and sorted, and that kept working for a month on the free tier.
- If it imported my whole Obsidian vault or Notion workspace and the whiteboard-to-organized-notes thing was so good I kept reaching for it after the first week, without me having to rebuild everything.
- If after a few weeks on the free tier it actually let me cancel my budgeting app, so Plus costs me nothing extra, or if there was a student price around $2 to $3 a month.
- A free student or first-year deal, plus whiteboard photos turning into clean, searchable notes far better than just saving the picture in Google Docs.
- A few months of solid reviews and Reddit posts from students saying the AI got their apps right the first time, and that they hit the free limit and found Plus worth it.
- A clear promise that my data is private and not used for training, plus one-tap export to plain files or Google Docs, so trying it costs me nothing if I leave.
- A free student plan through my university, or the free tier being generous enough that I never hit the wall.
- If it actually replaced my budgeting app so I could cancel that subscription, and I was still opening it every day after a month on the free plan.
- If I was still opening it every day after a month because the purchase-to-budget thing actually replaced my budgeting app, so I could cancel that and pay for this instead.
- If it imported my Notion databases cleanly and the snap-a-receipt or whiteboard-to-the-right-database part saved me real time every week, something Notion still makes me do by hand.
- If it could pull in my whole Goodnotes library in one go and let me keep writing with the pencil on my iPad, so I'm not running two note apps.

20 buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder.

## Pricing

Simulated buyers chose what to test here. None of it is proof; real people decide.

### 1. The price

**Plus stays at $6 a month ($48 a year), with a Student Plus at $4 a month ($15 a semester).** The panel's acceptable range is $1.02 to $6.99 (`pricing-curve.md`), with the point where as many call it a bargain as call it expensive at $3.02. $6 is inside the range, near the top. It's level with Taskade Starter, the closest product, above note apps (around $4) and well below AI app builders (around $19) and Notion's AI tier ($20; `competitors.md`).

At $6, with capture on Haiku 5.5 and builds on Sonnet 5.5, each paying user-month leaves $3.24 (54%). At the $4 student price it leaves about $1.54 (39%) once the 15% fee is taken on $4. The tool's what-if keeps the $0.90 fee from $6 and gives $1.24 (31%; `cfo.md`). A $3 student price would leave only about $0.69, too thin while free users run at 20 per payer.

Price isn't what stopped this panel. 15 of 20 passed on habit: their notes and trackers already live in Apple Notes, Google Docs, Notion, Obsidian or Goodnotes, and moving them "sounds like a weekend of work".

### 2. The ladder

| Rung | Price | What it holds | Why step up |
| --- | --- | --- | --- |
| Free | $0 | Up to 5 apps, built and filled on the low-cost models; **import from Notion, Apple Notes, Google Docs, Obsidian and Goodnotes PDFs; full export to Markdown and CSV**; no credit counter on screen | It has to replace something they use today, so import and export can't be paywalled |
| Student Plus | $4 a month or $15 a semester, with a school email | Everything in Plus | Notion is free for students; this is the answer |
| Plus | $6 a month or $48 a year | Unlimited apps, the stronger builder, voice, automations | More than 5 apps, or the app they're building needs the stronger model |
| Pro | $12 a month | Connectors to other services, webhooks, bring your own AI key | Data that lives somewhere else (the Base44-style connectors) |

### 3. The opening offer

Move week: anyone who imports an existing setup gets Plus free for their first month. The offer ends Sun 31 Jan 2027. It pays the switching cost the panel named, once, and doesn't teach anyone to wait for discounts.

### 4. What to test with real people

- Two waitlist pages, identical except the price: Plus at **$6** against **$4**, with the student price shown on both. Count "reserve my price" clicks.
- One button on both pages, "Import from Notion / Notes / Obsidian": count clicks as a measure of how much switching cost matters.
- Survey question: "What would you move first?" It names the first app to build well.

### 5. The panel's objections, verbatim

- "My notes live in Apple Notes and Google Docs, they already sync between my phone and laptop, and I can already snap a whiteboard into a note." (P001)
- "Another $6 a month isn't happening unless Quilt replaces something I already pay for." (P004)
- "It's brand new, so there are no Play ratings or Reddit threads for me to read, and I don't pay for apps nobody has reviewed." (P006)

## The numbers

**The margin.** At $6 a month, with capture and chat on Claude Haiku 5.5 and app builds on Sonnet 5.5, each paying user-month leaves **$3.24 (54%)**. That's after AI, the 15% store fee and the AI of the 20 free users each payer carries. The margin at 500 paying users is 51%.

**The line to watch: which model does what.** With Opus 5.5 on every Clair action (what `spec/clair-agent.md` says today), each paying user-month loses $19.58 (`cfo-as-specced.md`), almost all of it from free users. Builds are the costliest action: one is about $0.20 on Opus and $0.10 on Sonnet. Free users building apps on Opus would cost more than the paid plan earns. Free users get Haiku and a build cap. Paid users get the stronger builder.

**Cash.** $374 before it pays for itself, earned back in month 5, if the ramp (10 paying users in month 1, 500 by month 12) holds. The panel's 0% buy rate doesn't support that ramp yet; a real waitlist has to.

**Three ways to improve the margin**, each from the tool:
1. Price $5 instead of $6: contribution falls from $3.24 to $2.24 and year-1 profit from $6,671 to $4,311. Price matters, but less than the model choice.
2. Web sign-ups through card payments instead of the store fee save about $0.43 each at $6.
3. Fewer free users per payer. 20 (a 5% conversion) is an assumption; at 10, contribution rises by $0.72.

**The board's money condition.** "AI cost per active user below revenue at every tier, including free" is **met only with the model split** (Haiku for capture, Sonnet for builds, a build cap on free). With Opus everywhere it fails badly.

An accountant should check the structure, payroll and tax before money moves. AI costs are estimates from published per-token prices with guessed token counts (`cfo-sources.md`); measure them on real runs.

## Unit economics: Quilt builder, recommended: $6 Plus, capture on Haiku 5.5, builds on Sonnet 5.5

Every number below comes from the input file. Nothing is looked up or guessed.

### One paying user-month

| line | per paying user-month |
| --- | ---: |
| Price | $6.00 |
| AI for one paying user (30 photo or file fills and 60 chat steps on Haiku 5.5; 3 app builds on Sonnet 5.5 at $0.10), estimate | -$0.42 |
| Store or card fee (15% subscription fee) | -$0.90 |
| AI for the 20 free users each payer carries (each: 6 fills, 10 chat steps on Haiku, half a build a month on Sonnet = $0.072), estimate | -$1.44 |
| **Contribution** (what each paying user-month leaves to pay the fixed costs) | **$3.24** (54%) |

### The margin that matters

Fixed costs: $81 a month (Vercel Pro, 2 members $40, Supabase Pro $25, Apple Developer Program ($99 a year) $8, Domain and email $8).

- **Break-even: 26 paying user-months a day.** Below that you lose money every month.
- **Profit margin at your plan** (500 a day): **51%** of every sale, after every cost.

### Year 1, month by month

| month | paying user-months a day | revenue | profit | cumulative (after $325 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 10 | $60 | -$49 | -$374 |
| 2 | 25 | $150 | -$0 | -$374 |
| 3 | 45 | $270 | $65 | -$310 |
| 4 | 70 | $420 | $146 | -$164 |
| 5 | 100 | $600 | $243 | $79 |
| 6 | 140 | $840 | $372 | $451 |
| 7 | 180 | $1,080 | $502 | $953 |
| 8 | 230 | $1,380 | $664 | $1,617 |
| 9 | 290 | $1,740 | $858 | $2,475 |
| 10 | 350 | $2,100 | $1,053 | $3,528 |
| 11 | 420 | $2,520 | $1,280 | $4,808 |
| 12 | 500 | $3,000 | $1,539 | $6,346 |

- **Year 1 operating profit: $6,671** on $14,160 of revenue.
- After the $325 startup spend: $6,346.
- Startup money earned back: month 5.
- Cash you need before it pays for itself: **$374**.

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 51% | 26 | $6,671 |
| Price -10% | 46% | 31 | $5,255 |
| Volume -20% | 51% | 26 | $5,142 |
| Unit costs +15% | 44% | 29 | $5,694 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.

## Not done yet

- The offer: run /founder-offer
- Marketing: run /founder-marketing
- Brand: run /founder-brand
- Operations: run /founder-ops
- Launch plan: run /founder-launch

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
