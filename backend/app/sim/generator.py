"""Public scenario generation and private bundle access."""

from dataclasses import dataclass

import numpy as np

from .archetypes import a1_times, plant_a1, plant_a2, plant_a3, plant_a4, plant_a5
from .background import make_background
from .base_table import case_key, seconds, warm_cache as _warm_cache
from .company import make_company
from .discovery import make_discovery
from .exports import plant_canaries
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
    return _generate_scenario(archetype, seed, log_loss, canary_mode, scale)


def _generate_scenario(archetype: str, seed: int, log_loss: float,
                       canary_mode: bool, scale: str, forced_actor: str | None = None,
                       injected_id: str | None = None) -> ScenarioBundle:
    if archetype not in ("A1", "A2", "A3", "A4", "A5"):
        raise ValueError("unsupported archetype")
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
    if archetype == "A4":
        company["actors"].append({"id": "act:anonymous", "kind": "service", "name": "Anonymous",
                                  "role": "anonymous", "team": "External", "access": []})
    if archetype == "A1":
        planted = plant_a1(base, company, seed, scale, found_ts, rng, forced_actor)
    elif archetype == "A2":
        planted = plant_a2(base, company, seed, found_ts, rng, forced_actor)
    elif archetype == "A3":
        planted = plant_a3(base, company, seed, found_ts, rng, forced_actor)
    elif archetype == "A4":
        planted = plant_a4(base, company, seed, found_ts, rng)
    else:
        planted = plant_a5(base, company, seed, found_ts, rng)
    registry, canaries = (plant_canaries(planted["artifacts"], case_key(scale))
                          if canary_mode else ([], {}))
    if canary_mode:
        for event in planted["events"]:
            if event["meta"].get("artifact_id") or (
                    event["object"] == planted["origin_id"] and
                    event["action"] in ("download", "send", "copy", "api_call")):
                event["rows"] += 3
    origin_artifact = next(artifact for artifact in planted["artifacts"]
                           if artifact["id"] == planted["origin_id"])
    leak, private = make_leak(base, planted["origin_indices"], seed, scale, found_ts,
                              archetype, canaries.get(planted["origin_id"]),
                              "MARKETING" if archetype == "A3" else "ETL",
                              origin_artifact["columns"])
    events = make_background(company, base, found_ts, seed) + planted["events"]
    fixed = archetype == "A1" and seed == 42 and scale == "demo" and forced_actor is None
    preserve = (log_loss <= 0.4 if log_loss <= 0.4 or log_loss >= 0.6 else None) if fixed else None
    public_events, dropped = assign_and_drop(events, seed, log_loss, planted["critical"], preserve)
    suffix = (f"{archetype}-{seed}-L{round(log_loss * 100)}" +
              ("-C" if canary_mode else "") + ("-b" if scale == "bench" else ""))
    scenario_id = injected_id or f"scn:{suffix}"
    discovery = make_discovery(seed, leak, planted["upload_ts"])
    public = {
        "contract_version": "1.0", "id": scenario_id, "archetype": archetype, "seed": seed,
        "params": {"log_loss": log_loss, "canary_mode": canary_mode, "scale": scale},
        "company": "Nova Health", "now_ts": found_ts,
        **company, "events": public_events, "artifacts": planted["artifacts"],
        "canary_registry": registry, "leak_sample": leak, "discovery": discovery,
    }
    truth = {
        "scenario_id": scenario_id, "origin_artifact": planted["origin_id"],
        "true_path": [
            {"from_loc": source, "to_loc": target, "actor": actor,
             "ts": event["ts"] if event else planted["upload_ts"],
             "event_id": event["id"] if event else None,
             "dropped": event["id"] in dropped if event else False}
            for source, target, actor, event in planted["path"]
        ],
        "true_actors": planted.get("true_actors", [planted["insider"]]),
        "leak_location": "ext:telegram-leak-channel", "dropped_event_ids": dropped,
    }
    bundle = ScenarioBundle(public, truth, private)
    register(bundle)
    return bundle


def reveal_value(bundle: ScenarioBundle, row_index: int, field: str) -> str:
    if field not in bundle.private.columns:
        raise KeyError(field)
    return render_leak_row(bundle.private, row_index)[field]


def canary_alert(bundle: ScenarioBundle, canary_id: str) -> dict:
    if not bundle.public["params"]["canary_mode"]:
        raise ValueError("canary mode is off")
    entry = next((entry for entry in bundle.public["canary_registry"]
                  if entry["id"] == canary_id), None)
    if entry is None:
        raise KeyError(canary_id)
    slug, number = canary_id.removeprefix("can:").rsplit("-", 1)
    return {"canary_id": canary_id, "export_id": entry["export_id"],
            "ts": bundle.public["now_ts"],
            "message": f"Phishing email received at canary.{slug.lower()}.{number}@example.net"}


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
