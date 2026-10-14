# Phase 0 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- `common/sketch.py` exactly as contract section 6 (normalize, h64, make_sketch, jaccard, containment, K_DEFAULT, IDENTIFIER_COLUMNS): done.
- Tests for all contract section 6 vectors (6 normalization vectors, jaccard identical = 1.0 and disjoint = 0.0, 50 percent subset containment within 0.05 of 1.0, determinism, small-set exactness): done.
- `tests/fixtures/mini.py` building H1 to H8 per `docs/04_TEST_PLAN.md` sections 2 and 3, `build(name)` plus committed `H1.json` to `H8.json`: done.
- Fixture tests (structure, constants from 04 sec 2 and 3, committed JSON equals builder output, H8 is H1 renamed): done.

## Files created or changed
- backend/app/common/sketch.py
- backend/tests/engine/test_sketch.py
- backend/tests/engine/test_fixtures.py
- backend/tests/fixtures/mini.py
- backend/tests/fixtures/H1.json ... H8.json
- docs/DECISIONS.md, docs/QUESTIONS.md (appended lines, bookkeeping rule from AGENTS.md)
- docs/reports/phase-0-engine.md

## Commands run and real output
$ cd backend && python3 -m pytest -q tests/engine      # before implementation
ImportError: cannot import name 'IDENTIFIER_COLUMNS' from 'app.common.sketch'
2 errors in 0.19s

$ cd backend && python3 -m tests.fixtures.mini && python3 -m pytest -q tests/engine
................................                                         [100%]
32 passed in 1.47s

$ cd backend && python3 -m pytest -q
................................                                         [100%]
32 passed in 1.09s

Independent sanity check of fixture values against 04 (script run from backend/):
H1 art:E1 containment=1.0000 format_sim=1.0000
H1 art:E2 containment=0.9993 format_sim=0.1111
H3 art:E1 containment=1.0000 format_sim=0.6667
H4 art:E1 containment=1.0000 / art:E5 containment=1.0000
H7 art:E1 containment=0.0000 / art:E2 containment=0.0000
H1 E1 watermark term = -0.3333

## Gate checks
- [x] `test_sketch.py` passes (all contract vectors): pass
- [x] Fixtures H1 to H8 build and match 04 sec 2 constants: pass
- [ ] Fixtures pass `validate.py`: not run, `backend/scripts/validate.py` is empty (Anmol, Phase 1). Local structural check in `test_fixtures.py` passes instead.
- [ ] `test_mask.py`, `/api/health`, `npm run build`, tag `ok-0`: not engine scope (api / ui sessions, Tanish at the gate).

## Not done / cut
- Nothing from the engine Phase 0 list is cut. `config.py`, `models.py`, `privacy/mask.py`, `main.py` are api-module work and were not touched. Engine stage code (Phase 1) not started.

## Contract or spec discrepancies
- 04 sec 7 gate requires `validate.py`, which does not exist yet (logged in docs/QUESTIONS.md).
- Contract sec 8 forbids key `rows`, but `Event.rows` is required (already in docs/QUESTIONS.md); the fixture check allows `rows` for that reason.
- Test plan lists leak columns without customer_id/email, so leak sketches exist only for `phone` and `policy_no` (logged in docs/DECISIONS.md).

## Risks for integration
- Fixture JSON is built by `mini.py`; `test_names_and_committed_json_match_builder` fails if either is edited alone, so regenerate with `python3 -m tests.fixtures.mini` from `backend/`.
- Anmol's UI placeholder `demo.json` (Phase 0) can be hand-built from `tests/fixtures/H1.json`.
- Work is on branch `feat/engine`, not yet merged to `main`.

STOPPED. Waiting for APPROVED PHASE 0.
