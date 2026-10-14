# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

PRATYAKSH (codename PUGMARK) is a hackathon project (INNOVATHON 2026, Problem Statement #18: tracing a data leak across systems). At the time of writing the repo contains **only `README.md` and `docs/`** — no `backend/` or `frontend/` code exists yet. The docs are the spec; implement from them. `README.md` shows the intended layout (`backend/app/{main,config,models}.py`, `common/`, `sim/`, `engine/`, `privacy/`, `report/`, `bench/`, `backend/tests/`, `backend/scripts/`, `frontend/`). `AGENTS.md` and `docs/DECISIONS.md`, `IDEAS.md`, `QUESTIONS.md`, `reports/` are referenced by the docs but not created yet (Phase 0 deliverables). `README.md` links a `LICENSE` that does not exist.

## Commands (once the scaffold exists; from `docs/04_TEST_PLAN.md` and `docs/05_PHASES.md`)

```bash
cd backend && pip install -r requirements.txt          # Python 3.11+, in a venv
cd backend && pytest -q                                # all tests
cd backend && pytest -q tests/engine                   # engine only (also tests/sim, tests/api)
cd backend && pytest -q tests/engine/test_origin.py::<test_name>   # single test
cd backend && python scripts/validate.py scenario tests/fixtures/H1.json
cd backend && python scripts/validate.py trace <trace.json> <scenario.json>
cd backend && uvicorn app.main:app --port 8000 --reload   # GET /api/health
python backend/scripts/make_demo_bundle.py             # regenerate frontend/public/demo.json
cd frontend && npm install && npm run dev              # http://localhost:5173
cd frontend && npm run build && npm run lint
```

Everything must run fully offline. The frontend falls back to `frontend/public/demo.json` (committed) when the backend is down and shows an OFFLINE REPLAY badge.

## Architecture (big picture)

Two sides joined by a frozen JSON contract (`docs/01_DATA_CONTRACT.md`, v1.0 — authoritative for all shapes; snake_case everywhere, TS interfaces in the doc are mirrored 1:1 as Pydantic v2 models in `backend/app/models.py` and `frontend/src/types/contract.ts`):

- **Simulator** (`backend/app/sim/`, `docs/02_SIMULATOR.md`): generates a fictional company ("Nova Health"), its lossy event logs, export artifacts, and a mock Telegram leak. It holds *ground truth* (`ScenarioTruth`, `case_key`) which must never leave the sim/test boundary.
- **Engine** (`backend/app/engine/`, `docs/03_ENGINE.md`): `trace(scenario: dict, top_k=5) -> TraceResult`, a pure deterministic function over the **PublicScenario only**. Pipeline stages: 0 canary pin → 1–2 origin candidates (hard rules `schema` / `watermark_before` / `after_found`, then soft `origin_fit` from MinHash containment, specificity, format similarity, watermark penalty) → 3 custody-path search with penalized hidden hops (`paths.py`) → 4 actor anomaly (`anomaly.py`) → 5 softmax ranking (`rank.py`) → 6 greedy chokepoints → 7 evidence-to-collect (entropy) → graph + text templates. Loss rates per log source are estimated from `seq` gaps (`loss.py`).
- **API** (`backend/app/main.py`, contract §12): FastAPI endpoints (`/api/scenario/generate`, `/api/leak/export`, `/api/trace`, `/api/reveal`, `/api/canary/alert`, `/api/benchmark/...`, `/api/report/{trace_id}`, `/api/audit`) wrapping sim + engine, plus the privacy layer (`privacy/mask.py`, audit log at `backend/data/audit.jsonl`) and report generator.
- **Frontend** (`frontend/`, `docs/FRONTEND.md`, `UI_UX_DESIGN.md`, `FEATURES.md`): React + Vite + TS + Tailwind, Cytoscape provenance graph, Recharts, Framer Motion.

Shared code both sides must use verbatim: `backend/app/common/sketch.py` (HMAC-SHA256 bottom-k MinHash; normalization/containment spec in contract §6). The simulator imports it, never reimplements it. All tunable weights live in one dict in `backend/app/config.py` (`ENGINE = {...}`, listed in `docs/03_ENGINE.md` §3); change them nowhere else and log changes in `docs/DECISIONS.md`.

## Invariants that are easy to break

- The engine **must not** import `app.sim`, read truth/`params.log_loss`/`case_key`, or make decisions from artifact/event id values (a test permutes ids). API responses must never contain `"truth"` or `"case_key"`.
- Determinism: seeded randomness only, no wall-clock, network, or global state inside sim/engine. Same seed → byte-identical scenario JSON; same scenario → identical trace JSON (except audit timestamps).
- Timestamps are ISO-8601 UTC with trailing `Z`, seconds precision; "off hours" = 22:00–05:00 UTC or weekend. Floats in API responses rounded to 4 decimals.
- Data is masked everywhere outside the audited reveal flow (`reveal` requires a justification and writes an audit entry).
- Wording guardrails: probabilities are **relative likelihoods**, never "calibrated"; don't claim "zero exposure", real Telegram monitoring, or legal deadlines in hours. Everything shown is SIMULATED.
- `docs/04_TEST_PLAN.md` expected values (hand-written scenarios H1–H8 built by `backend/tests/fixtures/mini.py`, independent of the simulator) are human-owned: never edit/loosen them to make a test pass — record the concern in `docs/QUESTIONS.md`.
- Don't add features, endpoints, fields, or files the docs don't describe; ideas go in `docs/IDEAS.md`, ambiguity choices (simplest reading) in `docs/DECISIONS.md`.
- Tune only on benchmark seeds 0–49; final report on seeds 50–199.

## Workflow rules from `docs/MASTER_PROMPT.MD` / `05_PHASES.md` / `06_WORK_SPLIT.md`

Two developers (Tanish: engine + api/shared files; Anmol: sim + ui) with per-module folder ownership and branches `feat/sim|ui|engine|api`; never commit to `main` or force-push; commit messages prefixed by module (`engine: add loss model`). Work proceeds in gated phases 0–5: build only the current phase, write `docs/reports/phase-N-<module>.md`, print `STOPPED. Waiting for APPROVED PHASE N.` and wait. Shared/frozen files (contract, `config.py`, `models.py`, `common/sketch.py`, `tests/fixtures/`, docs 00–06) are changed only by Tanish's sessions. The master prompt asks agents to first ask which developer/module a session is for and to stay inside that module's folders — follow it when the user has set up a phase-scoped agent session. Write tests first and show real command output before claiming anything works.
