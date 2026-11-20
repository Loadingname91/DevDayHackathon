# ADR-012: The API is one always-on Python server on Railway; the website stays on Vercel

## Status

Accepted · 2026-11-19 (late night) · Decider: the owner · Supersedes the hosting part of ADR-004 (FastAPI, Python and Supabase stand) and the "Vercel only, not Railway" line in `CLAUDE.md`

## Context

ADR-004 put the FastAPI app in Vercel Python functions. That brought three things to prove before any feature worked: whether a function streams SSE without buffering, what `maxDuration` the plan allows against Clair's 45 s run budget, and cold starts on stage. It also meant no process to run a schedule in, so the engine's scheduled rule needed Vercel Cron. The owner does not want Python functions; he wants an ordinary Python server.

## Decision

- **API.** One FastAPI app run by `uvicorn` as a single always-on service on Railway (`uvicorn api.index:app --host 0.0.0.0 --port $PORT`, one replica, health check on `/health`). Paths keep the `/api` prefix, so the endpoint table in `spec/backend.md` §10 does not change.
- **Website.** The React + Vite site stays on Vercel as static files. It calls the API cross-origin at `VITE_API_BASE`. The API allows the site's origin with CORS; auth is a bearer header, so there are no cookies to share.
- **Google sign-in.** Google redirects to the API on Railway (`/api/connect/google/callback`); the API then redirects the browser to the site at `WEB_ORIGIN`.
- **Schedules.** A one-minute loop inside the server runs the same code as `POST /cron/sweep`. No Vercel Cron. This is why there is exactly one replica.
- **Unchanged.** Supabase Postgres through the pooler with psycopg, uploads straight to Storage, the 45 s run budget (now Clair's own limit, not the host's), attempt limits kept in the database, the polling fallback for Clair's events.

The backend owner sets up the Railway service and owns its env vars. The frontend owner owns the Vercel project.

## Consequences

- SSE is an ordinary streaming response and there is no function time limit. The spike shrinks to one check: events reach the Vercel-hosted site unbuffered.
- No cold starts, but a deploy restarts the process and drops open streams. No API deploys inside the freeze or during the pitch.
- Two URLs instead of one: CORS has to be right, including for Vercel preview URLs if they are used, and the site needs `VITE_API_BASE` at build time.
- The frontend and the backend deploy independently, which fits the ownership split (ADR-011).
- One replica is a hard limit for DevDay because of the in-process loop.
- Sections written before this ADR that say "Vercel function", "`maxDuration`" or "cold start" have been reworded; old ADRs keep their wording as history.

## Alternatives considered

- **Stay on Vercel Python functions (ADR-004):** one URL, but the streaming and duration spikes sit in front of everything.
- **FastAPI serves the built site too:** one URL and no CORS, but every frontend change would need an API deploy, and the two owners would share one pipeline.
- **Render or Fly.io:** equivalent; Railway was chosen because the account is already set up.

## References

`spec/backend.md` §1, §8a, §10, §13; `spec/clair-agent.md` §2, §9, §15; `spec/split.md`; ADR-004, ADR-011.
