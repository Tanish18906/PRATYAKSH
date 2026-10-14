# PUGMARK: Phases and Gates

Rule of the project: build ONE phase, STOP, write a report, wait for a human to say `APPROVED PHASE N`, only then start the next phase.

Clock assumption: the event ends about 16:06 local. Times below are targets. If the organisers' deadline is earlier, shorten Phase 4 and 5 first and drop "Should" items.

| Phase | Target window | Time box | Theme |
|---|---|---|---|
| 0 | now to 12:00 | about 20 min left | Foundations |
| 1 | 12:00 to 13:00 | 60 min | Core slices on both sides, no integration yet |
| 2 | 13:00 to 14:15 | 75 min | End to end on seed 42 |
| 3 | 14:15 to 15:00 | 45 min | Product features |
| 4 | 15:00 to 15:25 | 25 min | Proof: benchmark and tuning |
| 5 | 15:30 to 16:06 | 36 min | Code freeze, rehearsal, submission |

Overrun rule: if an agent is 20 percent past its time box, it stops, reports what is done and what is blocking, and waits. A human decides whether to cut scope or extend.

---

## Gate procedure (same for every phase)

1. Each agent finishes its phase work and writes `docs/reports/phase-{N}-{module}.md` using the template in `AGENTS.md` (modules: `sim`, `engine`, `api`, `ui`).
2. The agent prints `STOPPED. Waiting for APPROVED PHASE {N}.` and does nothing else.
3. The module owner (see `06_WORK_SPLIT.md`) runs the checks for that phase below, with their own eyes, in under 5 minutes.
4. If good, the owner types `APPROVED PHASE {N}` into that agent's session. If not, `REJECTED PHASE {N}: <reason>`; the agent fixes only that and re-reports within 10 minutes.
5. When all four modules are approved, both humans merge to `main` in this order: contract or shared files, sim, engine, api, ui. Run `cd backend && pytest -q` and `cd frontend && npm run build` on `main`. Tag `ok-{N}`.
6. Tanish says `PHASE {N+1} START` in chat. Nobody starts early.

An agent may not start work from a later phase, even if it is idle or ahead. If an agent finishes early, it says so in its report and waits. Humans may give it a small side job (for example extra tests) in writing.

---

## Phase 0: Foundations

Goal: everyone can run something, the contract is frozen, tests can fail for the right reasons.

Deliverables
- Docs 00 to 06, `AGENTS.md`, `CLAUDE.md` (copy of AGENTS.md), the four ChatGPT docs (UI_UX_DESIGN, FRONTEND, FEATURES, DEMO_AND_PITCH), `docs/DECISIONS.md`, `docs/IDEAS.md`, `docs/QUESTIONS.md`, `docs/reports/`.
- Tanish (api and engine agents): git repo, `.gitignore`, `backend/` skeleton (FastAPI app with `/api/health`, `config.py`, `models.py` as Pydantic mirrors of the contract), `common/sketch.py` with its tests, `privacy/mask.py` with its tests, `tests/fixtures/mini.py` building H1 to H8 JSON.
- Anmol (ui and sim agents): `frontend/` Vite + React + TypeScript + Tailwind scaffold with Cytoscape, Recharts, Framer Motion installed, `src/types/contract.ts` copied from the contract, `public/demo.json` placeholder built from fixture H1 (hand-edited to match the DemoBundle shape); `backend/app/sim/` skeleton with `names.py` and `styles.py`.
- README with exact run commands.

Gate checks (Tanish)
- `cd backend && pytest -q` passes (sketch vectors, mask vectors, fixtures validate).
- `uvicorn app.main:app --port 8000` starts and `/api/health` answers.
- `cd frontend && npm run build` passes and `npm run dev` shows a blank shell.
- Contract file frozen: from now only Tanish edits it.
- Tag `ok-0`.

---

## Phase 1: Core slices (no integration)

Goal: simulator makes the seed 42 world; engine ranks origins on fixtures; UI shows a masked incident and the mock Telegram chat from fixture data.

Deliverables by module
- sim (Anmol): `generate_scenario("A1", ...)`, hash cache, styles, background events, loss model, mock Telegram discovery, `to_summary`, `reveal_value`, `scripts/validate.py` (scenario and trace validators), seed 42 acceptance checks from `02_SIMULATOR.md` section 14.
- engine (Tanish): `trace()` with stages 0 to 2 complete (canary pin, candidates, origin ranking), hypotheses may be a single direct hidden hop for now; the mini fixtures run through it.
- api (Tanish): `POST /api/scenario/generate`, `GET /api/scenario/{id}`, `POST /api/leak/export`, `POST /api/trace` (calls engine), JSON error shape, audit append. Uses `sim.generate_scenario` once it lands, fixtures before that.
- ui (Anmol): app shell; incident panel with masked preview; mock Telegram chat view with the "Export and trace" button (calls the API, or `demo.json` if the API is down); origin match table; basic hypothesis cards; SIMULATED and offline badges. No graph yet unless time allows.

