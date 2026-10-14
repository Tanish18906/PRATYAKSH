"""Actor-selected leak injection into the fixed synthetic company."""

import hashlib

from .generator import ScenarioBundle, _generate_scenario


def inject_leak(base: ScenarioBundle, actor_id: str) -> ScenarioBundle:
    actor = next((actor for actor in base.public["actors"] if actor["id"] == actor_id), None)
    if actor is None:
        raise ValueError(f"unknown actor: {actor_id}")
    access = set(actor["access"])
    if actor_id == "act:backup-svc":
        archetype = "A5"
    elif actor["kind"] == "service" and any(word in actor_id for word in ("api-key", "etl")):
        archetype = "A2"
    elif "sys:bi-warehouse" in access:
        archetype = "A1"
    elif "sys:partner-sftp" in access or "sys:email-gateway" in access:
        archetype = "A3"
    else:
        archetype = "A1"
    base_seed = base.public["seed"]
    seed = int.from_bytes(hashlib.sha256(f"{base_seed}|{actor_id}".encode()).digest()[:4], "big")
    params = base.public["params"]
    scenario_id = f"scn:INJ-{base_seed}-{actor_id.removeprefix('act:')}-L{round(params['log_loss'] * 100)}"
    return _generate_scenario(archetype, seed, params["log_loss"], params["canary_mode"],
                              params["scale"], actor_id, scenario_id)
