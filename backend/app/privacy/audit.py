"""Audit log (docs/01_DATA_CONTRACT.md section 11): in memory plus JSON lines at backend/data/audit.jsonl.

The only place the wall clock is allowed; engine and simulator never see it.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "data" / "audit.jsonl"

_entries: list = []
_base: int | None = None  # lines already in the file when this process wrote its first entry
# One lock covers read counter, increment, assign id, append in memory and write the line. Locking only the
# file write would still hand out duplicate ids. The API therefore needs a single uvicorn worker process.
_lock = threading.Lock()


def reset() -> None:
    """Forget in-memory entries (tests, or a fresh process). The file is left alone."""
    global _base
    with _lock:
        _entries.clear()
        _base = None


def append(action: str, scenario_id: str | None = None, object_id: str | None = None,
           field: str | None = None, reason: str | None = None) -> dict:
    global _base
    with _lock:
        if _base is None:
            _base = sum(1 for _ in PATH.open()) if PATH.exists() else 0
        entry = {
            "id": f"aud:{_base + len(_entries) + 1:04d}",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "who": "investigator-demo", "action": action, "scenario_id": scenario_id,
            "object_id": object_id, "field": field, "reason": reason,
        }
        PATH.parent.mkdir(parents=True, exist_ok=True)
        with PATH.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        _entries.append(entry)  # in memory only once the line is on disk, so both views agree
        return entry


def entries(scenario_id: str | None = None) -> list:
    with _lock:
        return [e for e in _entries if scenario_id is None or e["scenario_id"] == scenario_id]
