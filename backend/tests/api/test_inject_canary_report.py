import copy
import re
import types

import pytest

from app import main
from app.privacy import audit
from tests.fixtures.mini import build

LEGAL = "Verify current legal timelines with counsel."
EMAIL = re.compile(r"[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def err(r, status, code):
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


# ---------------------------------------------------------------- inject
@pytest.fixture
def with_inject(client, monkeypatch):
    calls = []

    def inject_leak(bundle, actor_id):
        calls.append(actor_id)
        pub = build("H2")
        pub["id"] = f"scn:INJ-0-{actor_id.split(':')[1]}-L0"
        return types.SimpleNamespace(public=pub, truth={"true_actors": [actor_id]}, private=object())

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=None, reveal_value=None, get_bundle=lambda i: None, inject_leak=inject_leak,
        canary_alert=None))
    main.register(build("H1"), bundle=object())
    client.calls = calls
    return client


def test_inject_creates_a_new_scenario_and_audits(with_inject):
    r = with_inject.post("/api/inject", json={"base_scenario_id": "scn:H1", "actor": "act:bob"})
    assert r.status_code == 200, r.text
    assert r.json()["id"] == "scn:INJ-0-bob-L0" and "truth" not in r.text
    assert with_inject.calls == ["act:bob"]
    assert with_inject.post("/api/trace", json={"scenario_id": "scn:INJ-0-bob-L0"}).status_code == 200
    e = [x for x in audit.entries() if x["action"] == "inject"]
    assert len(e) == 1 and e[0]["scenario_id"] == "scn:INJ-0-bob-L0" and e[0]["object_id"] == "act:bob"


def test_inject_rejections_write_no_audit(with_inject, client):
    c = with_inject
    err(c.post("/api/inject", json={"base_scenario_id": "scn:H1", "actor": "act:ghost"}), 400, "bad_request")
    err(c.post("/api/inject", json={"base_scenario_id": "scn:nope", "actor": "act:bob"}), 404, "not_found")
    err(c.post("/api/inject", json={"base_scenario_id": "scn:H1"}), 400, "bad_request")
    assert audit.entries() == [] and c.calls == []


def test_inject_is_not_ready_without_a_simulator_bundle(client):
    err(client.post("/api/inject", json={"base_scenario_id": "scn:H1", "actor": "act:bob"}), 409, "not_ready")
    assert audit.entries() == []


def test_regenerating_with_another_log_loss_makes_a_new_scenario(client, monkeypatch):
    def gen(archetype, seed, log_loss, canary_mode, scale):
        pub = build("H1")
        pub["id"] = f"scn:{archetype}-{seed}-L{round(log_loss * 100)}"
        pub["params"] = {"log_loss": log_loss, "canary_mode": canary_mode, "scale": scale}
        return types.SimpleNamespace(public=pub, truth={}, private=object())

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=gen, reveal_value=None, get_bundle=lambda i: None))
    body = {"archetype": "A1", "seed": 42, "canary_mode": False, "scale": "demo"}
    a = client.post("/api/scenario/generate", json={**body, "log_loss": 0.2}).json()
    b = client.post("/api/scenario/generate", json={**body, "log_loss": 0.6}).json()
    assert (a["id"], b["id"]) == ("scn:A1-42-L20", "scn:A1-42-L60")
    assert client.get("/api/scenario/scn:A1-42-L20").status_code == 200
    assert client.get("/api/scenario/scn:A1-42-L60").json()["params"]["log_loss"] == 0.6


# ---------------------------------------------------------------- canary alert
def test_canary_alert_pins_the_origin_and_audits_once(client):
    r = client.post("/api/canary/alert", json={"scenario_id": "scn:H6", "canary_id": "can:E2-1"})
    assert r.status_code == 200, r.text
    out = r.json()
    a = out["alert"]
    assert (a["canary_id"], a["export_id"], a["ts"]) == ("can:E2-1", "art:E2", "2026-10-12T08:00:00Z")
    assert a["message"]
    assert out["trace"]["origin_pinned"] is True
    assert {h["origin_artifact"] for h in out["trace"]["hypotheses"]} == {"art:E2"}
    assert [e["action"] for e in audit.entries()] == ["canary_alert"]


def test_alert_for_another_canary_pins_to_that_export(client):
    out = client.post("/api/canary/alert", json={"scenario_id": "scn:H6", "canary_id": "can:E1-1"}).json()
    assert out["alert"]["export_id"] == "art:E1" and out["trace"]["origin_pinned"] is True
    assert {h["origin_artifact"] for h in out["trace"]["hypotheses"]} == {"art:E1"}
    # the stored scenario is not changed by the alert
    assert client.get("/api/scenario/scn:H6", params={"full": "true"}).json()["leak_sample"]["canary_hits"] == [
        "can:E2-1"]


