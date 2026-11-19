# ADR-006: Supabase Postgres with the v3 blocks table, layout kept whole

## Status

Accepted · 2026-11-19 · Deciders: Quilt team · Adapts TabOS v3 ADR-3 and §3.1; defers v3 ADR-1 (encryption)

## Context

Apps are made by Clair at run time, so there is no fixed table per app. v3 stores everything as blocks in one table: every record is its own block under its collection, which gives per-record order, versioning, undo and sync. The earlier plan (ADR-002) kept each app as one JSON spec plus a rows map in memory. We also need accounts, live updates between devices and file storage, with no time to run those ourselves.

## Decision

Supabase: Postgres, anonymous auth that can later link Google or email, Realtime and Storage. One `blocks` table in v3's shape (`workspace_id`, `parent_id`, `position`, `block_type`, `collection_id`, `properties jsonb`, `version`, `deleted_at`). App (page), collection and record blocks are real blocks. For DevDay the app's layout stays one AppSpec JSON on the page block instead of a tree of layout blocks. Properties are plain JSONB protected by row-level security on `workspace_id`; v3's envelope encryption and query index are deferred.

## Consequences

- Records get per-record order, versions, soft delete and undo now; splitting the layout into child blocks later does not touch records.
- No encryption at rest beyond Supabase's own; the settings screen must not claim more.
- Queries filter JSONB directly; fine at personal scale, revisit with the v3 query index if a collection passes ~10k records.
- Reversal trigger: per-block sharing or encryption becomes a requirement.

## Alternatives considered

- **Full v3 block tree now:** most faithful; the renderer and Clair's spec compiler get much bigger.
- **Spec document + rows table:** simplest; diverges from v3's invariant and needs a migration later.
- **Railway Postgres:** we would build auth, pairing and live updates ourselves.

## References

`docs/backend.md` §2, TabOS v3 §3, §7.
