"""The canonical demo seed as Python data (spec/backend.md §2.2 and §2.3; the spec wins over boards and fixtures).

Every record has a stable human key ("i_eggs", "sp_01", "s_pull") so fixtures and tests can name it. A relation
value is a list of `Ref`s, resolved to block UUIDs by `load.py`. Datetimes are wall times in America/Denver,
turned into ISO 8601 with the offset that zone had then (`dt`). Money is integer cents.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/Denver')
DEMO_NOW = '2026-11-20T17:45:00-07:00'

# Page order in the workspace (Your apps). The original 8, then the four added later (§2.3 "The 12 apps").
APPS = ['notes', 'budget', 'subscriptions', 'groceries', 'calendar', 'classes', 'todos', 'workout',
        'calories', 'running', 'cycle', 'meditation']
BEFORE_APPS = APPS[:8]               # the recording's "before" state: 8 apps, no Calories/Running/Cycle/Meditation
PINS = ['groceries', 'budget', 'calendar', 'todos']


@dataclass(frozen=True)
class Ref:
    """A relation target: a record of `coll` ("app/collection") named by its human key."""
    coll: str
    key: str


def dt(s: str) -> str:
    """'2026-11-16 08:00' (Denver wall time) → '2026-11-16T08:00:00-07:00'."""
    return datetime.fromisoformat(s).replace(tzinfo=TZ).isoformat()


def cents(dollars: str) -> int:
    whole, _, frac = dollars.partition('.')
    return int(whole) * 100 + int((frac + '00')[:2])


# ---------------------------------------------------------------- workspace, member, credits, notes

WORKSPACE = {'name': 'My quilt', 'tz': 'America/Denver', 'read_level': 'full'}
WORKSPACE_SETTINGS = {'credits_monthly': 50, 'notes_enabled': True}   # + pins (page ids), filled at load
DISPLAY_NAME = 'Sam'

APP_OPENS = {   # §2.3 workspace_members.app_opens
    'groceries': dt('2026-11-20 17:41'), 'budget': dt('2026-11-20 17:30'), 'calories': dt('2026-11-20 15:40'),
    'calendar': dt('2026-11-20 12:10'), 'todos': dt('2026-11-20 08:05'), 'running': dt('2026-11-19 17:15'),
    'meditation': dt('2026-11-19 22:45'), 'notes': dt('2026-11-19 10:30'), 'workout': dt('2026-11-19 18:50'),
    'classes': dt('2026-11-19 09:00'), 'subscriptions': dt('2026-11-15 12:00'), 'cycle': dt('2026-11-15 12:00'),
}

# usage_ledger for November: 50 granted, 18 used, 32 left (§2.3 "Credits")
LEDGER = [
    ('grant', 50, dt('2026-11-01 00:00')),
    ('build', -10, dt('2026-11-01 14:00')),    # Subscriptions build
    ('chat', -1, dt('2026-11-08 11:00')),      # "Costco receipts go on Costco run"
    ('chat', -1, dt('2026-11-17 08:30')),      # "move leg day to 7 am"
    ('chat', -1, dt('2026-11-17 08:35')),      # "don't suggest snacks"
    ('photo', -5, dt('2026-11-19 12:50')),     # Union food court receipt
]
LEDGER_PERIOD = '2026-11-01'

CLAIR_NOTES = [
    ('Receipts from Costco go on Costco run.', 'preference', dt('2026-11-08 11:00')),
    ("Don't suggest snacks", 'preference', dt('2026-11-17 08:35')),
]

# Stitched history Activity lists (§2.3 "Change sets"); app key, title, when. No ops: the rows are in the seed.
HISTORY = [
    ('subscriptions', 'Build Subscriptions', 'Made a Subscriptions app from a bank-app screenshot.', dt('2026-11-01 14:00')),
    ('workout', 'Leg day moved to 7 am', 'Leg day moves from 6:00 pm to 7:00 am on Tuesdays.', dt('2026-11-17 08:30')),
    ('budget', 'Union food court receipt', 'Lunch $11.40 to Budget and a rice bowl to Calories.', dt('2026-11-19 12:50')),
]

# ---------------------------------------------------------------- spec overrides on top of api/templates/*.json

SPEC_OVERRIDES = {
    'budget': {'settings': {'limit': 120000}},
    'calories': {'settings': {'target': 2200}},
    'cycle': {'settings': {'clair_read': True}},       # on in the demo account (Sun 15 Nov)
}
# Groceries' lists beyond the template's Weekly shop (§2.2)
GROCERY_LISTS = [
    {'id': 'l_weekly', 'label': 'Weekly shop'},
    {'id': 'l_taco', 'label': 'Taco night', 'hint': 'Sat 21 Nov'},
    {'id': 'l_costco', 'label': 'Costco run', 'hint': 'Once a month'},
]

# ---------------------------------------------------------------- Groceries (§2.2, §2.3 "Groceries trips")

OPEN_ITEMS = [  # (key, name, list, qty)
    ('i_oat_milk', 'Oat milk', 'l_weekly', None), ('i_eggs', 'Eggs', 'l_weekly', '1 dozen'),
    ('i_bananas', 'Bananas', 'l_weekly', None), ('i_chicken_thighs', 'Chicken thighs', 'l_weekly', None),
    ('i_rice', 'Rice', 'l_weekly', '5 lb'), ('i_spinach', 'Spinach', 'l_weekly', None),
    ('i_greek_yogurt', 'Greek yogurt', 'l_weekly', None), ('i_coffee_beans', 'Coffee beans', 'l_weekly', None),
    ('i_coffee_filters', 'Coffee filters', 'l_weekly', None), ('i_tortillas', 'Tortillas', 'l_weekly', None),
    ('i_olive_oil', 'Olive oil', 'l_weekly', None), ('i_dish_soap', 'Dish soap', 'l_weekly', None),
    ('i_ground_beef', 'Ground beef', 'l_taco', None), ('i_avocados', 'Avocados', 'l_taco', None),
    ('i_limes', 'Limes', 'l_taco', None), ('i_salsa', 'Salsa', 'l_taco', None),
    ('i_shredded_cheese', 'Shredded cheese', 'l_taco', None),
    ('i_paper_towels', 'Paper towels', 'l_costco', None), ('i_laundry_pods', 'Laundry pods', 'l_costco', None),
    ('i_frozen_berries', 'Frozen berries', 'l_costco', None), ('i_almonds', 'Almonds', 'l_costco', None),
    ('i_toilet_paper', 'Toilet paper', 'l_costco', None),
]

# November trips: (key, day, store, total, [(item name, price)])
NOV_TRIPS = [
    ('tr_05', '2026-11-05', "Smith's", '41.37', [('Coffee beans', '2.99'), ('Butter', '4.79')]),
    ('tr_09', '2026-11-09', 'Corner Market', '8.62', [('Chicken thighs', '8.62')]),
    ('tr_10', '2026-11-10', 'Corner Market', '4.29', [('Greek yogurt', '4.29')]),
    ('tr_11', '2026-11-11', "Smith's", '27.15', [('Spinach', '3.29'), ('Cheddar', '3.99')]),
    ('tr_12', '2026-11-12', 'Corner Market', '4.29', [('Eggs', '4.29')]),
    ('tr_13', '2026-11-13', 'Corner Market', '7.78', [('Oat milk', '3.49'), ('Parmesan', '4.29')]),
    ('tr_14', '2026-11-14', "Smith's", '45.01', [('Bananas', '1.87'), ('Orange juice', '3.69')]),
    ('tr_15', '2026-11-15', 'Corner Market', '3.49', [('Hummus', '3.49')]),
]
TRIP_TIME = '17:30'

# Usuals: name → every_days (clair-agent.md §8 snapshot; Butter, Cheddar, Orange juice, Hummus from §2.2)
USUAL_EVERY = {
    'Eggs': 6, 'Oat milk': 7, 'Bananas': 5, 'Spinach': 7, 'Greek yogurt': 7, 'Coffee beans': 14,
    'Chicken thighs': 10, 'Butter': 14, 'Cheddar': 7, 'Orange juice': 10, 'Hummus': 7,
}
OCT_FIRST, OCT_LAST = date(2026, 10, 9), date(2026, 10, 31)


def slug(name: str) -> str:
    return name.lower().replace(' ', '_').replace(',', '').replace("'", '')


def _nov_purchases():
    """name → (November day, price) for each usual."""
    out = {}
    for _, day, _, _, items in NOV_TRIPS:
        for name, price in items:
            out[name] = (date.fromisoformat(day), price)
    return out


def october_trips():
    """§2.3: each usual bought every `every_days` counting back from its November date, inside Fri 9 to Sat 31 Oct,
    one trip per day, Smith's for 3+ items else Corner Market, at the November prices. Returns
    [(key, day, store, total, [(name, price)])] in date order."""
    nov = _nov_purchases()
    by_day: dict[date, list] = {}
    for name, every in USUAL_EVERY.items():
        d, price = nov[name]
        d -= timedelta(days=every)
        while d >= OCT_FIRST:
            if d <= OCT_LAST:
                by_day.setdefault(d, []).append((name, price))
            d -= timedelta(days=every)
    trips = []
    for d in sorted(by_day):
        items = sorted(by_day[d], key=lambda it: list(USUAL_EVERY).index(it[0]))
        store = "Smith's" if len(items) >= 3 else 'Corner Market'
        total = sum(cents(p) for _, p in items)
        trips.append((f'tr_{d:%m%d}', d.isoformat(), store, f'{total // 100}.{total % 100:02d}', items))
    return trips


def groceries():
    trips, items = [], []
    for key, day, store, total, bought in october_trips() + NOV_TRIPS:
        trips.append((key, {'store': store, 'total': cents(total), 'at': dt(f'{day} {TRIP_TIME}')}))
        for name, price in bought:
            items.append((f'ib_{slug(name)}_{day[5:7]}{day[8:10]}', {
                'name': name, 'list': 'l_weekly', 'status': 'bought', 'price': cents(price),
                'bought_on': day, 'trip': [Ref('groceries/trips', key)], 'usual': 'auto'}))
    for key, name, lst, qty in OPEN_ITEMS:
        p = {'name': name, 'list': lst, 'status': 'to_buy', 'usual': 'auto'}
        if qty:
            p['qty'] = qty
        items.append((key, p))
    return {'items': items, 'trips': trips}


# ---------------------------------------------------------------- Budget (§2.3 "Budget")

# (key, day, note, category, amount, via) — via: ('groceries', trip key) or ('subscriptions', sub key)
NOV_SPEND = [
    ('sp_01', '2026-11-01', 'November rent', 'c_rent', '380.00', None),
    ('sp_02', '2026-11-01', 'Cafe Rio', 'c_eating_out', '11.48', None),
    ('sp_03', '2026-11-02', 'Hulu', 'c_subscriptions', '9.99', ('subscriptions', 'sub_hulu')),
    ('sp_04', '2026-11-02', 'Lime scooter', 'c_transport', '5.60', None),
    ('sp_05', '2026-11-03', 'Adobe CC, student', 'c_subscriptions', '13.49', ('subscriptions', 'sub_adobe')),
    ('sp_06', '2026-11-03', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_07', '2026-11-04', 'Chipotle', 'c_eating_out', '12.35', None),
    ('sp_08', '2026-11-05', "Smith's", 'c_groceries', '41.37', ('groceries', 'tr_05')),
    ('sp_09', '2026-11-06', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_10', '2026-11-07', 'Costa Vida', 'c_eating_out', '13.20', None),
    ('sp_11', '2026-11-07', 'Megaplex movie', 'c_fun', '12.50', None),
    ('sp_12', '2026-11-09', 'Corner Market', 'c_groceries', '8.62', ('groceries', 'tr_09')),
    ('sp_13', '2026-11-09', 'iCloud 50 GB', 'c_subscriptions', '2.99', ('subscriptions', 'sub_icloud')),
    ('sp_14', '2026-11-10', 'Corner Market', 'c_groceries', '4.29', ('groceries', 'tr_10')),
    ('sp_15', '2026-11-10', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_16', '2026-11-11', "Smith's", 'c_groceries', '27.15', ('groceries', 'tr_11')),
    ('sp_17', '2026-11-12', 'Corner Market', 'c_groceries', '4.29', ('groceries', 'tr_12')),
    ('sp_18', '2026-11-12', 'Sushi with Maya', 'c_eating_out', '22.40', None),
    ('sp_19', '2026-11-13', 'Corner Market', 'c_groceries', '7.78', ('groceries', 'tr_13')),
    ('sp_20', '2026-11-13', 'Thai Siam', 'c_eating_out', '28.00', None),
    ('sp_21', '2026-11-14', "Smith's", 'c_groceries', '45.01', ('groceries', 'tr_14')),
    ('sp_22', '2026-11-14', 'Cafe Rio', 'c_eating_out', '11.48', None),
    ('sp_23', '2026-11-14', 'Lime scooter', 'c_transport', '8.40', None),
    ('sp_24', '2026-11-14', 'Thrift shop', 'c_fun', '20.03', None),
    ('sp_25', '2026-11-15', 'Corner Market', 'c_groceries', '3.49', ('groceries', 'tr_15')),
    ('sp_26', '2026-11-15', 'Bagel Project', 'c_eating_out', '14.97', None),
    ('sp_27', '2026-11-16', 'Cafe Rio', 'c_eating_out', '9.62', None),
    ('sp_28', '2026-11-17', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_29', '2026-11-17', 'Gas', 'c_transport', '28.00', None),
    ('sp_30', '2026-11-18', 'Taco Bell', 'c_eating_out', '6.87', None),
    ('sp_31', '2026-11-19', 'Union food court', 'c_eating_out', '11.40', None),
    ('sp_32', '2026-11-19', 'Union vending', 'c_eating_out', '2.23', None),
]
OCT_SPEND = [
    ('sp_oct_blue_copper_1', '2026-10-03', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_oct_blue_copper_2', '2026-10-11', 'Blue Copper', 'c_eating_out', '5.25', None),
    ('sp_oct_starbucks', '2026-10-19', 'Starbucks', 'c_eating_out', '6.10', None),
]
SPEND_TIME = {'sp_31': '12:45'}   # Union food court: the receipt Clair read at lunch


def budget():
    rows = []
    trip_at = {k: (day, store, total) for k, day, store, total, _ in october_trips() + NOV_TRIPS}
    spends = list(OCT_SPEND)
    # October grocery trips reach Budget through the same stitch (§2.3: "plus the October grocery trips")
    for k, (day, store, total) in trip_at.items():
        if day < '2026-11-01':
            spends.append((f'sp_oct_{k}', day, store, 'c_groceries', total, ('groceries', k)))
    spends.sort(key=lambda r: r[1])
    for key, day, note, cat, amount, via in spends + NOV_SPEND:
        if via and via[0] == 'groceries':
            at = dt(f'{day} {TRIP_TIME}')                    # at ← trip.at
        elif via and via[0] == 'subscriptions':
            at = dt(f'{day} 00:00')                          # at ← the renewal (occurrence) date
        else:
            at = dt(f'{day} {SPEND_TIME.get(key, "12:00")}')
        p = {'note': note, 'amount': cents(amount), 'category': cat, 'at': at}
        if via:
            coll = 'groceries/trips' if via[0] == 'groceries' else 'subscriptions/subscriptions'
            p['_via'] = {'app': via[0], 'record_id': Ref(coll, via[1])}
        rows.append((key, p))
    return {'spend': rows}


# ---------------------------------------------------------------- Subscriptions

SUBSCRIPTIONS = [  # key, name, amount, next renewal, day of month word, first occurrence after the Nov 1 build
    ('sub_spotify', 'Spotify', '11.99', '2026-11-22', '22nd', '2026-11-22', []),
    ('sub_hulu', 'Hulu', '9.99', '2026-12-02', '2nd', '2026-11-02', ['2026-11-02']),
    ('sub_adobe', 'Adobe CC, student', '13.49', '2026-12-03', '3rd', '2026-11-03', ['2026-11-03']),
    ('sub_icloud', 'iCloud 50 GB', '2.99', '2026-12-09', '9th', '2026-11-09', ['2026-11-09']),
]


def subscriptions():
    return {'subscriptions': [
        (k, {'name': n, 'amount': cents(a), 'renews': r, 'every': f'Monthly on the {w}',
             'repeat': {'rule': 'FREQ=MONTHLY', 'start': f'{start}T00:00', 'log': log, 'skip': []}})
        for k, n, a, r, w, start, log in SUBSCRIPTIONS]}


# ---------------------------------------------------------------- Calendar

def calendar(gcal_fixture: bool = False):
    events = [
        ('e_haircut_aug', {'title': 'Haircut', 'at': dt('2026-08-08 11:00'), 'kind': 'barber'}),
        ('e_haircut_sep', {'title': 'Haircut', 'at': dt('2026-09-12 11:00'), 'kind': 'barber'}),
        ('e_haircut_oct', {'title': 'Haircut', 'at': dt('2026-10-17 11:00'), 'kind': 'barber'}),
        ('e_coffee', {'title': 'Coffee with Maya', 'at': dt('2026-11-21 10:00')}),
    ]
    if gcal_fixture:
        events += GOOGLE_EVENTS
    return {'events': events}


# The demo Google account's four events (§2.3); written by the seed only with DEMO_GCAL_FIXTURE=1.
GOOGLE_EVENTS = [
    ('g_dentist', {'title': 'Dentist', 'at': dt('2026-11-24 07:30'), 'ends': dt('2026-11-24 08:30'),
                   'source': 'google', 'ext_id': 'fixture-dentist'}),
    ('g_drive', {'title': 'Drive home for Thanksgiving', 'at': dt('2026-11-25 17:00'), 'ends': dt('2026-11-25 21:00'),
                 'source': 'google', 'ext_id': 'fixture-drive'}),
    ('g_thanksgiving', {'title': 'Thanksgiving at home', 'at': '2026-11-26', 'ends': '2026-11-28',
                        'source': 'google', 'ext_id': 'fixture-thanksgiving'}),
    ('g_back', {'title': 'Back to campus', 'at': dt('2026-11-29 12:00'), 'ends': dt('2026-11-29 13:00'),
                'source': 'google', 'ext_id': 'fixture-back'}),
]


# ---------------------------------------------------------------- Classes

def classes():
    def cls(key, name, title, room, meets, nxt, rule, start, skip):
        return (key, {'name': name, 'title': title, 'room': room, 'meets': meets, 'time': dt(nxt),
                      'repeat': {'rule': rule, 'start': start, 'log': [], 'skip': skip}})
    return {
        'classes': [
            cls('c01', 'ECON 1010', 'Principles of Microeconomics', 'Kendall 104', 'Tue and Thu 9:10 am',
                '2026-11-24 09:10', 'FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20261210T235959', '2026-08-25T09:10',
                ['2026-11-26']),
            cls('c02', 'MATH 1210', 'Calculus I', 'JWB 335', 'Mon and Wed 11:50 am',
                '2026-11-23 11:50', 'FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959', '2026-08-24T11:50', []),
            cls('c03', 'CS 3500', 'Software Practice', 'WEB L104', 'Mon and Wed 3:00 pm',
                '2026-11-23 15:00', 'FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261209T235959', '2026-08-24T15:00', []),
        ],
        'due': [
            ('d01', {'title': 'Start CS 3500 project', 'kind': 'assignment', 'at': dt('2026-11-23 23:59'),
                     'class': [Ref('classes/classes', 'c03')], 'done': False}),
            ('d02', {'title': 'Homework 11', 'kind': 'assignment', 'at': dt('2026-11-24 23:59'),
                     'class': [Ref('classes/classes', 'c02')], 'done': False}),
            ('d03', {'title': 'Homework 10', 'kind': 'assignment', 'at': dt('2026-11-17 23:59'),
                     'class': [Ref('classes/classes', 'c02')], 'done': True}),
        ],
    }


# ---------------------------------------------------------------- To-dos

def todos():
    return {'todos': [
        ('t_library', {'title': 'Return library books', 'due': dt('2026-11-20 21:00'), 'place': 'Marriott Library',
                       'done': False}),
        ('t_recycling', {'title': 'Take out recycling', 'due': dt('2026-11-20 20:00'), 'done': False,
                         'repeat': {'rule': 'FREQ=WEEKLY;BYDAY=FR', 'start': '2026-10-23T20:00',
                                    'log': ['2026-10-23', '2026-10-30', '2026-11-13'], 'skip': ['2026-11-06']}}),
        ('t_call_home', {'title': 'Call home', 'due': '2026-11-22', 'done': False}),
        ('t_maya', {'title': 'Pay Maya back for pizza ($14)', 'done': False}),
        ('t_devday', {'title': 'DevDay demo', 'due': dt('2026-11-20 15:00'), 'place': 'Lassonde Studios',
                      'done': True}),
        ('t_flu', {'title': 'Book flu shot', 'place': 'Student health', 'done': True}),
    ]}


# ---------------------------------------------------------------- Notes

def notes():
    return {
        'notebooks': [
            ('nb_econ', {'name': 'ECON 1010', 'class': [Ref('classes/classes', 'c01')]}),
            ('nb_math', {'name': 'MATH 1210', 'class': [Ref('classes/classes', 'c02')]}),
            ('nb_cs3500', {'name': 'CS 3500', 'class': [Ref('classes/classes', 'c03')]}),
            ('nb_personal', {'name': 'Personal'}),
        ],
        'notes': [
            ('n_related_rates', {'title': 'Related rates examples', 'notebook': [Ref('notes/notebooks', 'nb_math')],
                                 'at': dt('2026-11-10 12:40')}),
            ('n_gift_ideas', {'title': 'Gift ideas for mom', 'notebook': [Ref('notes/notebooks', 'nb_personal')],
                              'at': dt('2026-11-15 20:15')}),
            ('n_unit_testing', {'title': 'Unit testing with mocks', 'notebook': [Ref('notes/notebooks', 'nb_cs3500')],
                                'at': dt('2026-11-16 15:50')}),
            ('n_di', {'title': 'Dependency injection', 'notebook': [Ref('notes/notebooks', 'nb_cs3500')],
                      'at': dt('2026-11-18 15:55')}),
            ('n_elasticity', {'title': 'Price elasticity', 'notebook': [Ref('notes/notebooks', 'nb_econ')],
                              'at': dt('2026-11-19 10:30')}),
        ],
    }


# ---------------------------------------------------------------- Workout (§2.3 "Workout")

ROUTINES = [('ro_pull', 'Pull', 45), ('ro_push', 'Push', 40), ('ro_legs', 'Legs', 35)]
EXERCISES = [  # key, name, routine, sets, reps, weight (0 = bodyweight)
    ('ex_pull_ups', 'Pull-ups', 'ro_pull', 3, 8, 0),
    ('ex_lat_pulldown', 'Lat pulldown', 'ro_pull', 3, 10, 120),
    ('ex_seated_cable_row', 'Seated cable row', 'ro_pull', 3, 12, 100),
    ('ex_face_pulls', 'Face pulls', 'ro_pull', 3, 15, 40),
    ('ex_hammer_curl', 'Hammer curl', 'ro_pull', 3, 12, 25),
    ('ex_push_ups', 'Push-ups', 'ro_push', 3, 12, 0),
    ('ex_dumbbell_bench', 'Dumbbell bench', 'ro_push', 3, 10, 40),
    ('ex_goblet_squat', 'Goblet squat', 'ro_legs', 3, 10, 45),
    ('ex_walking_lunges', 'Walking lunges', 'ro_legs', 3, 12, 0),
]
# key, name, routine, weekdays (Mon=0), wall time, rule, start, meets, next open occurrence
SERIES = [
    ('s_pull', 'Pull day', 'ro_pull', (0, 4), '18:00', 'FREQ=WEEKLY;BYDAY=MO,FR', '2026-09-01T18:00',
     'Mon and Fri 6:00 pm', '2026-11-20 18:00'),
    ('s_legs', 'Leg day', 'ro_legs', (1,), '07:00', 'FREQ=WEEKLY;BYDAY=TU', '2026-09-01T07:00',
     'Tue 7:00 am', '2026-11-24 07:00'),
    ('s_push', 'Push day', 'ro_push', (2,), '18:00', 'FREQ=WEEKLY;BYDAY=WE', '2026-09-02T18:00',
     'Wed 6:00 pm', '2026-11-25 18:00'),
]
SERIES_FIRST, SERIES_LAST = date(2026, 9, 1), date(2026, 11, 19)
SKIPPED = {'2026-09-07', '2026-10-12', '2026-10-13', '2026-10-14', '2026-10-16'}   # Labor Day, fall break
LEGS_MOVED_ON = date(2026, 11, 17)   # Leg day was 6:00 pm until Clair moved it to 7:00 am


def lat_pulldown_weight(d: date) -> int:
    """100 lb, +5 every two weeks: 105 on 5 Oct, 110 on 19 Oct, 115 on 2 Nov, 120 on 16 Nov."""
    for since, w in ((date(2026, 11, 16), 120), (date(2026, 11, 2), 115), (date(2026, 10, 19), 110),
                     (date(2026, 10, 5), 105)):
        if d >= since:
            return w
    return 100


def series_occurrences(weekdays) -> list[date]:
    out, d = [], SERIES_FIRST
    while d <= SERIES_LAST:
        if d.weekday() in weekdays:
            out.append(d)
        d += timedelta(days=1)
    return out


def workout():
    sessions, sets = [], []
    exercises = [(k, {'name': n, 'routine': [Ref('workout/routines', r)], 'plan': _plan(s, rp, w),
                      'sets': s, 'reps': rp, 'weight': w, 'order': i + 1})
                 for i, (k, n, r, s, rp, w) in enumerate(EXERCISES)]
    for key, name, routine, days, time, rule, start, meets, nxt in SERIES:
        occ = series_occurrences(days)
        log = [d.isoformat() for d in occ if d.isoformat() not in SKIPPED]
        skip = [d.isoformat() for d in occ if d.isoformat() in SKIPPED]
        sessions.append((key, {'name': name, 'routine': [Ref('workout/routines', routine)], 'at': dt(nxt),
                               'meets': meets, 'done': False,
                               'repeat': {'rule': rule, 'start': start, 'log': log, 'skip': skip}}))
        for day in log:
            d = date.fromisoformat(day)
            t = '18:00' if key == 's_legs' and d < LEGS_MOVED_ON else time
            began = datetime.fromisoformat(f'{day} {t}')
            n = 0
            for ex_key, _, ex_routine, n_sets, reps, weight in EXERCISES:
                if ex_routine != routine:
                    continue
                if ex_key == 'ex_lat_pulldown':
                    weight = lat_pulldown_weight(d)
                for i in range(n_sets):
                    n += 1
                    at = (began + timedelta(minutes=3 * n)).replace(tzinfo=TZ).isoformat()
                    sets.append((f'set_{day.replace("-", "")}_{ex_key[3:]}_{i + 1}', {
                        'exercise': [Ref('workout/exercises', ex_key)], 'session': [Ref('workout/sessions', key)],
                        'reps': reps, 'weight': weight, 'at': at}))
    sets.sort(key=lambda r: r[1]['at'])
    return {
        'sessions': sessions,
        'routines': [(k, {'name': n, 'minutes': m, 'needs': 'Gym'}) for k, n, m in ROUTINES],
        'exercises': exercises,
        'sets': sets,
    }


def _plan(sets: int, reps: int, weight: int) -> str:
    return f'{sets}×{reps} bodyweight' if weight == 0 else f'{sets}×{reps} at {weight} lb'


# ---------------------------------------------------------------- Calories (§2.3 "Calories")

MEALS = [  # key, wall time, name, meal, calories, protein
    ('m_1', '2026-11-16 08:00', 'Oatmeal and banana', 'breakfast', 350, 10),
    ('m_2', '2026-11-16 12:30', 'Turkey sandwich', 'lunch', 520, 28),
    ('m_3', '2026-11-16 19:00', 'Pasta with chicken', 'dinner', 780, 42),
    ('m_4', '2026-11-17 08:15', 'Greek yogurt and granola', 'breakfast', 310, 18),
    ('m_5', '2026-11-17 12:40', 'Leftover pasta', 'lunch', 640, 34),
    ('m_6', '2026-11-17 19:10', 'Tacos', 'dinner', 820, 38),
    ('m_7', '2026-11-18 08:05', 'Oatmeal and banana', 'breakfast', 350, 10),
    ('m_8', '2026-11-18 13:00', 'Taco Bell burrito', 'lunch', 690, 24),
    ('m_9', '2026-11-18 19:20', 'Chicken and rice', 'dinner', 640, 45),
    ('m_10', '2026-11-19 08:20', 'Eggs and toast', 'breakfast', 380, 22),
    ('m_11', '2026-11-19 12:45', 'Union food court rice bowl', 'lunch', 690, 30),
    ('m_12', '2026-11-19 19:30', 'Frozen pizza', 'dinner', 900, 36),
    ('m_13', '2026-11-20 08:10', 'Oatmeal and banana', 'breakfast', 350, 10),
    ('m_14', '2026-11-20 12:30', 'Chicken and rice', 'lunch', 640, 45),
    ('m_15', '2026-11-20 15:40', 'Greek yogurt', 'snack', 150, 15),
]
FOODS = [('fd_oatmeal', 'Oatmeal and banana', 350, 10), ('fd_chicken_rice', 'Chicken and rice', 640, 45),
         ('fd_greek_yogurt', 'Greek yogurt', 150, 15)]


def calories():
    return {
        'meals': [(k, {'name': n, 'calories': c, 'protein': p, 'meal': m, 'at': dt(t)}) for k, t, n, m, c, p in MEALS],
        'foods': [(k, {'name': n, 'calories': c, 'protein': p}) for k, n, c, p in FOODS],
    }


# ---------------------------------------------------------------- Running

RUNS = [  # key, wall time, kind, distance mi, minutes
    ('run_1', '2026-10-31 09:00', 'long', 4, 40), ('run_2', '2026-11-03 17:30', 'easy', 3, 30),
    ('run_3', '2026-11-07 09:00', 'long', 4.5, 44), ('run_4', '2026-11-10 17:30', 'easy', 3, 29),
    ('run_5', '2026-11-12 16:30', 'easy', 3.5, 34), ('run_6', '2026-11-14 09:00', 'long', 5, 49),
    ('run_7', '2026-11-17 17:30', 'easy', 3, 29), ('run_8', '2026-11-19 16:30', 'easy', 4, 38),
]


def running():
    return {
        'runs': [(k, {'name': 'Long run' if kind == 'long' else 'Easy run', 'kind': kind, 'distance': d,
                      'minutes': m, 'at': dt(t), 'done': True}) for k, t, kind, d, m in RUNS],
        'races': [('race_10k', {'name': 'Winter 10K', 'at': dt('2026-12-12 09:00'), 'distance': '10K'})],
    }


# ---------------------------------------------------------------- Cycle

def cycle():
    days = []
    for start in ('2026-09-01', '2026-09-29', '2026-10-27'):
        d0 = date.fromisoformat(start)
        for i, (flow, energy, symptoms) in enumerate((('medium', 2, 'Cramps'), ('heavy', 2, 'Cramps'),
                                                      ('light', 3, None))):
            p = {'date': (d0 + timedelta(days=i)).isoformat(), 'flow': flow, 'energy': energy}
            if symptoms:
                p['symptoms'] = symptoms
            days.append((f'cd_{(d0 + timedelta(days=i)):%m%d}', p))
    return {
        'days': days,
        'cycles': [('cy_sep', {'start': '2026-09-01', 'length': 28}), ('cy_sep29', {'start': '2026-09-29', 'length': 28}),
                   ('cy_oct', {'start': '2026-10-27'})],
    }


# ---------------------------------------------------------------- Meditation

def meditation():
    return {'sessions': [
        ('med_1', {'kind': 'sleep', 'minutes': 10, 'at': dt('2026-11-16 22:30'), 'mood_before': 2, 'mood_after': 4}),
        ('med_2', {'kind': 'breathing', 'minutes': 5, 'at': dt('2026-11-18 07:40'), 'mood_before': 3, 'mood_after': 4}),
        ('med_3', {'kind': 'body_scan', 'minutes': 10, 'at': dt('2026-11-19 22:45'), 'mood_before': 2,
                   'mood_after': 3}),
    ]}


# ---------------------------------------------------------------- all of it

def records(gcal_fixture: bool = False) -> dict[str, dict[str, list[tuple[str, dict]]]]:
    """{app key: {collection key: [(human key, properties)]}} for all 12 apps."""
    return {
        'notes': notes(), 'budget': budget(), 'subscriptions': subscriptions(), 'groceries': groceries(),
        'calendar': calendar(gcal_fixture), 'classes': classes(), 'todos': todos(), 'workout': workout(),
        'calories': calories(), 'running': running(), 'cycle': cycle(), 'meditation': meditation(),
    }
