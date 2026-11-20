"""Round-trip the frontend's fixtures (web/src/mocks/fixtures) through the contract models.

A fixture that fails here is a contract difference: fix the fixture or the spec, never loosen
the model (spec/split.md §2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `api` imports as a package

from api import models as m  # noqa: E402

FIX = Path(__file__).resolve().parents[2] / 'web' / 'src' / 'mocks' / 'fixtures'


def load(name: str) -> Any:
    return json.loads((FIX / name).read_text())


def strip_none(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: strip_none(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [strip_none(v) for v in x]
    return x


def roundtrip(adapter: TypeAdapter, raw: Any) -> Any:
    obj = adapter.validate_python(raw)
    out = adapter.dump_python(obj, mode='json', by_alias=True, exclude_none=True)
    return obj, out


def assert_same(raw: Any, out: Any) -> None:
    # Defaults the server always sends (mode, flagged, kind, voice…) may be added on dump;
    # every key the fixture has must come back unchanged.
    def sub(a: Any, b: Any, path: str = '$') -> None:
        if isinstance(a, dict):
            assert isinstance(b, dict), path
            for k, v in a.items():
                if v is None:
                    continue
                assert k in b, f'{path}.{k} dropped'
                sub(v, b[k], f'{path}.{k}')
        elif isinstance(a, list):
            assert isinstance(b, list) and len(a) == len(b), path
            for i, (x, y) in enumerate(zip(a, b)):
                sub(x, y, f'{path}[{i}]')
        elif isinstance(a, float) and isinstance(b, (int, float)):
            assert a == b, path
        else:
            assert a == b, f'{path}: {a!r} != {b!r}'

    sub(raw, out)


def test_me():
    for name in ('me.json', 'me.after-clair.json'):
        raw = load(name)
        _, out = roundtrip(TypeAdapter(m.Me), raw)
        assert_same(raw, out)


def test_home():
    for name in ('home.json', 'home.before.json'):
        raw = load(name)
        home, out = roundtrip(TypeAdapter(m.Home), raw)
        assert_same(raw, out)
    assert home.greeting.startswith('Evening')


def test_apps():
    for name in ('apps.json', 'apps.before.json'):
        raw = load(name)
        _, out = roundtrip(TypeAdapter(list[m.Patch]), raw)
        assert_same(raw, out)


APP_FIXTURES = sorted(p.name for p in FIX.glob('app.*.json'))


@pytest.mark.parametrize('name', APP_FIXTURES)
def test_app_detail(name: str):
    raw = load(name)
    app, out = roundtrip(TypeAdapter(m.AppDetail), raw)
    assert_same(raw, out)
    if '*dated' in app.data:
        assert all(isinstance(r, m.Dated) for r in app.data['*dated'])
    for ref, rows in app.data.items():
        if ref != '*dated':
            assert all(isinstance(r, m.Record) for r in rows), ref


def test_budget_values():
    app = m.AppDetail.model_validate(load('app.budget.json'))
    assert app.values['b_left'].text == '$412'
    assert app.spec.face.status is True


COMMAND_FIXTURES = sorted(p.name for p in FIX.glob('confirm.*.json')) + sorted(p.name for p in FIX.glob('undo.*.json'))


@pytest.mark.parametrize('name', COMMAND_FIXTURES)
def test_command_result(name: str):
    raw = load(name)
    _, out = roundtrip(TypeAdapter(m.CommandResult), raw)
    assert_same(raw, out)


# Known fixture/spec mismatches, logged for spec/split.md §7. The model follows the spec.
MISMATCH = {
    'run.planner.r1.sample.json': 'source.kind "fixture": the sample mark is mode "fixture" (ui-tech-plan.md §4)',
    'run.planner.r4.sample.json': 'source.kind "fixture": the sample mark is mode "fixture" (ui-tech-plan.md §4)',
}
RUN_FIXTURES = [
    pytest.param(n, marks=pytest.mark.xfail(reason=MISMATCH[n], strict=True)) if n in MISMATCH else n
    for n in sorted(p.name for p in FIX.glob('run.*.json'))
]
EVENTS = TypeAdapter(list[m.ClairEvent])


@pytest.mark.parametrize('name', RUN_FIXTURES)
def test_clair_run(name: str):
    raw = [{k: v for k, v in e.items() if k != 'delay'} for e in load(name)]  # delay is the mock's replay timing
    events, out = roundtrip(EVENTS, raw)
    assert_same(raw, out)
    assert isinstance(events[-1], m.DoneEvent)


def test_change_sets():
    lunch = next(e for e in load('run.lunch.json') if e['event'] == 'proposal')['data']['change_set']
    cs, out = roundtrip(TypeAdapter(m.ChangeSet), lunch)
    assert_same(lunch, out)
    assert cs.actions.primary == 'Add to Budget'
    assert cs.deltas[0].before == '$412' and cs.deltas[0].after == '$400'

    planner = next(e for e in load('run.planner.r4.json') if e['event'] == 'proposal')['data']['change_set']
    cs = m.ChangeSet.model_validate(planner)
    kinds = [type(o).__name__ for o in cs.ops]
    assert kinds.count('KeepOp') == 1 and kinds.count('MoveOccurrenceOp') == 3
    assert cs.actions.primary == 'Add to 5 apps'

    card = TypeAdapter(m.Card).validate_python({'kind': 'change_set', 'change_set': lunch})
    assert isinstance(card, m.ChangeSetCard)


def test_connect():
    TypeAdapter(list[m.Connection]).validate_python(load('connect.json'))
    m.ConnectSyncResult.model_validate(load('connect.sync.json'))


def test_turn_requests():
    ta = TypeAdapter(m.ClairTurnRequest)
    assert isinstance(ta.validate_python({'text': 'Plan my training for next week', 'run_id': 'r1'}), m.NewTurn)
    assert isinstance(ta.validate_python({'fixture': 'planner'}), m.FixtureTurn)
    assert isinstance(
        ta.validate_python({'thread_id': 't', 'answer': {'question_id': 'q_1', 'choices': ['Butter']}}), m.AnswerTurn
    )


def test_unknown_keys_rejected():
    raw = load('home.json')
    raw['surprise'] = 1
    with pytest.raises(Exception):
        m.Home.model_validate(raw)


def test_openapi_is_current():
    from api.scripts.export_openapi import OUT, build

    assert json.loads(OUT.read_text()) == json.loads(json.dumps(build())), 'run: python -m api.scripts.export_openapi'
