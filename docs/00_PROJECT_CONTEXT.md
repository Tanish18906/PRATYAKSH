# PUGMARK: Project Context (read this first)

Status: v1, written at T+1h of a 6-hour hackathon (INNOVATHON 2026). About 5 hours remain.
Team: 2 developers. All code is written by coding agents (Claude Code, Codex, Antigravity). The humans write specs, review output and run the demo.

---

## v1.1 CHANGES (supersede anything below that disagrees)

1. **Ownership.** Anmol owns the simulator, the mock Telegram part and the frontend. Tanish owns the engine, the API and integration. After the simulator, Anmol also takes the benchmark, baselines, chokepoints and canary flow. Details in `WORK_SPLIT.md`.
2. **Leak location in the demo.** The leaked file is found in a mock Telegram channel (`ext:telegram-leak-channel`), not on a file-share site. Flow: the investigator opens the simulated Telegram chat, sees the post with the CSV, clicks "Export and trace", and the tool fingerprints the file and traces it. Everything is simulated and labelled SIMULATED in the UI. No real Telegram access exists.
3. **Phases replace section 17.** The project is built in gated phases (see `PHASES.md`). Agents build one phase, stop, write a report, and wait for a human message `APPROVED PHASE N`. Rules are in `AGENTS.md`.
4. **Company time is UTC.** The 9:40 pm download in the story is 21:40Z. No time zone conversion anywhere.
5. **Exact shapes** are in `01_DATA_CONTRACT.md`.

---

## 0. How agents must use this document

1. Read this whole file before writing any code. It is the single source of truth for what we are building and why.
2. More documents follow in `docs/`. When they exist, read them in this order:
   - `01_DATA_CONTRACT.md` (exact JSON schemas, frozen after T+1:25)
   - `02_SIMULATOR_SPEC.md`
   - `03_ENGINE_SPEC.md`
   - `04_FRONTEND_SPEC.md`
   - `05_TEST_PLAN.md` (hand-written scenarios with known answers)
   - `06_DEMO_AND_PITCH.md`
   - `AGENTS.md` (short working rules, copied from section 18 below)
3. If this file and a later spec disagree, the later spec wins for details, this file wins for intent. Write the conflict into `docs/DECISIONS.md` and keep going.
4. You are one agent working on one module. Do not edit other modules, the data contract, or the tests written by humans.

---

## 1. One-paragraph summary

PUGMARK is a data-leak tracing tool. An investigator is handed a leaked file (for example 48,212 customer rows found on a file-sharing site) and a messy, partly missing set of event logs from the company's systems. PUGMARK answers three questions: (1) which export or dataset did the leaked file come from, (2) what is the most likely path it took to get out, including hops whose logs are missing, and (3) which single permission, key or channel should be shut first. It does this by matching the leaked file's hashed fingerprint to known exports (so raw data never has to be shared between systems), and by searching a provenance graph with explicit "missing log" hypotheses, then ranking the candidate paths. Output is ranked hypotheses with evidence, never a verdict.

---

## 2. The problem statement (verbatim) and how we read it

Problem statement #18, domain Cybersecurity, title "Tracing a Data Leak Across Systems":

> Sensitive information appears in an unexpected location, but several services, users, and data transfers may be involved. Investigators need to narrow down possible causes from incomplete event records without exposing more data.

Our reading, clause by clause. Every clause must be visibly handled in the demo.

| Clause | What we build |
|---|---|
| "appears in an unexpected location" | The investigator uploads a leaked sample and says where and when it was found. Detection is out of scope (see 3.2), but canary records show how detection plugs in. |
| "several services, users, and data transfers may be involved" | A provenance graph of users, service accounts, systems, datasets, export files and destinations, built from event logs. |
| "narrow down possible causes" | Ranked list of candidate origins and paths with relative likelihoods, plus a chokepoint recommendation. |
| "from incomplete event records" | Logs are lossy. The engine inserts explicit, penalised "missing log" hops and reports exactly which missing evidence would settle the question. |
| "without exposing more data" | Systems share only keyed-hash sketches, never rows. UI and reports mask values by default. Revealing a value requires a reason and is written to an audit log. |

---

## 3. Scope

