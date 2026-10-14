# Integration report: simulator + engine + api

Date: 2026-10-14 | Branch: `integrate/sim-engine-api` (pushed) | `main` NOT updated, no tags.

## Status
**AMBER, not merged into main.** Everything works end to end and the seed 42 acceptance table is fully green at all three loss
levels, but the full test suite is not 100 percent green: 1 test fails (252 passed). It is a stale test written by the api module
before the simulator existed, not an engine or sim bug. Your rule says merge only when green, so I stopped at the pushed branch.

## What was merged, in order (no conflicts anywhere)
1. `origin/feat/sim` (6 commits, simulator phases 0 to 5). Step 2 diff over `config.py`, `models.py`, `common/`, `docs/01`, `tests/fixtures/`: empty, the simulator touched no shared file.
2. `feat/engine`: already contained in `main` (merge `69f03d1`), nothing to do.
3. `feat/api` (api phases 0 to 5, hostile-test fixes: audit lock, nullable `Event.object`, deterministic candidate tie order).
4. Glue commit `5d1ac81`: startup `warm_cache` in a background thread, README commands, `backend/scripts/smoke.py`, one test, decision log.

Housekeeping: 15 local untracked 0-byte placeholder files (old sim stubs, `validate.py`) sat at the same paths as the simulator's real
files; they were moved to the scratchpad (not deleted) so the merge could land. `backend/app/common/__init__.py` is still untracked and unneeded (namespace package).

## pytest summary (real, last lines; fresh clone and fresh venv give the same)
```
.....................F.................................................. [ 28%]
........................................................................ [ 56%]
........................................................................ [ 85%]
.....................................                                    [100%]
FAILED tests/api/test_demo_bundle.py::test_cli_without_simulator_or_fixture_fails_clearly
1 failed, 252 passed, 1 warning in 23.57s
```
252 = 117 engine + 8 files of simulator tests + 109 api/other.

## Seed 42, A1, demo, canary off (live server, real HTTP, public scenario only)
| log_loss | origin top 3 (relative likelihood) | E2 | E3 | top 3 hypotheses (actor, likelihood) | final hop | generate | trace |
|---|---|---|---|---|---|---|---|
| 0.0 | E1 1.0, E4 0.0, E5 0.0 | excluded, watermark_before | excluded, schema | Ravi 0.9808, Reyan 0.0038, Kairav 0.0026 | inferred ep:ravi-menon to telegram | 0.49 s | 0.022 s |
| 0.2 | E1 0.9999, E4 0.0001, E5 0.0 | excluded, watermark_before | excluded, schema | Ravi 0.9344, Reyan 0.0130, Kairav 0.0102 | inferred | 0.36 s | 0.016 s |
| 0.4 | E1 0.9997, E4 0.0001, E5 0.0001 | excluded, watermark_before | excluded, schema | Ravi 0.8789, Reyan 0.0235, Kairav 0.0193 | inferred | 0.36 s | 0.014 s |

All 04 sec 4 expectations passed at each level: E1 wins; E4, E5, E6 candidates with watermark term -8.0 (cap) and E1 -0.9136; Ravi first in
`actor_ranking` and in hypothesis 1; last hop inferred from `ep:ravi-menon`; first chokepoint `perm:act:ravi-menon@egress`; last-accessor
baseline does not rank Ravi first; trace under 3 s; the simulator's `validate_public_scenario` and `validate_trace` return no errors on every output.
Not asserted by 04, printed for information: at log_loss 0.6 Ravi's download is dropped by design, origin is still E1 (0.9981) and Ravi ranks 5th of 11 listed actors.
Privacy: grep of generate, export, trace, full scenario and report responses for `truth`, `case_key`, `true_path`: 0 hits; email-like strings: 0.
No weights were tuned.

## Failures, with owner
1. `tests/api/test_demo_bundle.py::test_cli_without_simulator_or_fixture_fails_clearly`
   - Owner: Tanish (api glue). Category (a), interface/premise mismatch, NOT an engine or sim bug.
   - Command: `cd backend && pytest -q tests/api/test_demo_bundle.py`. Expected: non-zero exit with "simulator" on stderr (true when no simulator existed).
     Actual: exit 0 and a real 72 KB seed 42 bundle written, because the simulator now exists.
   - Not edited (rule: no editing failing tests). One-line fix when you approve: monkeypatch `scripts.make_demo_bundle.api._sim` to `lambda: None` in that test. Logged in `docs/QUESTIONS.md`.
No engine bug and no sim bug was found in this job.

## Exact run commands (all run as written, including on a fresh clone with a new venv)
```
git clone https://github.com/Tanish18906/PRATYAKSH.git && cd PRATYAKSH && git checkout integrate/sim-engine-api
python3 -m venv .venv && source .venv/bin/activate
cd backend && pip install -r requirements.txt
pytest -q
uvicorn app.main:app --port 8000            # one worker, never --workers
# other terminal, from the repo root:
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/scenario/generate -H 'content-type: application/json' -d '{"archetype":"A1","seed":42,"log_loss":0.4,"canary_mode":false,"scale":"demo"}'
curl -s -X POST http://127.0.0.1:8000/api/trace -H 'content-type: application/json' -d '{"scenario_id":"scn:A1-42-L40"}'
python backend/scripts/smoke.py              # prints PASS or FAIL, exit 0 or 1
```
Smoke on the fresh clone: `scenario scn:A1-42-L40: generate 0.42s, trace 0.016s, origin art:E1 0.9997, top hypothesis ['act:ravi-menon'] 0.8789` then PASS. Against a dead port it prints FAIL and exits 1.

## What is NOT working or NOT verified
- Not merged to `main`; `main` is local `69f03d1` (engine merge, not pushed) and `origin/main` is still `9c1c854`. Pushing `main` later also pushes the engine merge.
- The stale test above is red.
- Not exercised live against the real simulator in this job: `POST /api/reveal` values, `POST /api/inject`, `POST /api/canary/alert` with the simulator's message, and `POST /api/benchmark/run` (runner, baselines and sanity gates on real scenarios). Their API paths are covered by tests with a fake simulator; the simulator's own suite covers its side. Benchmark numbers therefore still do not exist.
- `frontend/` not touched: `src/types/contract.ts` needs `object: string | null` and `origin_ranking`; `frontend/public/demo.json` was not generated.
- `ACTOR_ALT_MAX` recall limit for service-account leakers (QUESTIONS.md) is untouched by design.
- `docs/04_TEST_PLAN.md` section 4 integration file `tests/integration/test_seed42.py` does not exist (the simulator ships `tests/sim/test_seed42.py`, which passes); the live table above is the equivalent check.
