import json
import types

from app import main
from app.privacy import audit
from tests.fixtures.mini import build

BAD = ('"truth"', '"case_key"', '"true_path"')


def err(r, status, code):
    assert r.status_code == status, r.text
    body = r.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code and body["error"]["message"]


def test_get_summary(client):
    r = client.get("/api/scenario/scn:H1")
    assert r.status_code == 200
    s = r.json()
    assert s["id"] == "scn:H1" and s["contract_version"] == "1.0" and s["archetype"] == "A1"
    assert s["counts"] == {"actors": 5, "locations": 9, "datasets": 1, "events": len(build("H1")["events"]),
                           "artifacts": 2}
    assert s["leak_sample"]["found_at"] == "ext:telegram-leak-channel"
    assert s["discovery"]["leak_message_id"] == 1
    assert len(s["actors"]) == 5 and len(s["locations"]) == 9
    assert not any(b in r.text for b in BAD)
    assert "events" not in s and "artifacts" not in s  # summary, not the scenario


def test_get_full_scenario_has_no_truth_and_matches_input(client):
    r = client.get("/api/scenario/scn:H1", params={"full": "true"})
    assert r.status_code == 200
    assert r.json() == build("H1")
    assert not any(b in r.text for b in BAD)


def test_unknown_scenario_is_404_with_error_shape(client):
    err(client.get("/api/scenario/scn:nope"), 404, "not_found")
    err(client.post("/api/trace", json={"scenario_id": "scn:nope"}), 404, "not_found")
    err(client.post("/api/leak/export", json={"scenario_id": "scn:nope", "message_id": 1}), 404, "not_found")
    err(client.get("/api/does-not-exist"), 404, "not_found")


def test_generate_validates_the_body(client):
    ok = {"archetype": "A1", "seed": 42, "log_loss": 0.4, "canary_mode": False, "scale": "demo"}
    for bad in ({**ok, "log_loss": 0.9}, {**ok, "log_loss": -0.1}, {**ok, "archetype": "A9"},
                {**ok, "scale": "huge"}, {k: v for k, v in ok.items() if k != "seed"}, {**ok, "extra": 1}):
        err(client.post("/api/scenario/generate", json=bad), 400, "bad_request")
    assert audit.entries() == []


def test_generate_reports_not_ready_until_the_simulator_exists(client):
    r = client.post("/api/scenario/generate", json={"archetype": "A1", "seed": 42, "log_loss": 0.4,
                                                    "canary_mode": False, "scale": "demo"})
    err(r, 409, "not_ready")
    assert audit.entries() == []


def test_generate_with_a_simulator_registers_and_audits(client, monkeypatch):
    calls = []

    def fake_generate(archetype, seed, log_loss, canary_mode, scale):
        calls.append((archetype, seed, log_loss, canary_mode, scale))
        pub = build("H4")
        pub["id"], pub["seed"] = "scn:A1-7-L12", seed
        pub["params"] = {"log_loss": log_loss, "canary_mode": canary_mode, "scale": scale}
        return types.SimpleNamespace(public=pub, truth={"origin_artifact": "art:E1"}, private=object())

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(generate_scenario=fake_generate))
    r = client.post("/api/scenario/generate", json={"archetype": "A1", "seed": 7, "log_loss": 0.123456,
                                                    "canary_mode": False, "scale": "demo"})
    assert r.status_code == 200, r.text
    assert calls == [("A1", 7, 0.123456, False, "demo")]
    s = r.json()
    assert s["id"] == "scn:A1-7-L12" and s["params"]["log_loss"] == 0.1235  # 4 decimals in responses
    assert "truth" not in r.text and "origin_artifact" not in r.text
    assert client.get("/api/scenario/scn:A1-7-L12").status_code == 200
    e = audit.entries()
    assert len(e) == 1 and e[0]["action"] == "scenario_generate" and e[0]["scenario_id"] == "scn:A1-7-L12"


def test_export_returns_masked_leak_and_file_info(client):
    r = client.post("/api/leak/export", json={"scenario_id": "scn:H1", "message_id": 1})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["file"] == {"name": "mini_leak.csv", "size_bytes": 1828 * 60}
    assert body["leak_sample"]["id"] == "leak:H1"
    e = audit.entries()
    assert len(e) == 1 and e[0]["action"] == "telegram_export" and e[0]["scenario_id"] == "scn:H1"


