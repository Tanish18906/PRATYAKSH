# PUGMARK: Test Plan

Owner: Tanish (expected results are written by a human on purpose). Agents implement the fixture builder and the test code but MUST NOT change any expected value in this file. If a correct implementation of `03_ENGINE.md` cannot meet an expectation, the agent writes the problem in `docs/QUESTIONS.md` and stops that test, it does not edit the expectation.

Tolerances: probabilities and scores are compared with `abs_tol = 0.01` unless stated.

---

## 1. Layers of testing

| Layer | What | When | Owner |
|---|---|---|---|
| Unit | sketch, mask, loss, anomaly, paths, rank, simulator pieces | every phase | module agents |
| Hand-written scenarios H1 to H7 + H8 | engine correctness with known answers on a tiny company | from Phase 1 | Tanish (expectations), engine agent (code) |
| Seed 42 integration | simulator + engine + API on the demo story | Phase 2 onward | both |
| Benchmark | accuracy vs naive baselines on generated scenarios | Phase 4 | Tanish |
| Demo rehearsal | the real demo path, offline | Phase 5 | both |

---

## 2. The mini company (fixture builder: `backend/tests/fixtures/mini.py`)

The fixture builder is independent of the simulator. It imports only `app.common.sketch`. It writes JSON files `backend/tests/fixtures/H1.json` ... `H8.json` (PublicScenario dicts) and exposes `build(name) -> dict`.

### 2.1 Constants

- `BASE = 2026-09-01T00:00:00Z`. Row `i` (1-based, 1 to 2000) has `created_at = BASE + 30*i minutes`.
- Identifiers: `customer_id = f"C{i:06d}"`, `email = f"u{i}@mini.test"`, `phone = f"9{i:09d}"`, `policy_no = f"MN-{i:06d}"`.
- Case key: `b"mini-test-key"`, sketch size `k = 512`.
- Rows existing at time `t`: `floor((t - BASE) / 30 min)`. Useful values: at 2026-10-09T02:10Z there are 1828 rows (newest row 1828, created 2026-10-09T02:00Z); at 02:40Z 1829 rows (newest 02:30Z); at 2026-10-10T02:10Z 1876 rows; at 2026-09-22T02:10Z 1012 rows.
- `found_ts = now_ts = 2026-10-12T08:00:00Z`, `found_at = ext:telegram-leak-channel`.
- Dataset `ds:cust` on `sys:db`, `arrivals_per_hour = 2.0`, identifier columns [customer_id, email, phone, policy_no].
- Artifact columns (all artifacts): [customer_id, full_name, email, phone, policy_no, created_at].
- Leak columns (all leaks unless stated): [full_name, phone, policy_no, created_at].

### 2.2 Locations, sources, actors

Locations: `sys:db` (src:db), `sys:wh` (src:wh), `sys:sftp` (src:sftp, egress_capable true), `sys:bucket` (src:bucket, egress_capable true), `ep:ann`, `ep:bob`, `ep:cat` (owners act:ann, act:bob, act:cat; unlogged; egress_capable true), `ext:telegram-leak-channel`, `ext:vendor-x` (unlogged externals). All other `egress_capable` false.

Actors (names are the id slug capitalised: Ann, Bob, Cat):

| id | role | access |
|---|---|---|
| act:ann | analyst | sys:wh, ep:ann |
| act:bob | analyst | sys:wh, sys:bucket, ep:bob |
| act:cat | bi-admin | sys:wh, sys:bucket, ep:cat |
| act:etl | service | sys:db, sys:wh, sys:bucket |
| act:key1 | service | sys:wh, sys:sftp |

### 2.3 Format styles

| style | delimiter | quoting | header_case | line_ending | encoding | null_token | phone | full_name | created_at |
|---|---|---|---|---|---|---|---|---|---|
| ETL | `,` | minimal | snake | LF | utf-8 | `""` | e164_dash | title | iso |
| OTHER | `;` | all | title | CRLF | utf-8-bom | NULL | digits10 | upper | iso |
| NOTEBOOK | `,` | minimal | camel | LF | utf-8 | `""` | digits10 | lower | iso |

