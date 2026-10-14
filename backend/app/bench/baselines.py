"""Naive baselines (docs/04_TEST_PLAN.md section 6.3). Each takes a PublicScenario dict and returns ids, best first.

Ties keep the scenario's own order. Origin baselines only consider exports created at or before found_ts.
"""
from collections import defaultdict

MOVE_ACTIONS = {"export", "download", "copy", "send", "api_call", "upload"}


def _arts(sc: dict) -> list:
    found = sc["leak_sample"]["found_ts"]
    return [a for a in sc["artifacts"] if a["created_ts"] <= found]


def largest_export(sc: dict) -> list:  # B3
    return [a["id"] for a in sorted(_arts(sc), key=lambda a: -a["row_count"])]


def most_recent_export(sc: dict) -> list:  # B4
    return [a["id"] for a in sorted(_arts(sc), key=lambda a: a["created_ts"], reverse=True)]


def last_accessor(sc: dict) -> list:  # B1
    found = sc["leak_sample"]["found_ts"]
    data = {d["id"] for d in sc["datasets"] if d["name"] == "customers"} | {"ds:customers"}
    last = {}
    for e in sc["events"]:
        if e["ts"] <= found and (e["object"] in data or e["object"].startswith("art:")):
            last[e["actor"]] = max(last.get(e["actor"], ""), e["ts"])
    return [a["id"] for a in sorted(sc["actors"], key=lambda a: last.get(a["id"], ""), reverse=True)]


def biggest_exporter(sc: dict) -> list:  # B2
    total = defaultdict(int)
    for e in sc["events"]:
        if e["action"] in MOVE_ACTIONS:
            total[e["actor"]] += e["rows"]
    return [a["id"] for a in sorted(sc["actors"], key=lambda a: -total[a["id"]])]
