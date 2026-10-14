# Phase 1 report: engine
Developer: Tanish | Date: 2026-10-14

## Done
- `config.py` ENGINE dict (03 sec 3), added under `OVERRIDE OWNERSHIP: api` (config.py only): done.
- `normalize.py`, `index.py`, `loss.py` (seq-gap loss per source, default 0.4 under 20 events, clip 0.05..0.9): done.
- `origin.py` stages 0 to 2: canary pin, hard rules `schema` / `watermark_before` / `after_found`, soft `origin_fit`, `format_sim`, candidate selection, no-match note: done.
- `trace()` returns candidates table, `origin_ranking`, `loss_estimates`, notes, hypotheses: done.
- Hypotheses are NOT a single-hop stub: see "Judgement call" below.

## Judgement call (please confirm)
The Phase 1 gate says H1 and H6 must pass. Their expected values include an observed download hop followed by an inferred final hop and `actor_ranking[0]`. A single direct hidden hop cannot satisfy that, so `paths.py` implements the M1 (observed move) and M2 (hidden move to the leak location) rules plus the fallback path, and `rank.py` the softmax and marginals. This is the smallest slice of Phase 2 needed for the gate. Not built: M3, M4, anomaly (stage 4), graph, chokepoints, evidence requests, text polish. H2 and H5 need M3/M4 and are intentionally not wired yet. If you want a strict stub instead, say so and I will revert `paths.py`/`rank.py` to a single hidden hop; H1 and H6 path assertions would then fail.

## Files created or changed
- backend/app/config.py (override)
- backend/app/engine/{normalize,index,loss,origin,paths,rank,evidence,trace}.py
- backend/tests/engine/{test_loss,test_origin,test_scenarios}.py
- docs/DECISIONS.md (appended), docs/reports/phase-1-engine.md

## Commands run and real output
$ cd backend && python3 -m pytest -q tests/engine     # before implementation
ImportError: cannot import name 'trace' from 'app.engine.trace'
3 errors in 0.09s

$ cd backend && python3 -m pytest -q
.............................................................            [100%]
61 passed in 2.18s

Key values from `trace()` (script run from backend/, wall time includes everything, 27 to 76 ms each):
H1 origin_ranking E1 0.9944, E2 0.0056; hyp:1 actors [act:ann], hops observed sys:wh->ep:ann, inferred ep:ann->ext:telegram-leak-channel
H3 origin_ranking E1 1.0 (E2 excluded watermark_before)
H4 origin_ranking E1 0.9188, E5 0.0812
H6 pinned=True, origin_ranking [E2 1.0], actor_ranking[0] act:bob; run B: E1 0.7319, E2 0.2681
H7 hypotheses [], origin_ranking [], note "The leak does not match any known export (best containment 0.00)..."
loss_estimates (H1): src:db 0.4, src:wh 0.05, src:sftp 0.4, src:bucket 0.4

$ grep -nE "app\.sim|log_loss|case_key|truth|true_path" backend/app/engine/*.py
only a docstring line in trace.py (no import or read)

## Gate checks
- [x] H1, H3, H6, H7 pass: pass
- [x] H4 and H8 pass their origin assertions (H4 and H8 also pass their path assertions here): pass
- [x] `test_sketch.py` and `test_origin.py` pass: pass
- [ ] `validate_trace` on output: not run, `backend/scripts/validate.py` is still empty (Anmol). `test_scenarios.py` checks the contract sec 9 invariants 1 to 5 and 7 locally.

## Not done / cut
- M3, M4, anomaly, graph, chokepoints, evidence requests, template polish: Phase 2/3.
- H2 and H5 wiring: need M3/M4.
- `test_trace_contract.py` (needs validate.py).

## Contract or spec discrepancies
- `origin_ranking` is used by 03/04 but is not in the contract TraceResult (already in QUESTIONS.md); emitted as an extra top-level key.
- 04 sec 2.3 lists leak columns without customer_id/email, so shared identifier columns are only phone and policy_no (from Phase 0).

## Risks for integration
- `config.py` was written on `feat/engine` under override; the api branch will also touch it. Take the ENGINE dict from here at merge.
- Engine output has `graph` empty and `chokepoints`/`recommended_evidence` empty until Phase 2/3; UI must not assume otherwise.
- `trace()` runs in under 0.1 s on the fixtures; demo-scale timing (about 3,000 events) is untested until the simulator lands.
- Hypothesis `summary_text` uses location/actor `name` fields from the scenario; fixture names are slugs, so the text reads oddly on fixtures only.

STOPPED. Waiting for APPROVED PHASE 1.
