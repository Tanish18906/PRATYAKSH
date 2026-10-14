# AGENTS.md: working rules for coding agents on PRATYAKSH (codename PUGMARK)

Hackathon project (INNOVATHON 2026, PS #18: tracing a data leak across systems). Two developers, several agents. The docs in `docs/` are the spec. Claude Code also reads `CLAUDE.md`; this file is the tool-neutral version (Codex, Antigravity: start the session with "Read AGENTS.md and follow it").

## 1. Before you do anything

1. Ask: "Which developer am I working for (Tanish or Anmol), and which module?" Wait for the answer. Never guess from the machine, git config or paths.
   - Anmol: `sim` or `ui`. Tanish: `engine` or `api`.
2. Confirm in one line: `Developer: X | Module: Y | Phase: N | Allowed folders: ... | I will not touch anything else.`
3. Read, in order: this file, `docs/00_PROJECT_CONTEXT.md`, `docs/01_DATA_CONTRACT.md`, `docs/05_PHASES.md`, `docs/06_WORK_SPLIT.md`, `docs/04_TEST_PLAN.md`, then your module doc (sim: `02_SIMULATOR.md`; engine: `03_ENGINE.md`; api: contract sec 12 plus the interface parts of 02 and 03; ui: `UI_UX_DESIGN.md`, `FRONTEND.md`, `FEATURES.md`).
4. Precedence: the contract wins for shapes, `00` wins for intent, later specs win for details. Log conflicts in `docs/QUESTIONS.md` and continue.

## 2. Ownership (edit only your own folders)

| Module | Owner | Allowed folders | Branch |
|---|---|---|---|
| sim | Anmol | `backend/app/sim/`, `backend/tests/sim/`, `backend/scripts/validate.py` | `feat/sim` |
| ui | Anmol | `frontend/` | `feat/ui` |
| engine | Tanish | `backend/app/engine/`, `backend/app/common/`, `backend/tests/engine/`, `backend/tests/fixtures/` | `feat/engine` |
| api | Tanish | `backend/app/main.py`, `privacy/`, `report/`, `bench/`, `backend/tests/api/`, `backend/scripts/make_demo_bundle.py`, `config.py`, `models.py`, `backend/requirements.txt`, repo setup files, `README.md`, bookkeeping docs | `feat/api` |

Shared and frozen (only Tanish's sessions change them): `docs/00` to `06`, `docs/01_DATA_CONTRACT.md`, `backend/app/config.py`, `backend/app/models.py`, `backend/app/common/sketch.py`, `backend/tests/fixtures/`.

Need a change outside your folders? Write it in `docs/QUESTIONS.md` and work on something else. Only a human typing `OVERRIDE OWNERSHIP: <module>` extends your scope.

## 3. Phase gating

Phases 0 to 5 (`docs/05_PHASES.md`). Build ONLY the current phase for your module, then:

1. Write `docs/reports/phase-N-<module>.md` using section 7.
2. Print exactly: `STOPPED. Waiting for APPROVED PHASE N.`
3. Do nothing until a human types `APPROVED PHASE N` (or `REJECTED PHASE N: <reason>`: fix only that, re-report). Never start the next phase early.
4. If you are 20 percent past the phase time box, stop and report.

## 4. Rules

1. Tests first, then implement. Show the real command and its real output. Never claim "works" without it.
2. Never edit, skip or weaken a human-written test, fixture or expected value in `docs/04_TEST_PLAN.md`. Write the concern in `docs/QUESTIONS.md`.
3. Pure, deterministic code: seeded randomness only, no wall clock, no network, no global state in sim or engine. All tunable numbers in `backend/app/config.py` (`ENGINE = {...}`), nowhere else.
4. No new dependency without a one-line note in `docs/DECISIONS.md`.
5. Do not add features, endpoints, fields or files the docs do not describe. Ideas go in `docs/IDEAS.md`. Ambiguity: choose the simplest reading and log one line in `docs/DECISIONS.md`.
6. Keep changes small, commit often on your own branch, prefix commit messages with the module (`engine: add loss model`). Never commit to `main`, never force push, never rewrite history.
7. Blocked more than 5 minutes: write it in `docs/QUESTIONS.md`, do other work in the same phase; if nothing is left, report and stop.
8. Tune engine weights on benchmark seeds 0 to 49 only; report numbers on seeds 50 to 199, once. Log every config change with before and after numbers in `docs/DECISIONS.md`.

## 5. Invariants that are easy to break

- The engine takes the PublicScenario dict only. It must not import `app.sim`, read truth, `params.log_loss` or `case_key`, or decide from artifact or event id values (test H8 permutes ids).
- Ground truth (`ScenarioTruth`), the case key and raw rows never reach the engine, the API responses or the UI. API JSON must never contain `"truth"`, `"case_key"` or `"true_path"`.
- Same seed gives byte-identical scenario JSON; same scenario gives identical trace JSON (except audit timestamps).
- Timestamps are ISO-8601 UTC with trailing `Z`, seconds precision. No time-zone conversion. Off hours = 22:00 to 05:00 UTC or weekend. Floats in API responses rounded to 4 decimals.
- Sketch and normalization code lives only in `backend/app/common/sketch.py`; the simulator imports it, never reimplements it.
- Data is masked everywhere except `POST /api/reveal`, which requires a reason of at least 8 characters and writes an audit entry.
- Everything runs offline. The frontend falls back to `frontend/public/demo.json` and shows OFFLINE REPLAY when the backend is down. The frontend never recomputes scores, ranks or paths.

## 6. Wording guardrails

- Probabilities are "relative likelihood", never "calibrated".
- Never claim zero exposure, guaranteed attribution, real Telegram monitoring, real-world benchmark accuracy, or a legal deadline in hours.
- Everything (company, data, Telegram) is labelled SIMULATED.
- The report must contain "Verify current legal timelines with counsel."
- Output is a ranked set of hypotheses for a human investigator, never a finding of guilt.

## 7. Phase report template (`docs/reports/phase-N-<module>.md`)

```
# Phase N report: <module>
Developer: <Tanish|Anmol> | Date: <date>

## Done
- <deliverable from docs/05_PHASES.md>: <status>

## Files created or changed
- <path>

## Commands run and real output
$ <command>
<pasted output>

## Gate checks
- [ ] <check from docs/05_PHASES.md>: pass | fail

## Not done / cut
- <item and why>

## Contract or spec discrepancies
- <item, also logged in docs/QUESTIONS.md>

## Risks for integration
- <item>

STOPPED. Waiting for APPROVED PHASE N.
```
