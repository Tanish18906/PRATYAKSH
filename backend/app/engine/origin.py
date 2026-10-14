"""Stages 0 to 2: canary pin, hard rules, soft origin score (docs/03_ENGINE.md sections 5 and 6)."""
import math
from datetime import timedelta

from app.common.sketch import IDENTIFIER_COLUMNS, containment
from app.config import ENGINE as CFG
from app.engine.normalize import parse_ts

GLOBAL_ATTRS = ["delimiter", "quoting", "header_case", "line_ending", "encoding", "null_token"]
NUM_FIELDS = ("containment", "specificity", "format_sim", "watermark_term", "origin_fit")


def pin_canary(sc: dict) -> tuple:
    """Stage 0. Returns (pinned artifact id or None, notes)."""
    hits = sc["leak_sample"]["canary_hits"]
    if not hits:
        return None, []
    reg = {c["id"]: c["export_id"] for c in sc["canary_registry"]}
    arts = {a["id"]: a for a in sc["artifacts"]}
    counts, first, notes = {}, {}, []
    for h in hits:
        export = reg.get(h)
        if export not in arts:
            notes.append(f"Canary {h} is not in the registry and was ignored.")
            continue
        counts[export] = counts.get(export, 0) + 1
        first.setdefault(export, h)
    if not counts:
        return None, notes
    best = min(counts, key=lambda a: (-counts[a], arts[a]["created_ts"]))
    notes.append(f"Origin pinned by canary {first[best]} planted in {best}.")
    return best, notes


def format_counts(leak: dict, art: dict) -> tuple:
    """(matching attribute pairs, total pairs) behind format_sim."""
    lp, ep = leak["format_profile"], art["format_profile"]
    pairs = [(lp[k], ep[k]) for k in GLOBAL_ATTRS]
    for c in leak["columns"]:
        if c not in art["columns"]:
            continue
        lcol, ecol = lp["columns"].get(c, {}), ep["columns"].get(c, {})
        pairs += [(lcol[k], ecol.get(k)) for k in ("style", "case") if k in lcol]
    return sum(a == b for a, b in pairs), len(pairs)


def format_sim(leak: dict, art: dict) -> float:
    matches, total = format_counts(leak, art)
    return matches / total


def _score(leak: dict, art: dict) -> dict:
    cand = {"artifact_id": art["id"], "verdict": "candidate", "exclusion_rule": None,
            **{k: None for k in NUM_FIELDS}, "notes": []}
    shared = [c for c in IDENTIFIER_COLUMNS if c in leak["sketches"] and c in art["sketches"]]
    if shared:
        C = sum(containment(leak["sketches"][c], art["sketches"][c]) for c in shared) / len(shared)
    else:
        C = 0.05
    created, newest = parse_ts(art["created_ts"]), parse_ts(leak["newest_record_ts"])
    rule = note = None
    if set(leak["columns"]) - set(art["columns"]):
        rule, note = "schema", "The export lacks columns that appear in the leaked file."
    elif created < newest - timedelta(minutes=CFG["WM_TOLERANCE_MIN"]):
        rule, note = "watermark_before", "Created before the newest leaked record existed."
    elif created > parse_ts(leak["found_ts"]):
        rule, note = "after_found", "Created after the leak was found."
    if rule:
        cand.update(verdict="excluded", exclusion_rule=rule, notes=[note])
        if rule != "schema" and shared:
            cand["containment"] = C
        return cand
    if not shared:
        cand["notes"].append("no shared identifier columns; containment set to 0.05")
    ratio = min(max(leak["row_count"] / art["row_count"] if art["row_count"] else 0.0, 0.01), 1.0)
    fsim = format_sim(leak, art)
    gap_h = max(0.0, (created - newest).total_seconds() / 3600.0)
    wm = -min(art["arrivals_per_hour"] * gap_h, CFG["WM_CAP"]) if ratio >= CFG["WM_RATIO_MIN"] else 0.0
    fit = (CFG["W_CONTAINMENT"] * math.log(max(C, 0.001)) + CFG["W_SPECIFICITY"] * math.log(ratio)
           + CFG["W_FORMAT"] * fsim + wm)
    cand.update(containment=C, specificity=ratio, format_sim=fsim, watermark_term=wm, origin_fit=fit)
    return cand


def score_candidates(sc: dict) -> list:
    """All artifacts, unrounded: candidates by origin_fit desc, then excluded by created_ts."""
    created = {a["id"]: a["created_ts"] for a in sc["artifacts"]}
    rows = [_score(sc["leak_sample"], a) for a in sc["artifacts"]]
    ok = sorted((r for r in rows if r["verdict"] == "candidate"), key=lambda r: -r["origin_fit"])
    out = sorted((r for r in rows if r["verdict"] == "excluded"), key=lambda r: created[r["artifact_id"]])
    return ok + out


def public_row(cand: dict) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in cand.items()}


def candidate_table(sc: dict) -> list:
    return [public_row(c) for c in score_candidates(sc)]


def select_used(scored: list, pinned: str | None) -> list:
    """Artifact ids that go on to path search."""
    if pinned:
        return [pinned]
    ok = [c for c in scored
          if c["verdict"] == "candidate" and c["containment"] >= CFG["NO_MATCH_CONTAINMENT"]]
    if not ok:
        return []
    best = max(c["origin_fit"] for c in ok)
    keep = [c for c in ok if c["origin_fit"] >= best - CFG["ORIGIN_MARGIN"]]
    return [c["artifact_id"] for c in keep[:CFG["MAX_CANDIDATES"]]]
