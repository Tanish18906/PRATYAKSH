# Phase 3 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- `chokepoint.py` stage 6: one item per hop (system permission / api_key / service_account, endpoint egress, external channel), service-account creator and `found_at` never yield items, greedy cover up to CHOKE_MAX with `marginal` and `cumulative_coverage`, spec text templates: done.
- Stage 7 recommended evidence: already built in Phase 2 (needed by H5); request texts follow 03 sec 11, no changes needed: done.
- Performance pass: profiled, one hotspot removed: done.
- Text templates: already complete from Phase 2; no polish beyond that was specified.

## Files created or changed
- backend/app/engine/chokepoint.py, trace.py (wire stage 6), paths.py (perf)
- backend/tests/engine/test_chokepoint.py
- docs/DECISIONS.md (appended), docs/reports/phase-3-engine.md

## Commands run and real output
$ cd backend && python3 -m pytest -q tests/engine/test_chokepoint.py   # before implementation
ImportError: cannot import name 'chokepoints' from 'app.engine.chokepoint'

$ cd backend && python3 -m pytest -q
..................................                                       [100%]
106 passed in 4.13s

Performance (synthetic stress, not the simulator; scratchpad script):
before: 3,224 events, 50 actors, 59 locations, 9 artifacts: 0.74 s  (233k strptime calls in alt_actors)
after:  same input: 0.12 s, identical output, all tests unchanged

Chokepoints on fixtures: H1 first item perm:act:ann@egress (marginal above 0.9); H2 two items, bob and cat,
coverage rises by more than 0.3 at rank 2; H7 []; H6 first item belongs to act:bob.

## Gate checks
- [x] Chokepoint tests (greedy order, cumulative coverage, item types, exclusions, CHOKE_MAX): pass
- [x] Evidence tests (informativeness order and values): pass
- [x] H1 to H8 still pass: pass
- [ ] Generate A2 and A3, `trace()` valid on both: not run, simulator files are still empty in this tree.
- [ ] `validate_trace` on outputs and seed 42 integration (item 5 there: first chokepoint `perm:act:ravi-menon@sys:bi-warehouse` or `@egress`): not run, same reason. The rule produces exactly these two ids for a Ravi path, and ties go to `@egress`.
- [ ] Judge flow (three injected actors, under 5 s each): API and simulator work, not engine.

## Not done / cut
- Nothing cut from the engine Phase 3 list.

## Contract or spec discrepancies
- None new. `origin_ranking` still missing from the contract TraceResult (QUESTIONS.md).

## Risks for integration
- All engine verification is on fixtures plus a synthetic stress. The first run on A1 seed 42, A2 and A3 may show weights or path shapes the fixtures do not cover; tuning belongs to Phase 4.
- Third chokepoint can have near-zero mass; UI may want to hide cards under a small marginal (display choice, not engine).
- `recommended_evidence` may contain items with mass 1.0 (informativeness 0) when every hypothesis shares a hidden hop; spec keeps them, UI could drop zeros.

STOPPED. Waiting for APPROVED PHASE 3.
