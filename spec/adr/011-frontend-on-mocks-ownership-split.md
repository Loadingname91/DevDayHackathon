# ADR-011: Frontend built on in-app mock data, backend behind the contract

## Status

Accepted · 2026-11-19 (late night) · Deciders: Quilt team · Adds to ADR-004 and ADR-008; does not bring back ADR-002

## Context

No application code exists and the base must be built tonight by two people. The build order in `spec/backend.md` §13 pairs each client step with an API step, so the client would wait on the API at every step. The owner wants to build the frontend without waiting, and each person works with their own coding agent, which needs to know which half is its job.

## Decision

1. **Owners.** Hitesh owns the frontend (`web/`, column B of §13). His teammate owns the backend (`api/`, Supabase, Google Cloud, Clair; column A). Each side writes code only in its own folder.
2. **The contract is the seam:** `spec/backend.md` §10, `spec/clair-agent.md` §2, `spec/ui-tech-plan.md` §3 and §4, and the seed in `spec/backend.md` §2.2 and §2.3. A change to it is made in the spec and logged in `spec/split.md` in the same commit.
3. **The frontend runs on a mock transport first:** fixtures inside the web app that answer the contract's paths, switched to the live API one route at a time (`VITE_API`, `VITE_MOCK_ROUTES`). Fixtures are finished responses taken from the seed; the mock computes nothing.
4. **Mock data is never the demo.** A screen on mock data shows a "mock data" mark. The base cut line, the go/no-go, `check.py` and the two-device check are judged on the live API only.
5. **The backend publishes its models first** (`api/openapi.json`) so the client's hand-written types can be replaced by generated ones early.

Details: `spec/split.md`.

## Consequences

- Neither side blocks the other tonight; the client's screens, motion and touch work can be finished before any route exists.
- Two copies of the demo values exist until every route is live (the seed and the fixtures). The seed wins; fixtures are checked against it at each switch.
- Integration risk moves later. The route-by-route switch and the rule that a mock-only screen is not done are what contain it.
- Mock mode is one device with no Realtime, so two-device sync still needs the live API, as ADR-002's rejection of in-browser mocks noted. That is accepted here because the mock is a build aid, not the demo's backend.
- Hand-written client types can drift from the Pydantic models until the generated file lands.

## Alternatives considered

- **Build in step, as §13 was written:** no drift, but the client idles whenever the API step is slower.
- **A shared mock server (the superseded ADR-002):** tests two devices, but it is a second backend to write tonight.
- **Backend first, client after:** leaves the motion and touch work, the riskiest client work, for the day.

## References

`spec/split.md`, `spec/backend.md` §10 and §13, `spec/ui-tech-plan.md` §3 to §6, ADR-002, ADR-004, ADR-008, ADR-010.
