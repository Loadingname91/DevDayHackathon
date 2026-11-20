"""Fractional position keys (backend.md §4).

A port of the `fractional-indexing` algorithm (David Greenspan, rocicorp/fractional-indexing), base 62,
sorted by byte. Postgres stores them with `collate "C"`, and Python's `str` comparison of ASCII is the
same order, so `a < b` here means `a` sorts before `b` in `ORDER BY position`.

A key is an integer part (head letter gives its length: 'a' → 2 chars, 'b' → 3, … 'A' → 27 chars,
'Z' → 2 chars on the negative side) plus a fraction with no trailing '0'. `key_between(None, None)` is
'a0'; 'a0' < 'a0V' < 'a1' < 'a2' …
"""
from __future__ import annotations

DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
REBALANCE_AT = 24          # a key longer than this makes the command service rewrite the parent (§4)
_SMALLEST_INT = 'A' + DIGITS[0] * 26


def _midpoint(a: str, b: str | None) -> str:
    """A string strictly between fractions a and b (b None = +infinity); neither may end in '0'."""
    zero = DIGITS[0]
    if b is not None and a >= b:
        raise ValueError(f'{a!r} >= {b!r}')
    if a[-1:] == zero or (b and b[-1:] == zero):
        raise ValueError('trailing zero')
    if b:
        n = 0
        while (a[n] if n < len(a) else zero) == b[n]:
            n += 1
        if n > 0:
            return b[:n] + _midpoint(a[n:], b[n:])
    digit_a = DIGITS.index(a[0]) if a else 0
    digit_b = DIGITS.index(b[0]) if b is not None else len(DIGITS)
    if digit_b - digit_a > 1:
        return DIGITS[int((digit_a + digit_b) / 2 + 0.5)]  # JS Math.round
    if b and len(b) > 1:
        return b[:1]
    return DIGITS[digit_a] + _midpoint(a[1:], None)


def _integer_length(head: str) -> int:
    if 'a' <= head <= 'z':
        return ord(head) - ord('a') + 2
    if 'A' <= head <= 'Z':
        return ord('Z') - ord(head) + 2
    raise ValueError(f'invalid order key head: {head!r}')


def _integer_part(key: str) -> str:
    n = _integer_length(key[0])
    if n > len(key):
        raise ValueError(f'invalid order key: {key!r}')
    return key[:n]


def validate_key(key: str) -> None:
    """Raise ValueError when `key` isn't a well-formed key."""
    if not key or key == _SMALLEST_INT:
        raise ValueError(f'invalid order key: {key!r}')
    i = _integer_part(key)
    if any(c not in DIGITS for c in key):
        raise ValueError(f'invalid order key: {key!r}')
    if key[len(i):][-1:] == DIGITS[0]:
        raise ValueError(f'invalid order key: {key!r}')


def is_valid(key: str | None) -> bool:
    try:
        validate_key(key or '')
        return True
    except ValueError:
        return False


def _increment_integer(x: str) -> str | None:
    head, digs = x[0], list(x[1:])
    carry = True
    for i in range(len(digs) - 1, -1, -1):
        if not carry:
            break
        d = DIGITS.index(digs[i]) + 1
        if d == len(DIGITS):
            digs[i] = DIGITS[0]
        else:
            digs[i] = DIGITS[d]
            carry = False
    if carry:
        if head == 'Z':
            return 'a' + DIGITS[0]
        if head == 'z':
            return None
        h = chr(ord(head) + 1)
        if h > 'a':
            digs.append(DIGITS[0])
        else:
            digs.pop()
        return h + ''.join(digs)
    return head + ''.join(digs)


def _decrement_integer(x: str) -> str | None:
    head, digs = x[0], list(x[1:])
    borrow = True
    for i in range(len(digs) - 1, -1, -1):
        if not borrow:
            break
        d = DIGITS.index(digs[i]) - 1
        if d == -1:
            digs[i] = DIGITS[-1]
        else:
            digs[i] = DIGITS[d]
            borrow = False
    if borrow:
        if head == 'a':
            return 'Z' + DIGITS[-1]
        if head == 'A':
            return None
        h = chr(ord(head) - 1)
        if h < 'Z':
            digs.append(DIGITS[-1])
        else:
            digs.pop()
        return h + ''.join(digs)
    return head + ''.join(digs)


def key_between(a: str | None, b: str | None) -> str:
    """A key strictly between a and b (either may be None for an open edge). Raises ValueError on bad input."""
    if a is not None:
        validate_key(a)
    if b is not None:
        validate_key(b)
    if a is not None and b is not None and a >= b:
        raise ValueError(f'{a!r} >= {b!r}')
    if a is None:
        if b is None:
            return 'a' + DIGITS[0]
        ib = _integer_part(b)
        fb = b[len(ib):]
        if ib == _SMALLEST_INT:
            return ib + _midpoint('', fb)
        if ib < b:
            return ib
        res = _decrement_integer(ib)
        if res is None:
            raise ValueError('cannot decrement any more')
        return res
    if b is None:
        ia = _integer_part(a)
        fa = a[len(ia):]
        i = _increment_integer(ia)
        return ia + _midpoint(fa, None) if i is None else i
    ia = _integer_part(a)
    fa = a[len(ia):]
    ib = _integer_part(b)
    fb = b[len(ib):]
    if ia == ib:
        return ia + _midpoint(fa, fb)
    i = _increment_integer(ia)
    if i is None:
        raise ValueError('cannot increment any more')
    if i < b:
        return i
    return ia + _midpoint(fa, None)


def keys_between(a: str | None, b: str | None, n: int) -> list[str]:
    """n ascending keys strictly between a and b, spread evenly (the rebalance helper)."""
    if n <= 0:
        return []
    if n == 1:
        return [key_between(a, b)]
    if b is None:
        out, k = [], a
        for _ in range(n):
            k = key_between(k, None)
            out.append(k)
        return out
    if a is None:
        out, k = [], b
        for _ in range(n):
            k = key_between(None, k)
            out.append(k)
        return list(reversed(out))
    mid = n // 2
    c = key_between(a, b)
    return keys_between(a, c, mid) + [c] + keys_between(c, b, n - mid - 1)


def even_keys(n: int) -> list[str]:
    """n short ascending keys for a parent rewritten from scratch ('a0', 'a1', …)."""
    return keys_between(None, None, n)


def needs_rebalance(key: str) -> bool:
    return len(key) > REBALANCE_AT
