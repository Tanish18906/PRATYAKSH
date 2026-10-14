# Phase 2 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- `trace` returns the full contract `TraceResult` (origin table, hypotheses with evidence, actor and location ranking, graph, chokepoints, recommended evidence), validated by the strict model on every call, with rounding to 4 decimals: done.
- Response time: `POST /api/trace` on a 3,040-event, 45-actor scenario takes 0.048 s over real HTTP (including full contract validation): done, under the 3 s target.
- `GET /api/audit` with optional `scenario_id`: done.
- `POST /api/reveal` with the reason rule and an audit entry: done and tested with a fake private store.

## Important: simulator not available
`backend/app/sim/*` is still an empty file set, so there is no private store: a real `reveal` cannot return a value and
`POST /api/reveal` answers 409 `not_ready` after the reason, scenario and target checks (verified live). The success path,
audit entry and the `no-store` header are covered by tests that supply a fake `reveal_value`; the api needs no change when the
simulator provides `reveal_value(bundle, row_index, field)` as in docs/02 sec 3.

## Files created or changed
- backend/app/main.py, backend/app/models.py (RevealRequest, RevealResponse, AuditList)
- backend/tests/api/test_reveal_audit.py
- docs/DECISIONS.md, docs/reports/phase-2-api.md

## Commands run and real output
$ cd backend && ../.venv/bin/python -m pytest -q tests/api/test_reveal_audit.py     # before implementation
8 failed, 2 passed

$ cd backend && ../.venv/bin/python -m pytest -q
175 passed, 1 warning in 12.42s     (107 engine + 68 api)

Live server, real HTTP:
POST /api/reveal (no reason)               -> 400 reason_required
POST /api/reveal (reason "short")          -> 400 reason_required
POST /api/reveal (good reason, no store)   -> 409 not_ready, no audit line written
POST /api/trace  (scn:BIG, 3,040 events)   -> 200 in 0.048 s, 16,724 bytes
GET  /api/audit                            -> one entry: aud:0001 trace scn:BIG

## Gate checks
- [ ] `pytest -q` all green including seed 42 integration (loss 0.0, 0.2, 0.4): all current tests green (175); seed 42 NOT run, no simulator.
- [x] Reveal reason rule (missing, empty, short, whitespace padded): pass
- [x] Audit: exactly one entry per generate / export / trace / reveal, none on failures, reveal visible in `GET /api/audit`: pass
- [x] `trace` under 3 s: pass on a scaled synthetic scenario; real demo scenario untested.

## Not done / cut
- Real reveal values (need the simulator's private store). Inject, canary alert, report, benchmark, demo bundle: Phase 3 and 4.
- Audit entries for inject, canary alert, report export, benchmark run (their endpoints are Phase 3 and 4).

## Contract or spec discrepancies
- `origin_ranking` still absent from the contract text (open since Phase 0).
- 04 sec 5 says reveal is exercised against a real scenario; until the simulator lands the success path is only test-covered.

## Risks for integration
- Reveal is the one endpoint that has never touched real simulator data. Row order ("ascending created_at", docs/02 sec 8) and the
  field list must match `leak_sample.columns`; the api checks `row_index < leak_sample.row_count` and `field in columns`, so a
  simulator that renders fewer rows than `row_count` will surface as 500 `engine_error` on reveal.
- `masked_preview` rows from the simulator must stay masked at the source; the api's re-mask guard is a safety net, not the design.

STOPPED. Waiting for APPROVED PHASE 2.
