# ADR-008: Online writes with a local read cache

## Status

Accepted · 2026-11-19 · Deciders: Quilt team · Defers TabOS v3 §5 (offline-first sync) and ADR-4 (WASM formulas)

## Context

v3 is local-first: a durable op queue on every device, device-suffixed positions, conflict events and a formula engine compiled to WASM so totals update offline. That is weeks of work. For DevDay the need is narrower: screens must open instantly, the laptop must update within a couple of seconds of a confirm on the phone, and every number must be right.

## Decision

Writes go to the server and only succeed online. Each device keeps a read cache in IndexedDB (blocks, faces, `last_server_seq`) per workspace, paints from it at once, then catches up with `GET /sync?since=seq`. Supabase Realtime on the `events` table tells devices when to catch up. Simple gestures (tick, swipe, reorder) update the screen at once and roll back if the server rejects them; Clair confirms wait for the server. All formulas and faces are computed in Python on the server and returned with every change.

## Consequences

- Fast opens and live two-device updates with little code; nothing is lost because nothing is queued.
- No offline editing: without a connection the app is read-only and says so.
- Totals change after the server answers (a few hundred milliseconds), not instantly on device.
- The cache is per workspace and cleared on sign-out and on a schema version change, so a shared device never shows another person's data.
- Reversal trigger: users editing offline (class, subway) or formula lag noticed in testing; then add v3's op queue and a client evaluator.

## Alternatives considered

- **v3 offline-first now:** right long term, far too large for the event.
- **No cache, always fetch:** simplest, but every open waits on the network and a cold Vercel function.

## References

`spec/backend.md` §6–7, TabOS v3 §5, §6, §11.
