import json
import time
import types

import pytest

from app import main
from app.bench import baselines, metrics, run as bench_run
from app.models import BenchmarkResult
from app.privacy import audit
from tests.fixtures.mini import build

NOTE = "Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy."
FIX = {"A1": "H1", "A2": "H3", "A3": "H4"}  # truth: origin art:E1, leaker act:ann in all three


def fake_generate(archetype, seed, log_loss, canary_mode, scale):
    assert canary_mode is False and scale == "bench"
    pub = build(FIX[archetype])
    pub["seed"] = seed
    truth = {"scenario_id": pub["id"], "origin_artifact": "art:E1", "true_actors": ["act:ann"]}
    return types.SimpleNamespace(public=pub, truth=truth, private=None)


def err(r, status, code):
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


# ---------------------------------------------------------------- baselines
def test_baselines_on_h1_by_hand():
    sc = build("H1")  # E1: 1828 rows 02:10, E2: 1829 rows 02:40; ann downloads E1 at 09:00
    assert baselines.largest_export(sc) == ["art:E2", "art:E1"]
    assert baselines.most_recent_export(sc) == ["art:E2", "art:E1"]
    assert baselines.last_accessor(sc)[0] == "act:ann"
    assert baselines.biggest_exporter(sc)[:2] == ["act:cat", "act:ann"]  # 1829 then a 1828 tie in actor order


def test_baselines_ignore_artifacts_created_after_the_leak_was_found():
    sc = build("H1")
    sc["artifacts"][1]["created_ts"] = "2026-10-13T00:00:00Z"
    assert baselines.largest_export(sc) == ["art:E1"]
    assert baselines.most_recent_export(sc) == ["art:E1"]


def test_last_accessor_only_counts_events_before_found_and_on_data_objects():
    sc = build("H1")
    late = {**sc["events"][-1], "id": "evt:999999", "actor": "act:bob", "ts": "2026-10-13T00:00:00Z"}
    sc["events"].append(late)
    assert baselines.last_accessor(sc)[0] == "act:ann"


# ---------------------------------------------------------------- metrics
def test_rank_helpers_and_stats():
    assert metrics.rank_of("b", ["a", "b", "c"], 9) == 2
    assert metrics.rank_of("z", ["a", "b"], 9) == 9
    assert metrics.best_rank(["z", "c"], ["a", "b", "c"], 9) == 3
    s = metrics.stats([1, 3, 4, 1])
    assert s == {"top1": 0.5, "top3": 0.75, "mean_rank": 2.25, "n": 4}
    assert metrics.stats([]) == {"top1": 0.0, "top3": 0.0, "mean_rank": None, "n": 0}


def test_sanity_gates():
    good = {"origin": {"pugmark": {"0.0": {"top3": 0.95, "top1": 0.8, "mean_rank": 1.2, "n": 10}},
                       "B3": {"0.0": {"top3": 0.5, "top1": 0.2, "mean_rank": 3, "n": 10}}},
            "actor": {"pugmark": {"0.0": {"top3": 0.9, "top1": 0.7, "mean_rank": 1.5, "n": 10}},
                      "B1": {"0.0": {"top3": 0.3, "top1": 0.1, "mean_rank": 5, "n": 10}}}}
    assert metrics.sanity_gates(good) == []
    bad = json.loads(json.dumps(good))
    bad["origin"]["pugmark"]["0.0"]["top3"] = 0.85
    assert any("top3" in m and "0.9" in m for m in metrics.sanity_gates(bad))
    same = json.loads(json.dumps(good))
    same["origin"]["B3"] = same["origin"]["pugmark"]
    assert any("identical" in m.lower() for m in metrics.sanity_gates(same))


# ---------------------------------------------------------------- runner
def test_runner_aggregates_and_skips_seed_42():
    res = bench_run.run_benchmark(fake_generate, (40, 44), [0.0, 0.6], ["A1", "A2", "A3"])
    assert res["status"] == "done" and res["progress"] == 1.0
    assert res["loss_levels"] == [0.0, 0.6] and res["note"] == NOTE
    assert res["tuned_on"] == "seeds 0-49" and res["reported_on"] == "seeds 40-44 (includes tuning seeds)"
    n = res["origin"]["pugmark"]["0.0"]["n"]
    assert n == 4  # seeds 40, 41, 43, 44: seed 42 is the demo and never benchmarked
    # archetype by seed: 40->A2, 41->A3, 43->A2, 44->A3 : H3, H4, H3, H4
    assert res["origin"]["pugmark"]["0.0"]["top1"] == 1.0
    assert res["origin"]["B3_largest_export"]["0.0"] == {"top1": 0.5, "top3": 1.0, "mean_rank": 1.5, "n": 4}
    assert res["origin"]["B4_most_recent_export"]["0.0"]["mean_rank"] == 1.5
    assert set(res["actor"]) == {"pugmark", "B1_last_accessor", "B2_biggest_exporter"}
    BenchmarkResult.model_validate({**res, "benchmark_id": "bench:0001"})


