"""PUGMARK API (docs/01_DATA_CONTRACT.md section 12). Phase 0: health endpoint and CORS only."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CONTRACT_VERSION, ENGINE

app = FastAPI(title="PUGMARK", version=ENGINE["ENGINE_VERSION"])
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"],
                   allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "contract_version": CONTRACT_VERSION, "engine_version": ENGINE["ENGINE_VERSION"]}
