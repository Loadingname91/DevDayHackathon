# Quilt · Business plan

**Verdict: Not yet**

- ✓ Each paying student-month earns $1.79 before fixed costs (60% contribution).
- ✓ Year 1 operating profit: $3,249.
- ✗ 0 of 20 simulated buyers buy (0%, the bar is 25%).

| key number | |
| --- | ---: |
| Price | $3.00 a paying student-month |
| Profit margin at plan | 54% per paying student-month |
| Break-even | 46 paying student-months a day |
| Year 1 operating profit | $3,249 |
| Startup spend | $325 |
| Cash needed before it pays for itself | $426 |
| Startup money earned back | month 7 |
| Buyer panel | 0 buy · 20 pass |

## The idea

- What it is: a phone-first app where an AI assistant, Clair (built on Claude), builds small personal apps (Budget, Groceries, Classes, To-dos, Workout, Subscriptions, Calendar) and fills them from a photo, a file or a sentence; every change waits as a draft until the user taps OK, and one confirm updates every app it touches.
- Who it is for: full-time undergraduates (18 to 24) at the University of Utah, phone-first, managing their own money for the first time, who pay a "forgetting tax" (forgotten renewals, late fees, groceries that go off, missed deadlines) and won't connect a bank account.
- What it sells, at what price (proposal, not decided): Free (5 apps, 50 Clair credits a month); Plus $6 a month or $48 a year (unlimited apps, 1,000 credits, voice, automations); Pro $12 a month or $96 a year (4,000 credits, connectors, bring your own AI key); Teams $10 per seat a month. Credits: chat step 1, photo fill 5, app build 10, scheduled run 2. Extra packs $5 for 500 credits. Later, a marketplace where creators sell apps and keep 80%.
- Where and how: online. Android app (APK first) and the same build as a website; first users found through U of U student groups, a survey and a waitlist landing page. Delivered as an app with a hosted API (Vercel) and database (Supabase); the AI runs on Anthropic's API.
- Budget and constraints: a two-person founding team building for a hackathon demo (Lassonde DevDay, Fri 20 Nov 2026). No funding, budget, survey results or waitlist numbers exist yet. The cost of AI per user is not yet measured.

## Summary

**What has to change first:** the price, the model behind capture, and the proof. The panel bought nothing at $6, so Quilt needs a student price ($12 a semester), a cheap model for photo fills, and real sign-ups at that price (`/founder-offer`, then a waitlist test from `/founder-launch`).

Quilt is a phone app where Clair turns a photo of a receipt, a syllabus or a fridge into updates across a student's budget, grocery list and due dates, with nothing saved until they tap OK and no bank login. It's for University of Utah undergrads managing money for the first time.

**Verdict: Not yet.**
- **Margin:** at $3 a month, with capture on Claude Haiku 5.5, each paying student-month leaves $1.79 (60%). At the pitched $6 with Opus 5.5 on every action, each one loses $17.18.
- **Break-even:** 46 paying students.
- **Year 1:** $3,249 operating profit if 500 students are paying by month 12.

That ramp is untested: 0 of 20 simulated buyers bought at $6, and the bar is 25%.

**Where the board and the panel agree:** narrow to the receipt wedge, prove capture works first time, and keep AI cost below the price. The panel adds what the board couldn't know: the acceptable price is $1 to $4 a month, 5 of 20 buyers raised the missing iPhone app, and 4 of 20 asked for a free student plan through the U.

**Where they disagree:** the Monopoly lens sees no durable advantage. The Product lens counts draft-then-confirm and no bank login as real ones. The panel mostly didn't care about either; it compared Quilt with the free Notes app.

**The biggest risk:** students use the free tier and never pay. The answer is to make the free tier cheap to serve (Haiku capture costs about $0.02 per free user a month) and to test who else pays: a semester price, or the university per student.

**To start:** about $426 of cash and the founders' time. The first test is a waitlist page at $12 a semester against $20 a year, plus the survey question "Would you use it if the U paid for it?"

**This week:** put the waitlist page up with a real price before the DevDay pitch, so the "[N] students joined" line has a real number.

These are simulated buyers and projected numbers. Real sign-ups at a real price outrank all of it.

## What the board said

**Vote: 3 fund if, 0 pass. Average score 4.7 / 10** (Offers 4, Monopoly 4, Product 6). The memos are in `founder/board/`.

### Risks more than one member raised

