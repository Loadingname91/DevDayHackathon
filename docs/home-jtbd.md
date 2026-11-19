---
artifact: jtbd-canvas
version: "1.0"
created: 2026-11-19
status: draft
---

# Jobs to be Done Canvas: Quilt Home

## Job Overview

**Job Title:** Check in on my life in one glance
**Date:** Nov 19, 2026
**Author:** Quilt founding team (drafted with Claude)
**Research Basis:** Founders' pitch doc, persona PU-001 (`docs/persona-sam-student.md`, Proto confidence), launcher research (`https://claude.ai/artifact/WtBMJUDese1MWWMTjFu8Dd`). No interviews yet; every insight below is a hypothesis to test in Thursday's survey.

---

## Job Performer

**Who:** Sam, a U of U undergrad who loses money and stress to what they forget, opening Quilt between other things.

**Key Characteristics:**
- Opens Home 10+ times a day in 5–30 second bursts (assumed)
- Has 5 to 30 apps they built themselves; no two students' Homes contain the same apps
- Wants to be told what matters, not to go looking

**Not Defined By:**
- Which apps they have (Home must work for any mix)
- How organised they are

---

## The Circumstance

**When does this job arise?** Opening Quilt with no specific task: waking up, between classes, after a purchase, before the gym, Sunday night.

**Where does this happen?** One-handed on a phone, often walking or in a line; on the laptop when planning.

**Frequency:** Many times a day.

**Urgency:** Low per visit, but a miss compounds (a renewal, a late fee, a deadline).

---

## Job Statement

> **"When** I open Quilt with a spare few seconds, **I want to** see whatever needs me, what's coming next and how I'm doing, without opening anything, **so I can** stop paying for what I forget and get on with my day."

---

## Functional Job

**What is the practical task to accomplish?** Know in under 5 seconds whether anything needs action, then act in one tap.

**Definition of "Done":**
- Anything waiting for Sam's OK is handled or knowingly left
- The next 1–3 time-bound things are known
- The one number Sam cares about right now is seen

**Key Steps in the Job:**
1. Scan: anything for me?
2. Act on it (confirm, dismiss, or open)
3. Glance at what's next
4. Jump into an app, or close Quilt

**Functional Pains:**
- Every app is different, so Home can't show "the budget widget" for everyone
- Too many apps makes Home a wall of tiles
- Things that need action hide inside apps until it's too late

---

## Emotional Job

**How do they want to feel?**

| Desired Feeling | Why It Matters |
|-----------------|----------------|
| Calm and caught up | The forgetting tax is mostly anxiety about what's slipping |
| In control | Sam built these apps; Home should feel like theirs |
| Quietly proud | Small wins (a cancelled subscription, a lift PR) keep the habit alive |

**How do they want to avoid feeling?**

| Feeling to Avoid | Current Trigger |
|------------------|-----------------|
| Judged | Red overspend banners, streak-loss guilt |
| Overwhelmed | Badges and counts on every app |
| Surprised | Renewals and due dates that appear the day of |

**Emotional Pains:**
- Notification-style apps make "nothing to do" feel like failure
- Dashboards full of numbers feel like homework

---

## Social Job

**How do they want to be perceived?**

| Desired Perception | By Whom |
|--------------------|---------|
| Has it together | Roommates, parents |
| Good with money | Friends who split costs |

**What perception do they want to avoid?**

| Perception to Avoid | By Whom |
|---------------------|---------|
| The one who forgot to pay | Roommates |
| Wasteful | Parents |

**Social Context:**
- Home is sometimes shown to a friend or on stage (the DevDay demo), so it must look good at a glance
- Shared bills are out of MVP scope

---

## Competing Solutions

| Solution Type | Solution | Strengths | Weaknesses |
|---------------|----------|-----------|------------|
| Direct Competitor | Notion home / dashboards | Fully custom | Sam has to build and maintain it; static |
| Indirect Alternative | iOS widgets + Smart Stack | Glanceable, context-aware | One app per widget; nothing joins up |
| Indirect Alternative | Notification centre | Pushes what's urgent | Noisy, no priorities, easy to swipe away |
| Non-consumption | Not checking | Zero effort | That's the forgetting tax |
| DIY/Manual | Notes app list, calendar app | Familiar | Manual, goes stale |

**Why Do They Switch?** A missed renewal or late fee; a dashboard they stopped updating.

**Why Do They Stay?** Widgets and notifications are already there; setting up something new feels like work.

---

## Hiring Criteria

**Must-Have (Table Stakes):**
- Works for any set of user-built apps
- Shows what needs action first, in thumb reach
- Fast: useful in under 5 seconds, no loading spinner

**Differentiators (Decision Drivers):**
- Joins things up across apps ("Groceries spend is pushing Eating out over")
- Changes with the time of day without Sam arranging it
- Quiet when nothing is happening: "all caught up" is a good state

**Nice-to-Have:**
- Small celebrations of real wins
- Laptop version for Sunday planning

---

## Insights and Implications

**Key Insight 1: Home can't be made of app widgets, because every user's apps differ.** It has to be made of signals every app emits because every app is a typed spec: things waiting for OK, dated items, a headline number, changes, and cross-app patterns.
- Product Implication: every app spec declares a **face** (headline value + short label) and exposes dated rows and pending items. Home is composed from those signals, ranked by Clair.

**Key Insight 2: The order of the job is act → next → glance → browse.**
- Product Implication: Home sections in that order: Waiting for you, Next up, Right now, Clair noticed, Your quilt. Empty sections disappear entirely.

**Key Insight 3: "Nothing to do" must feel like success, not emptiness.**
- Product Implication: an explicit caught-up state with the spool content, and no counts or badges on patches except "just changed".

**Key Insight 4: The headline sentence is the voice.** One sentence written from live data does more than five cards.
- Product Implication: a composed status line under the greeting ("Pull day in 15 minutes. $376 left this month."), plain, specific, never judging.

---

## Home modules (derived from this canvas)

| Module | Job step | Source signal (any app) | MoSCoW | Shows when |
|---|---|---|---|---|
| Greeting + status sentence | Scan | Top 1–2 signals, composed by Clair | Must | Always |
| Waiting for you | Act | Basted items, Clair proposals | Must | Only when something is waiting |
| Next up (thread) | Next | Dated rows from every app, next 24 h | Must | When anything is dated in 24 h |
| Right now (≤3 patches) | Glance | App faces ranked by time of day | Must | Always, if Sam has 2+ apps |
| Clair noticed (1 insight) | Glance | Cross-app pattern | Should | At most one, dismissible |
| Your quilt | Browse | All apps, sized by use | Must | Always |
| Caught up | Scan | No waiting items | Must | Replaces Waiting when empty |
| Day-one Home | Onboard | No apps yet | Must | First run |
| Streaks and badges | — | — | Won't | Never (guilt, noise) |

---

## Supporting Quotes

None yet. Assumed quote (to validate): "I just want to open it and know if I'm forgetting something."

## Questions for Further Research

1. How many times a day would students open a Home like this, and for how long? (survey + beta analytics)
2. Does a composed status sentence beat a set of number cards for "how am I doing"? (5-person preference test)
3. Which signals do students most want surfaced: money, deadlines or health? (survey ranking)