Format profile for a file includes `columns: {phone: {style}, full_name: {case}, created_at: {style: "iso"}}` for columns present. Expected `format_sim` values for a leak with columns [full_name, phone, policy_no, created_at] (9 attribute pairs: 6 global + phone + full_name + created_at): ETL vs ETL = 1.0; ETL vs OTHER = 1/9 = 0.1111; ETL vs NOTEBOOK = 6/9 = 0.6667.

### 2.4 Background events (all scenarios)

For each of ann, bob, cat: 12 `query` events, object `ds:cust`, `from_loc = sys:wh`, `to_loc = null`, source `src:wh`, one every 2 days starting 2026-09-14T10:00Z (so 09-14, 09-16, ..., 10-06), rows cycling:
- ann: 150, 220, 310, 180, 260, 200
- bob: 90, 140, 120, 160, 110, 130
- cat: 60, 80, 50, 70, 90, 40

`seq` is consecutive per source in time order and has NO gaps unless a scenario says so. Event ids `evt:{n:06d}` in time order. Therefore `src:wh` (more than 20 events, no gaps) has estimated loss `LOSS_FLOOR` = 0.05, so a hidden hop out of `sys:wh` costs `-ln(0.05) + 1.0 = 3.9957`. Sources with fewer than 20 events (`src:db`, `src:bucket`, `src:sftp`) use `LOSS_DEFAULT` = 0.4, so a hidden hop out of them costs `-ln(0.4) + 1.0 = 1.9163`. A hidden hop out of an endpoint costs 0.5.

### 2.5 Builder helpers

- `artifact(id, by, ts, location, n_rows or index list, style)`: `row_count`, `newest_record_ts = created_at of max index`, `arrivals_per_hour = 2.0`, sketches for customer_id/email/phone/policy_no via `make_sketch` over the indexed rows, `canary_ids` optional.
- `leak(indices, style, canary_hits=[])`: same, `masked_preview = []`.
- `export_event(by, ts, art_id)`: action `export`, object `ds:cust`, `from_loc = sys:db`, `to_loc = artifact.location`, `source = src:db`, `rows = row_count`, `meta.artifact_id`.

---

## 3. Hand-written scenarios and expected results

In all expectations, "origin_candidates" refers to `TraceResult.origin_candidates`. All scenarios use the background events of 2.4 unless stated.

### H1: two near-identical exports, different styles

Artifacts: `art:E1` by act:etl at 2026-10-09T02:10Z, `sys:wh`, rows 1..1828, ETL. `art:E2` by act:cat at 2026-10-09T02:40Z, `sys:wh`, rows 1..1829, OTHER.
Events: export of E1 (etl), export of E2 (cat), `download` of E1 by act:ann at 2026-10-09T09:00Z, `sys:wh` to `ep:ann`, rows 1828.
Leak: rows 1..1828, ETL.
Expected:
- `origin_candidates[0].artifact_id == "art:E1"`; E2 is a `candidate`; `E1.origin_fit - E2.origin_fit >= 1.5`.
- `E1.containment >= 0.95`; `E1.format_sim == 1.0`; `E2.format_sim == 0.1111`; `E1.watermark_term` between -0.5 and -0.2 (gap 10 min at 2/h = -0.3333); `E2.watermark_term` = -1.3333.
- `origin_ranking[0].artifact_id == "art:E1"` with `probability >= 0.8`.
- `hypotheses[0].origin_artifact == "art:E1"`; `hypotheses[0].actors == ["act:ann"]`; `hops[0].kind == "observed"` with `event_id` equal to ann's download event; last hop `kind == "inferred"`, `from_loc == "ep:ann"`, `to_loc == "ext:telegram-leak-channel"`.
- `actor_ranking[0].actor == "act:ann"`.

