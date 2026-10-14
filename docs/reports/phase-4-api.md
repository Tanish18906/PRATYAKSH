# Phase 4 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- `bench/baselines.py` (B1 last accessor, B2 biggest exporter, B3 largest export, B4 most recent export), `bench/metrics.py` (ranks, top1 / top3 / mean_rank / n, sanity gates), `bench/run.py` (runner and CLI): done.
- `POST /api/benchmark/run` (returns an id at once, runs in a background thread) and `GET /api/benchmark/{id}` (status, progress, results): done. One `benchmark_run` audit entry per run.
- `make_demo_bundle.py --benchmark FILE` so the final numbers can go into `demo.json`: done.
- Tuning on seeds 0 to 49 and the final run on seeds 50 to 199 are NOT done here: they need the simulator (see below) and belong to the engine side.

## Important: simulator not available
`backend/app/sim/*` is still empty. Everything is verified with a fake generator built from the hand-written scenarios plus a
scratch randomized generator that is not part of the repo. Therefore:
- `POST /api/benchmark/run` answers 409 `not_ready` on this tree (tested, and the CLI exits 1).
- NO benchmark numbers exist for the project, none may be shown or claimed, and `demo.json` has `benchmark: null`.
- Sanity gate 04 sec 6.4 (origin top3 at loss 0.0 at least 0.9; baselines differ) can only be judged on the real simulator.

## Files created or changed
- backend/app/bench/{baselines,metrics,run}.py, backend/app/main.py, backend/app/models.py
- backend/scripts/make_demo_bundle.py, backend/tests/api/{conftest,test_benchmark,test_demo_bundle}.py
- docs/DECISIONS.md, docs/reports/phase-4-api.md

## Commands run and real output
$ cd backend && ../.venv/bin/python -m pytest -q tests/api/test_benchmark.py      # before implementation
9 failed, 4 errors

$ cd backend && ../.venv/bin/python -m pytest -q
208 passed, 1 warning in 19.16s      (107 engine + 101 api)

Runner throughput, real `run_benchmark` with a scratch generator (NOT the simulator, NOT a project result):
800 scenarios (200 seeds x 4 losses) in 61.0 s, status done, n = 199 per cell (seed 42 skipped),
reported_on = "seeds 0-199 (includes tuning seeds)", sanity gates: pass.
$ python -m app.bench.run --seeds 50 52     (no simulator)  -> "error: the simulator is not available", exit 1

## Gate checks
- [x] Runner computes top1, top3, mean_rank, n for pugmark and B1 to B4 per loss level; hand-checked expected values on H1/H3/H4: pass
- [x] Result separates tuned_on and reported_on, note is always the synthetic-data sentence, no truth in the result: pass
- [x] Async: id returned immediately, progress observable while running, failed status on a crash: pass
- [ ] Sanity gates 04 sec 6.4 on real data: NOT RUN (no simulator).
- [ ] H1 to H8 and seed 42 still pass with the tuned config: H1 to H8 pass (config untouched); seed 42 and tuning NOT RUN.
- [ ] Chart shows the real numbers: UI work; there are no real numbers yet.
- [ ] Tag `ok-4`: yours.

## Not done / cut
- Tuning, the final 50 to 199 run, the five manual spot checks, regenerating `demo.json` with a benchmark (all need the simulator).
- No retention or cleanup of finished benchmarks (in memory only, lost on restart).

## Contract or spec discrepancies
- None new. `origin_ranking` still absent from the contract text (open since Phase 0).

## Risks for integration
- At bench scale the simulator must generate in about 0.3 s (docs/02 sec 14); 800 runs take about that times 800 plus about 0.1 s of engine each, so a few minutes; the endpoint is async but the CLI is the better tool for the final run.
- The benchmark is only as honest as the simulator's truth: `truth.origin_artifact` and `truth.true_actors` are read by the runner; if the simulator names the leaker's service creator among `true_actors`, baselines and pugmark are scored against a different target than 04 sec 6.3 intends (rank of the best-ranked true actor).
- Benchmark state is in memory and a server restart loses it; save the final run with `--out` and embed it with `make_demo_bundle.py --benchmark`.

STOPPED. Waiting for APPROVED PHASE 4.
