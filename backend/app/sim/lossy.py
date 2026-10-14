"""Per-source event sequencing and simulated log loss."""

from collections import defaultdict

from .base_table import seeded_rng


def new_event(ts: str, actor: str, action: str, object_id: str | None,
              from_loc: str | None, to_loc: str | None, rows: int = 0,
              meta: dict | None = None, source: str | None = None) -> dict:
    if source is None:
        logged = next((loc for loc in (from_loc, to_loc) if loc and loc.startswith("sys:")), None)
        if logged is None:
            raise ValueError("events without a logged system cannot be generated")
        source = "src:" + logged[4:]
    return {"id": "", "ts": ts, "seq": 0, "source": source, "actor": actor,
            "action": action, "object": object_id, "from_loc": from_loc,
            "to_loc": to_loc, "rows": int(rows), "meta": meta or {}}


def assign_and_drop(events: list[dict], seed: int, log_loss: float,
                    critical: dict | None = None, preserve_critical: bool | None = None):
    if not 0 <= log_loss <= 0.8:
        raise ValueError("log_loss must be between 0 and 0.8")
    rng = seeded_rng("loss", seed)
    sources = sorted({event["source"] for event in events})
    rates = {source: min(0.9, max(0.0, log_loss +
             (float(rng.uniform(-0.05, 0.05)) if log_loss else 0.0))) for source in sources}
    force_critical = log_loss > 0 and rng.random() < 0.5
    ordered = sorted(events, key=lambda event: (event["ts"], event["source"], event["actor"],
                                                event["action"], event["object"] or ""))
    sequences = defaultdict(int)
    kept = []
    dropped_ids = []
    for number, event in enumerate(ordered, 1):
        sequences[event["source"]] += 1
        event["id"] = f"evt:{number:06d}"
        event["seq"] = sequences[event["source"]]
        drop = rng.random() < rates[event["source"]]
        if event is critical:
            if preserve_critical is True:
                drop = False
            elif preserve_critical is False:
                drop = True
            else:
                drop |= force_critical
        if drop:
            dropped_ids.append(event["id"])
        else:
            kept.append(event)
    kept.sort(key=lambda event: (event["ts"], event["seq"]))
    return kept, dropped_ids
