# PUGMARK: Data Contract v1.0

Owner: Tanish. Frozen at the end of Phase 0. After that, only Tanish may change this file, and every change must be announced to Anmol and the agents.
Read `00_PROJECT_CONTEXT.md` first. This file defines exact shapes. If anything here conflicts with `00`, this file wins for shapes and `00` wins for intent.

Notation: schemas are written as TypeScript interfaces because the frontend uses them directly. Python agents translate them 1:1 into Pydantic v2 models in `backend/app/models.py`. Field names are snake_case everywhere, in Python and in JSON. Do not rename fields. Do not add fields without a contract change.

---

## 1. Global conventions

- **Time:** all timestamps are ISO-8601 UTC strings with a trailing `Z` and seconds precision, for example `2026-10-09T02:10:00Z`. The fictional company runs in UTC. Do NOT convert time zones anywhere. "Off hours" means 22:00 to 05:00 UTC or a weekend. The UI shows times as UTC and says so.
- **IDs:** strings with a type prefix.

| Prefix | Meaning | Example |
|---|---|---|
| `act:` | actor (user or service account) | `act:ravi-menon`, `act:etl-nightly` |
| `sys:` | system location | `sys:bi-warehouse` |
| `ep:` | endpoint (an employee's laptop) | `ep:ravi-menon` |
| `ext:` | external destination | `ext:telegram-leak-channel` |
| `ds:` | dataset | `ds:customers` |
| `art:` | export artifact | `art:E1` |
| `src:` | log source | `src:bi-warehouse` |
| `evt:` | event | `evt:000123` |
| `can:` | canary | `can:E1-1` |
| `scn:` | scenario | `scn:A1-42-L40` |
| `trc:` | trace | `trc:A1-42-L40` |
| `hyp:` | hypothesis (path) | `hyp:1` |
| `aud:` | audit entry | `aud:0007` |

- **Numbers:** probabilities and fractions are floats in [0, 1], rounded to 4 decimals in API responses. Counts are integers.
- **Nulls:** a field typed `T | null` is always present, with `null` when empty. Optional fields (`?`) may be absent.
- **Determinism:** same scenario seed gives byte-identical scenario JSON. Same scenario gives identical trace JSON, except `audit` timestamps, which use the wall clock.
- **Contract version:** every top-level scenario, trace and bundle carries `contract_version: "1.0"`.

---

## 2. Enums

```ts
type LocationKind = "system" | "endpoint" | "external";
type ActorKind = "user" | "service";
type Role = "analyst" | "bi-admin" | "engineer" | "marketing" | "support" | "contractor" | "service";
type Action =
  | "read" | "query" | "export" | "copy" | "send" | "upload" | "download"
  | "api_call" | "permission_change";
type Archetype = "A1" | "A2" | "A3" | "A4" | "A5";   // see 02_SIMULATOR.md
type Scale = "demo" | "bench";
type HopKind = "observed" | "inferred";
type Verdict = "candidate" | "excluded";
type ExclusionRule = "schema" | "watermark_before" | "after_found";
type ChokeItemType = "permission" | "api_key" | "service_account" | "channel";
```

---

## 3. Entities

```ts
interface Location {
  id: string;                 // sys:/ep:/ext:
  kind: LocationKind;
  name: string;
  owner_actor: string | null; // endpoints only: the user who owns the laptop
  monitored: boolean;         // false for most endpoints and externals
  log_source: string | null;  // src: id that records activity here, null if unlogged
  egress_capable: boolean;    // data can leave to the outside from here
}

interface LogSource {
  id: string;                 // src:
  name: string;
  location: string;           // Location.id this source observes
}

interface Actor {
  id: string;                 // act:
  kind: ActorKind;
  name: string;               // display name, synthetic
  role: Role;
  team: string;
  access: string[];           // Location ids the actor can read from or write to
}

interface Dataset {
  id: string;                 // ds:
  name: string;
  system: string;             // sys: where it lives
  columns: string[];
  identifier_columns: string[]; // subset of columns used for sketches, see section 6
  row_count: number;
  sensitivity: "high" | "medium" | "low";
  arrivals_per_hour: number;  // aggregate rate of new records, used by the watermark term
}
```

---

## 4. Events (lossy)

```ts
interface Event {
  id: string;                 // evt:
  ts: string;
  seq: number;                // per-source counter, assigned BEFORE loss; gaps are observable
  source: string;             // src: id that logged this event
  actor: string;              // act:
  action: Action;
  object: string;             // ds: or art:
  from_loc: string | null;    // Location.id where the data was
  to_loc: string | null;      // Location.id where the data went (null for plain reads)
  rows: number;               // rows touched, 0 if not applicable
  meta: EventMeta;
}

interface EventMeta {
  artifact_id?: string;       // export/copy events that create or move an artifact
  filter?: string;            // human-readable filter, e.g. "state = 'CG' AND signup_date >= '2025-01-01'"
  columns?: string[];
  client_ip?: string;         // api_call
  grantee?: string;           // permission_change: act: id receiving or losing access
  scope?: string;             // permission_change: Location.id
  change?: "grant" | "revoke";// permission_change
  note?: string;
}
```

Meaning of fields per action (the engine relies on this):

| Action | object | from_loc | to_loc | Notes |
|---|---|---|---|---|
| `read`, `query` | `ds:` | system | null | `rows` = rows returned |
| `export` | `ds:` | system holding dataset | system receiving file | creates `meta.artifact_id` |
| `copy` | `art:` | location | location | artifact duplicated between systems |
| `download` | `art:` | system | endpoint | to a person's laptop |
| `upload` | `art:` | endpoint or system | external or system | |
| `send` | `art:` | system | external or system | email gateway, SFTP push |
| `api_call` | `art:` or `ds:` | system | endpoint or external | `meta.client_ip` set |
| `permission_change` | `ds:` or null | null | null | uses `grantee`, `scope`, `change` |

Loss rules:
- The public event list has had events removed. `seq` values are NOT renumbered, so gaps remain.
- Artifacts (section 5) are never lost. We assume an export catalog that is complete (assumption A-1).

---

## 5. Export artifacts

```ts
interface Sketch {
  k: number;                  // sketch size, 512 by default
  distinct: number;           // exact count of distinct normalized values in the column
  hashes: string[];           // bottom-k 64-bit hashes, 16 lowercase hex chars each, sorted ascending
}

interface FormatProfile {
  delimiter: "," | ";" | "\t" | "|";
  quoting: "minimal" | "all" | "none";
  header_case: "snake" | "title" | "upper" | "camel";
  line_ending: "LF" | "CRLF";
  encoding: "utf-8" | "utf-8-bom" | "latin-1";
  null_token: "" | "NULL" | "N/A";
  columns: {                  // only columns present in the file
    [column: string]: {
      style?: "e164_dash" | "digits10" | "intl_spaced"   // phone
            | "iso" | "dmy_slash" | "mdy_dash_yy";       // dates
      case?: "lower" | "mixed" | "upper" | "title";      // email, names
    };
  };
}

interface Artifact {
  id: string;                 // art:
  dataset: string;            // ds:
  created_by: string;         // act:
  created_ts: string;
  location: string;           // where the file first landed
  columns: string[];
  row_count: number;
  filter_desc: string;
  format_profile: FormatProfile;
  sketches: { [identifier_column: string]: Sketch };
  newest_record_ts: string;   // newest record creation time inside the file
  arrivals_per_hour: number;  // arrival rate of records matching this export's filter
  canary_ids: string[];       // canaries planted in this export, [] if canary mode is off
}
```

---

## 6. Sketch and normalization spec (BOTH simulator and engine use this exact code)

The shared reference implementation lives in `backend/app/common/sketch.py`, owned by Tanish. The simulator imports it, never reimplements it. Behaviour must equal this:

```python
import hmac, hashlib, re

K_DEFAULT = 512
IDENTIFIER_COLUMNS = ["customer_id", "email", "phone", "policy_no"]

def normalize(column: str, value) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if column == "email":
        return s.lower()
    if column == "phone":
        digits = re.sub(r"\D", "", s)
        return digits[-10:] if len(digits) >= 10 else digits
    if column == "policy_no":
        return s.upper()
    if column == "customer_id":
        return s
    if column == "full_name":
        return " ".join(s.lower().split())
    return s

def h64(key: bytes, s: str) -> int:
    return int.from_bytes(hmac.new(key, s.encode("utf-8"), hashlib.sha256).digest()[:8], "big")

def make_sketch(column: str, values, key: bytes, k: int = K_DEFAULT) -> dict:
    hs = {h64(key, normalize(column, v)) for v in values}
    hs.discard(h64(key, ""))               # empty values never count
    ordered = sorted(hs)
    return {"k": k, "distinct": len(hs), "hashes": [f"{x:016x}" for x in ordered[:k]]}

def jaccard(a: list[str], b: list[str], k: int = K_DEFAULT) -> float:
    A = {int(x, 16) for x in a}
    B = {int(x, 16) for x in b}
    union = sorted(A | B)[:k]
    if not union:
        return 0.0
    inter = sum(1 for x in union if x in A and x in B)
    return inter / len(union)

def containment(leak: dict, export: dict) -> float:
    """Fraction of the leak's distinct values that also appear in the export."""
    J = jaccard(leak["hashes"], export["hashes"], leak["k"])
    nL, nE = leak["distinct"], export["distinct"]
    if nL == 0:
        return 0.0
    c = J * (nL + nE) / ((1.0 + J) * nL)
    return max(0.0, min(1.0, c))
```

Rules:
- One secret `case_key` (bytes) per scenario, generated from the seed (`sha256(f"pugmark-case-{seed}")`). It is NOT in the public scenario. The simulator and the fingerprint step get it from the private store. The engine never needs it, because it compares hashes only.
- `IDENTIFIER_COLUMNS` are the only columns sketched. Names and dates are not sketched.
- When a set has fewer than `k` distinct values the sketch holds all of them and the estimate is exact.
- Required unit tests (engine agent writes them): normalization vectors below, jaccard of identical sets = 1.0, of disjoint sets = 0.0, containment of a 50 percent subset within 0.05 of 1.0, determinism.

Normalization test vectors:

| column | input | output |
|---|---|---|
| email | ` Ravi.Menon@Example.com ` | `ravi.menon@example.com` |
| phone | `+91-9876543221` | `9876543221` |
| phone | `98765 43221` | `9876543221` |
| phone | `09876543221` | `9876543221` |
| policy_no | ` nh-2025-004217 ` | `NH-2025-004217` |
| full_name | `  RAVI   menon ` | `ravi menon` |

---

## 7. Leak sample, discovery (Telegram mock) and canaries

```ts
interface LeakSample {
  id: string;                      // "leak:" + scenario suffix
  found_at: string;                // Location.id, e.g. "ext:telegram-leak-channel"
  found_ts: string;
  file_name: string;
  columns: string[];
  row_count: number;
  format_profile: FormatProfile;
  sketches: { [identifier_column: string]: Sketch };
  newest_record_ts: string;
  masked_preview: Array<{ [column: string]: string }>;  // up to 5 rows, ALREADY MASKED (section 10)
  canary_hits: string[];           // can: ids found in the file, computed by the fingerprint step
}

interface TelegramMessage {
  id: number;
  ts: string;
  sender: string;                  // synthetic handle, e.g. "@datadump_demo"
  text: string;
  attachment: null | { file_name: string; size_bytes: number; rows_hint: number };
}

interface Discovery {
  platform: "telegram-mock";       // always labelled SIMULATED in the UI
  channel: { name: string; handle: string; members: number };
  messages: TelegramMessage[];     // the attachment message has the leak file
  leak_message_id: number;         // which message carries the leaked file
}

interface CanaryEntry {
  id: string;                      // can:
  export_id: string;               // art:
  hashes: { [identifier_column: string]: string };  // full 16-hex hash of the canary's normalized value
}
```

Flow in the product: the investigator opens the mock Telegram chat, sees the post with the CSV, clicks "Export and trace". The backend returns the masked `LeakSample` (the fingerprint step ran on the leaked file) and the UI then calls trace. No real Telegram access exists anywhere. Everything is simulated and must be labelled as such in the UI.

Canary hit rule (fingerprint step, runs on the raw leaked file the investigator holds): for every identifier column, normalize and hash each value with `case_key`; any hash that equals an entry in the canary registry for that column is a hit. `canary_hits` lists the `can:` ids. The engine only reads `canary_hits`.

---

## 8. Public scenario (the ONLY input the engine receives)

```ts
interface PublicScenario {
  contract_version: "1.0";
  id: string;                      // scn:
  archetype: Archetype;
  seed: number;
  params: { log_loss: number; canary_mode: boolean; scale: Scale };
  company: string;                 // "Nova Health"
  now_ts: string;                  // = leak_sample.found_ts
  locations: Location[];
  log_sources: LogSource[];
  actors: Actor[];
  datasets: Dataset[];
  events: Event[];                 // lossy, sorted by ts then seq
  artifacts: Artifact[];
  canary_registry: CanaryEntry[];  // [] when canary_mode is false
  leak_sample: LeakSample;
  discovery: Discovery;
}
```

Forbidden in a public scenario, enforced by the validator: any key named `truth`, `rows`, `raw`, `case_key`, `true_path`, `dropped`, or any list longer than 20 of objects containing raw personal values. `params.log_loss` is the nominal level and is allowed (the engine must not use it; it estimates loss from `seq` gaps or uses its default).

Private files, never sent to the engine or the UI:

```ts
interface ScenarioTruth {
  scenario_id: string;
  origin_artifact: string;                      // art:
  true_path: Array<{
    from_loc: string; to_loc: string; actor: string; ts: string;
    event_id: string | null;                    // null when the event was never generated
    dropped: boolean;                           // true if it was generated and then lost
  }>;
  true_actors: string[];                        // act: ids on the true path
  leak_location: string;
  dropped_event_ids: string[];
}
```

---

## 9. Trace result (engine output)

```ts
interface TraceResult {
  contract_version: "1.0";
  trace_id: string;                // trc:
  scenario_id: string;
  engine_version: string;
  origin_pinned: boolean;          // true if a canary pinned the origin
  origin_candidates: OriginCandidate[];   // ALL artifacts, sorted by origin_fit desc, excluded last
  hypotheses: Hypothesis[];        // top_k (default 5), sorted by probability desc
  actor_ranking: Array<{ actor: string; marginal: number; top_path_id: string | null }>;
  location_ranking: Array<{ location: string; marginal: number }>;
  chokepoints: Chokepoint[];       // greedy order
  recommended_evidence: EvidenceRequest[];   // [] if stage 7 not built
  loss_estimates: { [log_source: string]: number };   // estimated drop rate per source from seq gaps, or default
  graph: Graph;
  notes: string[];                 // warnings such as "no candidate survived"
}

interface OriginCandidate {
  artifact_id: string;
  verdict: Verdict;
  exclusion_rule: ExclusionRule | null;
  containment: number | null;      // null when excluded by schema
  specificity: number | null;
  format_sim: number | null;
  watermark_term: number | null;
  origin_fit: number | null;
  notes: string[];
}

interface Hop {
  from_loc: string;
  to_loc: string;
  actor: string;
  ts: string | null;               // inferred hops may carry null or an estimated time
  kind: HopKind;
  event_id: string | null;         // set for observed hops
  action: Action | null;           // null for inferred hops (unknown action)
  rows: number | null;
  est_loss: number | null;         // for inferred hops: estimated loss rate of the log source that would have recorded it
  note: string;
}

interface Evidence {
  kind: "observed" | "inferred" | "anomaly" | "fingerprint";
  text: string;                    // plain English, masked values only
  ts: string | null;
  event_id: string | null;
}

interface Hypothesis {
  rank: number;                    // 1-based
  path_id: string;                 // hyp:
  origin_artifact: string;
  probability: number;             // relative likelihood after softmax, NOT calibrated
  score: number;
  score_parts: { origin_fit: number; path_cost: number; anomaly: number };
  hops: Hop[];                     // contiguous: hops[i].to_loc == hops[i+1].from_loc
  actors: string[];
  summary_text: string;            // plain English, template-generated, one or two sentences
  evidence: Evidence[];
}

interface Chokepoint {
  rank: number;
  item_type: ChokeItemType;
  item_id: string;                 // act:, sys:, ext: or a permission descriptor like "perm:act:ravi-menon@sys:bi-warehouse"
  label: string;
  marginal: number;                // total probability of paths containing this item
  cumulative_coverage: number;     // share of probability closed after applying ranks 1..this
  action_text: string;             // e.g. "Revoke bulk download for Ravi Menon on bi-warehouse"
}

interface EvidenceRequest {
  rank: number;
  hop_ref: { from_loc: string; to_loc: string };
  mass: number;                    // probability of paths containing this hidden hop
  informativeness: number;         // binary entropy of mass
  request_text: string;
}

interface Graph {
  nodes: Array<{ id: string; kind: "actor" | "system" | "endpoint" | "external" | "dataset" | "artifact"; label: string }>;
  edges: Array<{
    id: string; from: string; to: string;
    kind: HopKind; ts: string | null; event_id: string | null;
    path_ids: string[];            // hypotheses that use this edge
    label: string;
  }>;
}
```

Trace invariants (the validator and tests check these):
1. `hypotheses` sorted by `probability` descending; sum of returned probabilities is at most 1.0000 (+ rounding).
2. Hops are contiguous and timestamps non-decreasing wherever both are non-null.
3. Every `event_id` mentioned exists in the scenario events.
4. `origin_candidates` contains every artifact in the scenario exactly once.
5. If `origin_pinned` is true, every hypothesis has `origin_artifact` equal to the pinned artifact.
6. No unmasked personal value appears anywhere in a trace.
7. Graph edges only reference node ids that exist in `graph.nodes`.

---

## 10. Masking rules (backend/app/privacy/mask.py)

All API responses mask personal values except `POST /api/reveal`.

| Column | Rule | Example in, out |
|---|---|---|
| email | first character, `***`, `@`, domain | `ravi.menon@example.com` -> `r***@example.com` |
| phone | keep first 6 chars and last 2, mask the rest with `*` | `+91-9876543221` -> `+91-98******21` |
| full_name | initials with dots | `Ravi Menon` -> `R. M.` |
| policy_no | keep first 2 and last 2, mask the rest | `NH-2025-004217` -> `NH**********17` |
| customer_id | keep last 3, mask the rest | `C0048211` -> `*****211` |
| dob | year only | `1990-05-14` -> `1990-**-**` |
| any other personal column | `***` | |

If a value is shorter than the kept parts, mask everything with `*`.

---

## 11. Audit log

```ts
interface AuditEntry {
  id: string;                      // aud:
  ts: string;                      // wall clock, UTC
  who: "investigator-demo";
  action: "scenario_generate" | "telegram_export" | "trace" | "reveal" | "report_export"
        | "inject" | "canary_alert" | "benchmark_run";
  scenario_id: string | null;
  object_id: string | null;
  field: string | null;
  reason: string | null;           // required for reveal
}
```

Every API call that does one of those actions appends exactly one entry. The log is in memory plus a JSON-lines file at `backend/data/audit.jsonl`.

---

## 12. API

Base path `/api`, JSON, CORS allowed for `http://localhost:5173`. Errors use one shape:

```ts
interface ApiError { error: { code: string; message: string } }
// codes: "bad_request" (400), "not_found" (404), "reason_required" (400), "engine_error" (500), "not_ready" (409)
```

| Method and path | Request | Response |
|---|---|---|
| `GET /api/health` | none | `{ status: "ok", contract_version: "1.0", engine_version: string }` |
| `POST /api/scenario/generate` | `{ archetype: Archetype, seed: number, log_loss: number (0 to 0.8), canary_mode: boolean, scale: Scale }` | `ScenarioSummary` |
| `GET /api/scenario/{id}` | query `full=true` optional | `ScenarioSummary`, or the whole `PublicScenario` when `full=true` |
| `POST /api/leak/export` | `{ scenario_id: string, message_id: number }` | `{ leak_sample: LeakSample, file: { name: string; size_bytes: number } }` |
| `POST /api/trace` | `{ scenario_id: string, top_k?: number }` | `TraceResult` |
| `POST /api/inject` | `{ base_scenario_id: string, actor: string }` | `ScenarioSummary` (a NEW scenario where that actor is the leaker) |
| `POST /api/canary/alert` | `{ scenario_id: string, canary_id: string }` | `{ alert: { canary_id: string; export_id: string; ts: string; message: string }, trace: TraceResult }` |
| `POST /api/reveal` | `{ scenario_id: string, object: "leak_sample", row_index: number, field: string, reason: string (min 8 chars) }` | `{ value: string, audit_id: string }` |
| `GET /api/audit` | query `scenario_id` optional | `{ entries: AuditEntry[] }` |
| `POST /api/benchmark/run` | `{ seed_range: [number, number], loss_levels: number[], archetypes: Archetype[] }` | `{ benchmark_id: string }` |
| `GET /api/benchmark/{id}` | none | `BenchmarkResult` |
| `GET /api/report/{trace_id}` | none | `text/html` incident report |

```ts
interface ScenarioSummary {
  contract_version: "1.0";
  id: string;
  archetype: Archetype;
  seed: number;
  params: { log_loss: number; canary_mode: boolean; scale: Scale };
  company: string;
  counts: { actors: number; locations: number; datasets: number; events: number; artifacts: number };
  discovery: Discovery;
  leak_sample: LeakSample;         // masked
  actors: Actor[];                 // for the "judge picks an actor" selector
  locations: Location[];
}

interface MethodStats { top1: number; top3: number; mean_rank: number | null; n: number }

interface BenchmarkResult {
  benchmark_id: string;
  status: "running" | "done" | "failed";
  progress: number;                // 0 to 1
  tuned_on: string;                // "seeds 0-49"
  reported_on: string;             // "seeds 50-199"
  loss_levels: number[];
  origin: { [method: string]: { [loss: string]: MethodStats } };
  actor:  { [method: string]: { [loss: string]: MethodStats } };
  // methods: origin = "pugmark" | "B3_largest_export" | "B4_most_recent_export"
  //          actor  = "pugmark" | "B1_last_accessor" | "B2_biggest_exporter"
  note: string;                    // always: "Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy."
}
```

Timing: `trace` on the seed 42 demo scenario must return within 3 seconds. `benchmark/run` is asynchronous and returns immediately.

`POST /api/scenario/generate` for `scale: "demo"` with seed 42 and archetype A1 MUST produce the story in `00_PROJECT_CONTEXT.md` section 4.4, with the leak found in the mock Telegram channel (see Appendix B).

---

## 13. Offline replay bundle (`frontend/public/demo.json`)

```ts
interface DemoBundle {
  contract_version: "1.0";
  scenario: ScenarioSummary;
  trace: TraceResult;
  audit: AuditEntry[];
  benchmark: BenchmarkResult | null;
  report_html: string;
}
```

Generated by a script `backend/scripts/make_demo_bundle.py` that calls the real functions with seed 42, A1, demo scale, loss 0.4, canary mode on.

---

## 14. Validator (Phase 1 deliverable for Anmol, used by everyone)

`backend/scripts/validate.py` with:
- `validate_public_scenario(obj)`: schema, all referenced ids exist, `seq` strictly increasing per source, `ts` non-decreasing within a source, sketch hashes sorted and 16 hex chars, `len(hashes) <= k`, `distinct >= len(hashes)`, forbidden keys absent, leak sample columns non-empty.
- `validate_trace(obj, scenario)`: the invariants in section 9.
- CLI: `python backend/scripts/validate.py scenario path.json` and `... trace path.json scenario.json`.

The engine agent and the simulator agent must both run it on their output before reporting a phase.

---

## 15. Assumptions (stated so nobody builds around them silently)

- A-1: The export catalog (artifacts with sketches) is complete. Only event logs are lossy.
- A-2: All times are UTC. No time zone conversion exists.
- A-3: One leak sample per scenario.
- A-4: Identifier columns are `customer_id`, `email`, `phone`, `policy_no`. Names and dates are never sketched.
- A-5: The investigator holds the raw leaked file. Raw rows from company systems are never available to the engine.
- A-6: The mock Telegram chat is simulated. No call to Telegram or any real website is ever made.

---

## Appendix A: fixed IDs for seed 42, archetype A1 (demo scenario)

```
actors:     act:ravi-menon (analyst, TRUE LEAKER), act:meena-iyer (bi-admin), act:arjun-das (contractor),
            act:kavya-rao (marketing), act:etl-nightly (service), act:partner-api-key-7 (service),
            act:backup-svc (service)  + about 13 more generated users
systems:    sys:customer-db, sys:claims-api, sys:crm, sys:bi-warehouse, sys:notebook-server,
            sys:partner-sftp, sys:object-store, sys:ticketing, sys:email-gateway
endpoints:  ep:<user-slug> for each user, e.g. ep:ravi-menon
externals:  ext:telegram-leak-channel, ext:file-share-site, ext:personal-cloud-drive
datasets:   ds:customers, ds:claims, ds:marketing-leads
artifacts:  art:E1 (etl-nightly, 2026-10-09T02:10:00Z, true origin)
            art:E2 (arjun-das, 2026-10-02T11:00:00Z, full table, DD/MM/YYYY, digits10 phones)
            art:E3 (kavya-rao, 2026-10-06T09:30:00Z, name,email,city only)
            art:E4 (etl-nightly, 2026-10-10T02:10:00Z, same filter and format as E1, about 400 more rows)
```

## Appendix B: seed 42 true path (ground truth; lives only in ScenarioTruth)

```
art:E1 created   etl-nightly   sys:customer-db -> sys:bi-warehouse   2026-10-09T02:10:00Z
download         ravi-menon    sys:bi-warehouse -> ep:ravi-menon      2026-10-09T21:40:00Z  (rows 48900)
upload (LOST)    ravi-menon    ep:ravi-menon -> ext:telegram-leak-channel  2026-10-10T22:00:00Z
leak found                                                            2026-10-12T08:30:00Z
leak_sample: 48212 rows (E1 minus duplicates), columns full_name, phone, policy_no,
             newest_record_ts 2026-10-08T17:42:00Z, file_name "nova_customers_cg.csv"
```
(Company time is UTC, so the 9:40 pm story in `00` reads as 21:40Z.) Note: `00` section 4.4 names `ext:file-share-site` as the leak site. For the demo it is `ext:telegram-leak-channel`. Treat `ext:file-share-site` as a decoy destination used by other actors.
