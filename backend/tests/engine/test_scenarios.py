"""Hand-written scenarios from docs/04_TEST_PLAN.md section 3 (expectations are human-owned).

Phase 1 wired H1, H3, H4, H6, H7, H8; Phase 2 adds H2 and H5.
"""
import copy
import json

import pytest

from app.engine.trace import trace
from tests.fixtures.mini import build


def origin_p(res, aid):
    return next(r["probability"] for r in res["origin_ranking"] if r["artifact_id"] == aid)


def cand(res, aid):
    return next(c for c in res["origin_candidates"] if c["artifact_id"] == aid)


def ann_download_id(sc):
    return next(e["id"] for e in sc["events"] if e["action"] == "download" and e["actor"] == "act:ann")


def test_h1_two_near_identical_exports():
    sc = build("H1")
    r = trace(sc)
    assert r["origin_candidates"][0]["artifact_id"] == "art:E1"
    e1, e2 = cand(r, "art:E1"), cand(r, "art:E2")
    assert e2["verdict"] == "candidate"
    assert e1["origin_fit"] - e2["origin_fit"] >= 1.5
    assert e1["containment"] >= 0.95 and e1["format_sim"] == 1.0 and e2["format_sim"] == 0.1111
    assert -0.5 <= e1["watermark_term"] <= -0.2 and e1["watermark_term"] == -0.3333
    assert e2["watermark_term"] == -1.3333
    assert r["origin_ranking"][0]["artifact_id"] == "art:E1"
    assert r["origin_ranking"][0]["probability"] >= 0.8
    h = r["hypotheses"][0]
    assert h["origin_artifact"] == "art:E1" and h["actors"] == ["act:ann"]
    assert h["hops"][0]["kind"] == "observed" and h["hops"][0]["event_id"] == ann_download_id(sc)
    last = h["hops"][-1]
    assert (last["kind"], last["from_loc"], last["to_loc"]) == ("inferred", "ep:ann", "ext:telegram-leak-channel")
    assert r["actor_ranking"][0]["actor"] == "act:ann"


def marginal(res, actor):
    return next((a["marginal"] for a in res["actor_ranking"] if a["actor"] == actor), 0.0)


def test_h2_shared_bucket_two_readers():
    r = trace(build("H2"))
    top2 = [a["actor"] for a in r["actor_ranking"][:2]]
    assert sorted(top2) == ["act:bob", "act:cat"]
    assert abs(marginal(r, "act:bob") - marginal(r, "act:cat")) <= 0.10
    assert marginal(r, "act:bob") >= 0.30 and marginal(r, "act:cat") >= 0.30
    assert r["hypotheses"][0]["probability"] <= 0.60
    assert "act:ann" not in top2
    assert all("act:etl" not in h["actors"] for h in r["hypotheses"])
    assert "act:etl" not in {a["actor"] for a in r["actor_ranking"]}


def test_h3_laundered_through_reformatting():
    r = trace(build("H3"))
    assert r["origin_candidates"][0]["artifact_id"] == "art:E1"
    e1, e2 = cand(r, "art:E1"), cand(r, "art:E2")
    assert e1["containment"] >= 0.95 and e1["format_sim"] == 0.6667
    assert e2["verdict"] == "excluded" and e2["exclusion_rule"] == "watermark_before"
    assert r["hypotheses"][0]["origin_artifact"] == "art:E1"


def test_h4_origin_parts_and_paths():
    r = trace(build("H4"))
    e1, e5 = cand(r, "art:E1"), cand(r, "art:E5")
    assert e1["verdict"] == e5["verdict"] == "candidate"
    assert e1["watermark_term"] == 0 and e5["watermark_term"] == 0
    assert e1["containment"] >= 0.7 and e5["containment"] >= 0.7
    assert r["hypotheses"][0]["origin_artifact"] == "art:E1"
    assert r["origin_ranking"][0]["artifact_id"] == "art:E1"
    assert r["origin_ranking"][0]["probability"] >= 0.5


def test_h5_critical_logs_dropped_two_insiders():
    r = trace(build("H5"))
    top2 = [a["actor"] for a in r["actor_ranking"][:2]]
    assert sorted(top2) == ["act:ann", "act:bob"]
    assert abs(marginal(r, "act:ann") - marginal(r, "act:bob")) <= 0.10
    assert "act:cat" not in top2
    assert r["hypotheses"][0]["probability"] <= 0.60
    ev = r["recommended_evidence"]
    assert len(ev) >= 1
    assert 0.30 <= ev[0]["mass"] <= 0.70
    assert ev[0]["hop_ref"]["from_loc"] in ("sys:wh", "ep:ann", "ep:bob")
    for h in r["hypotheses"]:
        assert all(hop["ts"] is None for hop in h["hops"] if hop["kind"] == "inferred")


