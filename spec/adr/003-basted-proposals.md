# ADR-003: Clair writes through basted proposals; the UI animates optimistically

## Status

Accepted · 2026-11-19 · Deciders: Quilt team (A, B)

Update (Nov 19): a proposal is stored as a change set with status `basted` (the same `change_sets` and `events` tables every user gesture uses, [spec/backend.md](../backend.md)); Clair creates it only through its `propose_changes` tool ([ADR-007](007-clair-agent-loop.md)).

## Context

Product principle 3: Clair proposes, you approve; nothing big changes without a visible preview and undo. The design makes this visible as stitch states (basted = waiting for OK, running stitch = saved) and one focal motion, the thread pull on confirm. The pull must start on tap, not after a server round trip, and Home must show exact before/after numbers ("$412 → $376") before anything is saved.

## Decision

We will route every Clair write through a `Proposal` holding row operations. The server, not Clair, expands stitches, computes target apps and face deltas by dry run, and stores inverses on apply so undo is exact. User edits inside an app write directly with an undo toast. On confirm the client animates immediately using the precomputed deltas, sends confirm in parallel, and reverses the animation if the request fails.

## Consequences

### Positive
- One card style and one confirm flow serve receipts, captures, check-ins, insights and shares.
- Thread targets and numbers are always true to the data, whatever Clair claimed.
- Undo is a single endpoint and a single reverse animation.

### Negative
- A rare failed confirm shows threads then retracts them; acceptable and honest.
- Proposals must be re-expanded after every Review items edit.

### Neutral
- Other devices see results through the change log as "just changed" tags, never the pull.

## Alternatives considered
- **Write first, then offer undo:** faster to build, breaks "nothing saves before OK". Rejected.
- **Wait for the server, then animate:** simpler failure handling, but adds a visible pause before the signature motion.

## References
`spec/ui-tech-plan.md` section 4; `.impeccable/surfaces/app.md` (stitch states, signature motion).
