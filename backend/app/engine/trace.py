"""Engine entry point: trace(scenario) -> TraceResult (docs/03_ENGINE.md section 1).

Pure and deterministic. Reads only the public scenario; never params.log_loss or any truth.
"""
from app.config import ENGINE as CFG
from app.engine.index import Index
from app.engine.loss import estimate_loss
from app.engine.origin import pin_canary, public_row, score_candidates, select_used
from app.engine.paths import find_paths
from app.engine.rank import rank

NO_MATCH = ("The leak does not match any known export (best containment {c:.2f}). It may be a join of "
            "several sources or come from an unknown system. Collect: export or query logs for the "
            "leaked identifier columns from any system outside the export catalog.")


def trace(scenario: dict, top_k: int = 5) -> dict:
    idx = Index(scenario)
    leak = scenario["leak_sample"]
    loss = estimate_loss(scenario)
    pinned, notes = pin_canary(scenario)
    scored = score_candidates(scenario)
    cands = {c["artifact_id"]: c for c in scored}
    used = select_used(scored, pinned)

    result = {
        "contract_version": "1.0",
        "trace_id": "trc:" + scenario["id"].removeprefix("scn:"),
        "scenario_id": scenario["id"],
        "engine_version": CFG["ENGINE_VERSION"],
        "origin_pinned": pinned is not None,
        "origin_candidates": [public_row(c) for c in scored],
        "origin_ranking": [], "hypotheses": [], "actor_ranking": [], "location_ranking": [],
        "chokepoints": [], "recommended_evidence": [], "loss_estimates": loss,
        "graph": {"nodes": [], "edges": []},  # graph builder is Phase 2
        "notes": notes,
    }
    if not used:
        best = max((c["containment"] for c in scored if c["containment"] is not None), default=0.0)
        notes.append(NO_MATCH.format(c=best))
        return result

    paths = []
    for art_id in used:
        found, more = find_paths(idx, idx.artifact[art_id], loss, leak["found_at"], leak["found_ts"])
        notes.extend(more)
        paths += [{"origin": art_id, **p} for p in found]
    result.update(rank(idx, paths, cands, pinned, top_k, leak["found_at"]))
    return result
