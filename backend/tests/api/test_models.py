"""models.py mirrors docs/01_DATA_CONTRACT.md; checked against the real fixtures and real engine output."""
import copy
import json

import pytest
from pydantic import ValidationError

from app.engine.trace import trace
from app.models import PublicScenario, TraceResult
from tests.fixtures.mini import NAMES, build


@pytest.mark.parametrize("name", NAMES)
def test_fixture_scenarios_validate_and_round_trip(name):
    raw = build(name)
    model = PublicScenario.model_validate(raw)
    assert model.model_dump(by_alias=True, exclude_unset=True) == raw


@pytest.mark.parametrize("name", NAMES)
def test_engine_output_validates_and_round_trips(name):
    out = trace(build(name))
    model = TraceResult.model_validate(out)
    assert json.loads(model.model_dump_json(by_alias=True)) == json.loads(json.dumps(out))


def test_graph_edge_uses_from_key():
    out = trace(build("H1"))
    dumped = TraceResult.model_validate(out).model_dump(by_alias=True)
    edge = dumped["graph"]["edges"][0]
    assert "from" in edge and "from_" not in edge


@pytest.mark.parametrize("key", ["truth", "case_key", "true_path"])
def test_forbidden_keys_are_rejected(key):
    raw = build("H1")
    raw[key] = {"x": 1}
    with pytest.raises(ValidationError):
        PublicScenario.model_validate(raw)


def test_unknown_fields_and_bad_values_are_rejected():
    raw = build("H1")
    bad = copy.deepcopy(raw)
    bad["events"][0]["surprise"] = 1
    with pytest.raises(ValidationError):
        PublicScenario.model_validate(bad)
    bad = copy.deepcopy(raw)
    bad["events"][0]["ts"] = "2026-10-09 02:10:00"  # not ISO with Z
    with pytest.raises(ValidationError):
        PublicScenario.model_validate(bad)
    bad = copy.deepcopy(raw)
    bad["artifacts"][0]["sketches"]["phone"]["hashes"][0] = "XYZ"
    with pytest.raises(ValidationError):
        PublicScenario.model_validate(bad)
    bad = copy.deepcopy(raw)
    bad["contract_version"] = "2.0"
    with pytest.raises(ValidationError):
        PublicScenario.model_validate(bad)
