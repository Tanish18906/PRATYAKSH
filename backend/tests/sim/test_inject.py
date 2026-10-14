import pytest

from app.sim.generator import generate_scenario
from app.sim.inject import inject_leak
from scripts.validate import validate_public_scenario


def test_inject_every_actor():
    base = generate_scenario("A1", 5, 0.0, False, "bench")
    for actor in base.public["actors"]:
        injected = inject_leak(base, actor["id"])
        validate_public_scenario(injected.public)
        assert injected.public["id"].startswith("scn:INJ-5-")
        assert injected.public["params"] == base.public["params"]
        assert actor["id"] in injected.truth["true_actors"]
        assert injected.truth["true_path"][-1]["event_id"] is None
        if actor["id"] == "act:backup-svc":
            assert injected.public["archetype"] == "A5"
        elif actor["kind"] == "service":
            assert injected.public["archetype"] == "A2"
        elif "sys:bi-warehouse" in actor["access"]:
            assert injected.public["archetype"] == "A1"
        elif "sys:partner-sftp" in actor["access"]:
            assert injected.public["archetype"] == "A3"
        else:
            assert injected.public["archetype"] == "A1"
            assert any(event["action"] == "permission_change" and
                       event["meta"].get("grantee") == actor["id"] and
                       event["meta"].get("scope") == "sys:bi-warehouse"
                       for event in injected.public["events"])


def test_inject_rejects_unknown_actor():
    base = generate_scenario("A1", 5, 0.0, False, "bench")
    with pytest.raises(ValueError):
        inject_leak(base, "act:missing")
