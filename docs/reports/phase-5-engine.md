# Phase 5 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- Engine is frozen at `5b27149` plus this report; no code or config changed in Phase 5.
- Freeze checks (below) all pass. Rehearsal, backup video and the `final` tag are human tasks.

## Files created or changed
- docs/reports/phase-5-engine.md

## Commands run and real output
$ cd backend && python3 -m pytest -q
106 passed in 4.20s

$ grep -rnE "^(from|import) app\.(sim|bench|privacy|report)|case_key|true_path|\"truth\"" app/engine app/common
none
$ grep -rnE "datetime\.now|time\.time|import random|uuid|requests|urllib|socket" app/engine app/common
none
Determinism: trace() output byte-identical across 3 runs for H1, H2, H5, H6.

## Gate checks
- [x] Engine tests green, engine never imports sim or reads truth, no clock/network/randomness: pass
- [ ] Seed 42 at loss 0.0 / 0.2 / 0.4, `validate_trace`, A2/A3 traces, trace time on the real demo scenario: NOT RUN.
      `backend/app/sim/*`, `bench/*`, `scripts/validate.py`, `models.py`, `main.py` are still empty files in this tree.
- [ ] Benchmark numbers: none exist; none may be shown or claimed.
- [ ] Rehearsal x3 offline, tag `final`: human tasks, not engine.

## Not done / cut
- Everything that needs the simulator (see above). Engine has only ever run on H1 to H8 and synthetic stress (0.12 s at 3,224 events).

## Risks for integration
- The demo path (seed 42 -> trace -> graph) is unverified end to end. If the simulator lands after the freeze, run seed 42 first; any crash fix needs Tanish's approval and should be one small commit on feat/engine.
- Do not show benchmark charts or accuracy claims unless real numbers from seeds 50 to 199 exist. Honest fallback for the pitch: fixtures H1 to H8 demonstrate behaviour on hand-built cases only; say so.
- Merge order at the gate: shared files, sim, engine, api, ui. `config.py` was written on feat/engine under override; take its ENGINE dict.

STOPPED. Waiting for APPROVED PHASE 5.
