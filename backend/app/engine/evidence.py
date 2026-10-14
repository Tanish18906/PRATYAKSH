"""Plain-English summary and evidence text (docs/03_ENGINE.md section 13).

Phase 1 scope: fingerprint, observed and inferred parts. Anomaly sentences arrive with stage 4.
Probabilities are relative likelihoods; nothing here claims certainty.
"""

VERBS = {"download": "downloaded", "copy": "copied", "upload": "uploaded", "send": "sent",
         "api_call": "pulled through the API"}


def _hop_text(idx, hop: dict) -> str:
    who, frm, to = idx.name(hop["actor"]), idx.name(hop["from_loc"]), idx.name(hop["to_loc"])
    if hop["kind"] == "observed":
        verb = VERBS.get(hop["action"], hop["action"])
        return f"{who} {verb} it from {frm} to {to} at {hop['ts']}."
    return f"A move from {frm} to {to} by {who} is inferred because no log was found."


def hypothesis_text(idx, art: dict, cand: dict, hops: list) -> tuple:
    """Returns (summary_text, evidence list) for one path."""
    pct = round(cand["containment"] * 100)
    creator = idx.name(art["created_by"])
    head = (f"{art['id']} (created by {creator} at {art['created_ts']}) is the likely source: "
            f"{pct}% of the leaked records are in it.")
    evidence = [{"kind": "fingerprint", "ts": art["created_ts"], "event_id": None,
                 "text": (f"{pct}% of the leaked identifiers appear in {art['id']}; "
                          f"format match {round(cand['format_sim'] * 100)}%; "
                          f"watermark term {cand['watermark_term']:.2f}.")}]
    parts = [head]
    for hop in hops:
        text = _hop_text(idx, hop)
        parts.append(text)
        evidence.append({"kind": hop["kind"], "text": text, "ts": hop["ts"], "event_id": hop["event_id"]})
    return " ".join(parts), evidence
