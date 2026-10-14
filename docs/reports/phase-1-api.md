# Phase 1 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- `POST /api/scenario/generate`, `GET /api/scenario/{id}` (summary, or full scenario with `full=true`), `POST /api/leak/export`, `POST /api/trace` (calls the engine): done.
- JSON error shape `{"error": {"code", "message"}}` with codes bad_request 400, not_found 404, not_ready 409, engine_error 500: done.
- Audit append (`privacy/audit.py`): in memory plus `backend/data/audit.jsonl`, one entry per successful generate / export / trace: done.
- Request-body models and strict contract validation at the API boundary; 4-decimal rounding; defensive masking of the leak preview: done.

## Important: simulator not available
`backend/app/sim/*` is still an empty file set in this tree, so `generate_scenario` cannot be called. The api is wired to it
through one hook (`main._sim()`). Until it exists: `generate` answers 409 `not_ready`, and H1..H8 are loaded at startup so
`get`, `export` and `trace` can be exercised. The gate item "curl generate then trace on seed 42" is therefore NOT met;
the same flow was verified on `scn:H1`. When the simulator lands no api code needs to change if its signature is
`generate_scenario(archetype, seed, log_loss, canary_mode, scale)` returning an object with `.public`, as in docs/02 sec 3.
A test with a fake simulator covers that call path.

## Files created or changed
- backend/app/main.py, backend/app/models.py (request models), backend/app/privacy/audit.py
- backend/tests/api/{conftest,test_scenario_api,test_audit}.py
- README.md (curl example), docs/DECISIONS.md, docs/reports/phase-1-api.md

## Commands run and real output
$ cd backend && ../.venv/bin/python -m pytest -q tests/api/test_scenario_api.py tests/api/test_audit.py   # before implementation
4 failed, 15 errors

$ cd backend && ../.venv/bin/python -m pytest -q
165 passed, 1 warning in 9.44s      (107 engine + 58 api)

Live server (uvicorn on :8000), real HTTP:
POST /api/scenario/generate {"log_loss":0.4,...}  -> 409 {"error":{"code":"not_ready",...}}
POST /api/scenario/generate {"log_loss":0.95,...} -> 400 {"error":{"code":"bad_request","message":"log_loss: Input should be less than or equal to 0.8"}}
GET  /api/scenario/scn:nope                       -> 404 {"error":{"code":"not_found",...}}
GET  /api/scenario/scn:H1                         -> counts {actors 5, locations 9, datasets 1, events 39, artifacts 2}
POST /api/leak/export {scn:H1, message 1}         -> file {name mini_leak.csv, size_bytes 109680}
POST /api/trace {scn:H1}                          -> 200 in 0.013 s, 12,265 bytes; origin art:E1 0.9967; top hypothesis act:ann 0.9662;
                                                     chokepoint[0] perm:act:ann@egress "Block outbound uploads from Ann's laptop"
grep -c '"truth"|"case_key"|"true_path"' on summary and full responses -> 0, 0
backend/data/audit.jsonl after export + trace: two lines (aud:0001 telegram_export, aud:0002 trace); the three failed calls wrote none.

## Gate checks
- [ ] `curl` generate then trace works on seed 42 without errors: NOT MET, no simulator. Same flow works on scn:H1 (above).
- [x] Response JSON contains none of `"truth"`, `"case_key"`: pass (live grep and tests).
- [x] Error shape, audit append, masking guard, determinism over HTTP: pass.

## Not done / cut
- `GET /api/audit`, `POST /api/reveal` (Phase 2); inject, canary alert, report, benchmark, `make_demo_bundle.py` (Phase 3 and 4).
- No in-process cache of trace results (needed by `GET /api/report/{trace_id}` in Phase 3).

## Contract or spec discrepancies
- Contract has no upper bound for `top_k`; I chose 20 (DECISIONS.md).
- `origin_ranking` still missing from the contract text (open since Phase 0).

## Risks for integration
- The simulator's real output has never passed through `PublicScenario`. If it differs in any detail (extra key, id format,
  an artifact column list), the API returns 500 `engine_error` with "scenario violates the data contract", which is
  intended but will be the first thing to show up on integration.
- The simulator's `masked_preview` is trusted only after the re-mask guard; a value with no `*` is re-masked by column name.
- Request validation on 16 MB-scale scenarios (bench) re-validates the full scenario per call; fine at 39 events and expected
  fine at about 3,000 but not measured on real simulator output.

STOPPED. Waiting for APPROVED PHASE 1.
