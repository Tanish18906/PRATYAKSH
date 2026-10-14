"""Stage 6: greedy chokepoints (docs/03_ENGINE.md section 10).

Each hop yields at most one actionable item. Marginals are sums of relative likelihoods over all
enumerated paths, not calibrated probabilities.
"""
from collections import defaultdict

from app.config import ENGINE as CFG


def _item(idx, hop: dict) -> tuple | None:
    """(item_id, item_type, action_text) for one hop, or None."""
    actor, frm = hop["actor"], hop["from_loc"]
    who, where = idx.name(actor), idx.name(frm)
    kind = idx.loc[frm]["kind"]
    if kind == "system":
        if "api-key" in actor:
            return f"perm:{actor}@{frm}", "api_key", f"Rotate and revoke API key {who}"
        if idx.actor[actor]["kind"] == "service":
            return f"perm:{actor}@{frm}", "service_account", f"Suspend service account {who} until reviewed"
        return f"perm:{actor}@{frm}", "permission", f"Revoke {who}'s access to {where}"
    if kind == "endpoint":
        return f"perm:{actor}@egress", "permission", f"Block outbound uploads from {who}'s laptop"
    return f"ch:{frm}", "channel", f"Block transfers to {where}"


def chokepoints(idx, paths: list, found_at: str) -> list:
    """paths carry "origin", "hops" and "prob". Greedy cover of the probability mass, up to CHOKE_MAX."""
    items_of, info, marginal = [], {}, defaultdict(float)
    for p in paths:
        creator = idx.artifact[p["origin"]]["created_by"]
        skip = creator if idx.actor[creator]["kind"] == "service" else None
        found = {}
        for h in p["hops"]:
            if h["actor"] == skip or h["from_loc"] == found_at:
                continue
            item = _item(idx, h)
            found[item[0]] = item
        items_of.append(set(found))
        info.update(found)
        for iid in found:
            marginal[iid] += p["prob"]
    uncovered, covered, out = set(range(len(paths))), 0.0, []
    while len(out) < CFG["CHOKE_MAX"]:
        gain = defaultdict(float)
        for i in uncovered:
            for iid in items_of[i]:
                gain[iid] += paths[i]["prob"]
        if not gain:
            break
        best = min(gain, key=lambda iid: (-gain[iid], iid))
        newly = {i for i in uncovered if best in items_of[i]}
        covered += sum(paths[i]["prob"] for i in newly)
        uncovered -= newly
        _, kind, text = info[best]
        out.append({"rank": len(out) + 1, "item_type": kind, "item_id": best, "label": text,
                    "marginal": round(marginal[best], 4), "cumulative_coverage": round(min(covered, 1.0), 4),
                    "action_text": text})
    return out
