"""Stage 3 custody paths (docs/03_ENGINE.md section 7).

Phase 1 scope: M1 (observed move) and M2 (hidden move to the leak location) plus the fallback path.
M3 (hidden download to an endpoint) and M4 (hidden copy between systems) arrive in Phase 2.
"""
import math
from datetime import timedelta

from app.config import ENGINE as CFG
from app.engine.normalize import parse_ts


def hidden_cost(idx, loc_id: str, loss: dict) -> tuple:
    """(cost, est_loss) of an unlogged move leaving loc_id."""
    src = idx.loc[loc_id]["log_source"]
    if src is None:
        return CFG["H_ENDPOINT"], None
    return -math.log(loss[src]) + CFG["H_BASE"], loss[src]


def _hop(frm, to, actor, kind, ts=None, event=None, action=None, rows=None, est=None, note=""):
    return {"from_loc": frm, "to_loc": to, "actor": actor, "ts": ts, "kind": kind, "event_id": event,
            "action": action, "rows": rows, "est_loss": est, "note": note}


def find_paths(idx, art: dict, loss: dict, found_at: str, found_ts: str) -> tuple:
    """Returns (paths, notes); each path is {"cost": float, "hops": [Hop dicts]}."""
    moves = idx.moves_by_artifact.get(art["id"], [])
    out, seen, notes, best = [], set(), [], [math.inf]
    alt_cache = {}

    def alt_actors(loc_id, holder):
        if loc_id not in alt_cache:
            lo = parse_ts(found_ts) - timedelta(days=CFG["ACTOR_ALT_WINDOW_DAYS"])
            who = []
            for e in sorted(idx.events, key=lambda e: (e["ts"], e["id"]), reverse=True):
                if parse_ts(e["ts"]) < lo or e["ts"] > found_ts or loc_id not in (e["from_loc"], e["to_loc"]):
                    continue
                if e["actor"] not in who:
                    who.append(e["actor"])
            alt_cache[loc_id] = who
        return [a for a in alt_cache[loc_id] if a != holder][:CFG["ACTOR_ALT_MAX"]]

    def record(cost, hops):
        key = tuple((h["from_loc"], h["to_loc"], h["actor"], h["event_id"]) for h in hops)
        if key not in seen:
            seen.add(key)
            out.append({"cost": cost, "hops": hops})
            best[0] = min(best[0], cost)

    def dfs(loc, t, holder, hidden, cost, hops, visited):
        if len(out) >= CFG["MAX_PATHS_PER_ORIGIN"] or cost > best[0] + CFG["COST_MARGIN"]:
            return
        if loc == found_at:
            record(cost, hops)
            return
        if len(hops) >= CFG["MAX_DEPTH"]:
            return
        options = []  # (kind, to_loc, actor, event_id, payload)
        for e in moves:
            if e["from_loc"] == loc and t <= e["ts"] <= found_ts and e["to_loc"] not in visited:
                options.append(("observed", e["to_loc"], e["actor"], e["id"], e))
        L = idx.loc[loc]
        if hidden < CFG["MAX_HIDDEN"] and (L["kind"] in ("endpoint", "external") or L["egress_capable"]):
            if L["kind"] == "endpoint":
                actors = [L["owner_actor"]] if L["owner_actor"] else []
            else:
                actors = [holder] + alt_actors(loc, holder)
            for a in actors:
                if L["kind"] != "endpoint" and loc not in idx.actor[a]["access"]:
                    continue
                options.append(("inferred", found_at, a, "", None))
        for kind, to, actor, eid, e in sorted(options, key=lambda o: o[:4]):
            if kind == "observed":
                hop = _hop(loc, to, actor, "observed", e["ts"], e["id"], e["action"], e["rows"])
                dfs(to, e["ts"], actor, hidden, cost + CFG["OBS_COST"], hops + [hop], visited | {to})
            else:
                c, est = hidden_cost(idx, loc, loss)
                if L["kind"] == "system" and actor != holder:
                    c += CFG["ACTOR_SWITCH"]
                hop = _hop(loc, to, actor, "inferred", est=est, note="No log was found for this move.")
                dfs(to, t, actor, hidden + 1, cost + c, hops + [hop], visited | {to})

    dfs(art["location"], art["created_ts"], art["created_by"], 0, 0.0, [], {art["location"]})
    if not out:
        _, est = hidden_cost(idx, art["location"], loss)
        hop = _hop(art["location"], found_at, art["created_by"], "inferred", est=est,
                   note="No log was found for this move.")
        out.append({"cost": CFG["UNKNOWN_CHANNEL"] + CFG["H_BASE"], "hops": [hop]})
        notes.append(f"No custody path found for {art['id']}; showing direct unknown channel.")
    return out, notes
