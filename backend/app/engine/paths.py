"""Stage 3 custody paths (docs/03_ENGINE.md section 7): M1 observed move, M2 hidden move to the leak
location, M3 hidden download to a person's endpoint, M4 hidden copy between systems, plus the fallback."""
import math

from app.config import ENGINE as CFG
from app.engine.normalize import shift_days


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
    seen_moves = {(e["actor"], e["from_loc"], e["to_loc"]) for e in moves}
    systems = [x["id"] for x in idx.loc.values() if x["kind"] == "system"]
    out, seen, notes, best = [], set(), [], [math.inf]
    alt_cache = {}
    recent = sorted(idx.events, key=lambda e: (e["ts"], e["id"]), reverse=True)
    lo = shift_days(found_ts, -CFG["ACTOR_ALT_WINDOW_DAYS"])  # ISO strings compare in time order

    def alt_actors(loc_id, holder):
        if loc_id not in alt_cache:
            who = []
            for e in recent:
                if lo <= e["ts"] <= found_ts and loc_id in (e["from_loc"], e["to_loc"]):
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
        L = idx.loc[loc]
        options = []  # (kind, to_loc, actor, event_id, extra cost, event)
        for e in moves:  # M1
            if e["from_loc"] == loc and t <= e["ts"] <= found_ts and e["to_loc"] not in visited:
                options.append(("observed", e["to_loc"], e["actor"], e["id"], CFG["OBS_COST"], e))
        if hidden < CFG["MAX_HIDDEN"]:
            hop_cost, _ = hidden_cost(idx, loc, loss)
            if L["kind"] in ("endpoint", "external") or L["egress_capable"]:  # M2
                if L["kind"] == "endpoint":
                    actors = [L["owner_actor"]] if L["owner_actor"] else []
                else:
                    actors = [holder] + alt_actors(loc, holder)
                for a in actors:
                    if L["kind"] != "endpoint" and loc not in idx.actor[a]["access"]:
                        continue
                    switch = CFG["ACTOR_SWITCH"] if L["kind"] == "system" and a != holder else 0.0
                    options.append(("inferred", found_at, a, "", hop_cost + switch, None))
            if L["kind"] == "system":
                for a, A in idx.actor.items():  # M3
                    ep = idx.owner_endpoint.get(a)
                    if (ep and ep not in visited and loc in A["access"] and ep in A["access"]
                            and (a, loc, ep) not in seen_moves):
                        options.append(("inferred", ep, a, "", hop_cost, None))
                for m in systems:  # M4
                    if m == loc or m in visited or any(f == loc and to == m for _, f, to in seen_moves):
                        continue
                    for a in [holder] + alt_actors(loc, holder):
                        acc = idx.actor[a]["access"]
                        if loc in acc and m in acc:
                            switch = CFG["ACTOR_SWITCH"] if a != holder else 0.0
                            options.append(("inferred", m, a, "", hop_cost + switch, None))
        for kind, to, actor, eid, c, e in sorted(options, key=lambda o: o[:4]):
            if kind == "observed":
                hop = _hop(loc, to, actor, "observed", e["ts"], e["id"], e["action"], e["rows"])
                dfs(to, e["ts"], actor, hidden, cost + c, hops + [hop], visited | {to})
            else:
                est = hidden_cost(idx, loc, loss)[1]
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
