"""PUGMARK API (docs/01_DATA_CONTRACT.md section 12).

Phase 1: scenario generate/get, leak export, trace, JSON error shape, audit append.
Scenarios come from the simulator when it exists (`_sim()`); until then the hand-written fixtures
H1..H8 are registered at startup and `generate` answers 409 not_ready.
"""
import copy
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import CONTRACT_VERSION, ENGINE
from app.engine.trace import trace as run_trace
from app.models import (ExportRequest, GenerateRequest, PublicScenario, ScenarioSummary, TraceRequest,
                        TraceResult)
from app.privacy import audit
from app.privacy.mask import mask_value

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

# scenario id -> {"public": PublicScenario dict, "bundle": simulator bundle or None}. The engine and API
# only ever read "public"; the bundle (truth, private store) is never serialised.
STORE: dict = {}


class ApiException(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _sim():
    """The simulator's generator module if it provides generate_scenario, else None."""
    try:
        from app.sim import generator
    except Exception:
        return None
    return generator if callable(getattr(generator, "generate_scenario", None)) else None


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
    if isinstance(o, float):
        return round(o, 4)
    if isinstance(o, dict):
        return {k: _round4(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round4(v) for v in o]
    return o


def _ok(model, **dump) -> JSONResponse:
    return JSONResponse(_round4(model.model_dump(by_alias=True, **dump)))


def _lookup(scenario_id: str) -> dict:
    entry = STORE.get(scenario_id)
    if entry is None and _sim() is not None and callable(getattr(_sim(), "get_bundle", None)):
        bundle = _sim().get_bundle(scenario_id)
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
    try:
        result = TraceResult.model_validate(run_trace(entry["public"], req.top_k or ENGINE["TOP_K"]))
    except Exception as exc:
        raise ApiException(500, "engine_error", f"trace failed: {type(exc).__name__}")
    audit.append("trace", scenario_id=sc.id, object_id=result.trace_id)
    return _ok(result)
