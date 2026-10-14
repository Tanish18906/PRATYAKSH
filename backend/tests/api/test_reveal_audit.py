import json
import time
import types

import pytest

from app import main
from app.models import AuditEntry
from app.privacy import audit
from tests.fixtures.mini import build

REASON = "ticket INC-4411 legal review"


def err(r, status, code):
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


def body(**kw):
    b = {"scenario_id": "scn:H1", "object": "leak_sample", "row_index": 0, "field": "phone", "reason": REASON}
    b.update(kw)
    return b


@pytest.fixture
def with_sim(client, monkeypatch):
    """A fake simulator whose private store reveals RAW values; scenario scn:H1 gets a bundle."""
    calls = []

    def reveal_value(bundle, row_index, field):
        calls.append((row_index, field))
        return f"RAW<{field}:{row_index}>"

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=None, reveal_value=reveal_value, get_bundle=lambda i: None))
    main.register(build("H1"), bundle=object())
    client.calls = calls
    return client


def test_reveal_requires_a_reason_of_at_least_8_characters(with_sim):
    c = with_sim
    no_reason = body()
    del no_reason["reason"]
    err(c.post("/api/reveal", json=no_reason), 400, "reason_required")
    err(c.post("/api/reveal", json=body(reason="")), 400, "reason_required")
    err(c.post("/api/reveal", json=body(reason="short")), 400, "reason_required")
    err(c.post("/api/reveal", json=body(reason="  1234567  ")), 400, "reason_required")  # 7 after trimming
    assert c.calls == [] and audit.entries() == []


def test_reveal_returns_value_and_writes_one_audit_entry(with_sim):
    r = with_sim.post("/api/reveal", json=body(row_index=3, field="policy_no"))
    assert r.status_code == 200, r.text
    out = r.json()
    assert out == {"value": "RAW<policy_no:3>", "audit_id": "aud:0001"}
    assert r.headers["cache-control"] == "no-store"
    e = audit.entries()
    assert len(e) == 1
    assert (e[0]["action"], e[0]["scenario_id"], e[0]["field"], e[0]["reason"]) == (
        "reveal", "scn:H1", "policy_no", REASON)
    assert e[0]["object_id"] == "leak:H1#3"
    AuditEntry.model_validate(e[0])


def test_audit_endpoint_lists_the_reveal(with_sim):
    c = with_sim
    c.post("/api/trace", json={"scenario_id": "scn:H1"})
    c.post("/api/reveal", json=body())
    all_ = c.get("/api/audit").json()
    assert set(all_) == {"entries"} and [e["action"] for e in all_["entries"]] == ["trace", "reveal"]
    for e in all_["entries"]:
        AuditEntry.model_validate(e)
    assert [e["action"] for e in c.get("/api/audit", params={"scenario_id": "scn:H1"}).json()["entries"]] == [
        "trace", "reveal"]
    assert c.get("/api/audit", params={"scenario_id": "scn:other"}).json() == {"entries": []}


def test_each_action_adds_exactly_one_entry(with_sim):
    c = with_sim
    c.post("/api/leak/export", json={"scenario_id": "scn:H1", "message_id": 1})
    c.post("/api/trace", json={"scenario_id": "scn:H1"})
    c.post("/api/reveal", json=body())
    assert [e["action"] for e in audit.entries()] == ["telegram_export", "trace", "reveal"]
    lines = audit.PATH.read_text().splitlines()
    assert [json.loads(x)["id"] for x in lines] == ["aud:0001", "aud:0002", "aud:0003"]


def test_bad_target_is_rejected_without_audit(with_sim):
    c = with_sim
    err(c.post("/api/reveal", json=body(field="ssn")), 400, "bad_request")
    err(c.post("/api/reveal", json=body(row_index=1828)), 400, "bad_request")  # row_count is 1828
    err(c.post("/api/reveal", json=body(row_index=-1)), 400, "bad_request")
    err(c.post("/api/reveal", json=body(object="artifact")), 400, "bad_request")
    err(c.post("/api/reveal", json=body(scenario_id="scn:nope")), 404, "not_found")
    assert c.calls == [] and audit.entries() == []


def test_reveal_last_valid_row_index(with_sim):
    assert with_sim.post("/api/reveal", json=body(row_index=1827)).status_code == 200


def test_reveal_is_not_ready_without_a_private_store(client):
    err(client.post("/api/reveal", json=body()), 409, "not_ready")  # fixtures have no private store
    assert audit.entries() == []


def test_failing_simulator_reveal_is_a_500_without_audit(with_sim, monkeypatch):
    def boom(bundle, row_index, field):
        raise RuntimeError("no such row")

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=None, reveal_value=boom, get_bundle=lambda i: None))
    err(with_sim.post("/api/reveal", json=body()), 500, "engine_error")
    assert audit.entries() == []


def test_revealed_value_is_not_returned_by_any_other_endpoint(with_sim):
    c = with_sim
    c.post("/api/reveal", json=body(row_index=2, field="email"))
    for url in ("/api/scenario/scn:H1", "/api/scenario/scn:H1?full=true", "/api/audit"):
        assert "RAW<" not in c.get(url).text
    assert "RAW<" not in c.post("/api/trace", json={"scenario_id": "scn:H1"}).text


def scaled(n_users=40, n_events=3000):
    sc = build("H2")
    for i in range(n_users):
        u, ep = f"act:u{i}", f"ep:u{i}"
        sc["actors"].append({"id": u, "kind": "user", "name": f"U{i}", "role": "analyst", "team": "t",
                             "access": ["sys:wh", "sys:bucket", "sys:sftp", ep]})
        sc["locations"].append({"id": ep, "kind": "endpoint", "name": f"u{i}", "owner_actor": u,
                                "monitored": False, "log_source": None, "egress_capable": True})
    users = [a["id"] for a in sc["actors"]]
    for k in range(n_events):
        sc["events"].append({
            "id": f"evt:9{k:06d}", "ts": f"2026-09-{1 + k % 28:02d}T{9 + k % 8:02d}:{k % 60:02d}:00Z",
            "seq": 100000 + k, "source": "src:wh", "actor": users[k % len(users)], "action": "query",
            "object": "ds:cust", "from_loc": "sys:wh", "to_loc": None, "rows": 50 + (k * 7) % 300, "meta": {}})
    sc["events"].sort(key=lambda e: e["ts"])
    sc["id"] = "scn:BIG"
    return sc


def test_trace_over_http_is_under_three_seconds_at_demo_scale(client):
    main.register(scaled())
    t = time.perf_counter()
    r = client.post("/api/trace", json={"scenario_id": "scn:BIG"})
    dt = time.perf_counter() - t
    assert r.status_code == 200, r.text
    assert len(client.get("/api/scenario/scn:BIG", params={"full": "true"}).json()["events"]) > 3000
    assert dt < 3.0, dt