### H2: shared bucket, two readers

Artifacts: `art:E1` (etl, 02:10, `sys:wh`, rows 1..1828, ETL).
Events: export of E1; `copy` of E1 by act:etl at 2026-10-09T02:20Z, `sys:wh` to `sys:bucket`, rows 1828 (source src:wh); `download` of E1 by act:bob at 2026-10-09T10:00Z `sys:bucket` to `ep:bob` rows 1828 (src:bucket); `download` by act:cat at 2026-10-09T10:05Z `sys:bucket` to `ep:cat` rows 1828.
Leak: rows 1..1828, ETL.
Expected:
- The two top entries of `actor_ranking` are `act:bob` and `act:cat` (either order); `abs(p_bob - p_cat) <= 0.10`; both `marginal >= 0.30`.
- `hypotheses[0].probability <= 0.60` (no false certainty).
- `act:ann` is not in the top 2.
- `act:etl` (service-account creator of the origin) appears in no hypothesis `actors` list and not in `actor_ranking`.

### H3: laundered through a reformatting tool

Artifacts: `art:E1` (etl, 02:10, `sys:wh`, rows 1..1828, ETL); `art:E2` by act:cat at 2026-09-22T02:10Z, `sys:wh`, rows 1..1012, ETL.
Events: exports of E1 and E2; `download` of E1 by act:ann at 2026-10-09T09:00Z.
Leak: rows 1..1828, style NOTEBOOK.
Expected:
- `origin_candidates[0].artifact_id == "art:E1"`; `E1.containment >= 0.95`; `E1.format_sim == 0.6667`.
- E2: `verdict == "excluded"`, `exclusion_rule == "watermark_before"`.
- `hypotheses[0].origin_artifact == "art:E1"`.

### H4: ten percent sample, big decoy

Artifacts: `art:E1` (etl, 2026-10-09T02:10Z, rows 1..1828, ETL); `art:E5` (etl, 2026-10-10T02:10Z, rows 1..1876, ETL).
Events: exports of both; `download` of E1 by act:ann at 2026-10-09T09:00Z. No downloads of E5.
Leak: rows {10, 20, ..., 1820} (182 rows), ETL; its `newest_record_ts` = created_at of row 1820 = 2026-10-08T22:00Z.
Expected:
- Both E1 and E5 are `candidate`; both `watermark_term == 0` (ratio 0.0996 and 0.097 are below 0.9).
- `E1.containment >= 0.7` and `E5.containment >= 0.7`.
- `hypotheses[0].origin_artifact == "art:E1"`; `origin_ranking[0].artifact_id == "art:E1"` with `probability >= 0.5`.

### H5: critical logs dropped, two equally suspicious insiders

Artifacts: `art:E1` (etl, 02:10, `sys:wh`, rows 1..1828, ETL).
Events: export of E1; `query` by act:ann at 2026-10-09T09:00Z, object `ds:cust`, from `sys:wh`, rows 20000; `query` by act:bob at 2026-10-09T09:10Z, same, rows 20000. NO download events (dropped).
Leak: rows 1..1828, ETL.
Expected:
- Top two of `actor_ranking` are `act:ann` and `act:bob` (either order); `abs(p_ann - p_bob) <= 0.10`; `act:cat` is not in the top 2.
- `hypotheses[0].probability <= 0.60`.
- `len(recommended_evidence) >= 1`; `recommended_evidence[0].mass` between 0.30 and 0.70 and `recommended_evidence[0].hop_ref.from_loc` is one of `sys:wh`, `ep:ann`, `ep:bob`.
- Every inferred hop has `ts == null`.

### H6: canary pins the origin

