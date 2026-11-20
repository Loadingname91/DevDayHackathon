# ADR-009: Look: Soft Quilt, with user-pickable grounds

## Status

Accepted · 2026-11-19 · Deciders: owner · Supersedes the Quilter's Workbench colour and type tokens in `spec/ui-tech-plan.md` §7 and the "dark theme is out" line in `spec/prd.md`

## Context

The boards and prototypes were drawn in the Quilter's Workbench look: muslin ground, denim chrome, a mustard tag, three type families. On Thu 19 Nov 2026 the owner picked a new look from a soft pastel reference and asked for the background and themes to be redone around it. Six grounds were tried on the canvas (Lilac haze, Peach morning, Mint air, Plain muslin, Midnight, Denim dusk). The owner chose Mint air for light mode and Denim dusk for dark, and then said yes to letting people choose a different ground themselves.

## Decision

The look is Soft Quilt: each app is a pastel patch with a running-stitch edge on a soft gradient ground, with frosted white cards, ink pill buttons, Figtree with tabular numbers, the spool for Clair and no red.

- Light mode uses the Mint air ground. Dark mode uses Denim dusk. Dark mode is part of the look.
- People can choose Light, Dark or Match phone, and one ground per mode, in Settings → Appearance (FR-T6). The four light grounds and two dark grounds are the six that were tried. Defaults: Match phone, Mint air, Denim dusk.
- Picking a ground is free on every plan.
- The choice is a per-user setting that applies on every device the person signs in on.
- A ground changes only the background. App colours, cards, type and layout are the same on every ground, so every ground has to pass the same contrast check (text at least 4.5:1).

## Consequences

- The Quilter's Workbench tokens in `spec/ui-tech-plan.md` §7 (muslin, denim, mustard, the three families) are superseded. Current values are `GROUNDS`, `MODE` and `APP` in `design/tools/gen_soft.py`. Motion, behaviour, copy and layout decisions still hold.
- The canvas boards were restyled in Soft Quilt, and a new board "You, Appearance" (`design/tools/gen_soft_themes.py`) shows the picker.
- Dark mode is new scope. It was out of scope in the PRD before this decision; whether the DevDay build ships it is an open question in `spec/prd.md`.
- Storing the choice is not built for DevDay. The demo uses the defaults. It needs a per-user field and a way to write it after DevDay (`spec/backend.md` §2.2, Workspace and member).
- Six grounds means six backgrounds to check whenever a card, patch or text colour changes.
- Reversal trigger: a ground that fails contrast in testing is dropped from the picker, not patched per screen.

## Alternatives considered

- **Keep Quilter's Workbench:** already drawn everywhere, but the owner preferred the softer look.
- **One fixed ground per mode, no picker:** less to test, but the owner wanted people to make it their own.
- **Grounds as a paid extra:** rejected by the owner; it is free on every plan.

## References

`.impeccable/surfaces/app.md` ("Look decision, Nov 19 night: Soft Quilt"), `design/tools/gen_soft.py`, `design/tools/gen_soft_themes.py`, `spec/prd.md` FR-T6, `spec/ui-tech-plan.md` §7, canvas page "Look: Soft Quilt".
