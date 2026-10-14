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


def permission_change_with_null_object(raw):
    raw = copy.deepcopy(raw)
    raw["events"].append({
        "id": "evt:P00001", "ts": "2026-10-05T09:00:00Z", "seq": 99999, "source": "src:db", "actor": "act:etl",
        "action": "permission_change", "object": None, "from_loc": None, "to_loc": None, "rows": 0,
        "meta": {"grantee": "act:ann", "scope": "sys:wh", "change": "grant"}})
    raw["events"].sort(key=lambda e: e["ts"])
    return raw


def test_permission_change_may_have_a_null_object():
    raw = permission_change_with_null_object(build("H1"))
    model = PublicScenario.model_validate(raw)
    assert model.model_dump(by_alias=True, exclude_unset=True) == raw
    assert any(e.object is None and e.action == "permission_change" for e in model.events)


def test_a_null_object_on_any_event_does_not_crash_the_engine():
    raw = build("H1")
    raw["events"][0]["object"] = None
    # the model accepts null for any action (the contract names permission_change); nothing downstream may crash
    PublicScenario.model_validate(raw)
    assert trace(raw)["origin_candidates"]


def test_null_object_flows_through_engine_and_baselines():
    from app.bench import baselines
    raw = permission_change_with_null_object(build("H1"))
    TraceResult.model_validate(trace(raw))
    assert baselines.last_accessor(raw)[0] == "act:ann"  # the null-object grant is simply not a data access
