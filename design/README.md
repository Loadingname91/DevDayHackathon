# Design files

**Start with `DESIGN.md`**: the design system the client applies (Mint colours from ADR-013, the Screens boards' layout and components, motion, Clair's spool, words, and which board each screen follows). **`screens-css.md`** has every component's exact CSS from the 40 Screens boards, with its token; `board-css-inventory.md` is the generated evidence (`tools/board_css.py`).

Trimmed on Nov 19, 2026, before the DevDay build. The design canvas on claude.ai is the single place to look at the design: its Screens page ends with link cards to every other Quilt artifact.

| What | Live link | Source here |
| --- | --- | --- |
| **Design canvas** (every screen, plus links to the rest) | https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P | removed; regenerate with `tools/` (below) |
| Home prototype | https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV | `prototypes/quilt-home.html` |
| Flows prototype | https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne | `prototypes/quilt-flows.html` |
| Motion catalogue | https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC | `prototypes/motion-catalogue.html` |
| Design book (old Quilter's Workbench look) | https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq | removed |

## What's here

- `prototypes/`: the clickable Home, Flows and motion pages. The client ports its CSS and motion from these (`spec/ui-tech-plan.md` §7).
- `notes/fixspec.md`: the motion and Clair-sheet spec that the files in `spec/` cite as "fixspec". `notes/motion-catalogue.md` and `notes/surface-brief.md` are the matching notes.
- `tools/gen_soft.py`, `tools/soft_theme.py`, `tools/gen_soft_themes.py`: the Soft Quilt look (chosen Nov 19, `spec/adr/009-soft-quilt-look-pickable-grounds.md`).
- `tools/mint_theme.py`: the Mint colours (picked Nov 20, `spec/adr/013-mint-one-family-palette.md`). The generators call it last, and it converts boards already on disk.
- `tools/gen_all.py`, `tools/layout_canvas.py`, `tools/gen_docs.py`: the generators for the canvas boards.

## What was removed, and how to get it back

Removed in the commit after `ee70002`: the generated canvas boards (`canvas/`), the design book (`book/`), the board tests (`tests/`), the stills, the early explorations and the rejected look generators (cross-stitch, Gen Z).

- Any of it: `git checkout ee70002 -- design/canvas` (or `design/book`, `design/tests`, and so on).
- The boards from the generators:

```bash
python3 design/tools/gen_all.py design/canvas
python3 design/tools/layout_canvas.py design/canvas
```

The boards and prototypes show the older demo (8 apps, the grocery receipt). They don't show the planner, the Workflows tab, Google Calendar rows or the four new apps.

The boards load a runtime file, `support.js`, that belongs to the canvas artifact type and isn't ours to publish, so it is git-ignored. To view boards locally, ask Claude Code to fetch it from the canvas artifact into `design/canvas/`.
