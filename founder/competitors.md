# Competitors: Quilt as a personal app builder for students

Checked 2026-11-19, public sources only. Raw rows: `founder/competitors.csv`. App Store ratings come from Apple's public lookup API (US). Google Play ratings come from the US listing pages. Both were read on 2026-11-19.

The job: a University of Utah student describes an app (class notes with a folder per course, a journal, a workout log, a car tracker, a budget). The AI builds it and fills any app from a photo, a sentence, a file or a connector. Every draft waits for one tap of OK, and the apps sync between phone and laptop. Android and web come first. Budgeting apps were covered in `run-1-photo-wedge/competitors.md` and aren't redone here.

## 1. The table, most direct first

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

## 2. Price range for the comparable paid plan

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

## 3. Positioning map

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

## 4. Complaints, ranked

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

## 5. The gap

**No product lets a student say "make me a class-notes app" on an Android phone, have the AI build it as a lasting, linked app, and fill it from a photo, at a student price, without the AI writing anything the student didn't approve.** The evidence:

- **The AI that builds structure is priced out of students' reach or pointed at business.** Notion's database-building AI is on Business at $20, while the plan students get free has only a trial. Base44 ($16), Softr ($19) and Lovable ($25) build business web apps. Base44's own reviews complain most about credits (theme 8).
- **The apps students already use are weakest on the phone** (theme 3, about 100 reviews). Notion, Obsidian and Capacities are all praised on desktop and panned on mobile. Base44 has no Android app on Play.
- **Photo and file fill exists, but scattered.** Capacities Pro reads images and PDFs, Base44 has an extraction integration, and Goodnotes and Notability make quizzes from notes. None of them turns a photo into rows across a student's own apps.
- **AI that acts without asking is a liability.** About 45 reviews revolt against AI pushed into the product (theme 7), and about 70 report lost notes (theme 4). One tap of OK before any change, and nothing lost, directly answers both. A note on this, though: the backlash means "AI" in the pitch will repel part of the market.

How strong the gap is: it's narrow. **Taskade Genesis already builds an app from one sentence for $6/mo, with iOS and Android apps.** What Quilt adds over Taskade is phone-first capture, filling from photos (not confirmed on Taskade's page), a student focus, and the consent step. Those are differences of degree, not a moat, so test them against Taskade by name in the survey.

## 6. The threat: who could copy fastest

1. **Notion, the biggest threat.** It already has student distribution (Plus is $0 with a school email) and an AI that "can help you create databases, complete with views and properties." If it moves AI to Plus or to the student plan, it covers "describe a class-notes app" at $0 overnight. Its weak spot is the mobile app (theme 3) and the anti-AI backlash in its own reviews (33 of 310). This is inference from the pricing page; Notion has announced no such move.
2. **Taskade, the closest product today.** Genesis does prompt-to-app at the same $6 price, on Android and iOS. Aiming it at students with a template gallery and photo capture is a marketing move more than a build. Limits: an Android rating of 3.8 (28.5K reviews) and positioning as a business "AI agents" tool.
3. **Base44 (Wix), the closest on capability.** It already has photo/PDF extraction, OAuth connectors and app generation. A "personal apps" mode would take little building. Limits: web-first, no Android app found, a 3.0 iOS rating and a 2.7 Trustpilot score with credit complaints, and Wix's business-website buyer.
4. Goodnotes and Notability own student handwriting on iPad and are adding AI fast, but they show no sign of building structured apps. ChatGPT and Claude can make a one-off tracker in chat today, and the student pays nothing extra for it. That's the substitute to beat in the demo.

Defence the evidence supports: phone-first with Android on day one, a visible OK before every AI change, no data loss (export and version history up front), and a student price published on the pricing page, where Goodnotes, Notability, Capacities and Taskade publish none.