### 3.1 In scope
- A synthetic company ("Nova Health") with a log simulator that can create leak scenarios with known ground truth.
- A tracing engine: fingerprinting, origin ranking, path search with missing hops, actor anomaly scoring, ranking, chokepoint analysis.
- A web UI with the provenance graph, ranked hypotheses, evidence, masked data, audit log.
- A benchmark that measures the engine against naive baselines under different log-loss levels.
- An auto-drafted incident report.

### 3.2 Out of scope (do not build, do not suggest building)
- Crawling Telegram, forums, the dark web or any real website. Not feasible in 5 hours, legally risky, and not what the PS asks.
- Training any ML model. The engine is deterministic scoring, not machine learning.
- Real personal data. All data is synthetic.
- Authentication, multi-user accounts, deployment, hosting, databases.
- Tracing leaks that leave no digital trail (screenshots, phone photos). We state this limit openly.
- Leaks that are a join of two sources (stretch only, see 16).

### 3.3 The one thing that makes this different from a SIEM or log search
A SIEM searches logs. PUGMARK starts from the leaked content, matches it to the export it came from, and then reasons about custody of that file across systems even when logs are missing. Keep this distinction in every explanation.

---

## 4. Demo company and the main story (seed 42)

Fictional company: Nova Health, a health insurer. Nothing here refers to a real company or person. All names are generated.

### 4.1 Systems (nodes of type `system`)
customer-db, claims-api, crm, bi-warehouse, notebook-server, partner-sftp, object-store, ticketing, email-gateway.

Also: employee endpoints (one per user, type `endpoint`, almost never logged) and external destinations (type `external`): `personal-cloud-drive`, `file-share-site`, `telegram-channel` (mock only).

### 4.2 Actors
About 20 users plus 3 service accounts. Roles: analyst, bi-admin, engineer, marketing, support, contractor.

Cast that matters for seed 42:
- Ravi Menon, data analyst (the true leaker in seed 42). Normally downloads about 300 rows a day.
- Meena Iyer, BI admin. Can read everything in bi-warehouse. Innocent but suspicious on paper.
- Arjun Das, contractor. Made a big full-table export weeks earlier.
- Kavya Rao, marketing. Made a narrower export with fewer columns.
- `etl-nightly`, service account that exports every night.
- `partner-api-key-7`, service account used by a vendor. Listed exports but never downloaded one.
- `backup-svc`, service account.

### 4.3 Datasets and columns
`customers` with columns: customer_id, full_name, email, phone, dob, city, state, signup_date, policy_no, premium_tier. Also `claims` and `marketing_leads` for noise.

### 4.4 The seed 42 story (ground truth, never visible to the engine)
- 2026-10-02: Arjun Das exports the full customers table (310,000 rows, dates as DD/MM/YYYY, phone as 10 digits) to his sandbox. This is export E2.
- 2026-10-06: Kavya Rao exports name, email, city for marketing (no policy_no). Export E3.
- 2026-10-09 02:10: `etl-nightly` exports customers where state = CG and signup_date >= 2025-01-01 to bi-warehouse. 48,900 rows, ISO dates, phone as +91-XXXXXXXXXX. Export E1. Newest record inside it was created 2026-10-08 23:12.
- 2026-10-09 21:40: Ravi downloads E1 from bi-warehouse to his laptop. 48,900 rows, his normal is about 300. This is 9:40 pm.
- 2026-10-10 02:10: `etl-nightly` runs again and creates E4 (same filter, same format, about 400 more rows). Good decoy: same job, same format.
- 2026-10-10 about 22:00: Ravi uploads the file from his laptop to `file-share-site`. This log is LOST (the "missing hop").
- 2026-10-12 08:30: the leaked file is found on `file-share-site`. It has 48,212 rows (E1 with duplicates removed), columns name, phone, policy_no, and the newest record is 2026-10-08 23:12.

What the engine should conclude: origin E1, path E1 to Ravi's download to (missing hop) to file-share-site, Ravi at roughly 70 percent, the partner key and Meena well below. Containment advice: revoke Ravi's download right and bi-warehouse bulk export right. Missing evidence that would settle it: endpoint or proxy logs for Ravi's laptop on 2026-10-09 to 10-10.

Why this story is good for the demo:
- A naive "last accessor" baseline picks `etl-nightly` (it touches the data every night). PUGMARK does not.
- E2 is excluded by the watermark rule (it was made before the newest leaked record existed).
- E4 is excluded by the watermark gap penalty (the leak lacks the 400 newer records E4 contains).
- The only link to Ravi's exit is a missing log, so the demo shows inference, not lookup.

