"""PUGMARK API (docs/01_DATA_CONTRACT.md section 12).

Phase 1: scenario generate/get, leak export, trace, JSON error shape, audit append.
Phase 2: reveal (reason of at least 8 characters, audited) and the audit list.
Phase 3: inject, canary alert, HTML incident report; emails are scrubbed from every response but reveal.
Phase 4: benchmark run (background thread) and result polling.
Scenarios come from the simulator when it exists (`_sim()`); until then the hand-written fixtures
H1..H8 are registered at startup, `generate` answers 409 not_ready and so does `reveal` (no private store).
"""
import copy
import importlib
import json
import re
import threading
import types
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.bench.run import _empty as _bench_empty
from app.bench.run import run_benchmark
from app.config import CONTRACT_VERSION, ENGINE
from app.engine.trace import trace as run_trace
from app.models import (AuditList, BenchmarkResult, BenchmarkRunRequest, BenchmarkRunResponse, CanaryAlert,
                        CanaryAlertRequest, CanaryAlertResponse, ExportRequest,
                        GenerateRequest, InjectRequest, PublicScenario, RevealRequest, RevealResponse,
                        ScenarioSummary, TraceRequest, TraceResult)
from app.privacy import audit
from app.privacy.mask import mask_value
from app.report.build import build_report

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

# scenario id -> {"public": PublicScenario dict, "bundle": simulator bundle or None}. The engine and API
# only ever read "public"; the bundle (truth, private store) is never serialised.
STORE: dict = {}
# trace id -> latest TraceResult dict, so the report can be built without re-running the engine
TRACES: dict = {}
# benchmark id -> BenchmarkResult dict (running, done or failed)
BENCHMARKS: dict = {}

_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


