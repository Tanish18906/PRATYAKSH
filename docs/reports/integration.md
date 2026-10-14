# Integration report: simulator + engine + api

Date: 2026-10-14 | Branch: `integrate/sim-engine-api` merged into `main` (merge commit, pushed) | no tags.

## Status
**GREEN and merged into `main`.** `pytest -q`: 254 passed, 0 failed. The one red test from the first pass (an api test written before the
simulator existed) was replaced with approval. Seed 42 passes every 04 sec 4 expectation at log_loss 0.0, 0.2, 0.4. The live exercise of
reveal, inject, canary alert, report and audit passes mechanically. **One real functional gap was found and is NOT fixed (engine/sim, see
Failures): the A2 key-theft leaker cannot be attributed, even with no log loss.**

## What was merged, in order (no conflicts anywhere)
1. `origin/feat/sim` (6 commits, simulator phases 0 to 5). Step 2 diff over `config.py`, `models.py`, `common/`, `docs/01`, `tests/fixtures/`: empty, the simulator touched no shared file.
2. `feat/engine`: already contained in `main` (merge `69f03d1`), nothing to do.
3. `feat/api` (api phases 0 to 5, hostile-test fixes: audit lock, nullable `Event.object`, deterministic candidate tie order).
4. Glue commit `5d1ac81`: startup `warm_cache` in a background thread, README commands, `backend/scripts/smoke.py`, one test, decision log.
5. Approved follow-up: stale test replaced, `frontend/public/demo.json` generated, live exercise, small benchmark, this report.

Housekeeping: 15 local untracked 0-byte placeholder files (old sim stubs, `validate.py`) sat at the same paths as the simulator's real
files; they were moved to the scratchpad (not deleted) so the merge could land. `backend/app/common/__init__.py` is still untracked and unneeded (namespace package).

## pytest summary (real; fresh clone with a new venv gave the same on the earlier commit)
```
......................................                                   [100%]
254 passed, 1 warning in 24.17s
```
(The earlier run had 252 passed and 1 failed: the stale `test_cli_without_simulator_or_fixture_fails_clearly`.)

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

## Live exercise against the real simulator (single worker, real HTTP, 31 checks, 0 failed mechanically)
| Item | Result |
|---|---|
| reveal, 7-char reason | PASS: 400 `reason_required` |
| reveal, 8-char reason | PASS: 200, value `+91-73...` unmasks to the preview, masks back to `+91-73******83` |
| revealed value absent from every other response (scenario, full scenario, export, trace, report, audit) | PASS |
| reveal full_name and policy_no (row 3), row out of range | PASS (200, 200, 400) |
| inject, 8 actors (A1 x4, A2 x2, A3 x1, A5 x1 seen) | PASS mechanically: 200, inject 0.31 to 0.58 s, trace 0.010 to 0.022 s. **Detection: injected actor in top 3 for 4 of 8** (see below) |
| inject unknown actor, unknown base | PASS (400, 404) |
| canary alert (can:E1-1 on scn:A1-42-L40-C) | PASS: export art:E1, ts = found_ts, origin pinned, message address masked (`c***@example.net`) |
| canary alert, mode off / unknown canary | PASS (400 / 404) |
| report | PASS: 200 html, legal line, SIMULATED, no deadline in hours, observed and inferred evidence, containment actions, no unmasked email, unknown trace 404 |
| audit | PASS: 27 entries, ids unique and contiguous, all 7 action types recorded, reveal entries hold field, reason and row but never the value, scenario filter works |
| grep of 40 live responses for truth / case_key / true_path | PASS: 0 hits |

## Small benchmark, real simulator, seeds 0 to 9, loss 0.0 and 0.4 (via `POST /api/benchmark/run`)
Result: status `done`, **no crash**, 20 scenarios in 1.0 s total = **0.05 s per scenario, 0.10 s per seed** (both loss levels).
`reported_on` is "seeds 0-9 (includes tuning seeds)". Information only, 10 seeds is not a result: origin top-1 pugmark 1.00 vs largest export 0.00
and most recent export 0.00; actor top-1 pugmark 0.70 vs last accessor 0.00 and biggest exporter 0.00 to 0.10. Nothing was tuned and the full 200 seeds were not run.

## Failures, with owner
1. **A2 (compromised API key) leaker is not attributable, even at loss 0.0.** Owner: Tanish (engine) and Anmol (sim), a spec mismatch between `03_ENGINE` sec 7 and `02_SIMULATOR` sec 8.
   - Command: `POST /api/scenario/generate` seed 42 A1 loss 0.0, then `POST /api/inject {actor: act:partner-api-key-7}`, then `POST /api/trace`.
   - Expected (02 sec 8 A2): the key is the true actor and appears in the ranking with its `api_call` as an observed hop.
   - Actual: key ABSENT from `actor_ranking` (0 of 11 listed); no observed `api_call` hop in the top 5 hypotheses; top hypothesis is a random analyst at 0.09.
     The benchmark agrees: A2 seeds 1, 4, 7 all missed at both loss levels.
   - Likely cause: no actor has `ext:unknown-host` in `access`, and engine M2 requires the actor to have the external location in `access`, so the observed move can never be completed.
2. Service-account creator exclusion: injecting `act:etl-nightly` (it created the origin export and also made the API call) cannot be named by design (03 sec 8). Owner: Tanish (engine), decision needed.
3. Detection on inject smoke: 4 of 8 in top 3 (the three misses are service accounts, see above and the earlier ACTOR_ALT_MAX note; `act:arohan-vey`, a plain analyst, ranked 6th).
All three are logged in `docs/QUESTIONS.md`. No glue bug was found; nothing in engine or sim was changed.

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
- **A2 attribution (above) is broken.** Until the engine rule or the simulator's access lists change, any demo that injects a service key will not show the key.
- The full benchmark (200 seeds, loss 0.0 to 0.6) has not been run, so there are no reportable accuracy numbers and the sanity gates (04 sec 6.4) are unjudged. Run it on seeds 50 to 199 only after tuning on 0 to 49.
- `frontend/` is untouched except `frontend/public/demo.json`; `src/types/contract.ts` still needs `object: string | null` and `origin_ranking`.
- Not tagged. `ok-N` tags are yours.
- `backend/app/common/__init__.py` is still untracked (works as a namespace package).
- `docs/04_TEST_PLAN.md` sec 4 `tests/integration/test_seed42.py` does not exist as such; the simulator's `tests/sim/test_seed42.py` passes and the live table above is the equivalent engine-plus-api check.
