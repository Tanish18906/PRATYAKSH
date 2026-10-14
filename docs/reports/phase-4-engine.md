# Phase 4 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- Nothing from the Phase 4 engine deliverables could be started. Blocked on missing inputs, see below.
- Read-only robustness check of the human-owned H1 to H8 expectations (no file or config changed).

## Blocker
Tuning needs scenarios from `sim.generate_scenario` (seeds 0 to 49) and a benchmark runner with baselines (`bench/run.py`, B1 to B4). In this tree all of these are empty files: `backend/app/sim/*`, `backend/app/bench/*`, `backend/scripts/validate.py`, `backend/app/models.py`, `backend/app/main.py`. These belong to Anmol (sim, validator) and the api module (bench), so I did not write them. I also did not tune on H1 to H8: 04 sec 6.2 allows tuning on seeds 0 to 49 only, and 8 hand-built cases would only overfit.

Logged in docs/QUESTIONS.md.

## Files created or changed
- docs/QUESTIONS.md (appended), docs/reports/phase-4-engine.md. No code and no config change.

## Commands run and real output
$ wc -l backend/app/sim/*.py backend/app/bench/*.py backend/scripts/*.py backend/app/models.py backend/app/main.py
0 total   (every file 0 lines)

$ cd backend && python3 -m pytest -q      # engine state unchanged since Phase 3
106 passed

Headroom of the human-owned H1 to H8 thresholds with the current ENGINE config (read-only script):
H1 origin_fit E1 minus E2 = 2.782 (need >= 1.5); origin p E1 = 0.9967 (need >= 0.8)
H2 top hyp p = 0.4426 (need <= 0.60); |bob - cat| = 0.0000 (need <= 0.10); min marginal 0.4962 (need >= 0.30)
H4 origin p E1 = 0.9960 (need >= 0.5); containments 1.000 / 1.000 (need >= 0.7)
H5 top hyp p = 0.4525 (need <= 0.60); |ann - bob| = 0.0404 (need <= 0.10); evidence[0].mass 0.4525 (need 0.30 to 0.70)
H6 run B origin p E1 = 0.7311 (need >= 0.6)
H7 containments 0.0 / 0.0 (need < 0.2)
Tightest: H5 |ann - bob| (0.06 of headroom) and H6 run B (0.13). Anything that raises W_ANOMALY or shifts
the alternative-actor ordering is most likely to trip H5 first.

## Gate checks
- [ ] Sanity gates in 04 sec 6.4 (origin top3 >= 0.9 at loss 0.0, baselines differ, 5 spot checks): not run, no benchmark.
- [x] H1 to H8 still pass with the current config: pass (106 passed)
- [ ] Seed 42 tests with tuned config: not run, no simulator.
- [ ] One final run on seeds 50 to 199: not run. No numbers exist, none are reported.

## Not done / cut
- Tuning on seeds 0 to 49, baselines B1 to B4, benchmark runs, final run on 50 to 199, DECISIONS.md config-change log entries: all blocked.

## Contract or spec discrepancies
- None new.

## Risks for integration
- The engine has never run on a simulator-generated scenario. Seed 42 integration, `validate_trace`, A2/A3 and the benchmark are all first contact whenever the simulator lands; expect at least one round of fixes before any tuning is meaningful.
- Phase 4 and 5 are time-boxed. If the simulator arrives late, the 04 sec 6.4 fallback applies: 100 seeds per level, and say so on the slide.
- When it lands, suggested order for the engine agent: run seed 42 at loss 0.0, 0.2, 0.4; run `validate_trace`; A2 and A3 smoke; only then benchmark and tune.

STOPPED. Waiting for APPROVED PHASE 4.