---

## 5. Architecture

```
 +-------------------+     public scenario JSON      +--------------------+
 |  SIMULATOR        | ----------------------------> |  ENGINE            |
 |  (backend/sim)    |  events (lossy), entities,    |  (backend/engine)  |
 |                   |  export artifacts+sketches,   |                    |
 |  private rows,    |  canary registry, leak sample |  never sees truth  |
 |  ground truth     |                               |  or raw rows       |
 +---------+---------+                               +----------+---------+
           | truth (separate file)                              | trace result JSON
           v                                                    v
 +-------------------+                               +--------------------+
 |  BENCHMARK        | <---------------------------- |  API (FastAPI)     |
 |  (backend/bench)  |   runs engine, compares       |  + privacy layer   |
 +-------------------+   with truth + baselines      +----------+---------+
                                                                | HTTP/JSON
                                                                v
                                                     +--------------------+
                                                     |  FRONTEND          |
                                                     |  React + Cytoscape |
                                                     +--------------------+
```

Stack:
- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, NetworkX (graph export only), NumPy, pandas, Faker (small tables only), pytest.
- Frontend: React, Vite, Tailwind, Cytoscape.js (use the built-in `breadthfirst` or `cose` layout, no extra layout plugin), Recharts, Framer Motion.
- Storage: files and memory only. No database.
- Runtime: everything works offline on one laptop. No call to the internet may be required for the demo.
- LLM: optional, used only to phrase the plain-English summary and report. Always has a template fallback and a 3 second timeout. The ranking never depends on an LLM.

Hard rule: the engine receives only the "public scenario". Ground truth lives in a separate file read only by tests and the benchmark. Mixing them invalidates the benchmark.

---

## 6. Data model (conceptual, exact schemas in 01_DATA_CONTRACT.md)

- Entity: `actor` (user or service account, with role and access list), `system`, `dataset`, `endpoint`, `external`.
- Event: `{id, ts, seq, source, actor, action, object, target, rows, meta}`. `action` is one of `read`, `query`, `export`, `copy`, `send`, `upload`, `download`, `api_call`, `permission_change`. `seq` is a per-source increasing counter assigned before loss, so gaps reveal how much a source lost.
- Export artifact: a file created by an export-like event. Fields: `id`, `dataset`, `created_by`, `ts`, `location`, `columns`, `row_count`, `format_profile`, `sketches` (per identifier column), `newest_record_ts`, `arrivals_per_hour` (aggregate count of new matching records per hour, not row data).
- Leak sample: what the investigator holds. Fields: `found_at`, `found_ts`, `columns`, `row_count`, `format_profile`, `sketches`, `newest_record_ts`, `masked_preview` (a few masked rows), `canary_hits`.
- Canary registry: hashes of planted fake identifiers mapped to the export they were planted in.
- Scenario public file: all of the above plus entities and lossy events. Scenario truth file: true origin artifact, true path, true actors, true leak location.

---

## 7. The simulator

Goal: produce realistic, messy, randomisable scenarios with known ground truth so we can demo, test and benchmark.

### 7.1 What it generates
- Entities as in section 4 (counts configurable).
- 30 days of background events (reads, queries, normal exports, API calls). Per actor, a baseline of normal behaviour (rows per action drawn from a log-normal distribution, usual hours, usual systems).
- A base customers table (synthetic). Generate it once with vectorised NumPy and cache it (pickle or parquet). Do not call Faker per row for tens of thousands of rows, it is too slow.
- Several export artifacts from that table with different filters, columns and formatting styles, each with sketches.
- One leak scenario from an archetype (7.2), with decoys.
- Event loss (7.3).
- A leak sample derived from the final artifact on the true path.

### 7.2 Archetypes
Must have (A1 to A3), should have (A4, A5):
1. A1 insider via laptop: export to warehouse, analyst downloads, upload from laptop to external site. Final hop usually unlogged.
2. A2 compromised API key: a service key pulls an export through the API from an unusual IP. The export hop is logged, the key theft is not.
3. A3 vendor SFTP: an export is sent to a vendor through partner-sftp (legitimate), vendor later leaks. Chain of custody ends at the vendor boundary. The report must say so.
4. A4 public bucket: an engineer changes an object-store ACL to public. The file is found at the bucket URL.
5. A5 backup copy: backup-svc copies a snapshot to a bucket readable by many.

