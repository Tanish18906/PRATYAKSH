import pytest

from app.sim.generator import canary_alert, generate_scenario, reveal_value
from scripts.validate import validate_public_scenario


@pytest.mark.parametrize("archetype", ("A1", "A2", "A3", "A4", "A5"))
def test_canaries_pin_origin_and_reveal(archetype):
    from app.common.sketch import h64, normalize

    bundle = generate_scenario(archetype, 2, 0.0, True, "bench")
    public = bundle.public
    validate_public_scenario(public)
    assert public["id"].endswith("-C-b")
    assert public["params"]["canary_mode"] is True
    assert len(public["canary_registry"]) == 3 * len(public["artifacts"])
    artifacts = {artifact["id"]: artifact for artifact in public["artifacts"]}
    assert all(set(entry["hashes"]) <= set(artifacts[entry["export_id"]]["columns"])
               for entry in public["canary_registry"])
    origin = next(artifact for artifact in public["artifacts"]
                  if artifact["id"] == bundle.truth["origin_artifact"])
    assert public["leak_sample"]["canary_hits"] == origin["canary_ids"]
    assert public["leak_sample"]["row_count"] == len(bundle.private.indices) + 3
    for canary_id in origin["canary_ids"]:
        alert = canary_alert(bundle, canary_id)
        assert alert["canary_id"] == canary_id
        assert alert["export_id"] == origin["id"]
        assert alert["ts"] == public["now_ts"]
        assert "canary" in alert["message"].lower()
    registry = {entry["id"]: entry for entry in public["canary_registry"]}
    for offset, canary_id in enumerate(origin["canary_ids"]):
        for column in public["leak_sample"]["sketches"]:
            value = reveal_value(bundle, len(bundle.private.indices) + offset, column)
            assert f"{h64(bundle.private.case_key, normalize(column, value)):016x}" == (
                registry[canary_id]["hashes"][column])
    assert reveal_value(bundle, len(bundle.private.indices), "email").startswith("canary.")


def test_canary_alert_rejects_off_or_unknown():
    plain = generate_scenario("A1", 2, 0.0, False, "bench")
    with pytest.raises(ValueError):
        canary_alert(plain, "can:E1-1")
    canary = generate_scenario("A1", 2, 0.0, True, "bench")
    with pytest.raises(KeyError):
        canary_alert(canary, "can:missing")
