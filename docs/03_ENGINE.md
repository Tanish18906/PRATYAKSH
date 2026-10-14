# PUGMARK: Engine Spec

Owner: Tanish. Suggested agent: Claude Code. Module folder: `backend/app/engine/`, plus `backend/app/common/sketch.py` and `backend/app/config.py`.
Read first: `00_PROJECT_CONTEXT.md`, `01_DATA_CONTRACT.md`, `04_TEST_PLAN.md`, `AGENTS.md`.

The engine answers three questions from a `PublicScenario`: which export did the leak come from, how did it get out (including hops whose logs are missing), and what should be shut first. Everything is deterministic arithmetic. There is no machine learning and no randomness.

---

## 1. Interface

```python
def trace(scenario: dict, top_k: int = 5) -> dict:   # returns TraceResult (contract section 9)
```

- Input is the public scenario only. The engine MUST NOT import `app.sim`, read truth, read `params.log_loss`, or use artifact or event id values for any decision (ids are labels only; a test permutes them).
- Output validates against the contract invariants (section 9 of the contract) and masks nothing itself (it never sees raw values).
- Pure function: no global state, no clock, no network, no randomness. Same input, same output.
- Target time: under 3 seconds for the demo scenario (about 3,000 events, 6 artifacts).

---

## 2. Modules

```
engine/
  normalize.py    (uses common/sketch.py)
  index.py        build lookup tables from the scenario
  loss.py         estimate loss rate per log source from seq gaps
  origin.py       stages 0 to 2: canary pin, candidate scoring
  anomaly.py      baselines and event anomaly
  paths.py        stage 3: custody path enumeration
  rank.py         stage 5: scoring, softmax, marginals
  chokepoint.py   stage 6
  evidence.py     stage 7 and the evidence/summary text templates
  graph.py        TraceResult.graph builder
  trace.py        orchestration
```

---

## 3. Config (all in `backend/app/config.py`, nowhere else)

```python
ENGINE = {
  # origin
  "W_CONTAINMENT": 5.0, "W_SPECIFICITY": 1.0, "W_FORMAT": 2.0,
  "WM_RATIO_MIN": 0.9,        # watermark term only if |L|/|E| >= this
  "WM_CAP": 8.0,              # max magnitude of the watermark penalty
  "WM_TOLERANCE_MIN": 5,      # minutes of slack on the watermark hard rule
  "NO_MATCH_CONTAINMENT": 0.2,# below this a candidate is not used for paths
  "ORIGIN_MARGIN": 12.0,      # keep candidates within this origin_fit of the best
  "MAX_CANDIDATES": 8,
  # path costs
  "OBS_COST": 0.10, "H_ENDPOINT": 0.50, "H_BASE": 1.0,
  "ACTOR_SWITCH": 1.0, "UNKNOWN_CHANNEL": 2.0,
  "LOSS_DEFAULT": 0.40, "LOSS_FLOOR": 0.05, "LOSS_CEIL": 0.90, "LOSS_MIN_EVENTS": 20,
  "MAX_HIDDEN": 2, "MAX_DEPTH": 6, "MAX_PATHS_PER_ORIGIN": 2000, "COST_MARGIN": 8.0,
  "ACTOR_ALT_MAX": 3, "ACTOR_ALT_WINDOW_DAYS": 7,
  # scoring
  "W_ORIGIN": 1.0, "W_PATH": 1.0, "W_ANOMALY": 0.6, "TEMPERATURE": 1.0,
  # anomaly
  "BASELINE_DAYS": 30, "BASELINE_MIN_EVENTS": 3, "SIGMA_FLOOR": 0.5,
  "DEFAULT_MU": 3.93, "DEFAULT_SIGMA": 1.0,     # ln(51)
  "Z_CAP": 4.0, "OFF_HOURS_W": 0.5, "FIRST_TIME_W": 0.7, "PRIV_W": 0.7, "PRIV_WINDOW_DAYS": 7,
  # outputs
  "TOP_K": 5, "CHOKE_MAX": 3, "EVIDENCE_MAX": 3,
  "ENGINE_VERSION": "1.0.0",
}
```

Tune only on benchmark seeds 0 to 49 (see `04_TEST_PLAN.md`). Every change to this dict is logged in `docs/DECISIONS.md` with before and after numbers.

---

## 4. Pre-processing (`index.py`, `loss.py`)