Each archetype randomises: which user or key is involved, which export, timestamps, volume, subsampling of the leak (10 percent to 100 percent), reformatting by an intermediate tool (for example CSV to Excel to CSV, which changes date and phone style), and the decoys.

### 7.3 Loss model
- Each log source has a base drop probability `p_loss` (benchmark levels 0.0, 0.2, 0.4, 0.6) with per-source jitter.
- `seq` is assigned before dropping, so missing sequence numbers are observable.
- Rule: in at least 50 percent of scenarios the final egress event of the true path MUST be dropped. Otherwise the benchmark is trivial.
- Endpoints (laptops) are unlogged by default in A1.

### 7.4 Formatting styles (these create the fingerprint)
Each export job or tool has a style: date format (`ISO`, `DD/MM/YYYY`, `MM-DD-YY`), phone format (`+91-XXXXXXXXXX`, `XXXXXXXXXX`, `+91 XXXXX XXXXX`), name case (title, upper, lower), email case, null token (`""`, `NULL`, `N/A`), delimiter, quoting, header casing, line endings. The style is recorded in `format_profile` and applied to the real rows.

### 7.5 Canaries
When canary mode is on, each export gets 3 planted fake rows with unique fake email, phone and name. The registry stores only keyed hashes of those values. The simulator can also emit a "canary alert" (for example, a phishing mail reached canary address X at time T).

### 7.6 Scale
- Demo scale: base table about 60,000 rows, leak about 48,000 rows (precomputed and cached).
- Benchmark scale: base table about 5,000 rows, leak sizes scaled down. Must be configurable via `SCALE` in config.
- Everything is seeded. Same seed, same scenario, byte for byte.

---

## 8. The engine

Input: public scenario. Output: trace result (ranked candidates, evidence, chokepoints, suggested evidence, report data). Pure functions, deterministic, no network.

All weights below are defaults in `config.py`. Tune them on seeds 0 to 49 only. Report numbers on seeds 50 to 199.

### Stage 0: Canary check
Hash every identifier value of the leak sample with the case key and look it up in the canary registry. A hit pins the origin to that export with very high confidence and sets `origin_pinned = true`. Skip stages 1 and 2 scoring (still produce path analysis).

### Stage 1: Fingerprint the leak
Compute, from the leak sample (never shown raw):
- Column set.
- Row count and distinct count of each identifier column.
- Format profile (section 7.4 attributes).
- Normalised identifier sketches. Normalise before hashing: email lowercase and trimmed; phone digits only, last 10; policy_no uppercase and trimmed; name lowercase and whitespace collapsed; dates parsed to ISO. Hash with HMAC-SHA256 using a per-case secret key. Keep the k smallest hashes per identifier column (bottom-k sketch, default k = 512).
- `newest_record_ts`: newest creation or signup date among leaked rows.

### Stage 2: Rank candidate origins
Candidates are all export artifacts plus any base dataset snapshot. For each candidate E:

Hard rules (violations remove the candidate, reason shown in the UI):
- Every leaked column must exist in E's columns.
- `E.ts` must be on or after `leak.newest_record_ts` (minus a small tolerance).
- `E.ts` must be before `leak.found_ts`.

Soft score:
```
origin_fit(E) = 5.0 * ln(max(C, 0.001))
              + 1.0 * ln(clip(|L| / |E|, 0.01, 1))
              + 2.0 * format_sim
              + WM(E)
```
- `C` is containment of the leak inside E. From bottom-k sketches estimate the Jaccard index J of the identifier sets, then `C = J * (|L| + |E|) / ((1 + J) * |L|)`, using exact set sizes. Average C over identifier columns that both have.
- `|L| / |E|` is specificity: prefer the smallest export that still contains the leak.
- `format_sim` in [0, 1] is the share of matching format attributes over shared columns. A mismatch lowers the score but never excludes it, because intermediate tools can reformat (a laundering hop).
- Watermark term: if `|L| / |E| >= 0.9` (the leak looks like a full copy), then `WM(E) = -arrivals_per_hour * gap_hours` where `gap_hours = E.ts - leak.newest_record_ts`. Reasoning: if E was made long after the newest leaked record, E should contain newer records that the leak lacks. Otherwise `WM(E) = 0`.

Output: a table of every candidate with containment, specificity, format similarity, watermark term, verdict (`candidate`, `excluded: <rule>`) and the combined score.

