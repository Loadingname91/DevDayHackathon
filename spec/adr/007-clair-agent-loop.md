# ADR-007: One Clair agent loop on the Anthropic SDK tool runner

## Status

Accepted · 2026-11-19 · Deciders: Quilt team · Replaces the "structured call per request" design in `ui-tech-plan.md` §4; cuts down TabOS v3 §9.3

## Context

Clair must handle any input (words, voice, a live photo of a fridge or a schedule, a screenshot, a PDF), work out what it is, read Sam's apps, ask when unsure and propose changes across apps. A single structured call can only see what we pack into it and cannot ask a question. Anthropic's agent guidance: start simple, give actions their own tools when the harness must gate, show or audit them (Claude Code shows question-asking as a tool that blocks the loop), keep a stable cached prefix and an append-only history.

## Decision

Every input goes through one loop built on the Anthropic Python SDK tool runner (`@beta_tool`, `client.beta.messages.tool_runner`), model `claude-opus-5-5`, with our own typed tools: perceive (`report_understanding`), read (`list_apps`, `get_app`, `query_records`, `search_records`, `get_usuals`, `get_faces`, `get_notes`), ask (`ask_user`), remember (`save_note`) and propose (`propose_changes`, `propose_app`). Clair never writes app data: `propose_changes` only creates a basted change set (ADR-003). Because a Vercel request cannot wait for the user, `ask_user` ends the request and the answer resumes the saved, unchanged transcript. A context snapshot (apps, lists, open items, usuals, notes) is packed into each turn so most inputs need one or two model turns; there is no separate fast path for receipts.

## Consequences

- One code path to build, test and evaluate; any photo works, not only receipts.
- A receipt costs about as much as the old one-shot call because the snapshot is pre-packed; a fridge needs two or three turns.
- Pause and resume rely on restarting the runner from saved messages; confirm at the T1 spike, otherwise use a short manual loop with the same tools.
- Stage latency depends on the model; "Use sample" and recorded fixture runs are the fallback.

## Alternatives considered

- **Claude Managed Agents:** Anthropic runs the loop and keeps sessions, and a question waits natively; beta, a container per session, user data held in sessions, less predictable stage latency.
- **Claude Agent SDK:** the Claude Code harness, built for coding agents with file and shell tools; needs the CLI process, a poor fit for Vercel functions.
- **Pydantic AI, LangGraph:** another layer over what the SDK already does, with no gain for this tool set.
- **Structured call for receipts plus an agent for the rest:** two paths to build and test.

## References

`spec/clair-agent.md`, TabOS v3 §9.3–9.4.
