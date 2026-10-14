"""Per-source loss estimate from seq gaps (docs/03_ENGINE.md section 4).

Known bias: events dropped at the very end of a source's stream leave no visible gap.
"""
from app.config import ENGINE as CFG


def estimate_loss(scenario: dict) -> dict:
    seqs = {s["id"]: [] for s in scenario["log_sources"]}
    for e in scenario["events"]:
        seqs.setdefault(e["source"], []).append(e["seq"])
    out = {}
    for src, qs in seqs.items():
        if len(qs) < CFG["LOSS_MIN_EVENTS"]:
            p = CFG["LOSS_DEFAULT"]
        else:
            expected = max(qs) - min(qs) + 1
            p = (expected - len(qs)) / expected
        out[src] = round(min(max(p, CFG["LOSS_FLOOR"]), CFG["LOSS_CEIL"]), 4)
    return out