### Stage 3: Enumerate custody paths with missing hops
Model custody of the artifact as moving between locations (system, endpoint, external). Start from each surviving origin candidate, at its creation time and location.

- Observed edges: events where the artifact (by id) or an equivalent copy moved between locations (`copy`, `download`, `send`, `upload`, `api_call` returning the artifact).
- Hidden edges (hypothesised missing log): from any reached location to another location where (a) some actor has access to both, and (b) the move is plausible for the channel. Allowed targets: the leak location (if the source location can reach the outside), or an endpoint of an actor with access to the current location.
- Constraints: timestamps non-decreasing along the path; each hop's actor has access to the source location; at most 2 hidden hops per path; path ends at the leak location with time at or before `found_ts`.
- Enumeration: depth-first search with pruning, max depth 6. Expect tens to a few hundred paths. NetworkX is only for exporting the graph to the UI.

Path cost:
```
path_cost = sum over hops of:
    0.10                                  if observed
    0.50                                  if hidden and source is an unmonitored endpoint
    -ln(p_loss_source) + 1.0              if hidden otherwise
```
`p_loss_source` is the estimated loss rate of the log source that would have recorded the hop. Default 0.4. If sequence numbers are available (should-have), estimate it as `missing_seq / expected_seq` per source.

For a hidden hop, the default hypothesised actor is the previous holder. Using a different actor with access costs an extra 1.0.

### Stage 4: Actor anomaly
For each actor on a path, using that actor's 30-day baseline for the action type:
```
anomaly = min(z, 4) + 0.5*off_hours + 0.7*first_time_action + 0.7*recent_privilege_change
z = (ln(1 + rows) - mu_actor) / sigma_actor
```
Off hours means 22:00 to 05:00 local or a weekend. For hidden hops use the anomaly of the previous observed action in the path.

### Stage 5: Rank
```
S(path) = 1.0 * origin_fit(origin) - 1.0 * path_cost + 0.6 * sum(unique actor anomalies)
P(path) = softmax(S / T), T = 1.0
```
These are relative likelihoods, not calibrated probabilities. Never describe them as calibrated.

Also produce actor ranking and system ranking: marginal = sum of P(path) over paths containing that actor or system.

### Stage 6: Chokepoints
For every actionable item (a permission, API key, service account, export right, channel), compute its marginal over paths. Recommend the highest marginal item. Then remove paths that contain it, renormalise and pick the next one (greedy). Show "closing these two covers X percent of plausible paths."

### Stage 7: What evidence would help most (should-have)
For each hidden hop type h across candidate paths, let `m(h)` be the total probability of paths containing it. Informativeness is the binary entropy of `m(h)`. Recommend recovering the log source whose hidden hop has `m(h)` closest to 0.5, phrased as a concrete request ("endpoint or proxy logs for Ravi's laptop, 9 Oct 21:40 to 10 Oct 23:59").

### Edge cases the engine must handle
- No candidate survives: output "leak does not match any known export; possible join of sources or unknown source" and list what to collect. Do not crash.
- Several candidates with near-equal scores: show them near-equal. Do not fake confidence.
- Leak is a subsample (10 percent): containment still works, specificity handles size.
- Reformatted by an intermediate tool: format_sim drops, containment holds, origin still found.

---

## 9. Privacy by design (this is half of the PS, treat it as a feature)

1. Sketch-only matching. Systems expose per-export bottom-k sketches built with a per-case HMAC key. The engine never receives source rows.
2. Masking by default. Every API response masks identifiers (`ra***@example.com`, `+91-98*****21`). Names show initials only.
3. Reveal with reason. `POST /api/reveal` needs a reason string and writes `{ts, investigator, object, field, reason}` to the audit log.
4. Audit log. Every trace, reveal, report export and scenario injection is logged and visible in the UI.
5. Minimal reports. The report contains counts, hashes, timestamps and masked examples. No raw personal data.
6. Honest limits (must be stated in the pitch): low-entropy fields such as phone numbers can be brute-forced from plain hashes. The per-case secret key and bottom-k sketches reduce the risk, they do not remove it. This is a minimal-exposure design, not zero-exposure.

---

## 10. API (preliminary, final shapes in 01_DATA_CONTRACT.md)

