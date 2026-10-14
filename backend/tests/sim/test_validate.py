from copy import deepcopy

import pytest

from scripts.validate import validate_public_scenario, validate_trace


def scenario():
    profile = {"delimiter": ",", "quoting": "minimal", "header_case": "snake",
               "line_ending": "LF", "encoding": "utf-8", "null_token": "",
               "columns": {"phone": {"style": "digits10"}}}
    sketch = {"k": 512, "distinct": 1, "hashes": ["0000000000000001"]}
    return {
        "contract_version": "1.0", "id": "scn:A1-1-L0", "archetype": "A1", "seed": 1,
        "params": {"log_loss": 0.0, "canary_mode": False, "scale": "bench"},
        "company": "Nova Health", "now_ts": "2026-10-12T08:30:00Z",
        "locations": [
            {"id": "sys:db", "kind": "system", "name": "DB", "owner_actor": None,
             "monitored": True, "log_source": "src:db", "egress_capable": False},
            {"id": "ext:telegram-leak-channel", "kind": "external", "name": "Mock channel",
             "owner_actor": None, "monitored": False, "log_source": None, "egress_capable": False},
        ],
        "log_sources": [{"id": "src:db", "name": "DB audit", "location": "sys:db"}],
        "actors": [{"id": "act:etl", "kind": "service", "name": "etl", "role": "service",
                    "team": "Platform", "access": ["sys:db"]}],
        "datasets": [{"id": "ds:customers", "name": "Customers", "system": "sys:db",
                      "columns": ["phone"], "identifier_columns": ["phone"],
                      "row_count": 1, "sensitivity": "high", "arrivals_per_hour": 1.0}],
        "events": [{"id": "evt:000001", "ts": "2026-10-09T02:10:00Z", "seq": 1,
                    "source": "src:db", "actor": "act:etl", "action": "export",
                    "object": "ds:customers", "from_loc": "sys:db", "to_loc": "sys:db",
                    "rows": 1, "meta": {"artifact_id": "art:E1"}}],
        "artifacts": [{"id": "art:E1", "dataset": "ds:customers", "created_by": "act:etl",
                       "created_ts": "2026-10-09T02:10:00Z", "location": "sys:db",
                       "columns": ["phone"], "row_count": 1, "filter_desc": "all",
                       "format_profile": profile, "sketches": {"phone": sketch},
                       "newest_record_ts": "2026-10-09T02:00:00Z",
                       "arrivals_per_hour": 1.0, "canary_ids": []}],
        "canary_registry": [],
        "leak_sample": {"id": "leak:A1-1", "found_at": "ext:telegram-leak-channel",
                        "found_ts": "2026-10-12T08:30:00Z", "file_name": "demo.csv",
                        "columns": ["phone"], "row_count": 1, "format_profile": profile,
                        "sketches": {"phone": sketch}, "newest_record_ts": "2026-10-09T02:00:00Z",
                        "masked_preview": [], "canary_hits": []},
        "discovery": {"platform": "telegram-mock",
                      "channel": {"name": "Demo", "handle": "@demo", "members": 1},
                      "messages": [{"id": 1, "ts": "2026-10-10T22:30:00Z", "sender": "@demo",
                                    "text": "demo", "attachment": {"file_name": "demo.csv",
                                                                    "size_bytes": 62, "rows_hint": 1}}],
                      "leak_message_id": 1},
    }


def test_public_scenario_validation():
    public = scenario()
    validate_public_scenario(public)
    bad = deepcopy(public)
    bad["events"][0]["source"] = "src:missing"
    with pytest.raises(ValueError):
        validate_public_scenario(bad)
    bad = deepcopy(public)
    bad["artifacts"][0]["sketches"]["phone"]["hashes"] = ["NOT-HEX"]
    with pytest.raises(ValueError):
        validate_public_scenario(bad)
    bad = deepcopy(public)
    bad["case_key"] = "secret"
    with pytest.raises(ValueError):
        validate_public_scenario(bad)


def test_trace_validation():
    public = scenario()
    trace = {"contract_version": "1.0", "scenario_id": public["id"],
             "trace_id": "trc:A1-1-L0", "engine_version": "test", "origin_pinned": False,
             "origin_candidates": [{"artifact_id": "art:E1", "verdict": "candidate",
                                    "exclusion_rule": None, "containment": 1.0,
                                    "specificity": 1.0, "format_sim": 1.0,
                                    "watermark_term": 0.0, "origin_fit": 1.0, "notes": []}],
             "hypotheses": [], "actor_ranking": [], "location_ranking": [],
             "chokepoints": [], "recommended_evidence": [], "loss_estimates": {},
             "graph": {"nodes": [], "edges": []}, "notes": []}
    validate_trace(trace, public)
    trace["graph"]["edges"] = [{"id": "edge:1", "from": "missing", "to": "also-missing",
                                 "kind": "inferred", "ts": None, "event_id": None,
                                 "path_ids": [], "label": "hidden"}]
    with pytest.raises(ValueError):
        validate_trace(trace, public)