1. **Too much at once.** Seven app types, four tiers, credit packs, Teams and a marketplace (all three lenses). Each lens names the same wedge: receipt → Budget + Groceries.
2. **Capture has to work first time.** Two failures and the student goes back to Notes. First-try accuracy and photo-to-OK time are unmeasured (Offers, Product).
3. **AI cost against a $6 price.** Every fill costs money and the cost per active user is unknown. 50 free credits buy about 10 photo fills a month (all three).
4. **Willingness to pay.** Price-sensitive students, and every competitor has a free tier (Offers, Monopoly).

Where they disagree: the Monopoly lens says there is no durable advantage yet (the model is rented; Notion, Google or Apple could copy the feature). The Product lens rates draft-then-confirm and the no-bank-login stance as real craft advantages. The Offers lens doesn't count either as a moat; it wants the advantage to come from the offer (a result guarantee, a semester plan).

### Conditions checklist

- [ ] Willingness to pay measured before prices are fixed (`/founder-consumer`, `/founder-pricing`)
- [ ] AI cost per active user at the planned credit limits leaves a margin at $6 a month, and on the free tier (`/founder-cfo`)
- [ ] One wedge first: receipt → Budget + Groceries at one campus. Marketplace, Teams, connectors, bring-your-own-key and automations parked until it keeps users
- [ ] A capture bar hit before growth: first-try accuracy on 50 real student receipts, and photo-to-OK faster than typing into Notes (close to 10x)
- [ ] One offer named after the outcome (for example a semester plan: syllabus import, renewal alerts, rebuy list), priced per semester, with credits kept out of the pitch (`/founder-offer`)
- [ ] A guarantee tied to a result, and urgency from the start of term (`/founder-offer`)
- [ ] Credits out of the free user's way: no counter on the main screen, and a failed capture costs nothing
- [ ] A named durable advantage with first evidence: shared household lists, owned buying history, or a campus brand
- [ ] Distribution shown: U of U waitlist sign-ups and cost per user
- [ ] iPhone shipped, or evidence that Android plus web reaches the target students (`/founder-consumer`)

### The strongest version the board can see

A campus-first "stop the forgetting tax" plan for students, sold by the semester. One photo of a receipt or a syllabus updates money, groceries and deadlines in one tap, with no bank login and nothing to set up. It launches at the U of U with the receipt beat polished until it beats the Notes app on speed. It is priced around the outcome (renewals caught, deadlines met) with a guarantee rather than around credits. The other apps, the marketplace and Teams wait until students keep coming back. This is narrower than the pitch, which leads with "describe any need and Clair builds an app": the board would fund the wedge, not the platform.

## The competition