| Method and path | Purpose |
|---|---|
| `POST /api/scenario/generate` | body: `archetype`, `seed`, `log_loss`, `canary_mode`, `scale`. Returns `scenario_id` and the public scenario summary. |
| `GET /api/scenario/{id}` | Public scenario (masked). Never includes truth. |
| `POST /api/trace` | body: `scenario_id`. Runs the engine, returns the trace result. |
| `POST /api/inject` | body: `scenario_id`, `actor` (and optional `path_type`). The judge picks a user or service, a new leak is created through them, returns a new `scenario_id`. |
| `POST /api/canary/alert` | Simulates a canary being seen in the wild, starts a trace automatically. |
| `POST /api/reveal` | body: `object_id`, `field`, `reason`. Returns unmasked value from the leak sample and logs it. |
| `GET /api/audit` | Audit log entries. |
| `POST /api/benchmark/run` and `GET /api/benchmark/{id}` | Run and fetch benchmark results. |
| `GET /api/report/{trace_id}` | HTML incident report. |
| `GET /api/health` | Liveness. |

Performance targets: trace of the demo scenario under 3 seconds; full benchmark (800 runs at benchmark scale) under 3 minutes using multiprocessing, or reduce the number of seeds.

---

## 11. Frontend

Single page, dark investigative theme, one accent colour, readable at projector distance (large type, high contrast). It must not look like a default graph demo; spend real time on the path animation and layout.

Layout:
1. Top bar: archetype select, seed, log-loss slider (0 to 60 percent), canary toggle, buttons `Generate`, `Trace`, `Inject leak (judge picks)`, `Run benchmark`.
2. Left panel, Incident: where and when the leak was found, row count, column chips, format fingerprint chips, newest-record watermark, masked preview rows, `Reveal` button (asks for a reason).
3. Centre, Provenance graph (Cytoscape): nodes coloured by type (actor, system, dataset, artifact, endpoint, external). Observed edges are solid. Inferred (missing log) edges are dashed, amber, and labelled "log missing, est. loss 40%". Selecting a hypothesis highlights its path with a moving dash animation. A toggle switches between the top 3 paths.
4. Right panel, Hypotheses: ranked cards with a probability bar, plain-English summary, the evidence list (each item says observed or inferred, and shows its timestamp), and an anomaly note ("downloaded 48,900 rows, usual 300").
5. Tabs under the graph:
   - Origin match: the candidate table from stage 2 with exclusion reasons.
   - Containment: chokepoint card ("Close these two doors: covers 84 percent"), and the "evidence that would settle this" card.
   - Benchmark: grouped bar chart of top-1 and top-3 accuracy for PUGMARK vs two baselines at each loss level, with a note that these are synthetic-data numbers.
   - Report: preview and download.
   - Audit: reveal and trace log.
6. Fallback mode: if the backend is unreachable, load `public/demo.json` (precomputed seed 42 trace) so the demo still runs. Show a small "offline replay" badge in that mode.

---

## 12. Incident report (auto-drafted)

Sections: incident summary; how it was found; scope (counts only); probable origin (with ranking); probable path (observed vs inferred hops, clearly marked); evidence gaps; recommended containment; notification checklist; audit trail.

The notification checklist must refer to India's DPDP breach-reporting obligations in general terms ("report to the Data Protection Board and notify affected people as the rules require"). Do NOT state specific hour deadlines or claim the rules are in force unless the team has verified the official notification. Add a visible line: "Verify current legal timelines with counsel."

Narrative text: template by default. Optional LLM phrasing with a 3 second timeout and automatic fallback to the template.

---

## 13. Benchmark and tests

### 13.1 Benchmark
- 200 seeds per loss level, loss levels 0.0, 0.2, 0.4, 0.6, archetypes mixed.
- Tune weights on seeds 0 to 49. Report only on seeds 50 to 199.
- Metrics: origin top-1 and top-3, actor top-1 and top-3 (true actor within the first n ranked), mean rank of the true actor.
- Baselines:
  - B1, last accessor: rank actors by recency of access to any dataset the leak could come from.
  - B2, biggest exporter: rank actors by total rows exported.
  - For origin: B3 largest export, B4 most recent export.
- Output: JSON for the UI chart plus a printed table.
- The generator and the engine are written by DIFFERENT agents. This is deliberate, to reduce the chance that the scorer is fitted to the generator's quirks.

