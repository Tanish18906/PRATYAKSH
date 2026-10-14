# Phase 5 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- API is frozen at the Phase 4 commit `643b2aa` plus this report. No code or config changed in Phase 5.
- Freeze checks on a trial merge of `feat/api` onto `main` (throwaway clone, your branches untouched): clean merge, `pytest -q` 208 passed,
  the README server command starts and answers.

## Files created or changed
- docs/reports/phase-5-api.md

## Commands run and real output
$ git clone <repo> <tmp> && git checkout main && git merge --no-ff origin/feat/api
merge clean (main 69f03d1 + feat/api)

$ cd backend && pytest -q                      # plain command from the README, in the merged clone
208 passed, 1 warning in 19.19s                # 107 engine + 101 api

$ uvicorn app.main:app --port 8001 ; curl /api/health
{"status":"ok","contract_version":"1.0","engine_version":"1.0.0"}
POST /api/trace scn:H1      -> 200 in 0.019 s
GET  /api/report/trc:H1     -> 200 text/html
POST /api/benchmark/run     -> 409 not_ready (no simulator)

Guardrail scan (zero exposure / calibrated / real Telegram / deadline in hours) over backend/app and README.md:
no claims; the only hits are code comments saying probabilities are NOT calibrated.

## Gate checks (what I can vouch for)
- [x] Backend tests green on the merged tree, server starts, health, trace, report work, errors use the contract shape: pass
- [x] No truth / case_key / true_path in any response, reveal needs a reason and writes an audit entry, no unmasked email in any response or report: pass (tests plus live runs)
- [ ] Demo path with the simulator (seed 42: generate, export, trace, graph, evidence cards, reveal, report), timing under 3 s on the real scenario: NOT VERIFIED.
      `backend/app/sim/*` and `backend/scripts/validate.py` are still empty files; `frontend/public/demo.json` does not exist.
- [ ] Offline replay with the real bundle: NOT VERIFIED. `make_demo_bundle.py --fixture H1` produces a valid placeholder bundle only.
- [ ] Benchmark numbers: none exist. Do not show a benchmark chart or claim an accuracy figure.
- [ ] Rehearsal x3 offline, backup video, tags `ok-N` and `final`: human tasks.

## Not done / cut
- Everything that needs the simulator: real generate, inject, reveal values, canary message from the simulator, benchmark, real `demo.json`.

## What to tell people (honest framing for the pitch)
- What is demonstrable today: the engine on 8 hand-built scenarios (H1 to H8), the API on those scenarios (summary, export, trace, reveal rules,
  audit, report, canary alert), masking and the reason rule.
- What is NOT demonstrable today: the Nova Health story on seed 42, loss levels, the benchmark. Say so; do not imply otherwise.

## Risks for integration
- First contact between the real simulator and the strict contract models is untested; a mismatch shows as 500 `engine_error` ("scenario violates the data contract").
- If the simulator lands after the freeze, crash fixes only, one small commit each, approved by Tanish; the first run to do is `generate` seed 42 then `trace`,
  then `python -m app.bench.run --seeds 0 9` to see the runner on real data.
- `main` currently has `feat/engine` only; merge order at the gate is shared files, sim, engine, api, ui. `config.py` was first written on `feat/engine` and extended on `feat/api`; the trial merge was clean.

STOPPED. Waiting for APPROVED PHASE 5.