Checked 2026-11-19, public sources only. The raw rows are in `founder/competitors.csv`. Ratings come from the US App Store (via Apple's public lookup API) and the US Google Play listing, both read on 2026-11-19.

Buyer: a University of Utah undergrad, 18 to 24, phone-first, managing money alone for the first time. Won't connect a bank and drops any app that needs setup. Job: stop the "forgetting tax". Wedge: receipt photo → Budget + Groceries in one tap.

### 1. The table, most direct first

| # | Name | Type | Platforms | Comparable paid plan | Student price | No bank login? | Own headline | Rating (reviews) |
|---|---|---|---|---|---|---|---|---|
| 1 | [Finny](https://getfinny.app/) | direct | iPhone only | Pro [$3.49 / $24.99](https://apps.apple.com/us/app/finny-ai-money-manager/id6736472735) (period not labelled) | none listed | yes, "No bank login, ever" | "Stop typing your transactions." | iOS 4.4 (38) |
| 2 | [Yomio](https://apps.apple.com/us/app/yomio-budget-expense-tracker/id6757447181) | direct | iPhone | $5.99/mo, $49.99/yr | none | not stated | "Scan receipts, manage budget" | iOS 5.0 (4) |
| 3 | [Monarch](https://www.monarch.com/pricing) | direct | iOS, Android, web | Core $14.99/mo, $99.99/yr | none listed | no; [receipt scan matches a bank transaction](https://www.monarch.com/blog/winter-release) | "Your home base for money clarity" | iOS 4.9 (119,099); Android 4.8 (26.8K) |
| 4 | [Cleo](https://web.meetcleo.com/pricing) | direct | iOS, Android | Plus $5.99/mo ([via Toolradar](https://toolradar.com/tools/cleo-ai/pricing); Cleo's page returned 403) | none found | no (Plaid) | "Credit Builder & Savings Goals" (App Store subtitle) | iOS 4.7 (270,188); Android 4.6 (158K) |
| 5 | [YNAB](https://www.ynab.com/pricing) | direct | iOS, Android, web | $14.99/mo, $109/yr | **free for one year** ([college program](https://www.ynab.com/college)) | direct import from select banks, or [file import](https://www.ynab.com/pricing) | "Save $600 in one month, $6,000 in one year" | iOS 4.8 (62,249); Android 4.6 (25.5K) |
| 6 | [Rocket Money](https://help.rocketmoney.com/en/articles/2217739-how-much-does-rocket-money-cost) | direct | iOS, Android, web | Premium pay-what-you-want ([App Store](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675): $2.99 to $9.99); Premium+ $15/mo | none | no (account linking) | "The money app that works for you." | iOS 4.5 (408,979); Android 4.5 (142K) |
| 7 | [Goodbudget](https://goodbudget.com/signup) | direct | iOS, Android, web | Premium $10/mo, $80/yr | none | yes on Free (manual); bank sync is paid | "Budget with a why" | iOS 4.6 (13,552); Android 3.1 (19.2K) |
| 8 | [Copilot Money](https://copilot.money/pricing) | direct | iPhone, iPad, Mac, web; **no Android** | $9/mo, $109/yr on the site; [App Store](https://apps.apple.com/us/app/copilot-track-budget-money/id1447330651) shows $18 monthly | none | no | "Your money finally has a copilot." | iOS 4.8 (31,079) |
| 9 | [Notion + Notion AI](https://www.notion.com/pricing) | direct (DIY) | iOS, Android, web | Plus $10/member/mo; AI only a "Limited Trial" below Business ($20) | **Plus free with a school email** | yes | "One tool to run your company." | iOS 4.8 (90,737); Android 4.6 (408K) |
| 10 | [My Study Life](https://mystudylife.com/) | indirect | iOS, Android, web | MSL+ $6.99/mo, $39.99/yr | core is free | n/a | "The free student planner that keeps school life organised." | iOS 4.5 (6,243) |
| 11 | [AnyList](https://www.anylist.com/complete) | indirect | iOS, Android, web | Complete $9.99/yr ($14.99 household) | none | n/a | "One app for stress-free shopping, cooking, and meal planning." | iOS 4.9 (81,600); Android 4.9 (31.1K) |
| 12 | [Bring!](https://www.getbring.com/en/home) | indirect | iOS, Android | Premium $1.99/mo, $8.99/yr ([NerdWallet](https://www.nerdwallet.com/article/finance/best-grocery-list-apps)) | none | n/a | "The easiest shopping list to share" | iOS 4.8 (9,890); Android 4.1 (145K) |
| 13 | [Todoist](https://www.todoist.com/pricing) | indirect | iOS, Android, web | Pro $5/mo yearly ($60), $7 monthly | none listed | n/a | "Clarity, finally." | iOS 4.8 (130,892); Android 4.6 (308K) |
| 14 | [Hevy](https://apps.apple.com/us/app/hevy-workout-tracker-gym-log/id1458862350) | indirect | iOS, Android, web | Pro $2.99 to $3.99/mo, $23.99/yr, $74.99 lifetime | none | n/a | "Log Workouts" | iOS 4.9 (104,519); Android 4.9 (293K) |
| 15 | [Fetch](https://fetch.com/) | indirect | iOS, Android | free; scanned receipts earn points | n/a | n/a | "EARN REWARDS ON EVERYTHING" | iOS 4.9 (7,881,375) |
| 16 | Notes app ([Keep](https://keep.google.com/) / Apple Notes) | substitute | preinstalled | free | n/a | yes | n/a | n/a |
| 17 | [Google Sheets](https://www.google.com/sheets/about/) template | substitute | web, mobile | free | n/a | yes | n/a | n/a |
| 18 | The bank's own app alerts | substitute | the student's bank | free | n/a | uses their own bank | n/a | n/a |
| 19 | Doing nothing | substitute | n/a | $0 up front; the forgetting tax later (no public per-student figure found) | n/a | n/a | n/a | n/a |

Also on the App Store but not checked in detail: single-job syllabus scanners such as [Sylly](https://apps.apple.com/us/app/id6759631749), [Ahead](https://apps.apple.com/us/app/id6756762430) and [PlanPilot](https://apps.apple.com/us/app/planpilot/id6751422511) (photo or voice → schedule; no ratings shown yet). The syllabus beat is crowded with small apps. None of them touches money.

#### Re-check of the price table in `docs/pitch.md`

| App | Pitch says | Found 2026-11-19 | Verdict |
|---|---|---|---|
| Notion | Free, Plus $10, Business $20 | [Same](https://www.notion.com/pricing). Also: **Plus is free for students** and AI is a "Limited Trial" on Free and Plus | correct; add the student line |
| Zapier | Free 100 tasks, Pro from $19.99 for 750 | [$19.99/mo billed yearly, $29.99 billed monthly](https://zapier.com/pricing) | correct only for yearly billing |
| Make | paid from about $9 | the [pricing page](https://www.make.com/en/pricing) as fetched showed 1,000 free credits but no paid prices | could not verify $9 |
| Airtable | Team $20, Business $45 | [$20 and $45 per user per month, billed yearly](https://www.airtable.com/pricing) | correct (yearly billing) |
| Taskade | Free to Max $100 | [Starter $6, Pro $10, Business $25, Max $100 a month, billed yearly](https://www.taskade.com/pricing) | correct |
| Todoist | Pro $5 | [$5/mo billed yearly, $7 billed monthly](https://www.todoist.com/pricing) | correct only for yearly billing |
| Rocket Money | Premium pay-what-you-want, Premium+ $15 | [Same](https://help.rocketmoney.com/en/articles/2217739-how-much-does-rocket-money-cost) | correct |
| Glide | Free to Pro $125 | [Free, Basic $25, Plus $50, Pro $125](https://www.glideapps.com/pricing) | correct |

That table compares builder and automation tools, and this buyer doesn't shop for those. The anchors this student will actually see are YNAB and Notion, both **$0 for a student**, and Cleo at $5.99.

### 2. Price range for the comparable paid plan

Comparable plan: the cheapest paid plan that unlocks the capture or budgeting feature, for the nine direct competitors.

| | Monthly | Yearly |
|---|---|---|
| Lowest | $2.99 (Rocket Money Premium, pay-what-you-want floor on the App Store) | $24.99 (Finny Pro, period inferred) |
| Median | **$9** (Copilot) | **about $90** (between Goodbudget $80 and Monarch $99.99) |
| Highest | $14.99 (YNAB, Monarch); outliers are Rocket Money Premium+ at $15 and Copilot's App Store price of $18 | $109 (YNAB, Copilot) |

What the student actually pays: YNAB is $0 for year one and Notion Plus is $0. The no-bank AI capture apps sit at $3.49 to $5.99 a month. Indirect single-job apps are cheap: Bring $8.99 a year, AnyList $9.99, Hevy $23.99, My Study Life $39.99, Todoist $60. Quilt's proposed Plus at $6 a month or $48 a year sits at the bottom of the direct range, next to Cleo ($5.99) and Yomio ($5.99 or $49.99 a year).

### 3. Positioning map

Axis X: setup effort, including whether a bank login is needed. Axis Y: how many life areas one capture updates (money, groceries, classes, to-dos).

```
Breadth across life areas
  HIGH |  [ EMPTY: Quilt's target ]           Notion (you build it yourself;
       |                                      AI gated above $20)
       |
   MID |  Fetch (receipts -> points,          Cleo (money chat + cash advance)
       |   no budget)                         Rocket Money (money + subscriptions)
       |
   LOW |  Finny, Yomio (money only,           YNAB, Monarch, Copilot
       |   iPhone only)                       (bank-first; Monarch scans receipts
       |  Goodbudget free (manual money)       against bank transactions)
       |  AnyList, Bring, Todoist, Hevy,
       |  My Study Life, syllabus scanners
       |  (one job each)
       +--------------------------------------------------------------------
          snap / type, no bank login                  bank login + setup
                              Setup effort
```

The top-left corner is empty. That means low setup, no bank login, and one capture landing in several life areas. The no-bank tools are single-job. The broad tool (Notion) is a blank canvas you have to build. The money leaders start by asking for a bank login.

### 4. Complaints, ranked

Source: the 100 most recent US App Store reviews for each of Cleo, YNAB, Rocket Money, Goodbudget and Monarch, from Apple's public review feed (`https://itunes.apple.com/us/rss/customerreviews/id=<app id>/sortby=mostrecent/json`). 302 of them were rated 1 to 4 stars. Date windows: Cleo Nov 6 to 17, 2026; Rocket Money Nov 5 to 17; Monarch Oct 20 to Nov 18; YNAB Sep 1 to Nov 17; Goodbudget Jan 2024 to Nov 2026 (it gets fewer reviews). I coded themes by keyword and then removed the false positives I spotted by hand, so treat the counts as approximate. One review can count toward several themes. The Google Play pages only showed three old "most relevant" reviews each, so they're used for the grocery theme alone.

| Rank | Theme | ~Count | Where | Quotes |
|---|---|---|---|---|
| 1 | **Bank sync is late, wrong or drops out** | ~50 | Goodbudget 20, YNAB 13, Monarch 13, Rocket 9 | "unless you check it every day you’ll lose stretches of spending or deposits" ([YNAB, 1★, Sep 2026](https://apps.apple.com/us/app/ynab/id1010865877?see-all=reviews)); "in the past year I found 5K in missing transactions" ([Rocket Money, 1★, Nov 2026](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675?see-all=reviews)) |
| 2 | **Price and paywalls** | ~40 (~24 without Cleo's cash-advance fees) | Cleo 16, Rocket 12, Monarch 5, Goodbudget 4, YNAB 3 | "now it just seems every feature is now a paid thing" ([Rocket Money, 1★, a user who first used it "as a teenager/early adult"](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675?see-all=reviews)); "This app doesn’t need a subscription. Just charge $10.00 to buy the full version." ([Goodbudget, 3★](https://apps.apple.com/us/app/goodbudget-budget-planner/id471112395?see-all=reviews)) |
| 3 | **Too much setup and upkeep; redesigns add taps** | ~39 | YNAB 19, Goodbudget 11, Monarch 8 | "It proved to require a lot more setup and maintenance for my needs." ([YNAB, 3★](https://apps.apple.com/us/app/ynab/id1010865877?see-all=reviews)); a student on the free year: "the reconciliation process seemed very tedious and ultimately made me not want to open the app" ([YNAB, 4★, Oct 2026](https://apps.apple.com/us/app/ynab/id1010865877?see-all=reviews)) |
| 4 | **Bugs, crashes, lost data** | ~35 | Goodbudget 16, Monarch 8 | "Updated the app and all my envelopes got deleted!" ([Goodbudget, 1★](https://apps.apple.com/us/app/goodbudget-budget-planner/id471112395?see-all=reviews)); "the app crashes within 10 seconds of opening" ([Monarch, 1★](https://apps.apple.com/us/app/monarch-budget-track-money/id1459319842?see-all=reviews)) |
| 5 | **The money app adds its own forgetting tax: surprise renewals, charges after cancelling** | ~23 | Rocket 14, Monarch 6 | "The billing renewal occurs without any notice." ([Monarch, 2★, Nov 2026](https://apps.apple.com/us/app/monarch-budget-track-money/id1459319842?see-all=reviews)); "Canceled my subscription and am still getting charged several months later." ([Rocket Money, 1★](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675?see-all=reviews)) |
| 6 | **No human support** | ~16 | Cleo 7, Monarch 4 | "There is no real customer support, only an automated system." ([Cleo, 1★](https://apps.apple.com/us/app/cleo-ai-cash-advance-budget/id1447274646?see-all=reviews)) |
| 7 | **Subscription tracking misses or gets dates wrong** | ~14 | Rocket Money only | "Frequently has wrong dates for upcoming bills and is late with “reminders” of bills that are past due." ([Rocket Money, 3★](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675?see-all=reviews)); "each of them told me I couldn’t cancel them in the rocket money app" ([Rocket Money, 1★](https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675?see-all=reviews)) |
| 8 | **Data-selling worries** (reviewers' claims, not checked) | 8 | Monarch 6, Goodbudget 2 | "They sell everything from your demographics, to what you buy, to your financial data." ([Monarch, 1★](https://apps.apple.com/us/app/monarch-budget-track-money/id1459319842?see-all=reviews)) |
| 9 | **Grocery lists don't know what things cost** (thin) | 2 | AnyList, Bring (Google Play, 2018 and 2019) | "wish it would auto-fill the prices in" ([AnyList, 4★](https://play.google.com/store/apps/details?id=com.purplecover.anylist)); "so I can get an idea of how much I'm about to spend before I go to the store" ([Bring!, 3★](https://play.google.com/store/apps/details?id=ch.publisheria.bring)) |

Cleo's low reviews are mostly about cash-advance fees and limits, which is a different job from Quilt's. Monarch also had about 10 complaints about missing iPhone Duo screen support, which don't matter here.

### 5. The gap

**No app turns one photo into updates across money, groceries and deadlines without a bank login, and none does it on Android and iPhone both.** The evidence:

- The incumbents' top complaint is the bank link itself (theme 1, about 50 of 302 reviews), and this buyer won't make one. YNAB's student offer is free, yet the student reviewer still stalled on imports and reconciliation (theme 3).
- The apps that skip the bank link are single-job and iPhone-only. [Finny](https://apps.apple.com/us/app/finny-ai-money-manager/id6736472735) and [Yomio](https://apps.apple.com/us/app/yomio-budget-expense-tracker/id6757447181) are money only, and so is Goodbudget free, where you type everything by hand. Copilot has no Android app either.
- [Monarch](https://www.monarch.com/blog/winter-release) already reads receipts and splits them into categories, but only to attach them to a bank transaction. The items never reach a grocery list.
- Grocery-list apps don't know spend (theme 9, thin). Syllabus scanners don't know money. Notion can hold it all, but the student has to build it, and AI is a trial below $20.
- The money apps themselves add to the forgetting tax (theme 5). A renewal reminder before Quilt charges anyone, and one-tap cancel, would be cheap proof of the promise.

How strong this is: it's a real gap in posture (no bank login, cross-app, Android), but it's a gap in features, not a moat. Whether students want a receipt to touch their grocery list as well as their budget is backed by only two old reviews. Test it in the survey before treating it as demand.

### 6. The threat: who could copy fastest

1. **Finny, the fastest copier.** It already has no bank login, AI capture by text, voice and receipt scan, and family sharing. Adding "send these items to a list" is one feature away. Limits: iPhone only, 38 ratings, a solo developer.
2. **Monarch, the closest on capability.** Its receipt parsing already itemizes and recategorizes, and it has an AI Assistant. Routing items to a list or due dates to a calendar would be a small step for it. Limits: bank-first, $99.99 a year, no student price, and an older household buyer.
3. **Notion, the biggest threat on distribution.** Plus is already free to every student with a school email, and its AI autofills databases. If Notion moves AI capture down to the free or Plus plan, a "student life" template with photo fill would undercut Quilt on price ($0) and on reach. This one is inference, not evidence: Notion's pricing page shows AI gated today.
4. Cleo has the young AI-chat audience (270K iOS ratings), but its reviews show a cash-advance business now, not a capture tool.

Defence the evidence supports: Android plus web on day one (Finny and Copilot aren't there), no bank login as a promise, first-try capture accuracy that beats typing, and a U of U campus brand before Notion or Monarch notice the segment.

## The buyer panel

**0 buy · 20 pass** (0% buy) out of 20 simulated buyers. Seed 485390, so the same cards can be dealt again.

These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the big ones with real people before you spend.

### By segment

| group | buyers | buy rate |
| --- | ---: | ---: |
| Part-time job plus some support | 9 | 0% |
| Mostly supported by family or aid | 8 | 0% |
| Self-funded, working most weeks | 3 | 0%  (thin) |

### By buying behaviour

| group | buyers | buy rate |
| --- | ---: | ---: |
| Notes-app loyalist | 4 | 0%  (thin) |
| Organised planner | 2 | 0%  (thin) |
| Stressed and behind | 3 | 0%  (thin) |
| Free-tier only | 4 | 0%  (thin) |
| Reads every review | 2 | 0%  (thin) |
| Loyal to a finance app | 1 | 0%  (thin) |
| App hopper | 4 | 0%  (thin) |

### By income

| group | buyers | buy rate |
| --- | ---: | ---: |
| $4,000 to $15,000 | 6 | 0%  (thin) |
| under $4,000 | 6 | 0%  (thin) |
| $15,000 and up | 8 | 0% |

### Why they pass

| reason | buyers | in their words |
| --- | ---: | --- |
| habit | 8 | "I already have my Notion and a spreadsheet set up exactly how I like them, and I don't earn anything, so another $6 a month isn't happening. I might try the free version, but 5 apps and 10 photos is more than I'd actually use." (P002) · "My Notes app already does my grocery list and money notes, and it's free and I never have to check anything. I might try the free version once out of curiosity, but I'm not paying $6 a month when I make like $2,000 a year." (P007) |
| price | 7 | "I'm literally trying to cancel subscriptions after getting burned by a renewal this semester, so I'm not adding a $6 one. I'd maybe try the free version to catch due dates, but I'm not paying for Plus." (P003) · "I don't pay for apps, period. And it's not even on iPhone yet, so I can't use the free version either. Our house Venmo request and the Notes app already handle groceries fine." (P004) |
| convenience | 4 | "I'm on an iPhone and it says iPhone later, so I'd be stuck using a website in Safari, and my Notes app already does lists and money stuff fine. Not paying for something I can't even install." (P001) · "I've got an iPhone, so it's out for now. I'm not saving a website to snap receipts from Smith's. Even if it was on iPhone I'd use the free version for a week and forget about it, and I'm not paying $6 a month for that." (P012) |
| trust | 1 | "It's brand new, so there are no Play ratings or Reddit threads for me to check, and I'm not paying for anything I can't read reviews on first. At most I'd poke at the free tier with a syllabus PDF, and on $4,000 a year the free version would have to fail me before I'd even think about $6." (P010) |

### Why they buy

| reason | buyers | in their words |
| --- | ---: | --- |

### What would flip a no

- A real iPhone app where the free tier handles my groceries and budget well enough that I'd actually ditch Notes.
- If it could pull in my existing Notion or spreadsheet so I didn't have to start over, and I actually kept using the free version for a full month.
- If the free tier actually caught a renewal or a late fee for me and saved more than it costs, I'd think about Plus around finals.
- An iPhone app with a free student plan that covers what I'd actually use, like unlimited Plus with a uNID.
- A free student deal through the U, like a year of Plus free with my uNID email.
- A free student plan through the U, or the Plus tier bundled with something I already pay for, like a student discount at $1 or $2 a month.
- Seeing it read a crumpled corner-store receipt perfectly on the first try, and the free tier being enough that I never hit a paywall.
- Solid Play Store ratings and Reddit threads from other U of U students saying the free tier actually saves them money, plus a one-time price or a cheap student price around $1-2 a month.
- If the syllabus photo really dropped every due date for the semester into my calendar, I might use the free tier for that. I still wouldn't pay unless it replaced the budgeting app I already have.
- A bunch of real reviews from other U of U students saying it read their receipts and syllabi correctly without much fixing, plus a student price around $2 to $3 a month.
- If I actually kept using the free version for a month and it nailed my receipts and syllabus without me fixing stuff, I'd maybe pay, but only around $3 a month.
- An iPhone app that's still worth opening after the first week, like if it actually stopped me running out of money before payday.

20 buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder.

## Pricing

Simulated buyers chose what to test here. None of it is proof; real students decide.

### 1. The price

**Student Plus at $3 a month, sold as $12 a semester (four months).** It sits in the middle of the panel's acceptable range ($1.00 to $4.00; `pricing-curve.md`), just above the point where as many buyers call it a bargain as call it expensive ($2.02). It's below every direct competitor's paid plan (lowest $2.99, median $9; `competitors.md`) and level with Rocket Money's pay-what-you-want floor. At $3, with photos and chat on Claude Haiku 5.5, each paying student-month leaves $1.79 (60%) after AI, the store fee and the free users each payer carries (`cfo.md`).

The pitched $6 is above the range: all 20 buyers passed, and 12 of the 20 named $6 or less as "too expensive to buy at all". At $6 with Opus 5.5 on every action, each paying student-month loses $17.18 (`cfo-as-pitched.md`).

### 2. The ladder

| Rung | Price | What it holds | Why step up |
| --- | --- | --- | --- |
| Free | $0 | Every starter app; about 30 photo fills a month on Haiku (about $0.07 of AI); no credit counter on screen | It has to beat the Notes app for a whole month on its own (the most repeated flip condition) |
| Student Plus | $12 a semester ($3 a month) | Unlimited apps and photo fills (fair-use cap), syllabus import, renewal reminders, voice | Students think in semesters, and syllabus week and finals are when the free cap would bite |
| Campus | Paid by the university per student (to test) | Plus for every student with a uNID | 4 of 20 buyers asked for a free student plan through the U |

Credits stay in the background as a cost control. The pitch never mentions them.

### 3. The opening offer

Waitlist students get Plus free through finals (ends Wed 16 Dec 2026), then $12 for the spring semester. It's a real end date tied to the term, and it doesn't train anyone to wait for discounts.

### 4. What to test with real students

- Two waitlist pages, identical except the price: **$12 a semester** against **$20 a year**. Count sign-ups that click "reserve my price".
- One question for the survey: "Would you use it if the U paid for it?" That tests the Campus rung before anyone pitches a university.

### 5. The panel's price objections, verbatim

- "I'm literally trying to cancel subscriptions after getting burned by a renewal this semester, so I'm not adding a $6 one." (P003)
- "I don't pay for apps, period." (P004)
- "If I actually kept using the free version for a month and it nailed my receipts and syllabus without me fixing stuff, I'd maybe pay, but only around $3 a month." (P011)

## The numbers

**The margin.** At $3 a paying student-month, with capture and chat on Claude Haiku 5.5, each one leaves **$1.79 (60%)** after AI, the 15% store fee and the AI of 20 free users per payer. The profit margin at 500 paying students is 54%.

**The line to watch: which model runs capture.** The spec has every Clair action on Opus 5.5. With that model and the pitched $6, each paying student-month loses $17.18, mostly because 20 free users on Opus cost about $17.40 (`cfo-as-pitched.md`, red flags: below variable cost, year 1 −$41,520). The model choice moves the result far more than the price does. Only a cheap model for capture keeps a generous free tier affordable.

**Cash.** $426 before it pays for itself, earned back in month 7, if the ramp (10 paying students in month 1 to 500 in month 12) holds. The panel's 0% buy rate at $6 doesn't support that ramp yet; it is the assumption a real waitlist has to test.

**Three ways to improve the margin**, each from the tool:
1. Price −10% ($2.70) costs 5 points of margin (54% → 49%) and $708 of year-1 profit: price matters less than the model.
2. Selling through the website instead of Google Play swaps the 15% fee ($0.45) for card fees (2.9% + $0.30, about $0.39). It's a small gain, and only for web sign-ups.
3. Unit costs +15% still leave 48%. The free-user AI line is the one to watch: 20 free users per payer is an assumption (a 5% conversion rate).

**The board's money conditions.** "AI cost per active user leaves a margin at $6": **met only with a cheap capture model**; at Opus on everything it fails badly. "Willingness to pay measured": **not met**; the panel says $1 to $4, and real students haven't been asked.

An accountant should check the structure, payroll and tax before money moves. The AI costs are estimates from published per-token prices with guessed token counts (`cfo-sources.md`); measure them on real runs before trusting them.

## Unit economics: Quilt (recommended model: student price, cheap model for capture)

Every number below comes from the input file. Nothing is looked up or guessed.

### One paying student-month

| line | per paying student-month |
| --- | ---: |
| Price | $3.00 |
| AI for one paying student (30 photo fills, 60 chat steps on Haiku 5.5; 1 app build on Opus 5.5), estimate | -$0.32 |
| Store or card fee (15% Google Play subscription fee) | -$0.45 |
| AI for the free users each payer carries (20 free users x $0.022, Haiku), estimate | -$0.44 |
| **Contribution** (what each paying student-month leaves to pay the fixed costs) | **$1.79** (60%) |

### The margin that matters

Fixed costs: $81 a month (Vercel Pro, 2 members $40, Supabase Pro $25, Apple Developer Program ($99 a year) $8, Domain and email $8).

- **Break-even: 46 paying student-months a day.** Below that you lose money every month.
- **Profit margin at your plan** (500 a day): **54%** of every sale, after every cost.

### Year 1, month by month

| month | paying student-months a day | revenue | profit | cumulative (after $325 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 10 | $30 | -$63 | -$388 |
| 2 | 25 | $75 | -$36 | -$425 |
| 3 | 45 | $135 | -$1 | -$426 |
| 4 | 70 | $210 | $44 | -$382 |
| 5 | 100 | $300 | $98 | -$284 |
| 6 | 140 | $420 | $169 | -$114 |
| 7 | 180 | $540 | $241 | $127 |
| 8 | 230 | $690 | $330 | $457 |
| 9 | 290 | $870 | $438 | $895 |
| 10 | 350 | $1,050 | $545 | $1,440 |
| 11 | 420 | $1,260 | $671 | $2,111 |
| 12 | 500 | $1,500 | $814 | $2,924 |

- **Year 1 operating profit: $3,249** on $7,080 of revenue.
- After the $325 startup spend: $2,924.
- Startup money earned back: month 7.
- Cash you need before it pays for itself: **$426**.

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 54% | 46 | $3,249 |
| Price -10% | 49% | 55 | $2,541 |
| Volume -20% | 53% | 46 | $2,405 |
| Unit costs +15% | 48% | 51 | $2,821 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.

## Not done yet

- The offer: run /founder-offer
- Marketing: run /founder-marketing
- Brand: run /founder-brand
- Operations: run /founder-ops
- Launch plan: run /founder-launch

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