def test_export_rejects_a_message_without_the_file(client):
    err(client.post("/api/leak/export", json={"scenario_id": "scn:H1", "message_id": 99}), 404, "not_found")
    assert audit.entries() == []


def test_export_never_returns_an_unmasked_preview(client):
    pub = build("H1")
    pub["id"] = "scn:RAW"
    pub["leak_sample"]["masked_preview"] = [{"email": "ravi.menon@example.com", "phone": "+91-9876543221",
                                            "full_name": "Ravi Menon", "policy_no": "r***"}]
    main.register(pub)
    r = client.post("/api/leak/export", json={"scenario_id": "scn:RAW", "message_id": 1})
    row = r.json()["leak_sample"]["masked_preview"][0]
    assert row == {"email": "r***@example.com", "phone": "+91-98******21", "full_name": "R. M.",
                   "policy_no": "r***"}
    assert "ravi.menon" not in r.text and "9876543221" not in r.text


def test_summary_preview_is_masked_too(client):
    pub = build("H1")
    pub["id"] = "scn:RAW2"
    pub["leak_sample"]["masked_preview"] = [{"email": "ravi.menon@example.com"}]
    main.register(pub)
    r = client.get("/api/scenario/scn:RAW2")
    assert r.json()["leak_sample"]["masked_preview"] == [{"email": "r***@example.com"}]


def test_trace_returns_a_valid_trace_result(client):
    r = client.post("/api/trace", json={"scenario_id": "scn:H1"})
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["contract_version"] == "1.0" and t["scenario_id"] == "scn:H1" and t["trace_id"] == "trc:H1"
    assert t["origin_candidates"][0]["artifact_id"] == "art:E1"
    assert t["hypotheses"][0]["actors"] == ["act:ann"]
    assert "from" in t["graph"]["edges"][0]
    assert not any(b in r.text for b in BAD)
    e = audit.entries()
    assert len(e) == 1 and e[0]["action"] == "trace" and e[0]["object_id"] == "trc:H1"


def test_trace_top_k(client):
    assert len(client.post("/api/trace", json={"scenario_id": "scn:H2", "top_k": 2}).json()["hypotheses"]) == 2
    err(client.post("/api/trace", json={"scenario_id": "scn:H2", "top_k": 0}), 400, "bad_request")


def test_trace_floats_are_rounded_to_four_decimals(client):
    t = client.post("/api/trace", json={"scenario_id": "scn:H2"}).json()

    def floats(o):
        if isinstance(o, float):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from floats(v)
        elif isinstance(o, list):
            for v in o:
                yield from floats(v)

    assert all(f == round(f, 4) for f in floats(t))


def test_engine_failure_is_a_500_engine_error(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("kaput")

    monkeypatch.setattr(main, "run_trace", boom)
    err(client.post("/api/trace", json={"scenario_id": "scn:H1"}), 500, "engine_error")
    assert audit.entries() == []


def test_trace_is_deterministic_over_http(client):
    a = client.post("/api/trace", json={"scenario_id": "scn:H6"}).text
    b = client.post("/api/trace", json={"scenario_id": "scn:H6"}).text
    assert a == b and json.loads(a)["origin_pinned"] is True


def test_api_accepts_a_scenario_with_a_null_object_permission_change(client):
    from tests.api.test_models import permission_change_with_null_object
    pub = permission_change_with_null_object(build("H1"))
    pub["id"] = "scn:PERM"
    main.register(pub)
    assert client.get("/api/scenario/scn:PERM").status_code == 200
    r = client.post("/api/trace", json={"scenario_id": "scn:PERM"})
    assert r.status_code == 200, r.text
    assert client.get("/api/scenario/scn:PERM", params={"full": "true"}).json() == pub


def test_startup_warms_the_simulator_cache_in_a_background_thread(monkeypatch):
    import threading
    import time
    called, done = [], threading.Event()

    def warm(scale):
        called.append((scale, threading.current_thread() is not threading.main_thread()))
        if len(called) == 2:
            done.set()

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=lambda *a: None, reveal_value=None, get_bundle=lambda i: None, inject_leak=None,
        canary_alert=None, warm_cache=warm))
    t = time.time()
    from fastapi.testclient import TestClient
    with TestClient(main.app):
        assert time.time() - t < 5  # startup does not wait for the cache
        assert done.wait(5)
    assert sorted(c[0] for c in called) == ["bench", "demo"] and all(c[1] for c in called)
    assert main.STORE == {} or "scn:H1" not in main.STORE  # fixtures are not loaded when a simulator exists
