"""The demo Google account's four events as Google's `events.list` would return them (backend.md §2.3, §8a).

Used when DEMO_GCAL_FIXTURE=1: "Add Google Calendar" connects this instead of Google, so the demo needs no Google
Cloud project and no network. The ids are the ones the seed writes (api/seed/data.py GOOGLE_EVENTS), so syncing
after a seed that wrote the fixtures changes nothing. tests/test_connect_google.py keeps the two in step.
"""
from __future__ import annotations

FIXTURE_TOKEN = 'fixture'   # stored in connections.refresh_token for a fixture connection: a marker, not a secret


def _timed(eid: str, title: str, start: str, end: str) -> dict:
    return {'kind': 'calendar#event', 'id': eid, 'status': 'confirmed', 'summary': title,
            'start': {'dateTime': start, 'timeZone': 'America/Denver'},
            'end': {'dateTime': end, 'timeZone': 'America/Denver'}}


GOOGLE_RESPONSE: list[dict] = [
    _timed('fixture-dentist', 'Dentist', '2026-11-24T07:30:00-07:00', '2026-11-24T08:30:00-07:00'),
    _timed('fixture-drive', 'Drive home for Thanksgiving', '2026-11-25T17:00:00-07:00', '2026-11-25T21:00:00-07:00'),
    # all day Thu 26 to Sat 28 Nov: Google's end date is the day after the last day
    {'kind': 'calendar#event', 'id': 'fixture-thanksgiving', 'status': 'confirmed', 'summary': 'Thanksgiving at home',
     'start': {'date': '2026-11-26'}, 'end': {'date': '2026-11-29'}},
    _timed('fixture-back', 'Back to campus', '2026-11-29T12:00:00-07:00', '2026-11-29T13:00:00-07:00'),
]
