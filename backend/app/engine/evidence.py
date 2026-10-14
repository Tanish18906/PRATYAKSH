"""Summary and evidence text (docs/03_ENGINE.md section 13) and stage 7, which missing log helps most (section 11).

Probabilities are relative likelihoods; nothing here claims certainty. Values are names, counts and times only.
"""
import math

from app.config import ENGINE as CFG
from app.engine.origin import format_counts

VERBS = {"download": "downloaded", "copy": "copied", "upload": "uploaded", "send": "sent",
         "api_call": "pulled through the API"}


def _hop_text(idx, hop: dict) -> str:
    who, frm, to = idx.name(hop["actor"]), idx.name(hop["from_loc"]), idx.name(hop["to_loc"])
    if hop["kind"] == "observed":
        verb = VERBS.get(hop["action"], hop["action"])
        return f"{who} {verb} it from {frm} to {to} at {hop['ts']}."
    return f"A move from {frm} to {to} by {who} is inferred because no log was found."


def hypothesis_text(idx, leak: dict, art: dict, cand: dict, hops: list, per_actor: dict) -> tuple:
    """Returns (summary_text, evidence list) for one path. per_actor: actor -> (event, info) or None."""
    pct = round(cand["containment"] * 100)
    matches, total = format_counts(leak, art)
    parts = [f"{art['id']} (created by {idx.name(art['created_by'])} at {art['created_ts']}) is the likely "
             f"source: {pct}% of the leaked records are in it."]
    evidence = [{"kind": "fingerprint", "ts": art["created_ts"], "event_id": None,
                 "text": (f"{pct}% of the leaked identifiers appear in {art['id']}; {matches} of {total} "
                          f"format attributes match; watermark term {cand['watermark_term']:.2f}.")}]
    for kind in ("observed", "inferred"):
        for hop in hops:
            if hop["kind"] == kind:
                text = _hop_text(idx, hop)
                parts.append(text)
                evidence.append({"kind": kind, "text": text, "ts": hop["ts"], "event_id": hop["event_id"]})
    for actor, found in per_actor.items():
        if found and found[1]["score"] >= 2:
            e, info = found
            text = (f"{idx.name(actor)} moved {e['rows']} rows; their usual is about "
                    f"{round(math.exp(info['mu']))}.")
            parts.append(text)
            evidence.append({"kind": "anomaly", "text": text, "ts": e["ts"], "event_id": e["id"]})
    return " ".join(parts), evidence


def recommend(idx, paths: list, loss: dict, leak: dict) -> list:
    """Stage 7. paths carry "prob"; one request per distinct inferred (from_loc, to_loc)."""
    mass = {}
    for p in paths:
        for sig in {(h["from_loc"], h["to_loc"]) for h in p["hops"] if h["kind"] == "inferred"}:
            m = mass.setdefault(sig, {"mass": 0.0, "origin": p["origin"], "best": -1.0})
            m["mass"] += p["prob"]
            if p["prob"] > m["best"]:
                m["origin"], m["best"] = p["origin"], p["prob"]
    rows = []
    for (frm, to), m in mass.items():
        x = min(max(m["mass"], 0.0), 1.0)
        h = 0.0 if x in (0.0, 1.0) else -x * math.log(x) - (1 - x) * math.log(1 - x)
        rows.append((h / math.log(2), x, (frm, to), m["origin"]))
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    out = []
    for rank, (info, x, (frm, to), origin) in enumerate(rows[:CFG["EVIDENCE_MAX"]], 1):
        span = f"between {idx.artifact[origin]['created_ts']} and {leak['found_ts']}"
        L = idx.loc[frm]
        if L["kind"] == "endpoint":
            text = f"Endpoint, proxy or DLP logs for {idx.name(L['owner_actor'])}'s laptop {span}"
        elif L["log_source"]:
            text = f"{L['name']} audit logs ({L['log_source']}) {span}"
            if loss[L["log_source"]] >= CFG["LOSS_DEFAULT"]:
                text += f" (about {round(loss[L['log_source']] * 100)}% of this source's events appear to be missing)"
        else:
            text = f"Network logs for transfers from {L['name']}"
        out.append({"rank": rank, "hop_ref": {"from_loc": frm, "to_loc": to}, "mass": round(x, 4),
                    "informativeness": round(info, 4), "request_text": text})
    return out
