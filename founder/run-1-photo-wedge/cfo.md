# CFO note

**The margin.** At $3 a paying student-month, with capture and chat on Claude Haiku 5.5, each one leaves **$1.79 (60%)** after AI, the 15% store fee and the AI of 20 free users per payer. The profit margin at 500 paying students is 54%.

**The line to watch: which model runs capture.** The spec has every Clair action on Opus 5.5. With that model and the pitched $6, each paying student-month loses $17.18, mostly because 20 free users on Opus cost about $17.40 (`cfo-as-pitched.md`, red flags: below variable cost, year 1 −$41,520). The model choice moves the result far more than the price does. Only a cheap model for capture keeps a generous free tier affordable.

**Cash.** $426 before it pays for itself, earned back in month 7, if the ramp (10 paying students in month 1 to 500 in month 12) holds. The panel's 0% buy rate at $6 doesn't support that ramp yet; it is the assumption a real waitlist has to test.

**Three ways to improve the margin**, each from the tool:
1. Price −10% ($2.70) costs 5 points of margin (54% → 49%) and $708 of year-1 profit: price matters less than the model.
2. Selling through the website instead of Google Play swaps the 15% fee ($0.45) for card fees (2.9% + $0.30, about $0.39). It's a small gain, and only for web sign-ups.
3. Unit costs +15% still leave 48%. The free-user AI line is the one to watch: 20 free users per payer is an assumption (a 5% conversion rate).

**The board's money conditions.** "AI cost per active user leaves a margin at $6": **met only with a cheap capture model**; at Opus on everything it fails badly. "Willingness to pay measured": **not met**; the panel says $1 to $4, and real students haven't been asked.

An accountant should check the structure, payroll and tax before money moves. The AI costs are estimates from published per-token prices with guessed token counts (`cfo-sources.md`); measure them on real runs before trusting them.

# Unit economics: Quilt (recommended model: student price, cheap model for capture)

Every number below comes from the input file. Nothing is looked up or guessed.

## One paying student-month

| line | per paying student-month |
| --- | ---: |
| Price | $3.00 |
| AI for one paying student (30 photo fills, 60 chat steps on Haiku 5.5; 1 app build on Opus 5.5), estimate | -$0.32 |
| Store or card fee (15% Google Play subscription fee) | -$0.45 |
| AI for the free users each payer carries (20 free users x $0.022, Haiku), estimate | -$0.44 |
| **Contribution** (what each paying student-month leaves to pay the fixed costs) | **$1.79** (60%) |

## The margin that matters

Fixed costs: $81 a month (Vercel Pro, 2 members $40, Supabase Pro $25, Apple Developer Program ($99 a year) $8, Domain and email $8).

- **Break-even: 46 paying student-months a day.** Below that you lose money every month.
- **Profit margin at your plan** (500 a day): **54%** of every sale, after every cost.

## Year 1, month by month

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

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 54% | 46 | $3,249 |
| Price -10% | 49% | 55 | $2,541 |
| Volume -20% | 53% | 46 | $2,405 |
| Unit costs +15% | 48% | 51 | $2,821 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