Build once:
- `loc[id]`, `actor[id]`, `artifact[id]`, `dataset[id]`, `src_to_loc`.
- `events` sorted by `(ts, seq, id)`; `events_by_actor`, `events_by_object`.
- `owner_endpoint[actor_id]` = the endpoint Location whose `owner_actor == actor_id`.
- `moves_by_artifact[art_id]` = events with `object == art_id`, `action` in {copy, download, upload, send, api_call}, and `to_loc` not null.

Loss estimate per log source `s` (`loss.py`):
```
seqs = sorted seq of surviving events with source s
if len(seqs) < LOSS_MIN_EVENTS: p = LOSS_DEFAULT
else: expected = seqs[-1] - seqs[0] + 1; p = (expected - len(seqs)) / expected
p = clip(p, LOSS_FLOOR, LOSS_CEIL)
```
Known bias: dropped events at the very end of a source's stream are invisible. Accept it, mention it in `notes` only if a source has zero events.
Output `loss_estimates = {src_id: p}` rounded to 4 decimals (for all log sources in the scenario, including the default ones).

---

## 5. Stage 0: canary pin (`origin.py`)

If `leak_sample.canary_hits` is non-empty: look each hit up in `canary_registry`; count hits per `export_id`; pick the export with the most hits (ties: earliest `created_ts`). Set `origin_pinned = true`, `pinned = that artifact id`, and add a note `"Origin pinned by canary {can_id} planted in {art_id}."` (the word "canary" must appear). Unknown canary id: ignore and add a note.
If pinned, only that artifact is used for paths (stages 3 to 5). Stage 2 is still computed for the `origin_candidates` table.

---

## 6. Stages 1 and 2: origin candidates (`origin.py`)

Let `L` = leak sample, `E` = an artifact.

Shared identifier columns `S = [c for c in IDENTIFIER_COLUMNS if c in L.sketches and c in E.sketches]`.

Hard rules (first violated rule wins, in this order):
1. `schema`: `set(L.columns) - set(E.columns)` is non-empty.
2. `watermark_before`: `E.created_ts < L.newest_record_ts - WM_TOLERANCE_MIN minutes`.
3. `after_found`: `E.created_ts > L.found_ts`.

Excluded candidates get `verdict = "excluded"`, `exclusion_rule` set, numeric fields `null` (except `containment` can still be filled for rules 2 and 3 if `S` is non-empty; schema exclusion leaves all null), and a note explaining in plain English (for example "Created before the newest leaked record existed").

Soft score for the rest:
```
containment C   = mean over c in S of containment(L.sketches[c], E.sketches[c])     # common/sketch.py
                  if S is empty: C = 0.05 and add note "no shared identifier columns"
ratio           = clip(L.row_count / E.row_count, 0.01, 1.0)
format_sim      = see 6.1
gap_hours       = max(0, (E.created_ts - L.newest_record_ts) in hours)
WM              = -min(E.arrivals_per_hour * gap_hours, WM_CAP)   if ratio >= WM_RATIO_MIN else 0
origin_fit      = W_CONTAINMENT*ln(max(C,0.001)) + W_SPECIFICITY*ln(ratio) + W_FORMAT*format_sim + WM
```
Reasoning for WM: if the leak is a full copy of E, then any records created between the leak's newest record and E's creation time should be in E, but then they would also be in the leak. Missing newer records mean E was made close to the newest record. The cap stops the term from dominating when rates are mis-modelled.

`OriginCandidate` output: `containment`, `specificity = ratio`, `format_sim`, `watermark_term = WM`, `origin_fit`, `notes`. Sort `origin_candidates`: candidates by `origin_fit` descending, then excluded ones (by `created_ts`).

Candidates used for paths: verdict `candidate`, containment >= `NO_MATCH_CONTAINMENT`, `origin_fit >= best_fit - ORIGIN_MARGIN`, at most `MAX_CANDIDATES` (best first). If none qualify: return a result with `hypotheses = []`, `origin_ranking = []`, `chokepoints = []`, `recommended_evidence = []`, empty graph, and `notes = ["The leak does not match any known export (best containment X). It may be a join of several sources or come from an unknown system. Collect: ..."]`. Never raise.

### 6.1 `format_sim`

Collect attribute pairs:
- 6 global: `delimiter`, `quoting`, `header_case`, `line_ending`, `encoding`, `null_token`.
- For each column `c` in `L.columns ∩ E.columns`: for each key (`style` or `case`) present in `L.format_profile.columns[c]`, one pair (leak value, export value). If the export entry lacks the key, count it as a mismatch.

`format_sim = matches / total_pairs`, in [0, 1]. Round to 4 decimals.

---

## 7. Stage 3: custody paths (`paths.py`)

