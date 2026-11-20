# Unit economics: Quilt builder as specced: $6 Plus, Opus 5.5 for every Clair action

Every number below comes from the input file. Nothing is looked up or guessed.

## One paying user-month

| line | per paying user-month |
| --- | ---: |
| Price | $6.00 |
| AI for one paying user (30 fills, 60 chat steps, 3 builds, all on Opus 5.5), estimate | -$5.28 |
| Store or card fee (15% subscription fee) | -$0.90 |
| AI for the 20 free users each payer carries (each $0.97 on Opus), estimate | -$19.40 |
| **Contribution** (what each paying user-month leaves to pay the fixed costs) | **-$19.58** (-326%) |

## The margin that matters

Fixed costs: $81 a month (Vercel Pro, 2 members $40, Supabase Pro $25, Apple Developer Program ($99 a year) $8, Domain and email $8).

- **Break-even: never (each unit loses money) paying user-months a day.** Below that you lose money every month.
- **Profit margin at your plan** (500 a day): **-329%** of every sale, after every cost.

## Year 1, month by month

| month | paying user-months a day | revenue | profit | cumulative (after $325 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 10 | $60 | -$277 | -$602 |
| 2 | 25 | $150 | -$571 | -$1,173 |
| 3 | 45 | $270 | -$962 | -$2,135 |
| 4 | 70 | $420 | -$1,452 | -$3,587 |
| 5 | 100 | $600 | -$2,039 | -$5,626 |
| 6 | 140 | $840 | -$2,822 | -$8,449 |
| 7 | 180 | $1,080 | -$3,606 | -$12,054 |
| 8 | 230 | $1,380 | -$4,585 | -$16,639 |
| 9 | 290 | $1,740 | -$5,759 | -$22,398 |
| 10 | 350 | $2,100 | -$6,934 | -$29,333 |
| 11 | 420 | $2,520 | -$8,305 | -$37,638 |
| 12 | 500 | $3,000 | -$9,871 | -$47,509 |

- **Year 1 operating profit: -$47,184** on $14,160 of revenue.
- After the $325 startup spend: -$47,509.
- Startup money earned back: not within year 1.
- Cash you need before it pays for itself: **$47,509**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | -329% | never | -$47,184 |
| Price -10% | -377% | never | -$48,600 |
| Volume -20% | -330% | never | -$37,942 |
| Unit costs +15% | -393% | never | -$56,239 |

## Red flags

- Each unit loses money before rent and salaries: the price is below the variable cost.
- Year 1 loses money on operations (-$47,184).
- The startup spend is not earned back within year 1.
