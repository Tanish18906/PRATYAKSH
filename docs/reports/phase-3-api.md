# Phase 3 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- `POST /api/inject`, `POST /api/canary/alert`, `GET /api/report/{trace_id}` (HTML), `backend/scripts/make_demo_bundle.py`: done.
- Audit for every action that has an endpoint now: generate, export, trace, reveal, inject, canary alert, report export (benchmark run is Phase 4).
- Masking everywhere: leak preview re-mask guard (Phase 1) plus an email scrub on every response except reveal; swept in a test across scenario, full scenario, export, trace, report and audit.
- Log-loss regeneration through `generate`: covered by a test with two losses giving two scenarios.

## Important: simulator not available
`backend/app/sim/*` is still empty, so inject and a simulator-made canary message cannot be exercised against the real thing:
- `inject` answers 409 `not_ready` without a simulator bundle (tested with a fake `inject_leak`).
- `canary/alert` works on fixtures (H6) from the public registry and uses `canary_alert` when a bundle exists.
- `make_demo_bundle.py` without `--fixture` exits 1 with a clear message. `frontend/public/demo.json` was NOT written.
So gate items "judge flow with three actors" and "generate A2 and A3, trace valid" are not met.

## Files created or changed
- backend/app/main.py, backend/app/models.py, backend/app/report/{build.py,template.html}, backend/scripts/make_demo_bundle.py
- backend/tests/api/{test_inject_canary_report,test_demo_bundle}.py
- README.md, docs/DECISIONS.md, docs/reports/phase-3-api.md

## Commands run and real output
$ cd backend && ../.venv/bin/python -m pytest -q tests/api/test_inject_canary_report.py tests/api/test_demo_bundle.py   # before implementation
collection error (modules missing)

$ cd backend && ../.venv/bin/python -m pytest -q
193 passed, 1 warning in 14.97s     (107 engine + 86 api)

Live server, real HTTP:
POST /api/canary/alert (scn:H6, can:E2-1)   -> alert {export art:E2, ts 2026-10-12T08:00:00Z}; trace origin_pinned true; top actors bob, cat
POST /api/canary/alert (scn:H1, mode off)   -> 400 bad_request
POST /api/inject (no simulator)             -> 409 not_ready
GET  /api/report/trc:H6                     -> 200 text/html, 6,305 bytes, legal line present once
GET  /api/audit                             -> aud:0001 canary_alert, aud:0002 report_export (one entry per action)
$ python backend/scripts/make_demo_bundle.py --fixture H2 --out <tmp>    -> 55,330 bytes, audit [telegram_export, trace, report_export]
$ python backend/scripts/make_demo_bundle.py --out <tmp>                  -> "error: the simulator is not available; ..." exit 1

## Gate checks
- [x] API tests from 04 sec 5: health, no truth/case_key/true_path, masked export, valid trace, reveal reason rule and audit, one audit entry per action (generate, export, trace, reveal, inject, canary alert, report export), mask vectors, report has no unmasked email and carries the legal line: pass.
- [ ] A2 and A3 scenarios pass the validator and trace: NOT RUN (no simulator, no validator).
- [ ] Offline replay with the real bundle: NOT RUN (no simulator). A placeholder bundle can be built from a fixture.
- [ ] Judge flow, three injected actors under 5 s: NOT RUN.
- [ ] Tag `ok-3`: yours.

## Not done / cut
- Benchmark endpoints and baselines (Phase 4). Writing the real `frontend/public/demo.json`.

## Contract or spec discrepancies
- `origin_ranking` still absent from the contract text (open since Phase 0); it is in `models.py` and in `DemoBundle.trace`, so the UI types must have it.
- Contract does not define the canary alert flow beyond the response shape; the "alert counts as a canary hit for that trace" reading is mine (DECISIONS.md).

## Risks for integration
- The report and bundle have only seen fixture-shaped data (names are slugs like "bob"); real simulator display names should read better, but check the wording once.
- `DemoBundle` is strictly validated; a simulator scenario that violates the contract will stop the bundle script (intended).
- Report text for A3 relies on a heuristic (send hop to an external location, or an `sftp` location on the path); confirm against the real A3 once it exists.

STOPPED. Waiting for APPROVED PHASE 3.