Model: the leaked file's custody moves between locations. A path is a list of hops from the origin artifact's first location to `L.found_at`.

State: `(loc, t, holder, hidden_count, depth, cost, hops, visited)`.
Start for candidate artifact `E`: `loc = E.location`, `t = E.created_ts`, `holder = E.created_by`, `cost = 0`.

Goal: `loc == L.found_at`.

Moves from a state (try all, depth-first, deterministic order: sort by `(kind, to_loc, actor, event_id)`):

**M1 observed move.** For each event `e` in `moves_by_artifact[E.id]` with `e.from_loc == loc`, `e.ts >= t`, `e.ts <= L.found_ts`, `e.to_loc not in visited`: new state `(e.to_loc, e.ts, e.actor)`; hop `kind = observed`, `event_id = e.id`; cost `+OBS_COST`.

**M2 hidden move to the leak location.** If `loc != found_at` and (`loc.kind` in {endpoint, external} or `loc.egress_capable`):
- Actors: if `loc.kind == endpoint`: `[owner_actor]` (skip if none). Otherwise `[holder] + alt`, where `alt` = up to `ACTOR_ALT_MAX` other actors that have an observed event with `from_loc == loc` or `to_loc == loc` in the `ACTOR_ALT_WINDOW_DAYS` days before `found_ts` (most recent first, tie by id).
- Actor must have `loc` in its `access` (endpoint owner always passes).
- Cost: hidden hop cost (7.1) `+ ACTOR_SWITCH` if `loc.kind == system` and actor != holder.
- Terminal: the path ends here.

**M3 hidden download to a person's endpoint.** If `loc.kind == system`: for every actor `X` with `loc` in `X.access` and an endpoint `ep:X` in `X.access`, and `ep:X` not visited, and NO observed event exists with actor `X`, object `E.id`, `from_loc == loc`, `to_loc == ep:X` (otherwise M1 covers it): hop to `ep:X`, actor `X`, kind inferred, cost = hidden hop cost (7.1). `hidden_count += 1`.

**M4 hidden copy between systems.** If `loc.kind == system`: for every other system `M` not visited, and every actor `X` that has both `loc` and `M` in `access` (candidates: `holder` first, then `alt` as above): hop to `M`, kind inferred, cost = hidden hop cost `+ ACTOR_SWITCH` if `X != holder`. `hidden_count += 1`. Only allowed if no observed event already moves `E` from `loc` to `M`.

Limits and pruning:
- `hidden_count <= MAX_HIDDEN`; `depth <= MAX_DEPTH`; no revisiting a location in one path.
- Time: observed moves need `e.ts >= t`. Hidden hops keep `t` unchanged (their time is unknown; `Hop.ts = null`).
- Prune a branch if `cost > best_complete_cost + COST_MARGIN` once any complete path is known.
- Stop after `MAX_PATHS_PER_ORIGIN` complete paths per origin.
- Deduplicate paths with identical hop tuples `(from, to, actor, event_id)`.
- If an origin yields no complete path: add one fallback path with a single hidden hop from `E.location` to `found_at` by `E.created_by`, cost `UNKNOWN_CHANNEL + H_BASE`, and add a note `"No custody path found for {E.id}; showing direct unknown channel."`.

### 7.1 Hidden hop cost

```
if source location has no log_source (endpoint, external):  H_ENDPOINT
else:                                                       -ln(loss_estimates[log_source]) + H_BASE
```
`est_loss` on an inferred hop = `loss_estimates[log_source]` for logged sources, `null` otherwise.

`path_cost = sum of hop costs` (observed hops cost OBS_COST each).

---

## 8. Stage 4: anomaly (`anomaly.py`)

For an observed event `e` (rows > 0) by actor `a`:

Baseline: events of the same actor with `rows > 0`, `ts` in `[e.ts - BASELINE_DAYS, e.ts)`, `id != e.id`. Use `x = ln(1 + rows)`. If fewer than `BASELINE_MIN_EVENTS`: use all such events of other actors with the same `role` (same window). If still fewer: `mu = DEFAULT_MU`, `sigma = DEFAULT_SIGMA`. Otherwise `mu = mean(x)`, `sigma = max(std(x), SIGMA_FLOOR)`.

```
z      = clip((ln(1 + e.rows) - mu) / sigma, 0, Z_CAP)
off    = 1 if actor.kind == "user" and (hour(e.ts) >= 22 or hour(e.ts) < 5 or weekday(e.ts) >= 5) else 0     # UTC
first  = 1 if the actor has no earlier event (within BASELINE_DAYS) with the same action and the same from_loc else 0
priv   = 1 if a permission_change grant with grantee == actor exists within PRIV_WINDOW_DAYS before e.ts and scope in {e.from_loc, null} else 0
event_anomaly(e) = z + OFF_HOURS_W*off + FIRST_TIME_W*first + PRIV_W*priv
```

