# Design files

Everything behind Quilt's design canvas and prototypes. The live versions are on claude.ai:

| What | Live link | Source here |
| --- | --- | --- |
| Design canvas (42 boards, every screen) | https://claude.ai/artifact/TuTh7izChf3Dk74gvBvi7P | `canvas/` |
| Home prototype | https://claude.ai/artifact/Wr2p4rLD6Zgow3uxmSykRV | `prototypes/quilt-home.html` |
| Flows prototype | https://claude.ai/artifact/HrLSUSPiXKCLphYfHVFxne | `prototypes/quilt-flows.html` |
| Motion catalogue | https://claude.ai/artifact/VPM8mrtefTzb7n6e5GwLAC | `prototypes/motion-catalogue.html` |
| Design book | https://claude.ai/artifact/N37FhQVVYTNoeDf4rJFyjq | `book/` |

## Folders

- `canvas/`: one `*.dc.html` file per board plus `canvas.json` (board positions and rows). These files are generated, so edit `tools/gen_all.py` instead of the boards.
- `tools/gen_all.py` writes every board; `tools/layout_canvas.py` lays the boards out in `canvas.json`.
- `prototypes/`: the clickable Home, Flows and motion pages. `explorations/` holds earlier directions kept for reference.
- `tests/`: Playwright checks for the boards and prototypes, run at phone size with touch.
- `notes/fixspec.md`: the motion and Clair-sheet spec the specs in `spec/` cite as "fixspec". `notes/motion-catalogue.md` and `notes/surface-brief.md` are the matching notes.
- `book/`: the design book page and its images.

## Regenerating the canvas

```bash
python3 design/tools/gen_all.py design/canvas
python3 design/tools/layout_canvas.py design/canvas
```

The boards load a runtime file, `support.js`, that belongs to the canvas artifact type and isn't ours to publish, so it is git-ignored. To view boards or run the tests locally, ask Claude Code to fetch `support.js` from the canvas artifact into `design/canvas/`. To update the live canvas, ask Claude Code to publish `design/canvas/canvas.json` and the changed boards to the canvas URL above.

## Docs on the canvas

The canvas has three pages: Screens, Docs and Specs. The Docs and Specs pages are the markdown files in `docs/` and `spec/`, rendered as page artboards (long docs are split into parts, because a canvas frame is at most 8,000 px tall). After editing a doc, rebuild them:

```bash
pip install markdown
python3 design/tools/gen_docs.py . design/canvas            # writes Doc*/Spec* boards and previews
node design/tests/measure_docs.js /path/to/node_modules/playwright design/docs-preview heights.json
python3 design/tools/gen_docs.py . design/canvas heights.json   # again, with measured heights and splits
```

If a doc gains or loses parts, its entries in `canvas.json` need updating too. The Screens page also ends with link cards to every other Quilt artifact (the prototypes, motion pages, design book, studies and the Nov 15 brief).

## Running the tests

Each test takes the path to an installed `playwright` module, the page or folder URL, and an output folder for screenshots:

```bash
node design/tests/ob.js /path/to/node_modules/playwright "file://$PWD/design/canvas/" /tmp/shots
node design/tests/homecal.js /path/to/node_modules/playwright "file://$PWD/design/prototypes/quilt-home.html"
```

`test.js` checks the Clair boards, `ob.js` the onboarding row, `groc.js` Groceries, `flows.js` the Flows prototype and `homecal.js` the Home prototype's Calendar count before and after confirm and Undo.
