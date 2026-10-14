# Phase 0 report: api
Developer: Tanish | Date: 2026-10-14

## Done
- Git repo and `.gitignore` committed; branch `feat/api` from `main` (which now contains `feat/engine`): done.
- Backend skeleton: `requirements.txt` (committed), `app/main.py` with `GET /api/health` and CORS for `http://localhost:5173`, `config.py` (ENGINE from the engine phases plus `CONTRACT_VERSION`): done.
- `models.py`: strict Pydantic v2 mirrors of contract sections 2 to 13: done.
- `privacy/mask.py` with tests for every contract section 10 vector: done.
- README run commands verified and corrected; `AGENTS.md`, `CLAUDE.md`, `docs/DECISIONS.md`, `IDEAS.md`, `QUESTIONS.md`, `docs/reports/` committed: done.

## Files created or changed
- backend/app/{main,models,config}.py, backend/app/privacy/{__init__,mask}.py, backend/app/__init__.py
- backend/tests/api/{test_mask,test_health,test_models}.py, backend/tests/__init__.py, backend/tests/api/__init__.py
- backend/requirements.txt, .gitignore, README.md, AGENTS.md, CLAUDE.md
- docs/{DECISIONS,IDEAS,QUESTIONS}.md, docs/reports/phase-0-api.md

## Commands run and real output
$ cd backend && ../.venv/bin/python -m pytest -q tests/api       # before implementation
3 errors during collection (empty modules)

$ cd backend && ../.venv/bin/python -m pytest -q tests/api
39 passed, 1 warning in 0.96s

$ uvicorn app.main:app --port 8000   then   curl http://127.0.0.1:8000/api/health
{"status":"ok","contract_version":"1.0","engine_version":"1.0.0"}
$ curl -X OPTIONS .../api/health -H "Origin: http://localhost:5173" ...   -> 200, access-control-allow-origin: http://localhost:5173

Fresh clone of feat/api, `cd backend && pytest -q` (the README command):
146 passed, 1 warning in 5.17s     (107 engine + 39 api)

Strict models against reality: all 8 fixture scenarios validate as PublicScenario and round-trip; the real engine
output for H1 to H8 validates as TraceResult and round-trips (extra="forbid"). This also checks the engine against
the contract shape.

## Gate checks
- [x] `pytest -q` passes (sketch vectors, mask vectors, fixtures, models): pass
- [x] `uvicorn app.main:app --port 8000` starts and `/api/health` answers: pass
- [ ] `cd frontend && npm run build` / `npm run dev`: not run, frontend is Anmol's.
- [ ] Contract frozen, tag `ok-0`: yours. NOTE the contract text still lacks `origin_ranking`; models.py has it.
- [ ] `validate.py scenario tests/fixtures/H*.json`: validator is still an empty file (Anmol).

## Not done / cut
- Nothing from the api Phase 0 list is cut. Audit, report, bench, other endpoints are Phase 1 to 4.
- `.venv` was created locally; not committed.

## Contract or spec discrepancies
- `origin_ranking`: in 03/04/engine and models.py, missing from docs/01 section 9 (QUESTIONS.md). Needs your decision and an announcement to Anmol before the UI types are final.
- master prompt says CLAUDE.md "as a copy of AGENTS.md"; kept the existing richer file (DECISIONS.md).
- README had an invented benchmark chart and guardrail-violating wording; removed.

## Risks for integration
- `docs/01` and `frontend/src/types/contract.ts` must get `origin_ranking` too, or the UI will not see it.
- Merged state: `main` now includes `feat/engine` (69f03d1, local, not pushed). `feat/api` is on top of it.
- The simulator is still empty, so Phase 1 api (generate/export/trace endpoints) can only use fixtures until it lands.

STOPPED. Waiting for APPROVED PHASE 0.