Actor anomaly on a path: `A(actor, path) = max event_anomaly(e)` over observed events `e` by that actor with `rows > 0`, `ts` in `[origin.created_ts, found_ts]`, and (`e.from_loc` or `e.to_loc`) among the path's locations. If none: 0.
Actors on a path = the unique actors of its hops, EXCLUDING the origin artifact's creator when that creator is a service account (an export pipeline is not a suspect; a human creator who also moves the file IS counted). `Hypothesis.actors`, `actor_ranking` and the anomaly sum all use this definition.
Path anomaly = sum of `A(actor, path)` over the actors on the path. Record the best event per actor for the evidence text (including the actor's median rows `exp(mu)` for "usual about N").

---

## 9. Stage 5: rank (`rank.py`)

```
S(path) = W_ORIGIN*origin_fit(origin) - W_PATH*path_cost + W_ANOMALY*path_anomaly
P(path) = softmax(S / TEMPERATURE) over ALL enumerated paths of all used origins   (subtract the max first)
```
- `hypotheses` = the `top_k` highest `P`, with `rank`, `path_id = "hyp:{rank}"`, `score`, `score_parts = {origin_fit, path_cost, anomaly}` (anomaly before the weight), `probability` (4 decimals; remember the sum over returned hypotheses is at most 1).
- `origin_ranking` = for each origin artifact, sum of `P` over its paths, sorted descending.
- `actor_ranking` = for each actor on any hop, sum of `P` over paths containing it; `top_path_id` = the `hyp:` id of the best returned hypothesis containing it, else null. Sorted descending, ties by id.
- `location_ranking` = same for locations on hops (excluding `found_at`).
- If pinned: `origin_ranking = [{pinned, 1.0}]`.
- Probabilities are RELATIVE LIKELIHOODS. Never call them calibrated, anywhere (code comments, text templates, notes).

---

## 10. Stage 6: chokepoints (`chokepoint.py`)

Actionable item per hop (a hop can yield one item):
- `from_loc` is a system: `item_id = "perm:{actor}@{from_loc}"`; `item_type` = `api_key` if the actor id contains `api-key`, `service_account` if the actor kind is service, else `permission`.
- `from_loc` is an endpoint: `item_id = "perm:{actor}@egress"`, type `permission`.
- `from_loc` is external: `item_id = "ch:{from_loc}"`, type `channel`.
- Never produce an item for an actor excluded under section 8 (service-account creator of the origin artifact), and never for `found_at`.

Greedy (up to `CHOKE_MAX`):
1. `marginal(item)` = sum of `P` over ALL enumerated paths containing the item.
2. Pick the item with the highest marginal among paths not yet covered (tie: smaller item id). Record its own full `marginal`.
3. `cumulative_coverage` = sum of `P` over paths containing any chosen item so far.
4. Repeat on the uncovered paths.

`label` and `action_text` templates (use display names from the scenario, never raw ids):
- permission: `Revoke {name}'s access to {location name}`
- api_key: `Rotate and revoke API key {name}`
- service_account: `Suspend service account {name} until reviewed`
- egress: `Block outbound uploads from {name}'s laptop`
- channel: `Block transfers to {location name}`

---

## 11. Stage 7: which missing log helps most (`evidence.py`, SHOULD)

For each distinct inferred-hop signature `(from_loc, to_loc)` across all paths: `mass` = sum of `P` of paths containing it. `informativeness = H(mass) / ln 2` where `H(m) = -m ln m - (1-m) ln(1-m)`. Sort by informativeness descending (tie: larger mass, then id). Keep `EVIDENCE_MAX`.
`request_text`:
- from an endpoint: `Endpoint, proxy or DLP logs for {owner name}'s laptop between {created_ts} and {found_ts}`
- from a logged system: `{system name} audit logs ({src id}) between {created_ts} and {found_ts}`; if that source's `loss_estimates` is high say so: `(about {pct}% of this source's events appear to be missing)`.
- other: `Network logs for transfers from {location name}`.

---

## 12. Graph (`graph.py`)

Nodes: for the origin artifacts of the returned hypotheses (kind `artifact`, label = artifact id or filter description), every location on their hops (kind from the Location), the origin location. Edges: for each returned hypothesis, for each hop: `id = "e:{from}>{to}:{kind}:{event_id or 'hid'}"`; merge identical edges across hypotheses (`path_ids` union). Add one edge per origin artifact from the artifact node to its first location, kind observed, label `created by {creator name}`. Edge `label`: observed `"{actor name}: {action}, {rows} rows"`; inferred `"{actor name}: log missing (about {pct}% of {source} logs lost)"` or `"unlogged channel"`.

---

## 13. Text templates (no LLM; all values are names, counts, times, never raw personal data)

`summary_text` of a hypothesis, built from parts:
1. `"{Origin label} (created by {creator} at {ts}) is the likely source: {pct}% of the leaked records are in it."`
2. For each hop: observed: `"{actor} {verb} it from {from} to {to} at {ts}."`; inferred: `"A move from {from} to {to} by {actor} is inferred because no log was found."`
3. Anomaly: `"{actor} moved {rows} rows; their usual is about {median}."` (only if anomaly >= 2).

Verbs: download "downloaded", copy "copied", upload "uploaded", send "sent", api_call "pulled through the API".

`Evidence` list per hypothesis, in order: `fingerprint` (containment, format match count, watermark), `observed` per observed hop, `inferred` per inferred hop, `anomaly` per actor with anomaly >= 2.

---

## 14. Edge cases (each needs a test)

- No candidate survives or all containments < 0.2: empty hypotheses, note, no crash.
- Several candidates nearly equal: show them nearly equal; do not sharpen.
- Leak is a 10 percent sample: ratio < 0.9, no watermark term.
- Leak reformatted: format_sim drops, origin still found.
- Canary hit: origin pinned.
- Origin unreachable by any rule: fallback path (section 7) plus note.
- A source with no events: loss default 0.4.
- Scenario with zero events: still returns origin ranking, one fallback hypothesis per origin.
- Artifact ids permuted: same structure of result (a test remaps ids and compares).
- Two actors with identical evidence: probabilities within 0.10 of each other.

---

## 15. Complexity and performance

Enumeration is bounded by `MAX_PATHS_PER_ORIGIN * MAX_CANDIDATES` = 16,000 paths. Precompute per-actor event lists and baselines lazily with caching (dictionary keyed by event id). Target total under 3 seconds on demo scale; if slower, profile `paths.py` and `anomaly.py` first.

---

## 16. Required unit tests (engine agent writes, names in `tests/engine/`)

1. `test_sketch.py`: normalization vectors (contract section 6), jaccard identical = 1.0 and disjoint = 0.0, containment of a 50 percent subset within 0.05 of 1.0, determinism.
2. `test_loss.py`: seq gaps give the right fraction; fewer than 20 events gives the default; clipping.
3. `test_origin.py`: each hard rule; WM only when ratio >= 0.9; WM capped; format_sim exact values (the fixtures in `04_TEST_PLAN.md` give numbers: 1.0, 0.1111, 0.6667).
4. `test_anomaly.py`: baseline fallback chain, leave-one-out, off-hours only for users, first-time, privilege change.
5. `test_paths.py`: time order, hidden hop limit, no cycles, fallback path, observed move deduplicates M3.
6. `test_rank.py`: softmax sums to 1 over enumerated paths, marginals, pinned origin.
7. `test_chokepoint.py`: greedy order and cumulative coverage.
8. `test_trace_contract.py`: `trace()` output passes `validate_trace` on every fixture.
9. `test_scenarios.py`: H1 to H7 and the id-permutation test from `04_TEST_PLAN.md`. These tests are written by Tanish in the plan; the agent only wires them.
10. `test_determinism.py`: two runs equal.

---

## 17. Things the engine must never do

- Read or infer from artifact ids, event ids, `params`, or file names.
- Claim calibrated probabilities or certainty.
- Show unmasked personal values (it never has them).
- Silently drop a candidate without a reason in `notes` or `origin_candidates`.
- Take longer than 3 seconds on the demo scenario.

---

## 18. Phase deliverables

- Phase 1: `common/sketch.py` complete with tests; `normalize`, `index`, `loss`, `origin` (stages 0 to 2) complete; `trace()` returns origin tables and `origin_ranking`, hypotheses may be a single direct-hop stub; passes H1, H3, H6, H7 and the origin parts of H4.
- Phase 2: `paths`, `anomaly`, `rank`, `graph`, summary templates; passes H1 to H7 fully, id-permutation test, and the seed 42 checks at loss 0.0, 0.2, 0.4.
- Phase 3: `chokepoint`, `evidence` (stage 7), polish of text templates, performance.
- Phase 4: tuning (seeds 0 to 49 only) and benchmark runs.