### 13.2 Hand-written scenarios with known answers (humans write the expected results)
- H1: two near-identical exports, different styles. Expected: the one with matching format and watermark wins.
- H2: shared object-store bucket with two readers. Expected: both appear in the top 2 with near-equal likelihood.
- H3: laundered through reformatting (CSV to Excel to CSV). Expected: origin still found, format_sim lower.
- H4: leak is a 10 percent sample. Expected: correct origin in top 1.
- H5: critical hop dropped and two equally anomalous insiders. Expected: roughly equal ranking and a specific "evidence to collect" recommendation. The engine must not claim certainty.
- H6: canary hit. Expected: origin pinned.
- H7: no matching export. Expected: graceful "no match" output.

### 13.3 Unit tests the engine agent must write
Sketch estimator accuracy on known sets, normalisation (phone, email, date), hard-rule exclusions, watermark behaviour, path constraints (time order, hidden-hop limit), softmax and marginals, greedy chokepoints, determinism for a fixed seed.

Rule: agents may not edit tests to make them pass. If a test seems wrong, write the concern in `docs/DECISIONS.md` and ask a human.

---

## 14. Repository layout

```
pugmark/
  AGENTS.md
  docs/                     00 to 06 docs, DECISIONS.md
  backend/
    app/
      main.py               FastAPI app and routes
      config.py             all weights, constants, SCALE, seeds
      models.py             Pydantic models (mirror 01_DATA_CONTRACT)
      llm.py                optional LLM wrapper with fallback
      sim/                  generator.py, archetypes.py, styles.py, lossy.py, canary.py, truth.py
      engine/               normalize.py, sketch.py, profile.py, origin.py, paths.py,
                            anomaly.py, rank.py, chokepoint.py, evidence.py, trace.py
      privacy/              mask.py, audit.py
      report/               build.py, template.html
      bench/                run.py, baselines.py, metrics.py
    tests/                  unit tests, hand-written scenarios (H1 to H7)
    data/                   cached base tables, generated scenarios (gitignored)
  frontend/
    src/                    components for Incident, Graph, Hypotheses, Tabs
    public/demo.json        precomputed seed 42 trace for offline replay
```

---

## 15. Determinism, config, offline

- Every random call uses a seeded generator derived from the scenario seed. No global randomness, no use of current time inside the engine.
- All numeric weights live in `config.py`. No magic numbers elsewhere.
- No runtime network access is required. LLM calls are optional and wrapped.
- Same input, same output. The seed 42 demo must give the same ranking on every run.

---

## 16. Feature tiers (cut from the bottom when time runs short)

Must (demo fails without these):
- Simulator with archetypes A1 to A3, decoys, loss model, ground-truth separation.
- Leak upload, fingerprint display, origin ranking table with exclusion reasons.
- Path search with explicit missing hops, ranking, evidence cards.
- Graph UI with top 3 paths and dashed inferred edges.
- Masking, reveal with reason, audit log.
- Auto-drafted report.
- Offline replay (`demo.json`).

Should:
- Chokepoint card with greedy second action.
- Benchmark chart with baselines.
- Judge-driven "inject leak via this actor" button.
- Log-loss slider.
- Sequence-gap loss estimation.
- Archetypes A4 and A5.

Stretch (only if ahead at T+3:30):
- Canary records and canary alert flow.
- "Which missing log helps most" card.
- LLM narration.
- Leak that joins two sources.

---

## 17. Timeline for the remaining 5 hours (T = now)

Dev A owns backend (simulator then engine). Dev B owns frontend, report, demo, pitch. Agents are assigned by module; use different agents for the simulator and the engine.

| Time | Dev A | Dev B |
|---|---|---|
| T+0:00 to 0:25 | Together: write docs 01 to 05, freeze the data contract, scaffold repos, create a hand-made sample output JSON | same |
| T+0:25 to 1:25 | Simulator: entities, events, exports with sketches, archetype A1, loss model | UI shell on the sample JSON: layout, graph, masking, hypothesis cards |
| T+1:25 to 3:00 | Engine: fingerprint, origin ranking, paths, anomaly, ranking, tests H1 to H5 | Wire the API, path animation, evidence cards, reveal and audit log, origin table |
| T+3:00 to 3:40 | Integration, fix first end-to-end run, add A2 and A3 | Judge-drive button, loss slider, offline replay file |
| T+3:40 to 4:10 | Benchmark harness and chart data, tuning on seeds 0 to 49 | Report generator, chokepoint and evidence cards, benchmark chart |
| T+4:10 to 4:20 | Stretch (canary) only if everything above works | Polish, 4 slides |
| T+4:20 | CODE FREEZE | CODE FREEZE |
| T+4:20 to 5:00 | Rehearse the demo three times, record a backup video, prepare Q&A | same |