def test_reported_on_is_clean_for_held_out_seeds():
    res = bench_run.run_benchmark(fake_generate, (50, 52), [0.0], ["A1"])
    assert res["reported_on"] == "seeds 50-52"


def test_engine_failure_marks_the_run_failed_but_keeps_other_results(monkeypatch):
    real = bench_run.trace
    calls = {"n": 0}

    def flaky(public, top_k=5):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom")
        return real(public, top_k)

    monkeypatch.setattr(bench_run, "trace", flaky)
    res = bench_run.run_benchmark(fake_generate, (0, 3), [0.0], ["A1"])
    assert res["status"] == "failed" and res["origin"]["pugmark"]["0.0"]["n"] == 4


def test_result_never_contains_truth():
    text = json.dumps(bench_run.run_benchmark(fake_generate, (0, 2), [0.0], ["A1"]))
    assert "truth" not in text and "art:E1" not in text and "act:ann" not in text


# ---------------------------------------------------------------- api
@pytest.fixture
def with_sim(client, monkeypatch):
    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=fake_generate, reveal_value=None, get_bundle=lambda i: None))
    return client


def wait_done(client, bid, timeout=20):
    t = time.time()
    while time.time() - t < timeout:
        r = client.get(f"/api/benchmark/{bid}").json()
        if r["status"] != "running":
            return r
        time.sleep(0.05)
    raise AssertionError("benchmark did not finish")


def test_run_returns_an_id_immediately_and_result_is_pollable(with_sim):
    r = with_sim.post("/api/benchmark/run", json={"seed_range": [50, 55], "loss_levels": [0.0, 0.2],
                                                  "archetypes": ["A1", "A2", "A3"]})
    assert r.status_code == 200, r.text
    bid = r.json()["benchmark_id"]
    assert set(r.json()) == {"benchmark_id"} and bid.startswith("bench:")
    res = wait_done(with_sim, bid)
    BenchmarkResult.model_validate(res)
    assert res["status"] == "done" and res["progress"] == 1.0 and res["reported_on"] == "seeds 50-55"
    assert res["origin"]["pugmark"]["0.2"]["n"] == 6 and res["note"] == NOTE
    assert [e["action"] for e in audit.entries()] == ["benchmark_run"]
    assert audit.entries()[0]["object_id"] == bid


def test_progress_is_reported_while_running(with_sim, monkeypatch):
    import threading
    gate = threading.Event()
    real = fake_generate

    def slow(*a):
        gate.wait(5)
        return real(*a)

    monkeypatch.setattr(main, "_sim", lambda: types.SimpleNamespace(
        generate_scenario=slow, reveal_value=None, get_bundle=lambda i: None))
    bid = with_sim.post("/api/benchmark/run", json={"seed_range": [0, 1], "loss_levels": [0.0],
                                                    "archetypes": ["A1"]}).json()["benchmark_id"]
    r = with_sim.get(f"/api/benchmark/{bid}").json()
    assert r["status"] == "running" and r["progress"] < 1.0
    gate.set()
    assert wait_done(with_sim, bid)["status"] == "done"


def test_run_validation_and_not_ready(client, with_sim):
    ok = {"seed_range": [0, 3], "loss_levels": [0.0], "archetypes": ["A1"]}
    for bad in ({**ok, "seed_range": [5, 1]}, {**ok, "seed_range": [0]}, {**ok, "loss_levels": []},
                {**ok, "loss_levels": [0.9]}, {**ok, "archetypes": []}, {**ok, "archetypes": ["A9"]},
                {**ok, "seed_range": [0, 5000]}, {**ok, "extra": 1}):
        err(with_sim.post("/api/benchmark/run", json=bad), 400, "bad_request")
    assert audit.entries() == []
    err(with_sim.get("/api/benchmark/bench:9999"), 404, "not_found")


def test_run_is_not_ready_without_a_simulator(client):
    err(client.post("/api/benchmark/run", json={"seed_range": [0, 3], "loss_levels": [0.0],
                                                "archetypes": ["A1"]}), 409, "not_ready")
    assert audit.entries() == []
