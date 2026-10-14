"""Public A1 scenario generation and private bundle access."""

from dataclasses import dataclass

import numpy as np

from .archetypes import a1_times, plant_a1
from .background import make_background
from .base_table import seconds, warm_cache as _warm_cache
from .company import make_company
from .discovery import make_discovery
from .leakfile import PrivateStore, make_leak, render_leak_row
from .lossy import assign_and_drop
from .store import get_bundle, register


@dataclass(slots=True)
class ScenarioBundle:
    public: dict
    truth: dict
    private: PrivateStore


def warm_cache(scale: str) -> None:
    _warm_cache(scale)


def generate_scenario(archetype: str, seed: int, log_loss: float,
                      canary_mode: bool, scale: str) -> ScenarioBundle:
    if archetype != "A1":
        raise ValueError("Phase 1 supports A1 only")
    if canary_mode:
        raise ValueError("canary mode starts in Phase 3")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    if scale not in ("demo", "bench"):
        raise ValueError("scale must be demo or bench")
    if not 0 <= log_loss <= 0.8:
        raise ValueError("log_loss must be between 0 and 0.8")

    base = _warm_cache(scale)
    found_ts, rng = a1_times(seed, scale)
    found = seconds(found_ts)
    recent = int(np.count_nonzero((base.created <= found) &
                                  (base.created > found - 30 * 86400)))
    company = make_company(scale, round(recent / 720, 4))
    planted = plant_a1(base, company, seed, scale, found_ts, rng)
    leak, private = make_leak(base, planted["origin_indices"], seed, scale, found_ts)
    events = make_background(company, base, found_ts, seed) + planted["events"]
    fixed = seed == 42 and scale == "demo"
    preserve = (log_loss <= 0.4 if log_loss <= 0.4 or log_loss >= 0.6 else None) if fixed else None
    public_events, dropped = assign_and_drop(events, seed, log_loss, planted["critical"], preserve)
    suffix = f"A1-{seed}-L{round(log_loss * 100)}" + ("-b" if scale == "bench" else "")
    scenario_id = f"scn:{suffix}"
    discovery = make_discovery(seed, leak, planted["upload_ts"])
    public = {
        "contract_version": "1.0", "id": scenario_id, "archetype": "A1", "seed": seed,
        "params": {"log_loss": log_loss, "canary_mode": False, "scale": scale},
        "company": "Nova Health", "now_ts": found_ts,
        **company, "events": public_events, "artifacts": planted["artifacts"],
        "canary_registry": [], "leak_sample": leak, "discovery": discovery,
    }
    origin_event = planted["origin_event"]
    critical = planted["critical"]
    truth = {
        "scenario_id": scenario_id, "origin_artifact": planted["origin_id"],
        "true_path": [
            {"from_loc": "sys:customer-db", "to_loc": "sys:bi-warehouse",
             "actor": "act:etl-nightly", "ts": origin_event["ts"], "event_id": origin_event["id"],
             "dropped": origin_event["id"] in dropped},
            {"from_loc": "sys:bi-warehouse", "to_loc": planted["endpoint"],
             "actor": planted["insider"], "ts": critical["ts"], "event_id": critical["id"],
             "dropped": critical["id"] in dropped},
            {"from_loc": planted["endpoint"], "to_loc": "ext:telegram-leak-channel",
             "actor": planted["insider"], "ts": planted["upload_ts"], "event_id": None,
             "dropped": False},
        ],
        "true_actors": [planted["insider"]],
        "leak_location": "ext:telegram-leak-channel", "dropped_event_ids": dropped,
    }
    bundle = ScenarioBundle(public, truth, private)
    register(bundle)
    return bundle


def reveal_value(bundle: ScenarioBundle, row_index: int, field: str) -> str:
    if field not in bundle.private.columns:
        raise KeyError(field)
    return render_leak_row(bundle.private, row_index)[field]


def to_summary(bundle: ScenarioBundle) -> dict:
    public = bundle.public
    return {
        "contract_version": "1.0", "id": public["id"], "archetype": public["archetype"],
        "seed": public["seed"], "params": public["params"], "company": public["company"],
        "counts": {name: len(public[key]) for name, key in
                   (("actors", "actors"), ("locations", "locations"),
                    ("datasets", "datasets"), ("events", "events"),
                    ("artifacts", "artifacts"))},
        "discovery": public["discovery"], "leak_sample": public["leak_sample"],
        "actors": public["actors"], "locations": public["locations"],
    }
