import math

from app.config import ENGINE as CFG
from app.engine.rank import softmax
from app.engine.trace import trace
from tests.fixtures.mini import build


def test_softmax_sums_to_one_and_is_shift_invariant():
    p = softmax([1.0, 2.0, -3.0, 2.0])
    assert abs(sum(p) - 1.0) < 1e-12 and p[1] == p[3]
    q = softmax([x + 100 for x in [1.0, 2.0, -3.0, 2.0]])
    assert all(abs(a - b) < 1e-9 for a, b in zip(p, q))


def test_score_parts_reconstruct_score():
    for h in trace(build("H1"))["hypotheses"]:
        sp = h["score_parts"]
        expect = CFG["W_ORIGIN"] * sp["origin_fit"] - CFG["W_PATH"] * sp["path_cost"] + CFG["W_ANOMALY"] * sp["anomaly"]
        assert abs(h["score"] - expect) < 2e-3


def test_h1_anomaly_is_recorded_on_the_ann_path():
    h = trace(build("H1"))["hypotheses"][0]
    assert h["actors"] == ["act:ann"]
    assert abs(h["score_parts"]["anomaly"] - 4.7) < 1e-3  # z capped at 4.0 plus first-time 0.7
    assert any(e["kind"] == "anomaly" for e in h["evidence"])


def test_probabilities_are_relative_and_sorted():
    r = trace(build("H2"), top_k=3)
    probs = [h["probability"] for h in r["hypotheses"]]
    assert len(probs) == 3 and probs == sorted(probs, reverse=True) and sum(probs) <= 1.0001
    assert [h["rank"] for h in r["hypotheses"]] == [1, 2, 3]
    assert [h["path_id"] for h in r["hypotheses"]] == ["hyp:1", "hyp:2", "hyp:3"]


def test_marginals_and_top_path_ids():
    r = trace(build("H2"))
    ids = {h["path_id"] for h in r["hypotheses"]}
    for a in r["actor_ranking"]:
        assert 0 <= a["marginal"] <= 1.0001 and (a["top_path_id"] is None or a["top_path_id"] in ids)
    ms = [a["marginal"] for a in r["actor_ranking"]]
    assert ms == sorted(ms, reverse=True)
    assert "ext:telegram-leak-channel" not in {x["location"] for x in r["location_ranking"]}


def test_pinned_origin_ranking():
    r = trace(build("H6"))
    assert r["origin_ranking"] == [{"artifact_id": "art:E2", "probability": 1.0}]
    assert abs(sum(h["probability"] for h in r["hypotheses"]) - 1.0) < 0.01 or len(r["hypotheses"]) == CFG["TOP_K"]


def test_evidence_requests_are_ordered_by_information():
    r = trace(build("H5"))
    ev = r["recommended_evidence"]
    assert 1 <= len(ev) <= CFG["EVIDENCE_MAX"]
    info = [e["informativeness"] for e in ev]
    assert info == sorted(info, reverse=True)
    for e in ev:
        m = e["mass"]
        h = -m * math.log(m) - (1 - m) * math.log(1 - m) if 0 < m < 1 else 0.0
        assert abs(e["informativeness"] - h / math.log(2)) < 1e-3
        assert "logs" in e["request_text"] or "Network" in e["request_text"]
    assert [e["rank"] for e in ev] == list(range(1, len(ev) + 1))