def test_canary_alert_rejections(client):
    err(client.post("/api/canary/alert", json={"scenario_id": "scn:H6", "canary_id": "can:ghost"}), 404,
        "not_found")
    err(client.post("/api/canary/alert", json={"scenario_id": "scn:H1", "canary_id": "can:E1-1"}), 400,
        "bad_request")  # canary mode is off in H1
    err(client.post("/api/canary/alert", json={"scenario_id": "scn:nope", "canary_id": "can:E1-1"}), 404,
        "not_found")
    assert audit.entries() == []


def test_canary_alert_uses_the_simulator_message_but_masks_addresses(client, monkeypatch):
    def canary_alert(bundle, canary_id):
        return {"canary_id": canary_id, "export_id": "art:E2", "ts": "2026-10-12T08:00:00Z",
                "message": "Phishing email received at canary address canary.E2.1@example.net"}

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=None, reveal_value=None, get_bundle=lambda i: None, inject_leak=None,
        canary_alert=canary_alert))
    main.register(build("H6"), bundle=object())
    out = client.post("/api/canary/alert", json={"scenario_id": "scn:H6", "canary_id": "can:E2-1"}).json()
    assert out["alert"]["message"] == "Phishing email received at canary address c***@example.net"


# ---------------------------------------------------------------- report
def test_report_has_the_required_sections_and_guardrail_text(client):
    t = client.post("/api/trace", json={"scenario_id": "scn:H1"}).json()
    r = client.get(f"/api/report/{t['trace_id']}")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    html = r.text
    assert LEGAL in html and "SIMULATED" in html
    assert "never a finding of guilt" in html
    assert "downloaded it" in html                                  # observed evidence
    assert "inferred because no log was found" in html              # inferred evidence
    assert "Block outbound uploads from" in html                    # containment recommendation
    assert "relative likelihood" in html.lower()
    assert "calibrated" not in html.lower()
    assert not re.search(r"\b\d+\s*(hours|hrs|h)\b", html.lower().replace("<", " "))  # no deadline in hours
    assert not EMAIL.search(html)
    assert "<html" in html and "</html>" in html


def test_report_export_is_audited_once_per_download(client):
    tid = client.post("/api/trace", json={"scenario_id": "scn:H1"}).json()["trace_id"]
    client.get(f"/api/report/{tid}")
    client.get(f"/api/report/{tid}")
    e = [x for x in audit.entries() if x["action"] == "report_export"]
    assert len(e) == 2 and all(x["object_id"] == tid and x["scenario_id"] == "scn:H1" for x in e)


def test_report_for_an_untraced_scenario_is_computed_and_unknown_id_is_404(client):
    assert client.get("/api/report/trc:H2").status_code == 200
    err(client.get("/api/report/trc:nothing"), 404, "not_found")
    err(client.get("/api/report/garbage"), 404, "not_found")


def test_report_escapes_html_and_masks_values(client):
    pub = build("H1")
    pub["id"] = "scn:XSS"
    next(a for a in pub["actors"] if a["id"] == "act:ann")["name"] = "<script>alert(1)</script>"
    pub["leak_sample"]["masked_preview"] = [{"email": "ravi.menon@example.com", "phone": "+91-9876543221"}]
    main.register(pub)
    html = client.get("/api/report/trc:XSS").text
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert "ravi.menon" not in html and "9876543221" not in html and "r***@example.com" in html


def test_report_notes_the_vendor_boundary(client):
    pub = build("H1")
    pub["id"] = "scn:VEND"
    dl = next(e for e in pub["events"] if e["action"] == "download")
    dl["action"], dl["to_loc"] = "send", "ext:vendor-x"
    for a in pub["actors"]:
        a["access"] = a["access"] + ["ext:vendor-x"]
    main.register(pub)
    html = client.get("/api/report/trc:VEND").text
    assert "chain of custody ends at the vendor boundary" in html.lower()
    assert "chain of custody ends at the vendor boundary" not in client.get("/api/report/trc:H1").text.lower()


# ---------------------------------------------------------------- masking everywhere
def test_no_endpoint_returns_an_unmasked_email(client):
    pub = build("H1")
    pub["id"] = "scn:RAW3"
    pub["leak_sample"]["masked_preview"] = [{"email": "ravi.menon@example.com"}]
    pub["discovery"]["messages"][0]["text"] = "contact ravi.menon@example.com for the rest"
    main.register(pub)
    texts = [client.get("/api/scenario/scn:RAW3").text,
             client.get("/api/scenario/scn:RAW3", params={"full": "true"}).text,
             client.post("/api/leak/export", json={"scenario_id": "scn:RAW3", "message_id": 1}).text,
             client.post("/api/trace", json={"scenario_id": "scn:RAW3"}).text,
             client.get("/api/report/trc:RAW3").text, client.get("/api/audit").text]
    for t in texts:
        assert not EMAIL.search(t) and "ravi.menon" not in t
