# ADR-002: Mock API as Next route handlers over an in-memory store

## Status

Superseded by [ADR-004](004-python-backend-on-vercel.md) and [ADR-008](008-online-writes-read-cache.md) · 2026-11-19. The API is FastAPI on Vercel over Supabase; fixtures survive only as Clair's recorded "sample" runs.

Originally: Proposed · 2026-11-19 · Deciders: Quilt team (A, B)

## Context

The UI must run against a backend on day one, before Clair or a database is ready, and the demo's key moment is the same data updating live on a phone and a laptop. The pitch doc names Postgres or SQLite with one table. A database server, migrations and hosted credentials cost hours we do not have.

## Decision

We will implement the API as Next.js route handlers backed by `lib/db.ts`, an in-memory store (specs, rows, proposals, change log) seeded from fixtures, running in one long-running Node process on Railway. Clair sits behind one module with two adapters, `fixture` and `live` (Claude), chosen per call kind: photo parse is live by default (the judged feature), the rest default to fixture, and every fixture result is visibly marked "sample". The store lives on `globalThis` so Next never makes a second copy; reset and live calls need a demo key. Devices sync by polling `GET /api/changes?since=` every second.

## Consequences

### Positive
- Real HTTP, real shared state: the two-device moment can be tested on the day's third hour.
- Fixtures make every flow work with zero AI calls while the live photo path is built; a failed live call offers the marked sample instead of hiding the failure.
- `db.ts` has a small interface, so SQLite can replace the map later without touching callers.

### Negative
- State is lost on restart (acceptable: we reseed with `POST /api/dev/reset` before each run).
- Cannot run on serverless hosting; one process (replicas 1) is a hard limit, and no redeploys during the demo window.
- Polling adds up to a second of lag on the second device.

### Neutral
- Server-Sent Events can replace polling later behind the same `/api/changes` data.

## Alternatives considered
- **MSW in the browser:** fast to set up but each device has its own mock state, so the phone and laptop cannot share an update. Rejected.
- **SQLite or Postgres now:** right for beta; setup and hosting time is not worth it for one day.
- **Vercel + KV store:** works, but adds a service and keys for no demo gain.

## References
`spec/ui-tech-plan.md` sections 1, 5, 9.
