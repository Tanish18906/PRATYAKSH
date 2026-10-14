"""In-memory scenario lookup and separate public/truth JSON files."""

import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "scenarios"
_BUNDLES = {}


def register(bundle) -> None:
    scenario_id = bundle.public["id"]
    _BUNDLES[scenario_id] = bundle
    directory = DATA_DIR / scenario_id.replace(":", "_")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "public.json").write_text(json.dumps(bundle.public, sort_keys=True, separators=(",", ":")))
    (directory / "truth.json").write_text(json.dumps(bundle.truth, sort_keys=True, separators=(",", ":")))


def get_bundle(scenario_id: str):
    return _BUNDLES.get(scenario_id)
