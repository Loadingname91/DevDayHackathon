# ADR-004: Python (FastAPI) backend on Vercel

## Status

Accepted · 2026-11-19 · Deciders: Quilt team · Supersedes ADR-002 · Reverses TabOS v3 ADR-6 (Go, agent in-process)

## Context

TabOS v3 puts the command service and the agent loop in one Go monolith and rejects a separate Python agent service: a second runtime, tool types defined twice. Its own reversal trigger is "a Python-native agent team". That is us: the team writes Python, Anthropic's Python SDK has a tool runner, and the build is one day. The pitch needs one public URL for the laptop and an API the Android app can call without holding the Claude key.

## Decision

The whole backend is one FastAPI app on Vercel (Python functions): the command service, the Python formula engine, sync, auth helpers and Clair's agent loop. It reads and writes Supabase Postgres with psycopg through the Supabase pooler so a change set is one real transaction. The one Anthropic key lives only in Vercel's environment. Types cross to the React app as Pydantic models → OpenAPI → `openapi-typescript`, generated, never hand-copied.

## Consequences

- One runtime for API and agent, as v3 wanted; the language is Python instead of Go.
- Request-scoped functions: nothing can wait for the user between requests. Clair's menu questions therefore end the request and resume on the answer (ADR-007).
- Cold starts and the function duration limit apply to every agent run. Check `maxDuration` and SSE streaming for Python functions on our plan at T1; warm the functions before the pitch.
- No in-memory shared state; all state is in Supabase, which also removes ADR-002's single-process limit.
- Reversal trigger: agent runs regularly exceeding the function time limit, or a need for long-lived connections; then move the same FastAPI app to a container host.

## Alternatives considered

- **Go per v3:** matches the long-term doc; a new language and toolchain for a one-day build.
- **TypeScript (Node):** shares Zod schemas with the client; not the team's choice of agent stack.
- **Supabase Edge Functions:** no extra host, but Deno and tighter run limits for agent loops.

## References

`spec/backend.md`, `spec/clair-agent.md`, TabOS v3 §9.4.
