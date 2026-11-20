"""Pure tests for the command service: position keys and op validation / coercion (no database)."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from api.commands import position as pos  # noqa: E402
from api.commands.ops import (  # noqa: E402
    CoerceError, CommandError, coerce_value, parse_datetime, parse_money, parse_ops, parse_repeat, validate_rrule,
)

TZ = 'America/Denver'


# ---------------------------------------------------------------- position keys

def test_first_keys():
    assert pos.key_between(None, None) == 'a0'
    assert pos.key_between('a0', None) == 'a1'
    assert pos.key_between(None, 'a0') == 'Zz'
    assert pos.key_between('a0', 'a1') == 'a0V'
    assert pos.key_between('a0', 'a0V') == 'a0G'
    assert pos.key_between('az', None) == 'b00'


def test_seed_style_keys_are_valid():
    for k in ('a0', 'a1V', 'a4', 'a7'):
        pos.validate_key(k)
    assert pos.key_between('a1', 'a1V') < 'a1V'


@pytest.mark.parametrize('bad', ['', 'a', 'A', 'a00'[:2] + '0', 'b0', '!x'])
def test_invalid_keys(bad):
    with pytest.raises(ValueError):
        pos.validate_key(bad)


def test_rejects_unordered():
    with pytest.raises(ValueError):
        pos.key_between('a1', 'a0')
    with pytest.raises(ValueError):
        pos.key_between('a1', 'a1')


def test_byte_order_random_inserts():
    """Random inserts between neighbours keep strict byte order (collation "C")."""
    rnd = random.Random(7)
    keys = [pos.key_between(None, None)]
    for _ in range(500):
        i = rnd.randint(0, len(keys))
        a = keys[i - 1] if i > 0 else None
        b = keys[i] if i < len(keys) else None
        k = pos.key_between(a, b)
        assert (a is None or a < k) and (b is None or k < b)
        keys.insert(i, k)
    assert keys == sorted(keys)  # Python str order == byte order for ASCII
    assert keys == sorted(keys, key=lambda s: s.encode())


def test_repeated_insert_at_one_spot_grows_and_flags_rebalance():
    a, b = 'a0', 'a1'
    for _ in range(200):
        b = pos.key_between(a, b)
    assert pos.needs_rebalance(b)


def test_keys_between_and_even_keys():
    ks = pos.keys_between('a0', 'a1', 10)
    assert len(ks) == 10 and ks == sorted(ks) and len(set(ks)) == 10
    assert all('a0' < k < 'a1' for k in ks)
    ev = pos.even_keys(100)
    assert ev == sorted(ev) and len(set(ev)) == 100 and max(map(len, ev)) <= 3
    assert pos.keys_between(None, 'a0', 3) == sorted(pos.keys_between(None, 'a0', 3))


# ---------------------------------------------------------------- coercion

@pytest.mark.parametrize('raw,cents', [
    ('$1,200.50', 120050), ('35.83', 3583), ('12', 1200), ('-$5.00', -500), ('(4.29)', -429),
    ('$0.005', 1), (3583, 3583), (1200.0, 1200), (' 4.29 ', 429),
])
def test_money(raw, cents):
    assert parse_money(raw) == cents


@pytest.mark.parametrize('raw', ['three', '$', '12.3.4', True, 12.5, None])
def test_money_bad(raw):
    with pytest.raises(CoerceError):
        parse_money(raw)


def test_datetime_offsets_and_dst():
    assert parse_datetime('2026-11-20T17:41', TZ) == '2026-11-20T17:41:00-07:00'
    assert parse_datetime('2026-10-30T20:00', TZ) == '2026-10-30T20:00:00-06:00'
    assert parse_datetime('2026-11-20T17:41:00-07:00', TZ) == '2026-11-20T17:41:00-07:00'
    assert parse_datetime('2026-11-21', TZ) == '2026-11-21'
    # a wall time that doesn't exist moves forward by the gap (§11 #16)
    assert parse_datetime('2027-03-14T02:30', TZ) == '2027-03-14T03:30:00-06:00'
    # one that happens twice is the first one
    assert parse_datetime('2027-11-07T01:30', TZ) == '2027-11-07T01:30:00-06:00'


def test_field_types():
    sel = {'key': 'status', 'type': 'select', 'options': [{'id': 'to_buy', 'label': 'To buy'},
                                                          {'id': 'bought', 'label': 'Bought'}]}
    assert coerce_value(sel, 'bought', TZ) == 'bought'
    assert coerce_value(sel, 'to buy', TZ) == 'to_buy'
    with pytest.raises(CoerceError):
        coerce_value(sel, 'eaten', TZ)
    assert coerce_value({'type': 'number'}, '1,650', TZ) == 1650
    assert coerce_value({'type': 'number'}, '5.5', TZ) == 5.5
    assert coerce_value({'type': 'bool'}, 'true', TZ) is True
    assert coerce_value({'type': 'date'}, '2026-11-20T23:30:00-07:00', TZ) == '2026-11-20'
    assert coerce_value({'type': 'relation'}, 'new:trip', TZ) == ['new:trip']
    with pytest.raises(CoerceError):
        coerce_value({'type': 'formula'}, 3, TZ)
    assert coerce_value({'type': 'money'}, None, TZ) is None


def test_repeat():
    r = parse_repeat('FREQ=WEEKLY;BYDAY=FR', TZ, '2026-10-23T20:00:00-06:00')
    assert r == {'rule': 'FREQ=WEEKLY;BYDAY=FR', 'start': '2026-10-23T20:00', 'log': [], 'skip': []}
    with pytest.raises(CoerceError):
        validate_rrule('FREQ=YEARLY')
    with pytest.raises(CoerceError):
        validate_rrule('FREQ=WEEKLY;COUNT=3')
    assert validate_rrule('FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20261210T235959Z').endswith('UNTIL=20261210T235959')


# ---------------------------------------------------------------- op models

def test_clair_op_shape():
    [op] = parse_ops([{'op': 'insert', 'app': 'groceries', 'collection': 'trips', 'record_id': 'new:trip',
                       'fields': [{'key': 'store', 'value': 'Corner Market'}, {'key': 'total', 'value': '35.83'}],
                       'reason': 'from the receipt'}])
    assert op.fields == {'store': 'Corner Market', 'total': '35.83'}
    [keep] = parse_ops([{'op': 'update', 'app': 'workout', 'collection': 'sessions',
                         'record_id': '00000000-0000-0000-0000-000000000001', 'keep': True}])
    assert keep.op == 'keep'


@pytest.mark.parametrize('bad', [
    {'op': 'insert', 'fields': {'a': 1}},                                        # no collection
    {'op': 'update', 'record_id': 'new:x', 'fields': {'a': 1}},                  # temp name on update
    {'op': 'update', 'record_id': 'not-a-uuid', 'fields': {'a': 1}},
    {'op': 'delete'},                                                            # no record
    {'op': 'skip', 'record_id': '00000000-0000-0000-0000-000000000001'},         # no occurrence
    {'op': 'insert', 'app': 'a', 'collection': 'b', 'fields': {'_via': {}}},     # reserved key
    {'op': 'explode', 'record_id': '00000000-0000-0000-0000-000000000001'},
])
def test_bad_ops_are_422(bad):
    with pytest.raises(CommandError) as e:
        parse_ops([bad])
    assert e.value.status == 422 and e.value.body['issues']


def test_too_many_ops():
    with pytest.raises(CommandError):
        parse_ops([{'op': 'delete', 'record_id': '00000000-0000-0000-0000-000000000001'}] * 101)
