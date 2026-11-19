# Product

<!-- impeccable:product-schema 1 -->

> Written from `docs/pitch.md` (Nov 15, 2026); confirmed by the owner Nov 18, 2026.

## Platform

adaptive (one React app: Android via Capacitor first, the same build as a website for laptops)

## Stack

React + Vite (TypeScript) wrapped with Capacitor for Android and served as a website; FastAPI (Python) on Vercel; Supabase (Postgres blocks table, anonymous auth, Realtime, Storage); Clair runs on the Anthropic Python SDK tool runner with Claude (vision, tools). See spec/backend.md and spec/clair-agent.md.

## Users

First user: the "forgetting tax" University of Utah student, who loses money and stress to what they forget (unused renewals, late fees, spoiled groceries, missed deadlines) while juggling subscriptions, groceries, gym, classes and deadlines across separate paid apps that don't share data, and who won't hand a bank login to a finance app. Later personas: busy parents/households, caregivers, athletes/hobbyists, freelancers.

## Product Purpose

Quilt is one app for your money, workouts and to-dos that builds the tabs you describe and stitches them together. Snap a grocery receipt and your grocery list, budget and calendar all update. Success (north star): tabs with a new entry in the last 7 days per user.

## Positioning

Not "AI builds an app" (Notion, Airtable, Taskade do that). Quilt's tabs are joined up and fill themselves: one capture (photo, chat) updates several tabs at once. Clair never writes code; it writes a small checked spec drawn from a fixed block library, so tabs don't break.

## Operating Context

Used on a phone in the moment of logging (checkout line, gym floor, between classes) and on a laptop, the same tab live on both. DevDay demo (Nov 20, 2026): a 90-second pitch where a receipt photo fills groceries, drops the budget and lands on the calendar, live on phone and laptop.

## Capabilities and Constraints

- Nine blocks: page, text, metric, progress, collection, list/table/calendar view, form, chart.
- MVP tabs: budget & subscriptions, gym logger, to-dos, calendar of everything, grocery from a photo.
- Clair: builds a tab from a sentence; fills a tab from a photo with a one-tap confirm before saving; asks before deletes or big changes; every change can be undone.
- Out of MVP: marketplace, sharing, teams, bank feeds, iOS build, offline writes, encryption. Voice is in, using the phone's own speech in and out.

## Brand Commitments

- Name: Quilt. Assistant: Clair (the quilter).
- Terminology: the unit Clair builds is an "app"; sections inside an app are "tabs" (decided Nov 19, 2026).
- Metaphor: patch = app; stitching = data flowing between tabs; Clair = the quilter; patterns = templates; quilting circle = shared tabs.
- Feel: warm, personal, hand-made, grows over time; "not a cold system".
- No red. Urgency is never signalled with red.
- Copy: say what it does; avoid "platform", "AI-powered", "better UX".
- Taglines on the table: "Your life, stitched together." · "Every app you need, stitched into one." · "Say what you need. Clair stitches it in."
- Incumbent mock: Claude design canvas "Patchwork" (owner likes it). Stitch "TabOS" dark prototype is superseded.
- Visual direction chosen Nov 18, 2026: Quilter's Workbench (see `.impeccable/surfaces/app.md`). UI copy stays plain; quilt words only "patch", "stitch it in", "pieced by clair". Clair's face is the spool buddy mascot; copy never uses a pronoun for Clair.

## Evidence on Hand

- Pitch doc (above), the design canvas (`design/canvas/`, live at https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P), persona `docs/research/persona-sam-student.md`.
- No survey answers or waitlist numbers yet; pitch placeholders [N], [X], [Y], [D] must not be invented.

## Product Principles

1. Capture beats building: logging must take no effort.
2. Connection is the product: show data moving between tabs.
3. Clair proposes, you approve: nothing big changes without a visible preview and undo.
4. Templates before blank canvas.
5. Honest about privacy and money: no bank login, no surprise bills, never claim end-to-end encryption.

## Accessibility & Inclusion

Smallest tap target 44 px; primary actions in the bottom third; text at 4.5:1; states distinguishable without colour alone (no red/green reliance).