class ApiException(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


_SIM_MODULES = ("app.sim", "app.sim.generator", "app.sim.leakfile", "app.sim.store", "app.sim.inject",
                "app.sim.exports", "app.sim.archetypes", "app.sim.discovery")


def _sim_fn(name: str):
    for mod in _SIM_MODULES:
        try:
            fn = getattr(importlib.import_module(mod), name, None)
        except Exception:
            fn = None
        if callable(fn):
            return fn
    return None


def _sim():
    """The simulator's public functions (docs/02 sec 3) if generate_scenario exists, else None."""
    gen = _sim_fn("generate_scenario")
    if gen is None:
        return None
    return types.SimpleNamespace(generate_scenario=gen, reveal_value=_sim_fn("reveal_value"),
                                 get_bundle=_sim_fn("get_bundle"), inject_leak=_sim_fn("inject_leak"),
                                 canary_alert=_sim_fn("canary_alert"))


def register(public: dict, bundle=None) -> None:
    STORE[public["id"]] = {"public": public, "bundle": bundle}


def load_fixtures() -> None:
    for path in sorted(FIXTURE_DIR.glob("H[1-8].json")):
        register(json.loads(path.read_text()))


@asynccontextmanager
async def lifespan(_app):
    if _sim() is None:
        load_fixtures()
    yield


app = FastAPI(title="PUGMARK", version=ENGINE["ENGINE_VERSION"], lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"],
                   allow_headers=["*"])


@app.exception_handler(ApiException)
async def _api_exception(_req: Request, exc: ApiException):
    return _error(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def _validation(_req: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    where = ".".join(str(p) for p in first["loc"] if p != "body")
    return _error(400, "bad_request", f"{where or 'request'}: {first['msg']}")


@app.exception_handler(StarletteHTTPException)
async def _http(_req: Request, exc: StarletteHTTPException):
    code = "not_found" if exc.status_code == 404 else "bad_request"
    return _error(exc.status_code, code, str(exc.detail))


def _round4(o):
    """Responses: floats to 4 decimals and any email-looking string masked (first character, ***, domain)."""
    if isinstance(o, float):
        return round(o, 4)
    if isinstance(o, str):
        return _EMAIL.sub(r"\1***@\2", o)
    if isinstance(o, dict):
        return {k: _round4(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round4(v) for v in o]
    return o


def _ok(model, **dump) -> JSONResponse:
    return JSONResponse(_round4(model.model_dump(by_alias=True, **dump)))


def _lookup(scenario_id: str) -> dict:
    entry = STORE.get(scenario_id)
    sim = _sim()
    if entry is None and sim is not None and callable(getattr(sim, "get_bundle", None)):
        bundle = sim.get_bundle(scenario_id)
        if bundle is not None:
            register(bundle.public, bundle)
            entry = STORE[scenario_id]
    if entry is None:
        raise ApiException(404, "not_found", f"scenario {scenario_id} not found")
    return entry


def _public(entry: dict) -> PublicScenario:
    """Contract-validate the scenario (forbidden keys such as truth or case_key fail here) and make sure
    the leak preview is masked even if the producer forgot."""
    pub = copy.deepcopy(entry["public"])
    for row in pub.get("leak_sample", {}).get("masked_preview", []):
        for col, val in list(row.items()):
            if val and "*" not in val:
                row[col] = mask_value(col, val)
    try:
        return PublicScenario.model_validate(pub)
    except Exception as exc:
        raise ApiException(500, "engine_error", f"scenario violates the data contract: {type(exc).__name__}")


def _summary(sc: PublicScenario) -> ScenarioSummary:
    return ScenarioSummary(
        contract_version=sc.contract_version, id=sc.id, archetype=sc.archetype, seed=sc.seed, params=sc.params,
        company=sc.company,
        counts={"actors": len(sc.actors), "locations": len(sc.locations), "datasets": len(sc.datasets),
                "events": len(sc.events), "artifacts": len(sc.artifacts)},
        discovery=sc.discovery, leak_sample=sc.leak_sample, actors=sc.actors, locations=sc.locations)


def _run_trace(public: dict, top_k: int) -> TraceResult:
    try:
        result = TraceResult.model_validate(run_trace(public, top_k))
    except Exception as exc:
        raise ApiException(500, "engine_error", f"trace failed: {type(exc).__name__}")
    TRACES[result.trace_id] = result.model_dump(by_alias=True)
    return result


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "contract_version": CONTRACT_VERSION, "engine_version": ENGINE["ENGINE_VERSION"]}


@app.post("/api/scenario/generate")
def generate(req: GenerateRequest):
    sim = _sim()
    if sim is None:
        raise ApiException(409, "not_ready", "the simulator is not available yet; fixtures scn:H1 to scn:H8 "
                                             "are loaded and can be read with GET /api/scenario/{id}")
    bundle = sim.generate_scenario(req.archetype, req.seed, req.log_loss, req.canary_mode, req.scale)
    register(bundle.public, bundle)
    sc = _public(STORE[bundle.public["id"]])
    audit.append("scenario_generate", scenario_id=sc.id)
    return _ok(_summary(sc))


@app.get("/api/scenario/{scenario_id}")
def get_scenario(scenario_id: str, full: bool = False):
    sc = _public(_lookup(scenario_id))
    return _ok(sc, exclude_unset=True) if full else _ok(_summary(sc))


@app.post("/api/leak/export")
def leak_export(req: ExportRequest):
    sc = _public(_lookup(req.scenario_id))
    msg = next((m for m in sc.discovery.messages if m.id == req.message_id and m.attachment), None)
    if msg is None:
        raise ApiException(404, "not_found", f"message {req.message_id} has no attachment in {sc.id}")
    audit.append("telegram_export", scenario_id=sc.id, object_id=sc.leak_sample.id)
    return JSONResponse(_round4({
        "leak_sample": sc.leak_sample.model_dump(by_alias=True),
        "file": {"name": msg.attachment.file_name, "size_bytes": msg.attachment.size_bytes}}))


@app.post("/api/trace")
def trace(req: TraceRequest):
    entry = _lookup(req.scenario_id)
    sc = _public(entry)
    result = _run_trace(entry["public"], req.top_k or ENGINE["TOP_K"])
    audit.append("trace", scenario_id=sc.id, object_id=result.trace_id)
    return _ok(result)


@app.post("/api/reveal")
def reveal(req: RevealRequest):
    reason = (req.reason or "").strip()
    if len(reason) < 8:
        raise ApiException(400, "reason_required", "a justification of at least 8 characters is required")
    entry = _lookup(req.scenario_id)
    leak = _public(entry).leak_sample
    if req.field not in leak.columns:
        raise ApiException(400, "bad_request", f"field {req.field} is not a column of the leak sample")
    if not 0 <= req.row_index < leak.row_count:
        raise ApiException(400, "bad_request", f"row_index must be between 0 and {leak.row_count - 1}")
    sim = _sim()
    fn = getattr(sim, "reveal_value", None) if sim is not None else None
    if fn is None or entry["bundle"] is None:
        raise ApiException(409, "not_ready", "no private store is available for this scenario")
    try:
        value = fn(entry["bundle"], req.row_index, req.field)
    except Exception as exc:
        raise ApiException(500, "engine_error", f"reveal failed: {type(exc).__name__}")
    logged = audit.append("reveal", scenario_id=entry["public"]["id"],
                          object_id=f"{leak.id}#{req.row_index}", field=req.field, reason=reason)
    resp = JSONResponse(RevealResponse(value=str(value), audit_id=logged["id"]).model_dump())
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/api/audit")
def audit_list(scenario_id: str | None = None):
    return _ok(AuditList(entries=audit.entries(scenario_id)))


@app.post("/api/inject")
def inject(req: InjectRequest):
    entry = _lookup(req.base_scenario_id)
    sc = _public(entry)
    if req.actor not in {a.id for a in sc.actors}:
        raise ApiException(400, "bad_request", f"actor {req.actor} is not part of {sc.id}")
    sim = _sim()
    fn = getattr(sim, "inject_leak", None) if sim is not None else None
    if fn is None or entry["bundle"] is None:
        raise ApiException(409, "not_ready", "injection needs the simulator and a generated base scenario")
    try:
        bundle = fn(entry["bundle"], req.actor)
    except Exception as exc:
        raise ApiException(500, "engine_error", f"inject failed: {type(exc).__name__}")
    register(bundle.public, bundle)
    new = _public(STORE[bundle.public["id"]])
    audit.append("inject", scenario_id=new.id, object_id=req.actor)
    return _ok(_summary(new))


@app.post("/api/canary/alert")
def canary_alert(req: CanaryAlertRequest):
    entry = _lookup(req.scenario_id)
    sc = _public(entry)
    if not sc.params.canary_mode:
        raise ApiException(400, "bad_request", "canary mode is off for this scenario")
    registry = {c.id: c for c in sc.canary_registry}
    if req.canary_id not in registry:
        raise ApiException(404, "not_found", f"canary {req.canary_id} is not in the registry")
    sim = _sim()
    fn = getattr(sim, "canary_alert", None) if sim is not None else None
    if fn is not None and entry["bundle"] is not None:
        try:
            raw = fn(entry["bundle"], req.canary_id)
        except Exception as exc:
            raise ApiException(500, "engine_error", f"canary alert failed: {type(exc).__name__}")
    else:  # derived from the public registry when no simulator bundle exists (fixtures)
        raw = {"canary_id": req.canary_id, "export_id": registry[req.canary_id].export_id,
               "ts": sc.leak_sample.found_ts,
               "message": f"Canary {req.canary_id} planted in {registry[req.canary_id].export_id} was triggered."}
    public = copy.deepcopy(entry["public"])  # the alert counts as a canary hit for this trace only
    hits = public["leak_sample"]["canary_hits"]
    if req.canary_id not in hits:
        hits.append(req.canary_id)
    result = _run_trace(public, ENGINE["TOP_K"])
    audit.append("canary_alert", scenario_id=sc.id, object_id=req.canary_id)
    return _ok(CanaryAlertResponse(alert=CanaryAlert.model_validate(raw), trace=result))


@app.get("/api/report/{trace_id}")
def report(trace_id: str):
    trace_dict = TRACES.get(trace_id)
    if trace_dict is None:
        if not trace_id.startswith("trc:"):
            raise ApiException(404, "not_found", f"trace {trace_id} not found")
        entry = _lookup("scn:" + trace_id.removeprefix("trc:"))  # 404 if no such scenario
        _public(entry)
        trace_dict = _run_trace(entry["public"], ENGINE["TOP_K"]).model_dump(by_alias=True)
    entry = _lookup(trace_dict["scenario_id"])
    sc = _public(entry)
    html = build_report(_round4(_summary(sc).model_dump(by_alias=True)), _round4(trace_dict))
    audit.append("report_export", scenario_id=sc.id, object_id=trace_id)
    return HTMLResponse(html)


def _bench_worker(bid: str, generate, req: BenchmarkRunRequest) -> None:
    def progress(p: float) -> None:
        BENCHMARKS[bid]["progress"] = round(p, 4)

    try:
        result = run_benchmark(generate, req.seed_range, req.loss_levels, req.archetypes, progress)
    except Exception:
        result = _bench_empty(req.seed_range, req.loss_levels, "failed", BENCHMARKS[bid]["progress"])
    BENCHMARKS[bid] = {"benchmark_id": bid, **result}


@app.post("/api/benchmark/run")
def benchmark_run(req: BenchmarkRunRequest):
    sim = _sim()
    generate = getattr(sim, "generate_scenario", None) if sim is not None else None
    if generate is None:
        raise ApiException(409, "not_ready", "the benchmark needs the simulator, which is not available yet")
    bid = f"bench:{len(BENCHMARKS) + 1:04d}"
    BENCHMARKS[bid] = {"benchmark_id": bid, **_bench_empty(req.seed_range, req.loss_levels)}
    audit.append("benchmark_run", object_id=bid)
    threading.Thread(target=_bench_worker, args=(bid, generate, req), daemon=True).start()
    return _ok(BenchmarkRunResponse(benchmark_id=bid))


@app.get("/api/benchmark/{benchmark_id}")
def benchmark_get(benchmark_id: str):
    entry = BENCHMARKS.get(benchmark_id)
    if entry is None:
        raise ApiException(404, "not_found", f"benchmark {benchmark_id} not found")
    return _ok(BenchmarkResult.model_validate(entry))
