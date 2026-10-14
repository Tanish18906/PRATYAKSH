"""Benchmark runner (docs/04_TEST_PLAN.md section 6). Ground truth is read here and never leaves this module:
only aggregated rank statistics are returned.

    python -m app.bench.run --seeds 50 199 --losses 0 0.2 0.4 0.6 --out final.json   (from backend/)
"""
import argparse
import json
import sys

from app.bench import baselines, metrics
from app.engine.trace import trace

NOTE = "Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy."
TUNED_ON = "seeds 0-49"
DEMO_SEED = 42  # the demo story is never part of the benchmark
ORIGIN_METHODS = {"B3_largest_export": baselines.largest_export, "B4_most_recent_export": baselines.most_recent_export}
ACTOR_METHODS = {"B1_last_accessor": baselines.last_accessor, "B2_biggest_exporter": baselines.biggest_exporter}


def reported_on(seed_range) -> str:
    a, b = seed_range
    return f"seeds {a}-{b}" + (" (includes tuning seeds)" if a <= 49 else "")


def _empty(seed_range, loss_levels, status="running", progress=0.0) -> dict:
    return {"status": status, "progress": progress, "tuned_on": TUNED_ON, "reported_on": reported_on(seed_range),
            "loss_levels": list(loss_levels), "origin": {}, "actor": {}, "note": NOTE}


def run_benchmark(generate, seed_range, loss_levels, archetypes, progress=None) -> dict:
    """generate(archetype, seed, log_loss, canary_mode, scale) -> object with .public and .truth."""
    seeds = [s for s in range(seed_range[0], seed_range[1] + 1) if s != DEMO_SEED]
    total, done, failed = len(seeds) * len(loss_levels), 0, False
    ranks = {"origin": {}, "actor": {}}

    def add(kind, method, loss, rank):
        ranks[kind].setdefault(method, {}).setdefault(str(float(loss)), []).append(rank)

    for loss in loss_levels:
        for seed in seeds:
            done += 1
            try:
                bundle = generate(archetypes[seed % len(archetypes)], seed, loss, False, "bench")
                sc, truth = bundle.public, bundle.truth
            except Exception:
                failed = True
                continue
            n_art, n_act = len(sc["artifacts"]), len(sc["actors"])
            try:
                res = trace(sc)
                listed = [x["artifact_id"] for x in res["origin_ranking"]]
                o_order = listed + [c["artifact_id"] for c in res["origin_candidates"] if c["artifact_id"] not in listed]
                a_order = [x["actor"] for x in res["actor_ranking"]]
                o_rank = metrics.rank_of(truth["origin_artifact"], o_order, n_art)
                a_rank = metrics.best_rank(truth["true_actors"], a_order, n_act)
            except Exception:
                failed = True
                o_rank, a_rank = n_art, n_act  # a crash counts as the worst answer, and fails the run
            add("origin", "pugmark", loss, o_rank)
            add("actor", "pugmark", loss, a_rank)
            for name, fn in ORIGIN_METHODS.items():
                add("origin", name, loss, metrics.rank_of(truth["origin_artifact"], fn(sc), n_art))
            for name, fn in ACTOR_METHODS.items():
                add("actor", name, loss, metrics.best_rank(truth["true_actors"], fn(sc), n_act))
            if progress:
                progress(done / total)
    out = _empty(seed_range, loss_levels, "failed" if failed else "done", 1.0)
    for kind in ("origin", "actor"):
        out[kind] = {m: {loss: metrics.stats(r) for loss, r in by.items()} for m, by in ranks[kind].items()}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the benchmark on the simulator and print sanity gates.")
    ap.add_argument("--seeds", nargs=2, type=int, default=[50, 199])
    ap.add_argument("--losses", nargs="+", type=float, default=[0.0, 0.2, 0.4, 0.6])
    ap.add_argument("--archetypes", nargs="+", default=["A1", "A2", "A3"])
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    from app.main import _sim  # late import: app.main imports this module

    sim = _sim()
    if sim is None:
        print("error: the simulator is not available", file=sys.stderr)
        return 1
    result = run_benchmark(sim.generate_scenario, args.seeds, args.losses, args.archetypes)
    for msg in metrics.sanity_gates(result):
        print("SANITY GATE FAILED:", msg, file=sys.stderr)
    text = json.dumps(result, indent=1)
    if args.out:
        open(args.out, "w").write(text + "\n")
    else:
        print(text)
    return 0 if result["status"] == "done" else 2


if __name__ == "__main__":
    sys.exit(main())
