# Which first user should Quilt pitch? Segment prioritization

Nov 18, 2026 · decision: which first-user segment anchors the DevDay pitch (Nov 20) and the design-system persona. Proof (survey, waitlist) must be gathered by Thu Nov 19 from people we can reach.

## 1. Applicability filter

ICE and Weighted Scoring ran. MoSCoW ran because the pitch has room for one lead user plus one vision line, which is a scope decision. RICE was excluded: we have no reach, impact or effort numbers per segment, and guessing them would look more precise than it is (an estimation scaffold is in section 8). Kano was excluded: there is no customer research yet; the planned survey can unlock it if it asks paired "how would you feel with / without" questions.

## 2. Inputs

- Pitch doc: students first because they are reachable; personas for parent, caregiver, athlete, freelancer; demo = receipt photo → groceries, budget, calendar; "no bank login" as a privacy selling point; MVP cuts sharing, bank feeds, native apps.
- `PRODUCT.md`, `docs/persona-sam-student.md` (Proto confidence).
- **Assumed (no evidence yet):** every pain, willingness-to-pay and reach score below. Segments S2, S3, S4 and S6 are not in the pitch doc's student framing; they are new candidates.

| ID | Segment | One line |
| --- | --- | --- |
| S1 | Budget-conscious student (current "Sam") | Tight budget, scattered subscriptions, gym and classes in separate apps |
| S2 | The "forgetting tax" student | Overloaded, pays for what they forget: unused renewals, late fees, spoiled groceries, missed deadlines (includes, but doesn't require, ADHD) |
| S3 | Student gig worker / side hustler | DoorDash, tutoring, Etsy; receipts and mileage are tax deductions, income spread across apps |
| S4 | Off-campus roommate house | Shared bills, groceries and chores across 3 to 5 people |
| S5 | Student athlete / gym regular | Training, meals and class schedule in different apps |
| S6 | International student | New currency and banking, tight stipend, wary of linking accounts |

## 3. Scoring

**ICE** (1 to 10; Impact = effect on winning the pitch, Confidence = evidence we have, Ease = proof and demo ready by Friday)

| Segment | Impact | Confidence | Ease | ICE | Notes |
| --- | --- | --- | --- | --- | --- |
| S1 | 6 | 5 | 9 | 270 | Doc-backed; demo already fits; "budget app for students" is a crowded story |
| S2 | 8 | 4 | 8 | 256 | Sharper pain and emotion; same demo and survey pool; untested |
| S3 | 8 | 3 | 5 | 120 | Real money (tax deductions) but a smaller group to find in 2 days |
| S5 | 4 | 4 | 7 | 112 | Hevy and Strong win on depth |
| S4 | 6 | 4 | 4 | 96 | Needs sharing, which is cut from the MVP |
| S6 | 6 | 3 | 5 | 90 | Real pain, niche reach, little evidence |

**Weighted Scoring** (1 to 5). **These weights are my proposal, not yours; adjust them to what you and the judges value.**

| Segment | Pain (25%) | Demo fit (20%) | Proof by Thu (20%) | Willing to pay (15%) | MVP fit (10%) | Beats incumbents (10%) | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S2 | 5 | 4 | 4 | 3 | 5 | 4 | **4.20** |
| S1 | 3 | 5 | 5 | 2 | 5 | 3 | 3.85 |
| S3 | 4 | 5 | 3 | 5 | 3 | 2 | 3.85 |
| S6 | 4 | 4 | 3 | 2 | 4 | 3 | 3.40 |
| S4 | 4 | 4 | 4 | 2 | 1 | 2 | 3.20 |
| S5 | 3 | 3 | 4 | 3 | 4 | 1 | 3.10 |

Incumbents assumed: S3 vs Stride, QuickBooks Self-Employed, Everlance; S4 vs Splitwise; S5 vs Hevy, Strong; S2 vs planners (Tiimo, Todoist) that don't touch money.

**MoSCoW** (pitch scope)

| Segment | Bucket | Rationale | Risk if dropped |
| --- | --- | --- | --- |
| S1 + S2 merged | Must (lead user) | Same people, same survey pool, same demo; S2 is the sharper way to describe S1's pain | No clear first user |
| S3 | Should (Q&A: "who pays most") | Strongest willingness to pay; receipts are literally their tax records | Weaker answer to "how do you make money" |
| S4 | Could (roadmap: quilting circle) | Good story, needs sharing | None for DevDay |
| S5, S6 | Won't (this pitch) | Depth incumbents or thin reach | None |

## 4. Rankings

- ICE: S1 > S2 >> S3 > S5 > S4 > S6. Clear gap after S2.
- Weighted: S2 > S1 = S3 > S6 > S4 > S5. Clear gap after S3.

## 5. Cross-framework comparison

| Segment | ICE rank | Weighted rank | MoSCoW | Agreement |
| --- | --- | --- | --- | --- |
| S1 | 1 | 2 (tie) | Must | Strong |
| S2 | 2 | 1 | Must | Strong |
| S3 | 3 | 2 (tie) | Should | **Divergent** |
| S6 | 6 | 4 | Won't | Moderate |
| S4 | 5 | 5 | Could | Strong |
| S5 | 4 | 6 | Won't | Moderate |

**Why S3 diverges:** ICE punishes it for low confidence and low ease (hard to reach enough gig-working students by Thursday). Weighted Scoring rewards willingness to pay and demo fit. The finding: the gig worker is the best *business*, the student is the best *pitch this week*.

**Why S1 and S2 swap:** ICE rewards S1's evidence (it's in the doc); Weighted rewards S2's pain intensity. Both point to the same people, so the real question is the framing, not the segment.

