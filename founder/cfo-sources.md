# CFO sources

| Input | Value | Source |
| --- | --- | --- |
| Claude Opus 5.5 price | $4 input / $20 output per million tokens | Anthropic model pricing, as listed in the Claude API reference used to build Quilt (`shared/models.md`) |
| Claude Sonnet 5.5 price | $2 / $10 per million tokens | Same |
| Claude Haiku 5.5 price | $0.10 / $0.50 per million tokens (prompts of 100K or fewer) | Same |
| Tokens per photo fill | about 12,000 in, 2,000 out | **Estimate**: system prompt and tools, the workspace snapshot, one 1568 px image and two model turns (`spec/clair-agent.md` §4, §5). Gives $0.088 on Opus, $0.0022 on Haiku |
| Tokens per chat step | about 6,000 in, 500 out | **Estimate**. $0.034 on Opus, $0.00085 on Haiku |
| Tokens per app build | about 20,000 in, 6,000 out | **Estimate**. $0.20 on Opus 5.5, $0.10 on Sonnet 5.5 ($2 / $10 per million) |
| Usage, paying user | 30 photo or file fills, 60 chat steps, 3 app builds a month | **Estimate**, no usage data yet |
| Usage, free user | 6 fills, 10 chat steps, half an app build a month | **Estimate** |
| Free users per payer | 20 (a 5% free-to-paid conversion) | **Estimate**; freemium conversion is commonly low single digits |
| Google Play subscription fee | 15% | Google Play's published service fee for subscriptions; check the current terms |
| Vercel Pro | $20 per member a month, 2 members | Vercel pricing page; check current price |
| Supabase Pro | $25 a month | Supabase pricing page; check current price |
| Apple Developer Program | $99 a year | Apple; needed only when the iPhone app ships |
| Google Play developer account | $25 one-time | Google Play Console |
| Launch spend | $300 | **Estimate**: waitlist page, flyers, a few campus ads |
| Ramp | 10 to 500 paying users over 12 months | **Estimate**; untested, and neither panel bought at $6 |

Founder time is unpaid and isn't in fixed costs.
