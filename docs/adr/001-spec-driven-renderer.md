# ADR-001: Spec-driven renderer over generated UI code

## Status

Accepted · 2026-11-19 · Deciders: Quilt team (A, B)

Update (Nov 19): the AppSpec is now stored on the app's page block in Supabase ([ADR-006](006-supabase-blocks-table.md)), and the spec schema is a Pydantic model whose TypeScript types are generated ([ADR-004](004-python-backend-on-vercel.md)). The renderer contract is unchanged.

## Context

Clair has to turn a sentence into a working app in seconds, live on stage, and the app must keep working the next day. Code generators (Lovable, Bolt, Emergent) can build anything but output varies run to run, needs a build step and breaks in ways a user cannot fix. Quilt's pitch promise is "Clair builds from tested blocks, not generated code". Home also needs every app to emit the same signals (face, pending, dated rows, changes), which only works if every app has the same typed shape.

## Decision

We will have Clair write only an `AppSpec` (JSON, Zod schema in `lib/spec.ts`) drawn from a closed union of 9 blocks over typed collections. One `AppView` renderer draws every app; blocks are pure views that read rows and evaluate values, and cannot fetch, run code or style themselves. Invalid specs get one retry with the Zod errors, then a friendly error.

## Consequences

### Positive
- Builds are fast and deterministic to render; a spec that parses always draws.
- Home, search filters, stitches and the calendar of everything work for any app, because fields and dates are typed.
- Specs export cleanly (the marketplace format later) and can be diffed for History and undo.

### Negative
- Needs that don't fit 9 blocks can't be built; the demo must pick apps that fit.
- Every new capability is a schema change plus a component, not a prompt tweak.

### Neutral
- The same renderer serves the Build preview, so preview and result never differ.

### Model choice
Prompting a general model (Claude Opus 5.5) with structured output; building or fine-tuning was ruled out by time. Coupled to it: the system prompt and the Zod schema. Reversal cost is low because the schema, not the model, is the contract; any model that fills the schema works. Reopen if more than 1 in 10 build prompts in the test set need a retry.

## Alternatives considered
- **Generated React per app:** unlimited range, but slow, fragile and unsafe to run live. Rejected.
- **Spec plus escape-hatch custom code blocks:** reintroduces the fragility for a minority of apps. Deferred until the block library shows a real ceiling.

## References
`docs/ui-tech-plan.md` sections 2–3; pitch doc "Technical quirks and risks".
