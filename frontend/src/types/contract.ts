// PUGMARK Data Contract Types v1.0
// Copied directly from docs/01_DATA_CONTRACT.md

// ==========================================
// 2. Enums
// ==========================================
export type LocationKind = "system" | "endpoint" | "external";
export type ActorKind = "user" | "service";
export type Role = "analyst" | "bi-admin" | "engineer" | "marketing" | "support" | "contractor" | "service";
export type Action =
  | "read" | "query" | "export" | "copy" | "send" | "upload" | "download"
  | "api_call" | "permission_change";
export type Archetype = "A1" | "A2" | "A3" | "A4" | "A5";   // see 02_SIMULATOR.md
export type Scale = "demo" | "bench";
export type HopKind = "observed" | "inferred";
export type Verdict = "candidate" | "excluded";
export type ExclusionRule = "schema" | "watermark_before" | "after_found";
export type ChokeItemType = "permission" | "api_key" | "service_account" | "channel";

// ==========================================
// 3. Entities
// ==========================================
export interface Location {
  id: string;                 // sys:/ep:/ext:
  kind: LocationKind;
  name: string;
  owner_actor: string | null; // endpoints only: the user who owns the laptop
  monitored: boolean;         // false for most endpoints and externals
  log_source: string | null;  // src: id that records activity here, null if unlogged
  egress_capable: boolean;    // data can leave to the outside from here
}

export interface LogSource {
  id: string;                 // src:
  name: string;
  location: string;           // Location.id this source observes
}

export interface Actor {
  id: string;                 // act:
  kind: ActorKind;
  name: string;               // display name, synthetic
  role: Role;
  team: string;
  access: string[];           // Location ids the actor can read from or write to
}

export interface Dataset {
  id: string;                 // ds:
  name: string;
  system: string;             // sys: where it lives
  columns: string[];
  identifier_columns: string[]; // subset of columns used for sketches, see section 6
  row_count: number;
  sensitivity: "high" | "medium" | "low";
  arrivals_per_hour: number;  // aggregate rate of new records, used by the watermark term
}

// ==========================================
// 4. Events (lossy)
// ==========================================
export interface EventMeta {
  artifact_id?: string;       // export/copy events that create or move an artifact
  filter?: string;            // human-readable filter, e.g. "state = 'CG' AND signup_date >= '2025-01-01'"
  columns?: string[];
  client_ip?: string;         // api_call
  grantee?: string;           // permission_change: act: id receiving or losing access
  scope?: string;             // permission_change: Location.id
  change?: "grant" | "revoke";// permission_change
  note?: string;
}

export interface Event {
  id: string;                 // evt:
  ts: string;
  seq: number;                // per-source counter, assigned BEFORE loss; gaps are observable
  source: string;             // src: id that logged this event
  actor: string;              // act:
  action: Action;
  object: string | null;      // ds: or art:, null for permission_change
  from_loc: string | null;    // Location.id where the data was
  to_loc: string | null;      // Location.id where the data went (null for plain reads)
  rows: number;               // rows touched, 0 if not applicable
  meta: EventMeta;
}

// ==========================================
// 5. Export artifacts
// ==========================================
export interface Sketch {
  k: number;                  // sketch size, 512 by default
  distinct: number;           // exact count of distinct normalized values in the column
  hashes: string[];           // bottom-k 64-bit hashes, 16 lowercase hex chars each, sorted ascending
}

export interface FormatProfile {
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

export interface Artifact {
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

// ==========================================
// 7. Leak sample, discovery and canaries
// ==========================================
export interface LeakSample {
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

export interface TelegramMessage {
  id: number;
  ts: string;
  sender: string;                  // synthetic handle, e.g. "@datadump_demo"
  text: string;
  attachment: null | { file_name: string; size_bytes: number; rows_hint: number };
}

export interface Discovery {
  platform: "telegram-mock";       // always labelled SIMULATED in the UI
  channel: { name: string; handle: string; members: number };
  messages: TelegramMessage[];     // the attachment message has the leak file
  leak_message_id: number;         // which message carries the leaked file
}

export interface CanaryEntry {
  id: string;                      // can:
  export_id: string;               // art:
  hashes: { [identifier_column: string]: string };  // full 16-hex hash of the canary's normalized value
}

// ==========================================
// 8. Public scenario and ScenarioTruth
// ==========================================
export interface PublicScenario {
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

export interface ScenarioTruth {
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

// ==========================================
// 9. Trace result (engine output)
// ==========================================
export interface OriginCandidate {
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

export interface Hop {
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

export interface Evidence {
  kind: "observed" | "inferred" | "anomaly" | "fingerprint";
  text: string;                    // plain English, masked values only
  ts: string | null;
  event_id: string | null;
}

export interface Hypothesis {
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

export interface Chokepoint {
  rank: number;
  item_type: ChokeItemType;
  item_id: string;                 // act:, sys:, ext: or a permission descriptor like "perm:act:ravi-menon@sys:bi-warehouse"
  label: string;
  marginal: number;                // total probability of paths containing this item
  cumulative_coverage: number;     // share of probability closed after applying ranks 1..this
  action_text: string;             // e.g. "Revoke bulk download for Ravi Menon on bi-warehouse"
}

export interface EvidenceRequest {
  rank: number;
  hop_ref: { from_loc: string; to_loc: string };
  mass: number;                    // probability of paths containing this hidden hop
  informativeness: number;         // binary entropy of mass
  request_text: string;
}

export interface Graph {
  nodes: Array<{ id: string; kind: "actor" | "system" | "endpoint" | "external" | "dataset" | "artifact"; label: string }>;
  edges: Array<{
    id: string; from: string; to: string;
    kind: HopKind; ts: string | null; event_id: string | null;
    path_ids: string[];            // hypotheses that use this edge
    label: string;
  }>;
}

export interface TraceResult {
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

// ==========================================
// 11. Audit log
// ==========================================
export interface AuditEntry {
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

// ==========================================
// 12. API shapes & Benchmark
// ==========================================
export interface ApiError {
  error: { code: string; message: string };
}

export interface ScenarioSummary {
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

export interface MethodStats {
  top1: number;
  top3: number;
  mean_rank: number | null;
  n: number;
}

export interface BenchmarkResult {
  benchmark_id: string;
  status: "running" | "done" | "failed";
  progress: number;                // 0 to 1
  tuned_on: string;                // "seeds 0-49"
  reported_on: string;             // "seeds 50-199"
  loss_levels: number[];
  origin: { [method: string]: { [loss: string]: MethodStats } };
  actor:  { [method: string]: { [loss: string]: MethodStats } };
  note: string;
}

// ==========================================
// 13. Offline replay bundle
// ==========================================
export interface DemoBundle {
  contract_version: "1.0";
  scenario: ScenarioSummary;
  trace: TraceResult;
  audit: AuditEntry[];
  benchmark: BenchmarkResult | null;
  report_html: string;
}