Artifacts: `art:E1` (etl, 02:10, rows 1..1828, ETL, `canary_ids ["can:E1-1"]`); `art:E2` (cat, 2026-10-09T02:40Z, `sys:wh`, rows 1..1829, ETL, `canary_ids ["can:E2-1"]`).
Canary registry: `can:E1-1 -> art:E1`, `can:E2-1 -> art:E2` (hash values arbitrary, 16 hex chars).
Events: exports of both; `download` of E1 by act:ann at 2026-10-09T09:00Z; `download` of E2 by act:bob at 2026-10-09T09:05Z (both from `sys:wh` to their endpoints, rows equal to the artifact rows).
Leak: rows 1..1828, ETL, `canary_hits ["can:E2-1"]`.
Expected, run A (as built):
- `origin_pinned == true`; every hypothesis has `origin_artifact == "art:E2"`; `origin_ranking == [{"art:E2", 1.0}]`; `actor_ranking[0].actor == "act:bob"`; some entry of `notes` contains the word "canary".
Expected, run B (same scenario with `canary_hits = []`):
- `origin_pinned == false`; `origin_ranking[0].artifact_id == "art:E1"` with `probability >= 0.6`.

### H7: no matching export

Artifacts: `art:E1` (etl, 02:10 Oct 9, rows 1..1828, ETL); `art:E2` (cat, 2026-09-22T02:10Z, rows 1..1012, ETL).
Events: exports of both.
Leak: 400 rows with indices 5001..5400 (identifiers generated by the same formulas, they do not exist in the artifacts), ETL, `newest_record_ts = 2026-10-01T00:00:00Z`.
Expected:
- `hypotheses == []`, `origin_ranking == []`, `chokepoints == []`.
- Some entry of `notes` contains "does not match".
- `origin_candidates` still lists both artifacts; both containment values `< 0.2` (or null for excluded ones); no exception.

### H8: artifact id permutation

Take H1 and rename `art:E1 -> art:E7` and `art:E2 -> art:E3` everywhere (artifacts, events, canary registry if any).
Expected: the result equals the H1 result after applying the same renaming (same ordering, same probabilities within 0.0001, same actors). Proves ids are not used as signal.

---

## 4. Seed 42 integration tests (after Phase 2; file `tests/integration/test_seed42.py`)

Generate `A1`, seed 42, scale demo, canary off, with `log_loss` in {0.0, 0.2, 0.4}; run `trace()`.
Expected for each of the three loss levels:
1. `origin_ranking[0].artifact_id == "art:E1"`.
2. `art:E2` is excluded with `watermark_before`; `art:E3` is excluded with `schema`; `art:E4`, `art:E5`, `art:E6` are candidates with `watermark_term <= -5.0` (they will be about -8.0, the cap); `art:E1` `watermark_term >= -3.0`.
3. `actor_ranking[0].actor == "act:ravi-menon"` and `hypotheses[0].actors` contains it. (Loss 0.6 is intentionally not asserted: the download is dropped and the engine cannot see Ravi's behaviour; the test only checks it does not crash and prints Ravi's rank.)
4. `hypotheses[0].hops[-1].kind == "inferred"`, `from_loc == "ep:ravi-menon"`, `to_loc == "ext:telegram-leak-channel"`.
5. `chokepoints[0].item_id` is `perm:act:ravi-menon@sys:bi-warehouse` or `perm:act:ravi-menon@egress`.
6. The naive baseline B1 (last accessor) does NOT rank `act:ravi-menon` first.
7. `trace()` time under 3 seconds.
8. `validate_trace` passes.

With `canary_mode = true`, `origin_pinned == true`, and every hypothesis starts at `art:E1`.

---

## 5. API tests (Phase 2 and 3, `tests/api/`)

