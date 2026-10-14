# PUGMARK: Work Split (Tanish and Anmol)

Proposed assignment. Tanish confirms; any change is written into `docs/DECISIONS.md`.

---

## 1. Ownership

| Area | Owner | Suggested agent | Folders |
|---|---|---|---|
| Simulator, mock Telegram, canary and inject logic | Anmol | Codex | `backend/app/sim/`, `backend/tests/sim/`, `backend/scripts/validate.py` |
| Whole frontend | Anmol | Antigravity | `frontend/` |
| Engine | Tanish | Claude Code | `backend/app/engine/`, `backend/app/common/`, `backend/tests/engine/` |
| API, privacy, report, benchmark | Tanish | second Claude Code session (or Codex) | `backend/app/main.py`, `backend/app/privacy/`, `backend/app/report/`, `backend/app/bench/`, `backend/tests/api/`, `backend/scripts/make_demo_bundle.py` |
| Shared and frozen files | Tanish only | | `docs/01_DATA_CONTRACT.md`, `backend/app/config.py`, `backend/app/models.py`, `backend/app/common/sketch.py`, `backend/tests/fixtures/`, `docs/04_TEST_PLAN.md` |
| Docs written by ChatGPT | reviewed by Tanish | | `docs/UI_UX_DESIGN.md`, `docs/FRONTEND.md`, `docs/FEATURES.md`, `docs/DEMO_AND_PITCH.md` |

Rule: you only edit files in your own folders. If you need a change in someone else's folder or in a shared file, write it in `docs/QUESTIONS.md` addressed to the owner and keep working on something else.

Change from your last message: I moved the benchmark, chokepoints, report and API to Tanish, because Anmol already carries the simulator, the Telegram part and the whole frontend. If Anmol finishes early he helps with benchmark code (baselines B1 to B4 are separable) and with demo rehearsal. Tell me if you want it split differently.

---

## 2. Interfaces between the two sides

| From | To | Interface |
|---|---|---|
| Anmol's simulator | Tanish's API and engine | `generate_scenario()`, `inject_leak()`, `reveal_value()`, `canary_alert()`, `to_summary()`, `get_bundle()` as defined in `02_SIMULATOR.md` section 3, and the PublicScenario shape in the contract |
| Tanish's API | Anmol's frontend | HTTP endpoints in contract section 12, and the offline `demo.json` bundle (contract section 13) |
| Tanish's fixtures | Anmol's frontend | `backend/tests/fixtures/H*.json` as sample inputs before the simulator exists |
| Anmol's validator | everyone | `python backend/scripts/validate.py ...` |

Until the real API is up, Anmol's UI runs on `public/demo.json` and the fixtures. Until the real simulator is up, Tanish's engine runs on the fixtures.

---

## 3. Git rules

- One repo. Branches: `feat/sim`, `feat/ui`, `feat/engine`, `feat/api`. Nobody commits to `main` except at a gate.
- Commit small and often on your branch. Message format: `sim: add loss model` (module prefix).
- At a gate (see `05_PHASES.md`): merge into `main` in this order: shared files, sim, engine, api, ui. Whoever merges runs `cd backend && pytest -q` and `cd frontend && npm run build` straight after. If red, fix before tagging.
- Tags: `ok-0` to `ok-4`, `final`. If something breaks later, `git checkout ok-N -- <path>` to recover a module.
- Never force push. Never rewrite history.
- Generated data (`backend/data/`) and `node_modules` are in `.gitignore`. `frontend/public/demo.json` IS committed.

---

## 4. Approvals

| Phase approval for | Who says `APPROVED PHASE N` |
|---|---|
| sim and ui agents | Anmol (Tanish checks the sim output against the contract) |
| engine and api agents | Tanish |
| merge to main and the tag | Tanish |
| code freeze exceptions | Tanish |

Tanish has the final say on scope. If you disagree, say it once, then follow the decision.

---

## 5. Communication

- Blocked for more than 10 minutes: tell the other person. Do not wait silently.
- Every gate: a 3-minute sync in chat: what passed, what is red, what is cut.
- Agents write questions in `docs/QUESTIONS.md`, decisions in `docs/DECISIONS.md`, ideas they are NOT building in `docs/IDEAS.md`.

---

## 6. Load and cut order

Anmol carries the most (simulator, Telegram, frontend). To protect the demo path, if Anmol falls behind, cut in this order:
1. A4 and A5 archetypes.
2. Canary mode and its alert flow.
3. The evidence-to-collect card.
4. A3 archetype.
5. UI polish beyond the layout in `UI_UX_DESIGN.md`.
Do NOT cut: A1 on seed 42, the mock Telegram chat with "Export and trace", masking and reveal, the graph, hypothesis cards, offline replay.

If Tanish falls behind, cut: tuning depth (fewer seeds), then stage 7, then report styling. Do NOT cut: stages 0 to 5, chokepoints, H1 to H8.

---

## 7. Who does what in the pitch

- Anmol drives the demo (clicks) and tells the Telegram story.
- Tanish explains the method, the privacy design and the limits, and handles Q&A.
- Both rehearse together three times in Phase 5.

---

## 8. Setup both people do before Phase 1

- Python 3.11 or newer and Node 20 or newer installed.
- Clone the repo, create a venv, `pip install -r backend/requirements.txt`, `cd frontend && npm install`.
- Make sure the agent tool you use reads `AGENTS.md` (Claude Code reads `CLAUDE.md`, which is a copy; for Codex and Antigravity, start each session with: "Read AGENTS.md and follow it").
- Wifi test: turn wifi off and confirm the backend and frontend still run.
