# CFO note

**The margin.** At $6 a month, with capture and chat on Claude Haiku 5.5 and app builds on Sonnet 5.5, each paying user-month leaves **$3.24 (54%)**. That's after AI, the 15% store fee and the AI of the 20 free users each payer carries. The margin at 500 paying users is 51%.

**The line to watch: which model does what.** With Opus 5.5 on every Clair action (what `spec/clair-agent.md` says today), each paying user-month loses $19.58 (`cfo-as-specced.md`), almost all of it from free users. Builds are the costliest action: one is about $0.20 on Opus and $0.10 on Sonnet. Free users building apps on Opus would cost more than the paid plan earns. Free users get Haiku and a build cap. Paid users get the stronger builder.

**Cash.** $374 before it pays for itself, earned back in month 5, if the ramp (10 paying users in month 1, 500 by month 12) holds. The panel's 0% buy rate doesn't support that ramp yet; a real waitlist has to.

**Three ways to improve the margin**, each from the tool:
1. Price $5 instead of $6: contribution falls from $3.24 to $2.24 and year-1 profit from $6,671 to $4,311. Price matters, but less than the model choice.
2. Web sign-ups through card payments instead of the store fee save about $0.43 each at $6.
3. Fewer free users per payer. 20 (a 5% conversion) is an assumption; at 10, contribution rises by $0.72.

**The board's money condition.** "AI cost per active user below revenue at every tier, including free" is **met only with the model split** (Haiku for capture, Sonnet for builds, a build cap on free). With Opus everywhere it fails badly.

An accountant should check the structure, payroll and tax before money moves. AI costs are estimates from published per-token prices with guessed token counts (`cfo-sources.md`); measure them on real runs.

# Unit economics: Quilt builder, recommended: $6 Plus, capture on Haiku 5.5, builds on Sonnet 5.5

Every number below comes from the input file. Nothing is looked up or guessed.

## One paying user-month

| line | per paying user-month |
| --- | ---: |
| Price | $6.00 |
| AI for one paying user (30 photo or file fills and 60 chat steps on Haiku 5.5; 3 app builds on Sonnet 5.5 at $0.10), estimate | -$0.42 |
| Store or card fee (15% subscription fee) | -$0.90 |
| AI for the 20 free users each payer carries (each: 6 fills, 10 chat steps on Haiku, half a build a month on Sonnet = $0.072), estimate | -$1.44 |
| **Contribution** (what each paying user-month leaves to pay the fixed costs) | **$3.24** (54%) |

## The margin that matters

Fixed costs: $81 a month (Vercel Pro, 2 members $40, Supabase Pro $25, Apple Developer Program ($99 a year) $8, Domain and email $8).

- **Break-even: 26 paying user-months a day.** Below that you lose money every month.
- **Profit margin at your plan** (500 a day): **51%** of every sale, after every cost.

## Year 1, month by month

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

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 51% | 26 | $6,671 |
| Price -10% | 46% | 31 | $5,255 |
| Volume -20% | 51% | 26 | $5,142 |
| Unit costs +15% | 44% | 29 | $5,694 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