- `GET /api/health` returns ok.
- `POST /api/scenario/generate` (A1, 42, 0.4, false, demo) returns a summary with no `truth` key anywhere in the JSON text (string search for `"truth"`, `"case_key"`, `"true_path"`).
- `POST /api/leak/export` returns a masked sample: no `@` followed by an unmasked local part longer than 1 char (regex check on previews).
- `POST /api/trace` returns a valid `TraceResult`.
- `POST /api/reveal` without a reason, or with fewer than 8 characters: 400 `reason_required`. With a reason: unmasked value and an `aud:` id; `GET /api/audit` shows one reveal entry.
- Each of generate, export, trace, reveal, inject, canary alert, benchmark run, report export adds exactly one audit entry.
- Masking vectors from contract section 10 pass in `test_mask.py`.
- Report HTML contains no unmasked email (regex) and includes the "Verify current legal timelines with counsel" line.

---

## 6. Benchmark specification

### 6.1 Scenarios
- Archetypes: A1, A2, A3 (A4, A5 if built). Scale `bench`. Canary off. Seeds 0 to 199 (the archetype for seed `s` is `["A1","A2","A3"][s % 3]`).
- Loss levels: 0.0, 0.2, 0.4, 0.6. (4 x 200 = 800 runs.)
- Seed 42 is not part of the benchmark.

### 6.2 Tuning discipline
- Tuning set: seeds 0 to 49. Reporting set: seeds 50 to 199.
- Any config change must be justified by the tuning set only and logged in `docs/DECISIONS.md` (before and after metrics on the tuning set).
- After tuning, H1 to H8 and the seed 42 tests must still pass.
- The reported numbers come from one final run on seeds 50 to 199 with the final config, run once. If the numbers are bad, report them as they are.

### 6.3 Methods and metrics

Origin ranking:
- `pugmark`: artifacts sorted by `origin_ranking` probability (artifacts not in the list go last by `origin_fit`).
- `B3_largest_export`: artifacts with `created_ts <= found_ts`, sorted by `row_count` descending.
- `B4_most_recent_export`: same set, sorted by `created_ts` descending.
- Metric: rank of `truth.origin_artifact`. `top1` = rank 1, `top3` = rank <= 3.

Actor ranking (rank of the best-ranked actor in `truth.true_actors`):
- `pugmark`: `actor_ranking`; actors not listed go last (rank = number of actors).
- `B1_last_accessor`: actors sorted by their most recent event (before `found_ts`) whose object is `ds:customers` or any artifact, latest first.
- `B2_biggest_exporter`: actors sorted by total `rows` over events with action in {export, download, copy, send, api_call, upload}, descending.
- Metrics: `top1`, `top3`, `mean_rank`, `n`.

Output JSON matches `BenchmarkResult` in the contract. `note` is always the synthetic-data sentence.

### 6.4 Sanity gates before showing any benchmark
- At loss 0.0: pugmark origin top3 >= 0.9. If lower, there is a bug, not a result.
- Baselines must not equal pugmark exactly (else the benchmark is trivial).
- Spot check 5 failures by hand and write one sentence each in `docs/DECISIONS.md`.

---

## 7. Phase gates (what must pass)

| Phase | Must pass |
|---|---|
| 0 | `test_sketch.py` and `test_mask.py` pass; fixtures H1 to H8 build and pass `validate.py`; frontend builds |
| 1 | Simulator seed 42 acceptance (docs 02 section 14); engine H1, H3, H6, H7 and origin parts of H4 and H8; API health and generate |
| 2 | H1 to H8 all; seed 42 integration at loss 0.0 to 0.4; `trace` under 3 s; UI shows the top path |
| 3 | API tests (section 5); chokepoint and evidence tests; A2 and A3 produce valid scenarios; offline replay works |
| 4 | Benchmark run complete; sanity gates pass; chart shows real numbers |
| 5 | Full demo rehearsed 3 times offline without error |

Commands:
```
cd backend && pytest -q                     # all tests
cd backend && pytest -q tests/engine        # engine only
cd backend && python scripts/validate.py scenario tests/fixtures/H1.json
cd frontend && npm run build && npm run lint
```