def test_h6_canary_pins_origin():
    sc = build("H6")
    r = trace(sc)
    assert r["origin_pinned"] is True
    assert r["hypotheses"] and all(h["origin_artifact"] == "art:E2" for h in r["hypotheses"])
    assert r["origin_ranking"] == [{"artifact_id": "art:E2", "probability": 1.0}]
    assert r["actor_ranking"][0]["actor"] == "act:bob"
    assert any("canary" in n for n in r["notes"])
    # run B: same scenario without the canary hit
    b = copy.deepcopy(sc)
    b["leak_sample"]["canary_hits"] = []
    rb = trace(b)
    assert rb["origin_pinned"] is False
    assert rb["origin_ranking"][0]["artifact_id"] == "art:E1"
    assert rb["origin_ranking"][0]["probability"] >= 0.6


def test_h7_no_matching_export():
    r = trace(build("H7"))
    assert r["hypotheses"] == [] and r["origin_ranking"] == [] and r["chokepoints"] == []
    assert any("does not match" in n for n in r["notes"])
    assert {c["artifact_id"] for c in r["origin_candidates"]} == {"art:E1", "art:E2"}
    for c in r["origin_candidates"]:
        assert c["containment"] is None or c["containment"] < 0.2


def test_h8_artifact_ids_are_not_signal():
    r1, r8 = trace(build("H1")), trace(build("H8"))
    text = json.dumps(r1).replace("art:E1", "art:E7").replace("art:E2", "art:E3")
    expected = json.loads(text)
    expected["trace_id"], expected["scenario_id"] = r8["trace_id"], r8["scenario_id"]
    assert r8 == expected


@pytest.mark.parametrize("name", ["H1", "H2", "H3", "H4", "H5", "H6", "H7"])
def test_trace_is_deterministic_and_invariants_hold(name):
    sc = build(name)
    a, b = trace(sc), trace(copy.deepcopy(sc))
    assert json.dumps(a) == json.dumps(b)
    assert a["contract_version"] == "1.0" and a["scenario_id"] == sc["id"]
    probs = [h["probability"] for h in a["hypotheses"]]
    assert probs == sorted(probs, reverse=True) and sum(probs) <= 1.0001
    art_ids = [c["artifact_id"] for c in a["origin_candidates"]]
    assert sorted(art_ids) == sorted(x["id"] for x in sc["artifacts"])
    ev_ids = {e["id"] for e in sc["events"]}
    for h in a["hypotheses"]:
        for i, hop in enumerate(h["hops"]):
            assert hop["event_id"] is None or hop["event_id"] in ev_ids
            if i:
                assert h["hops"][i - 1]["to_loc"] == hop["from_loc"]
    nodes = {n["id"] for n in a["graph"]["nodes"]}
    assert all(e["from"] in nodes and e["to"] in nodes for e in a["graph"]["edges"])
    assert set(a["loss_estimates"]) == {s["id"] for s in sc["log_sources"]}


def test_engine_ignores_params_and_truth_like_keys():
    sc = build("H1")
    other = copy.deepcopy(sc)
    other["params"]["log_loss"] = 0.6
    assert trace(sc) == trace(other)


def test_pinned_artifact_that_fails_a_hard_rule_does_not_crash():
    sc = build("H6")
    next(a for a in sc["artifacts"] if a["id"] == "art:E2")["columns"].remove("policy_no")  # now fails schema
    r = trace(sc)
    assert r["origin_pinned"] is True and r["hypotheses"]
    assert all(h["origin_artifact"] == "art:E2" for h in r["hypotheses"])
    assert any("also fails" in n for n in r["notes"])


def test_zero_events_scenario_still_ranks_origins():
    sc = build("H1")
    sc["events"] = []
    r = trace(sc)
    assert r["origin_ranking"] and r["hypotheses"]


def test_all_artifacts_excluded_gives_note_not_exception():
    sc = build("H1")
    for a in sc["artifacts"]:
        a["created_ts"] = "2026-10-13T00:00:00Z"  # after the leak was found
    r = trace(sc)
    assert r["hypotheses"] == [] and r["origin_ranking"] == []
    assert any("does not match" in n for n in r["notes"])
