# ADR-013: Mint, a one-family palette (supersedes the colours of ADR-009)

Date: Fri 20 Nov 2026. Status: accepted (owner's pick).

## Context

The Soft Quilt look (ADR-009) gave every app one of nine full-strength pastel dyes, on a four-colour gradient ground, with violet-navy buttons. On Home the twelve patches sat side by side in nine unrelated hues and the owner said the colours clash. Dark mode (Denim dusk) turned the dyes brown, olive and maroon.

Four options were rendered from the running client on Home, Budget, Calendar and Groceries in light and dark (artifact https://claude.ai/artifact/QHVz9N5AjuiGj3CnhGbvjw): 3 cloths, Washed, Mint and Paper. The owner picked Mint.

## Decision

- All nine app dyes come from one family, pear through teal to blue (OKLCH hues 135 to 240). Apps are told apart by depth, icon and name, not by unrelated hues.
- The ground is plain: no gradient image. Light is a pale mint, dark a deep green-black. Ink, secondary text, cards and buttons take the ground's hue.
- Light and dark share one token set through `light-dark()`; dark is a `color-scheme` switch, not a second copy of the values.
- Dye names stay as they are (`sage`, `apricot`, `blush`…), because the API stores them; only their colours changed.
- Everything else in ADR-009 stands: patches with a stitched edge, dashed = waiting for OK, solid = saved, Figtree, ink pill buttons, no red.

## Consequences

- Tokens live in `web/src/styles/tokens.css`. The canvas boards were re-coloured to Mint on Nov 20 by `design/tools/mint_theme.py`, which `soft_theme.py` and `gen_soft.py` now call, so regenerated boards come out in Mint. The canvas page "Look: Soft Quilt" has a Mint palette board (SqMint); the grounds and Appearance boards stay in the Nov 19 colours as records.
- The Settings → Appearance ground picker (FR-T6, after DevDay) needs grounds redrawn for this palette; its old list (Lilac haze, Peach morning, Mint air, Plain muslin, Midnight, Denim dusk) no longer applies.
- Trade-off accepted: at a glance, apps are harder to tell apart than with nine hues.

## Amendment, Fri 20 Nov 2026 (afternoon): the dyes are distinct hues

The owner (Hitesh) said the app tiles and patches can use different colours. Review showed why: with every dye between hue 135 and 240, Home read as one green-blue block, three apps were near-identical greens, and the dyes sat at 1.04 to 1.39:1 against the ground. The trade-off above ("harder to tell apart") is withdrawn.

- **What changes:** only the nine `[data-dye]` rules in `web/src/styles/tokens.css`. The ground, ink, cards, buttons, focus and Clair's bubble stay the Mint family. Dye names and the API are untouched.
- **How it avoids the Nov 19 clash:** the nine are cloth dyed to one standard. Lightness (.90 to .94 light) and chroma (.05 to .085) are nearly equal, and only the hue moves: butter 95, pear 125, sage 150, sea glass 188, chambray 245, lavender 292, blush 340, apricot 60, linen 85 (a warm neutral). Dark mode uses patch lightness .34 to .41 from the same hues.
- **No red:** blush leans mauve (hue 340) so its deep tone reads plum, never an alert.
- **Neighbours never share a dye** on Home. Demo account: Budget sea glass, Groceries sage, Calories apricot, Calendar chambray, To-dos butter, Meditation lavender, Workout blush, Running sage, Notes linen, Classes chambray, Subscriptions lavender, Cycle pear. The four pins (Groceries, Budget, Calendar, To-dos) are four different hues.
- **Unknown dyes:** a name outside the nine falls back to the neutral in CSS and is mapped to one of the nine by hash at the data boundary (`web/src/lib/dye.ts`), so an app Clair builds is never invisible.
