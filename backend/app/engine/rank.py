"""Stage 5: score, softmax and marginals (docs/03_ENGINE.md section 9).

Probabilities are relative likelihoods, not calibrated. Phase 1 has no anomaly term (stage 4 is Phase 2).
"""
import math

from app.config import ENGINE as CFG
from app.engine.evidence import hypothesis_text


def path_actors(idx, art: dict, hops: list) -> list:
    """Unique hop actors in order, minus a service-account creator of the origin."""
    skip = art["created_by"] if idx.actor[art["created_by"]]["kind"] == "service" else None
    out = []
    for h in hops:
        if h["actor"] != skip and h["actor"] not in out:
            out.append(h["actor"])
    return out


def softmax(scores: list) -> list:
    top = max(scores)
    ex = [math.exp((s - top) / CFG["TEMPERATURE"]) for s in scores]
    total = sum(ex)
    return [x / total for x in ex]


def rank(idx, paths: list, cands: dict, pinned: str | None, top_k: int, found_at: str) -> dict:
    """paths: [{"origin": art id, "cost", "hops"}]; cands: art id -> raw candidate row."""
    scores = [CFG["W_ORIGIN"] * cands[p["origin"]]["origin_fit"] - CFG["W_PATH"] * p["cost"] for p in paths]
    prob = softmax(scores)
    order = sorted(range(len(paths)), key=lambda i: (-prob[i], i))[:top_k]
    hyps = []
    for r, i in enumerate(order, 1):
        p, art = paths[i], idx.artifact[paths[i]["origin"]]
        text, evidence = hypothesis_text(idx, art, cands[p["origin"]], p["hops"])
        hyps.append({
            "rank": r, "path_id": f"hyp:{r}", "origin_artifact": p["origin"],
            "probability": round(prob[i], 4), "score": round(scores[i], 4),
            "score_parts": {"origin_fit": round(cands[p["origin"]]["origin_fit"], 4),
                            "path_cost": round(p["cost"], 4), "anomaly": 0.0},
            "hops": p["hops"], "actors": path_actors(idx, art, p["hops"]),
            "summary_text": text, "evidence": evidence,
        })
    best_hyp_for = {}
    for h in hyps:
        for a in h["actors"]:
            best_hyp_for.setdefault(a, h["path_id"])
    actor_m, loc_m, origin_m = {}, {}, {}
    for p, pr in zip(paths, prob):
        origin_m[p["origin"]] = origin_m.get(p["origin"], 0.0) + pr
        for a in path_actors(idx, idx.artifact[p["origin"]], p["hops"]):
            actor_m[a] = actor_m.get(a, 0.0) + pr
        for loc in {x for h in p["hops"] for x in (h["from_loc"], h["to_loc"])} - {found_at}:
            loc_m[loc] = loc_m.get(loc, 0.0) + pr
    if pinned:
        origin_ranking = [{"artifact_id": pinned, "probability": 1.0}]
    else:
        origin_ranking = [{"artifact_id": a, "probability": round(m, 4)}
                          for a, m in sorted(origin_m.items(), key=lambda kv: -kv[1])]
    return {
        "hypotheses": hyps,
        "origin_ranking": origin_ranking,
        "actor_ranking": [{"actor": a, "marginal": round(m, 4), "top_path_id": best_hyp_for.get(a)}
                          for a, m in sorted(actor_m.items(), key=lambda kv: (-kv[1], kv[0]))],
        "location_ranking": [{"location": x, "marginal": round(m, 4)}
                             for x, m in sorted(loc_m.items(), key=lambda kv: (-kv[1], kv[0]))],
    }
