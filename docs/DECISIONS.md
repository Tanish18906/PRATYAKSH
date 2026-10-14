# Decisions

One line per ambiguity choice or config change (before/after numbers for ENGINE tuning).
- [engine P0] Leak sketches cover only identifier columns present in the leak's columns (phone, policy_no); artifacts sketch all four. Simplest reading of contract sec 5/7 and `S` in 03 sec 6.
- [engine P0] Fixture event `source` = `log_source` of `from_loc` (export -> src:db, wh/bucket moves -> src:wh/src:bucket, per 04 sec 2.4 and H2); `meta.artifact_id` is set on every event whose object is an `art:`.
- [engine P0] H6 run B (canary_hits = []) is not a separate fixture file; tests deep-copy `build("H6")` and clear `canary_hits` (04 lists only H1..H8.json).
- [engine P0] H6 canary registry hashes are `h64(b"mini-test-key", "canary:<id>:<column>")`, deterministic and arbitrary as 04 allows.
- [engine P0] `tests/engine/test_fixtures.py` carries a local structural check of H1..H8 because `scripts/validate.py` (Anmol, Phase 1) does not exist yet.
- [engine P1] OVERRIDE OWNERSHIP: api granted by Tanish for `backend/app/config.py` only; it holds exactly the ENGINE dict from 03 sec 3.
- [engine P1] Gate needs H1 and H6 path assertions, so Phase 1 `paths.py` has M1 (observed) + M2 (hidden move to leak location) + fallback only, and `rank.py` has the softmax with no anomaly term. M3, M4, anomaly (stage 4), graph, chokepoints, evidence requests stay Phase 2/3. `graph` is `{nodes: [], edges: []}` for now.
- [engine P1] `origin_ranking` is a top-level TraceResult key `[{artifact_id, probability}]` as 03 sec 9 and 04 use it (contract has no such field, see QUESTIONS.md). Pinned: `[{pinned, 1.0}]`.
- [engine P1] Candidate sort ties and path order never use artifact ids; enumeration order follows 03 sec 7 `(kind, to_loc, actor, event_id)`; `trace_id` is "trc:" + scenario id suffix.
- [engine P2] Stage 7 (`recommend`, 03 sec 11) was built in Phase 2 although 05 lists it for Phase 3, because H5 asserts `recommended_evidence`. Stage 6 chokepoints stay Phase 3 (`chokepoints = []`).
- [engine P2] Baseline std uses population std (`statistics.pstdev`), floored at SIGMA_FLOOR; 03 sec 8 says only "std".
- [engine P2] Graph edge ids for hidden hops are `e:{from}>{to}:inferred:hid:{actor}` (03 sec 12 says `hid`); two actors can hide the same from/to pair and must not merge.
- [engine P2] "High loss" in the stage 7 request text means loss_estimate >= LOSS_DEFAULT (0.4); 03 sec 11 gives no number.
- [engine P2] A pinned artifact that fails a hard rule is still used (canary wins); scored with origin_fit 0.0 and a note.
- [engine P2] Evidence list order: fingerprint, all observed hops, all inferred hops, anomalies (03 sec 13 order), not hop order.
- [engine P3] Chokepoint `label` and `action_text` both use the 03 sec 10 template text (the spec gives one set for both). The contract's sample "Revoke bulk download for Ravi Menon on bi-warehouse" is illustrative; templates win.
- [engine P3] Greedy selection uses mass on still-uncovered paths; the reported `marginal` is the item's mass over all enumerated paths; ties go to the smaller item id. Chokepoints are not filtered by a minimum mass (03 sec 10 sets none), so a low-mass third card is possible.
- [engine P3] Perf: `alt_actors` compares ISO strings instead of parsing timestamps per event (0.74 s to 0.12 s on a 3,224-event, 50-actor, 9-artifact synthetic scenario). No config or output change.
- [engine P5 fix] Export with row_count 0 made specificity divide by zero (found by randomized self-test, approved by Tanish); ratio now falls to the 0.01 clip floor.
