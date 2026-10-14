import json

import pytest

from app.sim.generator import generate_scenario
from app.sim.styles import format_profile
from scripts.validate import validate_public_scenario


@pytest.mark.parametrize("archetype", ("A2", "A3", "A4", "A5"))
def test_phase3_archetype_path(archetype):
    bundle = generate_scenario(archetype, 18, 0.0, False, "bench")
    public, truth = bundle.public, bundle.truth
    validate_public_scenario(public)
    assert public["archetype"] == archetype
    assert truth["origin_artifact"] in {artifact["id"] for artifact in public["artifacts"]}
    origin = next(artifact for artifact in public["artifacts"]
                  if artifact["id"] == truth["origin_artifact"])
    assert set(public["leak_sample"]["columns"]) <= set(origin["columns"])
    assert truth["true_path"][-1]["event_id"] is None
    assert truth["true_path"][-1]["to_loc"] == "ext:telegram-leak-channel"
    assert all(hop["event_id"] in {event["id"] for event in public["events"]}
               for hop in truth["true_path"][:-1])
    assert json.dumps(public, sort_keys=True) == json.dumps(
        generate_scenario(archetype, 18, 0.0, False, "bench").public, sort_keys=True)
    if archetype == "A2":
        critical = next(event for event in public["events"]
                        if event["id"] == truth["true_path"][-2]["event_id"])
        assert critical["actor"] == "act:partner-api-key-7"
        assert critical["action"] == "api_call"
        assert critical["meta"]["client_ip"].startswith("203.0.113.")
        assert critical["rows"] > 0
        assert truth["true_path"][-2]["to_loc"] == "ext:unknown-host"
    elif archetype == "A3":
        artifact = next(artifact for artifact in public["artifacts"]
                        if artifact["id"] == truth["origin_artifact"])
        assert artifact["dataset"] == "ds:customers"
        assert artifact["location"] == "sys:partner-sftp"
        assert artifact["columns"] == ["full_name", "email", "phone", "city", "created_at"]
        assert public["leak_sample"]["format_profile"] in (
            format_profile("MARKETING", public["leak_sample"]["columns"]),
            format_profile("NOTEBOOK", public["leak_sample"]["columns"]))
        assert any(event["action"] == "permission_change" and
                   event["meta"].get("grantee") == truth["true_actors"][0] and
                   event["meta"].get("scope") == "sys:customer-db"
                   for event in public["events"])
        assert truth["true_path"][-2]["to_loc"] == "ext:vendor-nimbus"
    elif archetype == "A4":
        assert "act:anonymous" in {actor["id"] for actor in public["actors"]}
        assert truth["true_path"][-2]["to_loc"] == "sys:object-store"
        assert any(event["action"] == "permission_change" and
                   event["meta"].get("grantee") == "act:anonymous" and
                   event["meta"].get("scope") == "sys:object-store"
                   for event in public["events"])
    else:
        assert truth["true_path"][-2]["to_loc"].startswith("ep:")
        assert "act:backup-svc" in truth["true_actors"]
        reads = [event for event in public["events"] if event["action"] == "read" and
                 event["object"] == truth["origin_artifact"]]
        assert len(reads) >= 2 and reads[0]["rows"] == reads[1]["rows"]
