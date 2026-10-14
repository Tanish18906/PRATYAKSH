"""Build the offline replay bundle (docs/01_DATA_CONTRACT.md section 13) by calling the real API code.

    python backend/scripts/make_demo_bundle.py                 # seed 42, A1, demo, loss 0.4, canary mode on
    python backend/scripts/make_demo_bundle.py --fixture H1    # placeholder from a hand-written scenario

Writes frontend/public/demo.json unless --out is given. Audit entries go to a temporary file, not the real log.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app import main as api  # noqa: E402
from app.models import DemoBundle  # noqa: E402
from app.privacy import audit  # noqa: E402

DEFAULT_OUT = BACKEND.parent / "frontend" / "public" / "demo.json"


class BundleError(Exception):
    pass


def _json(r):
    if r.status_code != 200:
        raise BundleError(f"{r.request.method} {r.request.url.path} -> {r.status_code}: {r.text}")
    return r.json()


def make_bundle(fixture: str | None = None) -> dict:
    saved_path, saved_store = audit.PATH, dict(api.STORE)
    with tempfile.TemporaryDirectory() as tmp:
        audit.PATH = Path(tmp) / "audit.jsonl"
        audit.reset()
        try:
            client = TestClient(api.app)
            if fixture:
                public = json.loads((api.FIXTURE_DIR / f"{fixture}.json").read_text())
                api.register(public)
                summary = _json(client.get(f"/api/scenario/{public['id']}"))
            else:
                if api._sim() is None:
                    raise BundleError("the simulator is not available; use --fixture H1 for a placeholder "
                                      "built from a hand-written scenario")
                summary = _json(client.post("/api/scenario/generate", json={
                    "archetype": "A1", "seed": 42, "log_loss": 0.4, "canary_mode": True, "scale": "demo"}))
            sid = summary["id"]
            _json(client.post("/api/leak/export", json={
                "scenario_id": sid, "message_id": summary["discovery"]["leak_message_id"]}))
            trace = _json(client.post("/api/trace", json={"scenario_id": sid}))
            r = client.get(f"/api/report/{trace['trace_id']}")
            if r.status_code != 200:
                raise BundleError(f"report failed: {r.status_code}")
            bundle = {"contract_version": "1.0", "scenario": summary, "trace": trace,
                      "audit": _json(client.get("/api/audit", params={"scenario_id": sid}))["entries"],
                      "benchmark": None, "report_html": r.text}
            return DemoBundle.model_validate(bundle).model_dump(by_alias=True)
        finally:
            audit.PATH = saved_path
            audit.reset()
            api.STORE.clear()
            api.STORE.update(saved_store)


def main_cli(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fixture", help="hand-written scenario H1..H8 instead of the simulator")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    try:
        bundle = make_bundle(args.fixture)
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=1) + "\n")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


main = main_cli  # tests call scripts.make_demo_bundle.main(argv)

if __name__ == "__main__":
    sys.exit(main_cli())
