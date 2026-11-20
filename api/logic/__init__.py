"""Pure data logic for the Quilt API (spec/backend.md §3 and §6).

No database access: every function takes plain dicts and returns plain dicts.

Modules:
- clock    : now() with the DEMO_NOW override, workspace-zone helpers, windows.
- repeats  : repeat rules -> occurrences (wall time, then zone), complete/skip/move.
- dated    : the virtual `*dated` source and Home's Next up.
- formula  : the formula engine (faces, metric/progress values, row formulas).
- fmt      : how numbers, money and dates are worded for the client.

Shapes used everywhere:
- Record:   {"id", "collection": "<app>/<collection>", "properties": {...}, "position"}
            ("ref" is accepted in place of "collection"; records with a truthy
            "deleted_at" are ignored).
- App spec: {"key", "name", "settings"?, "collections": [{"key", "fields", "titleField",
            "dateField"?, "calendar"?, "label"?, ...}], "face": {...}, "tabs": [...]}.
"""