Gate checks
- sim (Anmol shows Tanish): validator passes on seed 42; acceptance checks pass; generation time printed.
- engine (Tanish): H1, H3, H6, H7 pass; H4 and H8 pass their origin assertions (path assertions may fail until Phase 2); `test_sketch.py` and `test_origin.py` pass.
- api: `curl` generate then trace works on seed 42 without errors; response JSON string contains none of `"truth"`, `"case_key"`.
- ui: `npm run build`; in the browser, the Telegram chat shows the post, the button loads the incident panel with masked values only.

Cut if late: A1 only is already the scope; drop the UI hypothesis cards (Phase 2 will add them).

---

## Phase 2: End to end on seed 42

Goal: the demo path runs from Telegram post to ranked path on the graph.

Deliverables
- engine: stages 3 to 5 (`paths`, `anomaly`, `rank`, `graph`), text templates. All of H1 to H8 pass.
- sim: fixes for anything the engine needs, speed work.
- api: `trace` returns full contract output; response time under 3 s; `GET /api/audit`; `POST /api/reveal` with the reason rule.
- ui: provenance graph with top 3 hypotheses, dashed inferred edges, hypothesis cards with probability bars and evidence, click to highlight, hypothesis switching, origin match table with exclusion reasons, reveal dialog, audit tab.

Gate checks
- Tanish: `pytest -q` all green including seed 42 integration (loss 0.0, 0.2, 0.4).
- Anmol and Tanish together: do the demo steps 1 to 5 from `DEMO_AND_PITCH.md` on one laptop, offline (wifi off): Telegram chat, export and trace, origin table (E1 wins, E2 and E3 excluded with reasons), graph with Ravi's path and the dashed final hop, evidence cards. Timing under 3 s for the trace.
- Tag `ok-2`. If this tag does not exist by 14:15, the project is in trouble: stop adding features and fix integration.

---

## Phase 3: Product features

Goal: everything the demo needs beyond the core path.

Deliverables (Must unless noted)
- engine: chokepoints (stage 6), recommended evidence (stage 7, Should), performance pass.
- sim: A2 and A3 archetypes, `inject_leak`, canary mode and `canary_alert` (Should), A4 and A5 (Should, only if everything else is done).
- api: masking applied everywhere, audit for all actions, `POST /api/inject`, `POST /api/canary/alert`, `GET /api/report/{trace_id}` (HTML incident report), log-loss regeneration via `generate`, `backend/scripts/make_demo_bundle.py`.
- ui: chokepoint card, evidence-to-collect card (Should), judge "inject leak" picker, log-loss slider, canary toggle and alert flow (Should), report tab with preview, `public/demo.json` produced by the real script, offline replay mode.

Gate checks
- API tests from `04_TEST_PLAN.md` section 5 pass.
- Generate A2 and A3 scenarios; both pass the validator and `trace()` returns valid output without errors.
- Offline replay: stop the backend, reload the UI, the demo bundle loads with the offline badge, all tabs work.
- Judge flow: pick three different actors in the injector; each produces a trace in under 5 seconds; at least two of three show the picked actor in the top 3 (this is a smoke check, not a promise).
- Tag `ok-3`.

Cut order if late: A4/A5, then evidence-to-collect card, then canary, then A3, then report styling.

---

## Phase 4: Proof

Goal: honest numbers on the screen.

Deliverables
- api or Tanish's benchmark agent: `bench/run.py`, baselines (B1 to B4), metrics, `POST /api/benchmark/run`, `GET /api/benchmark/{id}`.
- Tanish: tune on seeds 0 to 49 only, log changes in `DECISIONS.md`, then one final run on seeds 50 to 199.
- ui: benchmark tab (grouped bars, synthetic-data note), loss slider labels.
- Regenerate `demo.json` with the final benchmark inside.

Gate checks
- Sanity gates in `04_TEST_PLAN.md` section 6.4 pass.
- H1 to H8 and seed 42 tests still pass with the tuned config.
- The chart shows the real numbers (compare the JSON to the chart by eye).
- Tag `ok-4`.

If time is nearly out: run the benchmark at 100 seeds per level instead of 200 and say so on the slide.

---

## Phase 5: Freeze and rehearse

- 15:30 CODE FREEZE. Only bug fixes for crashes, approved by Tanish, until the end.
- Rehearse the full demo three times, offline, with the real script. Time it.
- Record a backup video of a clean run.
- Make sure the repo, slides and demo bundle are exactly what will be submitted. Tag `final`.
- Print or save the Q&A sheet.

---

## Report template location

The template and the `STOPPED` line are in `AGENTS.md`. Reports are short: they exist so a human can approve in five minutes.
