"""Op models and value coercion for the command service (backend.md §5 steps 3 and 4).

Pure: nothing here touches the database. `service.py` resolves ops against the workspace and calls
`coerce_value` per field.

One `Op` model serves both producers:

- Clair's `propose_changes` (clair-agent.md §10): `{op, app, collection, record_id?, fields: [{key, value}],
  occurrence?, reason?, reason_source?, keep?, also?, also_source?}`. Values arrive as strings and are coerced.
- Gestures (backend.md §10 `/records…`): `{op, collection_id | record_id, fields: {key: value},
  before_id?, after_id?, list?, occurrence?, minutes?, base_version?}`.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

OpKind = Literal['insert', 'update', 'delete', 'restore', 'complete', 'skip', 'move', 'move_occurrence', 'keep']
MAX_OPS = 100
TEMP_PREFIX = 'new:'
GOOGLE = 'google'


class CommandError(Exception):
    """A command the service refuses. `status` is the HTTP code, `body` the JSON body (§10 status codes)."""

    def __init__(self, status: int, body: dict[str, Any]):
        super().__init__(f'{status} {body}')
        self.status = status
        self.body = body


def invalid(issues: list[dict[str, Any]], error: str = 'invalid', status: int = 422) -> CommandError:
    return CommandError(status, {'error': error, 'issues': issues})


class FieldValue(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str
    value: Any = None


class Op(BaseModel):
    model_config = ConfigDict(extra='forbid')

    op: OpKind = 'update'
    # addressing: Clair names app and collection by key; gestures send ids
    app: str | None = None
    collection: str | None = None
    collection_id: UUID | None = None
    record_id: str | None = None                 # a UUID, or on insert a temp name "new:trip"
    fields: dict[str, Any] = Field(default_factory=dict)
    # dates of a repeat
    occurrence: date | None = None
    minutes: float | None = None
    # order
    before_id: UUID | None = None                # neighbour above (smaller key)
    after_id: UUID | None = None                 # neighbour below (larger key)
    add_at: Literal['start', 'end'] | None = None
    list: str | None = None                      # move: target list option (id or label)
    base_version: int | None = None              # PATCH /records/{id}
    # card text (Clair), kept on the stored op, never written to blocks
    reason: str | None = None
    reason_source: str | None = None
    keep: bool = False
    also: str | None = None
    also_source: str | None = None

    @field_validator('fields', mode='before')
    @classmethod
    def _pairs_to_dict(cls, v: Any) -> Any:
        if v is None:
            return {}
        if isinstance(v, list):
            out: dict[str, Any] = {}
            for item in v:
                fv = FieldValue.model_validate(item)
                out[fv.key] = fv.value
            return out
        return v

    @model_validator(mode='after')
    def _shape(self) -> 'Op':
        if self.keep:
            self.op = 'keep'
        if self.op == 'keep':
            return self
        for k in self.fields:
            if k.startswith('_'):
                raise ValueError(f'field {k!r}: keys starting with "_" are reserved')
        if self.op == 'insert':
            if self.collection_id is None and not (self.app and self.collection):
                raise ValueError('insert needs collection_id, or app and collection')
            if self.record_id is not None and not self.record_id.startswith(TEMP_PREFIX) and not _is_uuid(self.record_id):
                raise ValueError('insert record_id must be a temp name "new:<name>" or a UUID')
        else:
            if not self.record_id:
                raise ValueError(f'{self.op} needs record_id')
            if self.record_id.startswith(TEMP_PREFIX):
                raise ValueError(f'{self.op} cannot target a temp name; only inserts make them')
            if not _is_uuid(self.record_id):
                raise ValueError(f'record_id {self.record_id!r} is not a UUID')
        if self.op in ('skip', 'move_occurrence') and self.occurrence is None:
            raise ValueError(f'{self.op} needs occurrence')
        if self.op == 'move_occurrence' and not self.fields:
            raise ValueError('move_occurrence needs the new date in fields')
        if self.op == 'update' and not self.fields:
            raise ValueError('update needs fields')
        return self


def _is_uuid(s: str) -> bool:
    try:
        UUID(str(s))
        return True
    except ValueError:
        return False


def parse_ops(raw: list[Any]) -> list[Op]:
    """Structural validation (§5 step 3). Raises 422 {error, issues[]} listing every bad op."""
    if not isinstance(raw, list):
        raise invalid([{'problem': 'ops must be a list'}])
    if len(raw) > MAX_OPS:
        raise invalid([{'problem': f'at most {MAX_OPS} ops, got {len(raw)}'}])
    ops, issues = [], []
    for i, item in enumerate(raw):
        if isinstance(item, Op):
            ops.append(item)
            continue
        try:
            ops.append(Op.model_validate(item))
        except ValidationError as e:
            for err in e.errors():
                loc = '.'.join(str(p) for p in err['loc'])
                issues.append({'op': i, **({'field': loc} if loc else {}), 'problem': err['msg']})
    if issues:
        raise invalid(issues)
    return ops


def dump_ops(ops: list[Op]) -> list[dict[str, Any]]:
    return [o.model_dump(mode='json', exclude_none=True, exclude_defaults=True) | {'op': o.op} for o in ops]


# ---------------------------------------------------------------- coercion

class CoerceError(ValueError):
    pass


_MONEY_RE = re.compile(r'^[+-]?\d+(\.\d+)?$')
_RRULE_KEYS = {'FREQ', 'BYDAY', 'INTERVAL', 'UNTIL'}
_FREQS = {'DAILY', 'WEEKLY', 'MONTHLY'}
_DAYS = {'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'}


def parse_money(v: Any) -> int:
    """Integer cents. A string is dollars ("$1,200.50" → 120050, "35.83" → 3583, "(5.00)" → -500);
    an int is already cents; a float must be a whole number of cents."""
    if isinstance(v, bool):
        raise CoerceError('not an amount')
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if v != int(v):
            raise CoerceError('a number is read as cents; send dollars as a string ("35.83")')
        return int(v)
    if not isinstance(v, str):
        raise CoerceError('not an amount')
    s = v.strip().replace('−', '-')
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg, s = True, s[1:-1].strip()
    if s.startswith('-'):
        neg, s = not neg, s[1:].strip()
    s = s.replace('$', '').replace(',', '').replace(' ', '').replace('USD', '')
    if s.startswith('-'):
        neg, s = not neg, s[1:]
    if not _MONEY_RE.match(s):
        raise CoerceError(f'not an amount: {v!r}')
    try:
        cents = int((Decimal(s) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except InvalidOperation as e:
        raise CoerceError(f'not an amount: {v!r}') from e
    return -cents if neg else cents


def parse_number(v: Any) -> int | float:
    if isinstance(v, bool):
        raise CoerceError('not a number')
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip().replace(',', '').replace('−', '-')
        try:
            d = Decimal(s)
        except InvalidOperation as e:
            raise CoerceError(f'not a number: {v!r}') from e
        if not d.is_finite():
            raise CoerceError(f'not a number: {v!r}')
        return int(d) if d == d.to_integral_value() else float(d)
    raise CoerceError('not a number')


def parse_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and v in (0, 1):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ('true', 'yes', 'y', '1', 'on', 'done'):
            return True
        if s in ('false', 'no', 'n', '0', 'off', ''):
            return False
    raise CoerceError(f'not true or false: {v!r}')


def localize(naive: datetime, tz: str) -> datetime:
    """Wall time in the workspace zone. A time that doesn't exist moves forward by the gap; a time that
    happens twice is the first one (fold=0) (§11 #16)."""
    zone = ZoneInfo(tz)
    aware = naive.replace(tzinfo=zone, fold=0)
    return aware.astimezone(timezone.utc).astimezone(zone)


def _parse_dt(v: str) -> datetime | date:
    s = v.strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return date.fromisoformat(s)
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00') if s.endswith('Z') else s)
    except ValueError:
        pass
    from dateutil import parser as du
    try:
        return du.parse(s)
    except (ValueError, OverflowError) as e:
        raise CoerceError(f'not a date: {v!r}') from e


def parse_datetime(v: Any, tz: str, *, allow_date: bool = True) -> str:
    """ISO 8601 with offset. No offset: wall time in the workspace zone (§3). A bare day stays a day
    (`YYYY-MM-DD`) when allow_date, since collections like `due.at` take a date or a datetime."""
    if isinstance(v, datetime):
        dt = v
    elif isinstance(v, date):
        dt = v
    elif isinstance(v, str):
        dt = _parse_dt(v)
    else:
        raise CoerceError(f'not a date and time: {v!r}')
    if not isinstance(dt, datetime):
        if allow_date:
            return dt.isoformat()
        dt = datetime.combine(dt, time())
    if dt.tzinfo is None:
        dt = localize(dt, tz)
    return dt.isoformat()


def parse_date(v: Any, tz: str) -> str:
    if isinstance(v, datetime):
        dt: date | datetime = v
    elif isinstance(v, date):
        return v.isoformat()
    elif isinstance(v, str):
        dt = _parse_dt(v)
    else:
        raise CoerceError(f'not a date: {v!r}')
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            dt = dt.astimezone(ZoneInfo(tz))
        return dt.date().isoformat()
    return dt.isoformat()


def parse_select(v: Any, field: dict[str, Any]) -> str:
    """An option id. Accepts the id or the label (case-insensitive); options may be strings (old contract)."""
    opts = field.get('options') or []
    ids = []
    for o in opts:
        if isinstance(o, dict):
            ids.append((str(o.get('id')), str(o.get('label', o.get('id')))))
        else:
            ids.append((str(o), str(o)))
    if not isinstance(v, str):
        v = str(v)
    for oid, _ in ids:
        if v == oid:
            return oid
    low = v.strip().casefold()
    for oid, label in ids:
        if label.strip().casefold() == low or oid.casefold() == low:
            return oid
    known = ', '.join(f'{oid} ({label})' if oid != label else oid for oid, label in ids)
    raise CoerceError(f'not an option: {v!r}; options: {known}')


def parse_relation(v: Any) -> list[str]:
    """A list of record ids (UUIDs or temp names). Accepts a list, one id, a JSON array string or a
    comma-separated string."""
    if isinstance(v, str):
        s = v.strip()
        if s.startswith('['):
            try:
                v = json.loads(s)
            except json.JSONDecodeError as e:
                raise CoerceError(f'not a list of records: {v!r}') from e
        else:
            v = [p.strip() for p in s.split(',') if p.strip()]
    if isinstance(v, UUID):
        v = [v]
    if not isinstance(v, list):
        raise CoerceError('not a list of records')
    out = []
    for x in v:
        x = str(x)
        if not (x.startswith(TEMP_PREFIX) or _is_uuid(x)):
            raise CoerceError(f'not a record id: {x!r}')
        out.append(x)
    return out


def validate_rrule(rule: str) -> str:
    """The RRULE subset of §3: FREQ=DAILY|WEEKLY|MONTHLY, BYDAY, INTERVAL, UNTIL."""
    rule = rule.strip()
    if rule.upper().startswith('RRULE:'):
        rule = rule[6:]
    parts = {}
    for part in rule.split(';'):
        if not part:
            continue
        if '=' not in part:
            raise CoerceError(f'bad repeat rule part: {part!r}')
        k, val = part.split('=', 1)
        k = k.strip().upper()
        if k not in _RRULE_KEYS:
            raise CoerceError(f'repeat rule key {k} is not supported (FREQ, BYDAY, INTERVAL, UNTIL)')
        parts[k] = val.strip().upper()
    if parts.get('FREQ') not in _FREQS:
        raise CoerceError('repeat rule needs FREQ=DAILY, WEEKLY or MONTHLY')
    if 'BYDAY' in parts:
        for d in parts['BYDAY'].split(','):
            if d[-2:] not in _DAYS:
                raise CoerceError(f'bad BYDAY {d!r}')
    if 'INTERVAL' in parts and not parts['INTERVAL'].isdigit():
        raise CoerceError('INTERVAL must be a whole number')
    if 'UNTIL' in parts:
        u = parts['UNTIL'].rstrip('Z')
        if not re.fullmatch(r'\d{8}(T\d{6})?', u):
            raise CoerceError('UNTIL must be YYYYMMDD or YYYYMMDDTHHMMSS')
        parts['UNTIL'] = u
    return ';'.join(f'{k}={parts[k]}' for k in ('FREQ', 'INTERVAL', 'BYDAY', 'UNTIL') if k in parts)


def wall_start(value: Any, tz: str) -> str:
    """A repeat's `start`: local wall time with no offset (`2026-10-23T20:00`)."""
    if isinstance(value, str):
        dt = _parse_dt(value)
    else:
        dt = value
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            dt = dt.astimezone(ZoneInfo(tz))
        return dt.replace(tzinfo=None).isoformat(timespec='minutes')
    if isinstance(dt, date):
        return datetime.combine(dt, time()).isoformat(timespec='minutes')
    raise CoerceError('repeat needs a start date')


def parse_repeat(v: Any, tz: str, date_value: Any = None) -> dict[str, Any] | None:
    """`{rule, start, log, skip}`. A plain rule string takes `start` from the record's date field."""
    if v is None or v == '':
        return None
    if isinstance(v, str):
        s = v.strip()
        if s.startswith('{'):
            try:
                v = json.loads(s)
            except json.JSONDecodeError as e:
                raise CoerceError('bad repeat value') from e
        else:
            if date_value is None:
                raise CoerceError('a repeat rule needs the record\'s date to start from')
            return {'rule': validate_rrule(s), 'start': wall_start(date_value, tz), 'log': [], 'skip': []}
    if not isinstance(v, dict) or 'rule' not in v:
        raise CoerceError('repeat must be a rule string or {rule, start, log, skip}')
    start = v.get('start') if v.get('start') is not None else date_value
    if start is None:
        raise CoerceError('repeat needs a start')
    out = {
        'rule': validate_rrule(str(v['rule'])),
        'start': wall_start(start, tz),
        'log': sorted({parse_date(d, tz) for d in (v.get('log') or [])}),
        'skip': sorted({parse_date(d, tz) for d in (v.get('skip') or [])}),
    }
    return out


def coerce_value(field: dict[str, Any], v: Any, tz: str, *, date_value: Any = None) -> Any:
    """Coerce one value to its field's type (§5 step 4). None clears the field. Raises CoerceError."""
    t = field.get('type', 'text')
    if v is None:
        return None
    if t == 'formula':
        raise CoerceError('a formula field is computed, never written')
    if isinstance(v, str) and v.strip() == '' and t not in ('text',):
        return None
    if t == 'text':
        return v if isinstance(v, str) else (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
    if t == 'money':
        return parse_money(v)
    if t == 'number':
        return parse_number(v)
    if t == 'bool':
        return parse_bool(v)
    if t == 'date':
        return parse_date(v, tz)
    if t == 'datetime':
        return parse_datetime(v, tz)
    if t == 'select':
        return parse_select(v, field)
    if t == 'relation':
        return parse_relation(v)
    if t == 'repeat':
        return parse_repeat(v, tz, date_value)
    return v  # file and anything newer: stored as sent


def is_from_google(props: dict[str, Any] | None) -> bool:
    return bool(props) and props.get('source') == GOOGLE
