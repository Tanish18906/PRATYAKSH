# Phase 2 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- `paths.py` stage 3 complete: M1 observed, M2 hidden to leak location, M3 hidden download to an endpoint (suppressed when an observed download exists), M4 hidden copy between systems (suppressed when an observed copy exists), fallback path: done.
- `anomaly.py` stage 4: baseline fallback chain (own, role peers, default), leave-one-out, off-hours (users only), first-time, privilege grant: done.
- `rank.py` stage 5: score with anomaly term, softmax over all enumerated paths, `actor_ranking`, `location_ranking`, `origin_ranking`, pinned handling: done.
- `graph.py`: nodes, merged edges with `path_ids`, origin edge, labels: done.
- Text templates (summary and evidence, in `evidence.py`): done.
- All of H1 to H8 pass, including the id-permutation test.

## Judgement calls
- Stage 7 (`recommended_evidence`) is built here, not Phase 3, because H5 asserts on it. Chokepoints (stage 6) are not built; `chokepoints` is `[]`.
- A canary-pinned artifact that fails a hard rule no longer crashes ranking (found while writing edge-case tests); it is used with `origin_fit` 0.0 and a note.
- Other small choices are logged in docs/DECISIONS.md (population std, `hid:{actor}` edge ids, high-loss threshold).

## Files created or changed
- backend/app/engine/{anomaly,paths,rank,evidence,graph,trace,origin,index,normalize}.py
- backend/tests/engine/{test_anomaly,test_paths,test_rank,test_graph,test_scenarios}.py
- docs/DECISIONS.md, docs/QUESTIONS.md (appended), docs/reports/phase-2-engine.md

## Commands run and real output
$ cd backend && python3 -m pytest -q tests/engine/test_anomaly.py   # before implementation
ImportError: cannot import name 'Anomaly' from 'app.engine.anomaly'

$ cd backend && python3 -m pytest -q
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 3.75s

Real values:
H1: hyp:1 E1 via ann (observed sys:wh->ep:ann, inferred ep:ann->telegram), anomaly term 4.7 (z cap 4.0 + first-time 0.7)
H2: hyp:1 bob 0.4426, hyp:2 cat 0.4426; marginals bob 0.4962, cat 0.4962, ann 0.0006; etl absent
H5: ann 0.4525, bob 0.4929, cat 0.0447; evidence[0] mass 0.4525 at ep:ann -> telegram
H6: pinned E2, actor_ranking[0] bob; run B E1 over E2
Stress (synthetic, not the simulator): 3,040 events, 22 actors, 31 locations -> 0.07 s

## Gate checks
- [x] H1 to H8 all pass (`tests/engine/test_scenarios.py`): pass
- [x] Engine tests green, `pytest -q` 96 passed: pass
- [ ] Seed 42 integration at loss 0.0, 0.2, 0.4: not run, simulator files are empty in this tree.
- [ ] `validate_trace` on every output: not run, `validate.py` is empty. Local invariant checks (sorted probabilities, contiguous hops, event ids exist, graph edges reference nodes, 1 candidate row per artifact) pass.
- [ ] `trace` under 3 s on the demo scenario: only the synthetic stress (0.07 s) is measured.

## Not done / cut
- Stage 6 chokepoints (Phase 3). Performance pass (Phase 3). `test_trace_contract.py` and `tests/integration/test_seed42.py` (need validator and simulator; the latter is also outside my folders).

## Contract or spec discrepancies
- `origin_ranking` still not in the contract TraceResult (QUESTIONS.md). Emitted as an extra top-level key.
- Zero-event scenario wording in 03 sec 14 vs sec 7 (QUESTIONS.md).

## Risks for integration
- Everything here is verified on hand-built fixtures only. The first run on the real simulator (seed 42) may expose weights that need tuning; tuning is Phase 4 and only on seeds 0 to 49.
- `Hypothesis.summary_text` and graph labels use `name` fields; they read well only when the simulator supplies display names (fixtures use slugs).
- Chokepoint card in the UI has no data until Phase 3.

STOPPED. Waiting for APPROVED PHASE 2.