## 6. Executive summary

Keep students as the first user, but reframe Sam's pain from "budget-conscious" to **the forgetting tax**: the money and stress students lose to what they forget (unused subscriptions, late fees, groceries that go off, deadlines that sneak up). The demo, survey pool and MVP are unchanged, and the hook gets sharper. Hold the **student gig worker** as the answer to "who pays most" and as the first paid expansion; don't lead with them, because we can't prove demand in two days. The recommendation flips only if the survey shows students rarely lose money to forgetting (then stay with S1's framing) or that many respondents do gig work (then S3 becomes a strong second persona).

## 7. Sensitivity

- **Judges weigh the business model more** (willingness to pay 30%; pain 20%, demo 15%, proof 15%, MVP 10%, incumbents 10%): S2 4.00, S3 4.00, S1 3.50. The gig worker ties for first, so prepare the S3 Q&A answer.
- **Survey shows forgetting isn't costly** (S2 pain 5 → 3): S2 falls to 3.70, below S1 at 3.85. Keep the original framing.
- **Survey shows gig work is common** (S3 proof-by-Thursday 3 → 4): S3 rises to 4.05, second only to S2. Write a second persona (PU-002).

## 8. Next steps

1. Add three questions to Thursday's survey: "In the last 3 months, did you pay for a subscription you forgot about?", "Did you pay a late fee or lose money because you forgot something?", "Do you earn money from gig or freelance work?" Add one Kano pair for photo receipt capture.
2. If the forgetting answers are strong, rewrite the persona's core reality and pitch hook (step 2 of the pitch) around the forgetting tax. Don't use "ADHD" in the pitch unless the survey supports it, and never make health claims.
3. If gig work is common, write PU-002 (student gig worker) with `foundation-persona`.
4. RICE scaffold for later: Reach = survey share × U of U undergrads (about 26,000 *(assumed; check)*), Impact from the survey's dollar answers, Effort in founder-days, at 2 people × about 10 h/day this week.

## 9. Limitations and biases

These frameworks rank segments on judgment scores from founders, not on user data; every score is an assumption until Thursday. Weighted Scoring favors whatever the weights favor, and pain and demo fit (45% combined) bias toward segments our existing demo already serves. ICE's Ease criterion favors whoever we can reach this week, not who will pay over time, which is exactly why S3 diverges.
