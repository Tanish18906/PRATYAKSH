"""Pydantic v2 mirrors of docs/01_DATA_CONTRACT.md (v1.0). snake_case everywhere, no extra fields.

`extra="forbid"` means a scenario carrying `truth`, `case_key` or any undocumented key fails validation.
Graph edges use the JSON key `from`; dump with `by_alias=True`.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Ts = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")]
Hash16 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{16}$")]

LocationKind = Literal["system", "endpoint", "external"]
ActorKind = Literal["user", "service"]
Role = Literal["analyst", "bi-admin", "engineer", "marketing", "support", "contractor", "service"]
Action = Literal["read", "query", "export", "copy", "send", "upload", "download", "api_call",
                 "permission_change"]
Archetype = Literal["A1", "A2", "A3", "A4", "A5"]
Scale = Literal["demo", "bench"]
HopKind = Literal["observed", "inferred"]
Verdict = Literal["candidate", "excluded"]
ExclusionRule = Literal["schema", "watermark_before", "after_found"]
ChokeItemType = Literal["permission", "api_key", "service_account", "channel"]


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ---- entities (section 3)
class Location(_M):
    id: str
    kind: LocationKind
    name: str
    owner_actor: str | None
    monitored: bool
    log_source: str | None
    egress_capable: bool


class LogSource(_M):
    id: str
    name: str
    location: str


class Actor(_M):
    id: str
    kind: ActorKind
    name: str
    role: Role
    team: str
    access: list[str]


class Dataset(_M):
    id: str
    name: str
    system: str
    columns: list[str]
    identifier_columns: list[str]
    row_count: int
    sensitivity: Literal["high", "medium", "low"]
    arrivals_per_hour: float


# ---- events (section 4)
class EventMeta(_M):
    artifact_id: str | None = None
    filter: str | None = None
    columns: list[str] | None = None
    client_ip: str | None = None
    grantee: str | None = None
    scope: str | None = None
    change: Literal["grant", "revoke"] | None = None
    note: str | None = None


class Event(_M):
    id: str
    ts: Ts
    seq: int
    source: str
    actor: str
    action: Action
    object: str
    from_loc: str | None
    to_loc: str | None
    rows: int
    meta: EventMeta


# ---- artifacts and leak (sections 5 and 7)
class Sketch(_M):
    k: int
    distinct: int
    hashes: list[Hash16]


class FormatColumn(_M):
    style: Literal["e164_dash", "digits10", "intl_spaced", "iso", "dmy_slash", "mdy_dash_yy"] | None = None
    case: Literal["lower", "mixed", "upper", "title"] | None = None


class FormatProfile(_M):
    delimiter: Literal[",", ";", "\t", "|"]
    quoting: Literal["minimal", "all", "none"]
    header_case: Literal["snake", "title", "upper", "camel"]
    line_ending: Literal["LF", "CRLF"]
    encoding: Literal["utf-8", "utf-8-bom", "latin-1"]
    null_token: Literal["", "NULL", "N/A"]
    columns: dict[str, FormatColumn]


class Artifact(_M):
    id: str
    dataset: str
    created_by: str
    created_ts: Ts
    location: str
    columns: list[str]
    row_count: int
    filter_desc: str
    format_profile: FormatProfile
    sketches: dict[str, Sketch]
    newest_record_ts: Ts
    arrivals_per_hour: float
    canary_ids: list[str]


class LeakSample(_M):
    id: str
    found_at: str
    found_ts: Ts
    file_name: str
    columns: list[str]
    row_count: int
    format_profile: FormatProfile
    sketches: dict[str, Sketch]
    newest_record_ts: Ts
    masked_preview: list[dict[str, str]]
    canary_hits: list[str]


class Attachment(_M):
    file_name: str
    size_bytes: int
    rows_hint: int


class TelegramMessage(_M):
    id: int
    ts: Ts
    sender: str
    text: str
    attachment: Attachment | None


class Channel(_M):
    name: str
    handle: str
    members: int


class Discovery(_M):
    platform: Literal["telegram-mock"]
    channel: Channel
    messages: list[TelegramMessage]
    leak_message_id: int


class CanaryEntry(_M):
    id: str
    export_id: str
    hashes: dict[str, Hash16]


class Params(_M):
    log_loss: float
    canary_mode: bool
    scale: Scale


class PublicScenario(_M):
    contract_version: Literal["1.0"]
    id: str
    archetype: Archetype
    seed: int
    params: Params
    company: str
    now_ts: Ts
    locations: list[Location]
    log_sources: list[LogSource]
    actors: list[Actor]
    datasets: list[Dataset]
    events: list[Event]
    artifacts: list[Artifact]
    canary_registry: list[CanaryEntry]
    leak_sample: LeakSample
    discovery: Discovery


# ---- trace result (section 9)
class OriginCandidate(_M):
    artifact_id: str
    verdict: Verdict
    exclusion_rule: ExclusionRule | None
    containment: float | None
    specificity: float | None
    format_sim: float | None
    watermark_term: float | None
    origin_fit: float | None
    notes: list[str]


class OriginRank(_M):
    """Not in contract v1.0 text; used by 03_ENGINE and 04_TEST_PLAN (see docs/QUESTIONS.md)."""
    artifact_id: str
    probability: float


class Hop(_M):
    from_loc: str
    to_loc: str
    actor: str
    ts: Ts | None
    kind: HopKind
    event_id: str | None
    action: Action | None
    rows: int | None
    est_loss: float | None
    note: str


class Evidence(_M):
    kind: Literal["observed", "inferred", "anomaly", "fingerprint"]
    text: str
    ts: Ts | None
    event_id: str | None


class ScoreParts(_M):
    origin_fit: float
    path_cost: float
    anomaly: float


class Hypothesis(_M):
    rank: int
    path_id: str
    origin_artifact: str
    probability: float
    score: float
    score_parts: ScoreParts
    hops: list[Hop]
    actors: list[str]
    summary_text: str
    evidence: list[Evidence]


class ActorRank(_M):
    actor: str
    marginal: float
    top_path_id: str | None


class LocationRank(_M):
    location: str
    marginal: float


class Chokepoint(_M):
    rank: int
    item_type: ChokeItemType
    item_id: str
    label: str
    marginal: float
    cumulative_coverage: float
    action_text: str


class HopRef(_M):
    from_loc: str
    to_loc: str


class EvidenceRequest(_M):
    rank: int
    hop_ref: HopRef
    mass: float
    informativeness: float
    request_text: str


class GraphNode(_M):
    id: str
    kind: Literal["actor", "system", "endpoint", "external", "dataset", "artifact"]
    label: str


class GraphEdge(_M):
    id: str
    from_: str = Field(alias="from")
    to: str
    kind: HopKind
    ts: Ts | None
    event_id: str | None
    path_ids: list[str]
    label: str


class Graph(_M):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TraceResult(_M):
    contract_version: Literal["1.0"]
    trace_id: str
    scenario_id: str
    engine_version: str
    origin_pinned: bool
    origin_candidates: list[OriginCandidate]
    origin_ranking: list[OriginRank]
    hypotheses: list[Hypothesis]
    actor_ranking: list[ActorRank]
    location_ranking: list[LocationRank]
    chokepoints: list[Chokepoint]
    recommended_evidence: list[EvidenceRequest]
    loss_estimates: dict[str, float]
    graph: Graph
    notes: list[str]


# ---- audit, summary, benchmark, bundle (sections 11 to 13)
class AuditEntry(_M):
    id: str
    ts: Ts
    who: Literal["investigator-demo"]
    action: Literal["scenario_generate", "telegram_export", "trace", "reveal", "report_export", "inject",
                    "canary_alert", "benchmark_run"]
    scenario_id: str | None
    object_id: str | None
    field: str | None
    reason: str | None


class Counts(_M):
    actors: int
    locations: int
    datasets: int
    events: int
    artifacts: int


class ScenarioSummary(_M):
    contract_version: Literal["1.0"]
    id: str
    archetype: Archetype
    seed: int
    params: Params
    company: str
    counts: Counts
    discovery: Discovery
    leak_sample: LeakSample
    actors: list[Actor]
    locations: list[Location]


class MethodStats(_M):
    top1: float
    top3: float
    mean_rank: float | None
    n: int


class BenchmarkResult(_M):
    benchmark_id: str
    status: Literal["running", "done", "failed"]
    progress: float
    tuned_on: str
    reported_on: str
    loss_levels: list[float]
    origin: dict[str, dict[str, MethodStats]]
    actor: dict[str, dict[str, MethodStats]]
    note: str


class DemoBundle(_M):
    contract_version: Literal["1.0"]
    scenario: ScenarioSummary
    trace: TraceResult
    audit: list[AuditEntry]
    benchmark: BenchmarkResult | None
    report_html: str


class ApiErrorBody(_M):
    code: Literal["bad_request", "not_found", "reason_required", "engine_error", "not_ready"]
    message: str


class ApiError(_M):
    error: ApiErrorBody


# ---- request bodies (section 12)
class GenerateRequest(_M):
    archetype: Archetype
    seed: int
    log_loss: float = Field(ge=0.0, le=0.8)
    canary_mode: bool
    scale: Scale


class ExportRequest(_M):
    scenario_id: str
    message_id: int


class TraceRequest(_M):
    scenario_id: str
    top_k: int | None = Field(default=None, ge=1, le=20)


class RevealRequest(_M):
    scenario_id: str
    object: Literal["leak_sample"]
    row_index: int
    field: str
    reason: str | None = None  # checked by the endpoint so a missing reason is `reason_required`, not `bad_request`


class RevealResponse(_M):
    value: str
    audit_id: str


class AuditList(_M):
    entries: list[AuditEntry]


class InjectRequest(_M):
    base_scenario_id: str
    actor: str


class CanaryAlertRequest(_M):
    scenario_id: str
    canary_id: str


class CanaryAlert(_M):
    canary_id: str
    export_id: str
    ts: Ts
    message: str


class CanaryAlertResponse(_M):
    alert: CanaryAlert
    trace: TraceResult


class BenchmarkRunRequest(_M):
    seed_range: list[int] = Field(min_length=2, max_length=2)
    loss_levels: list[float] = Field(min_length=1)
    archetypes: list[Archetype] = Field(min_length=1)

    @field_validator("seed_range")
    @classmethod
    def _seeds(cls, v):
        if v[0] < 0 or v[1] < v[0] or v[1] - v[0] >= 1000:
            raise ValueError("seed_range must be [first, last] with 0 <= first <= last and fewer than 1000 seeds")
        return v

    @field_validator("loss_levels")
    @classmethod
    def _losses(cls, v):
        if any(not 0.0 <= x <= 0.8 for x in v):
            raise ValueError("loss_levels must be between 0 and 0.8")
        return v


class BenchmarkRunResponse(_M):
    benchmark_id: str