Notes:
- `git tag ok-N` at every integration point that runs end to end. If something breaks after T+4:00, roll back to the last tag.
- If the organisers set a submission deadline earlier than T+5:00, move the freeze earlier and drop stretch work first, then "should" items from the bottom.

---

## 18. Working rules for coding agents (copy into AGENTS.md)

1. Read docs 00 to 06 before coding. Work only in your assigned module.
2. Never edit `01_DATA_CONTRACT.md` or any test written by a human. Never change a test to make it pass.
3. The engine must never read ground truth or raw source rows. Enforce this by types and imports.
4. Write tests first for engine functions, then implement until they pass. Report real test output, not a summary.
5. Pure, deterministic functions. Seeds everywhere. All constants in `config.py`.
6. No new dependency without a one-line note in `docs/DECISIONS.md`.
7. No network calls at runtime other than the optional LLM wrapper.
8. Keep changes small. Commit often. A working state is always more valuable than a bigger broken one.
9. When a spec is ambiguous, choose the simplest reading, record the choice in `docs/DECISIONS.md`, and continue.
10. Do not invent features. If an idea seems great, add it to `docs/IDEAS.md`, do not build it.
11. Do not claim anything the code does not do (for example calibrated probabilities, zero exposure, real-time Telegram monitoring).

---

## 19. Claims we can and cannot make (pitch guard-rails)

We can say:
- The engine ranks candidate origins and custody paths from incomplete logs and explains each.
- Matching uses keyed-hash sketches so source rows are not shared.
- On our simulator, PUGMARK beats the two naive baselines at every loss level (only if the benchmark shows it, quote the real numbers).
- Output is a ranked set of hypotheses for a human investigator.

We cannot say:
- That the probabilities are calibrated.
- That the benchmark proves real-world accuracy. It is synthetic.
- That exposure is zero.
- That it detects leaks on Telegram or the web.
- Anything about specific legal deadlines that the team has not verified.

Likely judge questions and short answers live in `06_DEMO_AND_PITCH.md`. Core answer to "is this just a SIEM?": a SIEM searches logs; PUGMARK matches the leaked content to its source and reasons about custody when logs are missing.

---

## 20. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Simulator takes too long | Cap at T+1:25. Ship archetype A1 only first, add A2 and A3 later. |
| Engine output looks wrong on the demo seed | Check stage by stage with the H-scenarios. Do not tune weights on the demo seed only. |
| Integration breaks late | Roll back to the last `ok-N` tag; demo from `demo.json` replay. |
| Benchmark is weak at 60 percent loss | Show top-3 and say so. Do not hide the bar. |
| Backend or laptop fails during the demo | Offline replay mode and a recorded backup video. |
| An agent hits its usage limit | Hand the module to another agent with the module's spec and tests. |
| Judges do not understand it in 30 seconds | Open with the story, not the architecture, and let a judge pick the leak source. |

---

## 21. Glossary

- Provenance graph: graph of who and what touched which data and where it moved.
- Export artifact: a file created by an export-like event.
- Containment: fraction of the leaked rows that also appear in a candidate export.
- Bottom-k sketch: the k smallest hash values of a set, used to estimate overlap without sharing the set.
- Watermark: the newest record time inside the leak. An export cannot predate it.
- Hidden hop: a transfer we hypothesise happened because its log is missing.
- Chokepoint: a permission, key or channel that many plausible paths pass through.
- Canary: a planted fake record that identifies which export leaked when it is seen in the wild.
- Format fingerprint: the formatting habits (date, phone, case, null token, delimiter) of the tool that produced a file.
- Relative likelihood: a normalised score that ranks hypotheses. Not a calibrated probability.

---

## 22. Open items to check with organisers (humans do this, agents ignore)

- Is pre-written code allowed, and is AI-agent use explicitly allowed?
- What is the submission format (slides, repo, video, live demo) and the exact deadline?
- How long is the demo slot?
- Is any dataset provided on the day? If yes, add a loader that maps it to the event schema in `01_DATA_CONTRACT.md`.
- Are prizes per domain or overall?
