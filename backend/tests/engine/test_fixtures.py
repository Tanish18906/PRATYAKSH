"""Fixture builder checks (Phase 0). Expected values come from docs/04_TEST_PLAN.md section 2 and 3."""
import copy
import json
import re
from pathlib import Path

import pytest

from app.common.sketch import IDENTIFIER_COLUMNS
from tests.fixtures.mini import NAMES, build

FIXDIR = Path(__file__).resolve().parents[1] / "fixtures"
TOP_KEYS = {
    "contract_version", "id", "archetype", "seed", "params", "company", "now_ts", "locations",
    "log_sources", "actors", "datasets", "events", "artifacts", "canary_registry", "leak_sample",
    "discovery",
}
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FORBIDDEN = {"truth", "raw", "case_key", "true_path", "dropped"}  # "rows" is a required Event field, see QUESTIONS.md


def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def check_sketch(sk):
    assert len(sk["hashes"]) <= sk["k"]
    assert sk["distinct"] >= len(sk["hashes"])
    assert sk["hashes"] == sorted(sk["hashes"])
    assert all(re.fullmatch(r"[0-9a-f]{16}", h) for h in sk["hashes"])


@pytest.mark.parametrize("name", NAMES)
def test_scenario_is_structurally_valid(name):
    sc = build(name)
    assert set(sc) == TOP_KEYS
    assert sc["contract_version"] == "1.0"
    assert FORBIDDEN.isdisjoint(set(walk(sc)))
    loc_ids = {l["id"] for l in sc["locations"]}
    src_ids = {s["id"] for s in sc["log_sources"]}
    actor_ids = {a["id"] for a in sc["actors"]}
    art_ids = {a["id"] for a in sc["artifacts"]}
    ds_ids = {d["id"] for d in sc["datasets"]}
    assert len(art_ids) == len(sc["artifacts"])
    for s in sc["log_sources"]:
        assert s["location"] in loc_ids
    for l in sc["locations"]:
        assert l["log_source"] is None or l["log_source"] in src_ids
    last_seq, last_ts, ev_ids = {}, {}, set()
    for e in sc["events"]:
        assert TS_RE.match(e["ts"])
        assert e["id"] not in ev_ids
        ev_ids.add(e["id"])
        assert e["source"] in src_ids and e["actor"] in actor_ids
        assert e["object"] in ds_ids | art_ids
        for k in ("from_loc", "to_loc"):
            assert e[k] is None or e[k] in loc_ids
        assert e["seq"] > last_seq.get(e["source"], 0)
        assert e["ts"] >= last_ts.get(e["source"], "")
        last_seq[e["source"]], last_ts[e["source"]] = e["seq"], e["ts"]
    keys = [(e["ts"], e["id"]) for e in sc["events"]]
    assert keys == sorted(keys)
    for a in sc["artifacts"]:
        assert a["created_by"] in actor_ids and a["location"] in loc_ids and a["dataset"] in ds_ids
        assert TS_RE.match(a["created_ts"]) and TS_RE.match(a["newest_record_ts"])
        assert set(a["sketches"]) == set(IDENTIFIER_COLUMNS)
        for sk in a["sketches"].values():
            check_sketch(sk)
    leak = sc["leak_sample"]
    assert leak["columns"] and leak["found_ts"] == sc["now_ts"]
    assert leak["found_at"] in loc_ids
    for sk in leak["sketches"].values():
        check_sketch(sk)
    reg = {c["id"] for c in sc["canary_registry"]}
    assert set(leak["canary_hits"]) <= reg
    for c in sc["canary_registry"]:
        assert c["export_id"] in art_ids
        assert all(re.fullmatch(r"[0-9a-f]{16}", h) for h in c["hashes"].values())


def test_names_and_committed_json_match_builder():
    assert NAMES == [f"H{i}" for i in range(1, 9)]
    for name in NAMES:
        on_disk = json.loads((FIXDIR / f"{name}.json").read_text())
        assert on_disk == build(name)


def test_build_is_deterministic():
    assert json.dumps(build("H1")) == json.dumps(build("H1"))


def test_h1_constants():
    sc = build("H1")
    e1, e2 = sc["artifacts"]
    assert (e1["id"], e1["created_ts"], e1["row_count"], e1["newest_record_ts"]) == (
        "art:E1", "2026-10-09T02:10:00Z", 1828, "2026-10-09T02:00:00Z")
    assert (e2["id"], e2["created_by"], e2["created_ts"], e2["row_count"], e2["newest_record_ts"]) == (
        "art:E2", "act:cat", "2026-10-09T02:40:00Z", 1829, "2026-10-09T02:30:00Z")
    assert e1["arrivals_per_hour"] == 2.0
    assert e1["format_profile"] == {
        "delimiter": ",", "quoting": "minimal", "header_case": "snake", "line_ending": "LF",
        "encoding": "utf-8", "null_token": "",
        "columns": {"phone": {"style": "e164_dash"}, "full_name": {"case": "title"},
                    "created_at": {"style": "iso"}},
    }
    assert e2["format_profile"]["delimiter"] == ";" and e2["format_profile"]["encoding"] == "utf-8-bom"
    leak = sc["leak_sample"]
    assert leak["columns"] == ["full_name", "phone", "policy_no", "created_at"]
    assert leak["row_count"] == 1828 and leak["found_ts"] == "2026-10-12T08:00:00Z"
    assert leak["found_at"] == "ext:telegram-leak-channel" and leak["masked_preview"] == []
    assert set(leak["sketches"]) == {"phone", "policy_no"}
    # leak is rows 1..1828 so its sketches equal E1's on shared columns
    assert leak["sketches"]["phone"] == e1["sketches"]["phone"]
    downloads = [e for e in sc["events"] if e["action"] == "download"]
    assert len(downloads) == 1
    d = downloads[0]
    assert (d["actor"], d["ts"], d["from_loc"], d["to_loc"], d["rows"], d["object"]) == (
        "act:ann", "2026-10-09T09:00:00Z", "sys:wh", "ep:ann", 1828, "art:E1")


def test_background_events_and_seq_contract():
    sc = build("H1")
    q = [e for e in sc["events"] if e["action"] == "query"]
    assert len(q) == 36
    ann = [e for e in q if e["actor"] == "act:ann"]
    assert [e["rows"] for e in ann] == [150, 220, 310, 180, 260, 200] * 2
    assert ann[0]["ts"] == "2026-09-14T10:00:00Z" and ann[-1]["ts"] == "2026-10-06T10:00:00Z"
    assert all(e["source"] == "src:wh" and e["to_loc"] is None and e["object"] == "ds:cust" for e in q)
    wh = [e["seq"] for e in sc["events"] if e["source"] == "src:wh"]
    assert wh == list(range(1, len(wh) + 1))  # no gaps
    assert len(wh) > 20
    assert sum(1 for e in sc["events"] if e["source"] == "src:db") == 2 < 20
    ids = [e["id"] for e in sc["events"]]
    assert ids == [f"evt:{n:06d}" for n in range(1, len(ids) + 1)]


def test_locations_actors_match_plan():
    sc = build("H1")
    loc = {l["id"]: l for l in sc["locations"]}
    assert set(loc) == {"sys:db", "sys:wh", "sys:sftp", "sys:bucket", "ep:ann", "ep:bob", "ep:cat",
                        "ext:telegram-leak-channel", "ext:vendor-x"}
    assert {k for k, v in loc.items() if v["egress_capable"]} == {"sys:sftp", "sys:bucket", "ep:ann", "ep:bob", "ep:cat"}
    assert loc["ep:ann"]["owner_actor"] == "act:ann" and loc["ep:ann"]["log_source"] is None
    assert loc["sys:wh"]["log_source"] == "src:wh"
    acc = {a["id"]: a["access"] for a in sc["actors"]}
    assert acc["act:cat"] == ["sys:wh", "sys:bucket", "ep:cat"]
    assert acc["act:key1"] == ["sys:wh", "sys:sftp"]
    assert [d["arrivals_per_hour"] for d in sc["datasets"]] == [2.0]


def test_h2_h3_h4_h5_h7_shapes():
    h2 = build("H2")
    mv = [e for e in h2["events"] if e["action"] in ("copy", "download")]
    assert [(e["action"], e["actor"], e["from_loc"], e["to_loc"], e["source"]) for e in mv] == [
        ("copy", "act:etl", "sys:wh", "sys:bucket", "src:wh"),
        ("download", "act:bob", "sys:bucket", "ep:bob", "src:bucket"),
        ("download", "act:cat", "sys:bucket", "ep:cat", "src:bucket"),
    ]
    h3 = build("H3")
    assert h3["leak_sample"]["format_profile"]["columns"]["phone"] == {"style": "digits10"}
    assert [a["row_count"] for a in h3["artifacts"]] == [1828, 1012]
    h4 = build("H4")
    assert h4["leak_sample"]["row_count"] == 182
    assert h4["leak_sample"]["newest_record_ts"] == "2026-10-08T22:00:00Z"
    assert [a["row_count"] for a in h4["artifacts"]] == [1828, 1876]
    h5 = build("H5")
    assert not [e for e in h5["events"] if e["action"] == "download"]
    big = [e for e in h5["events"] if e["rows"] == 20000]
    assert [(e["actor"], e["ts"]) for e in big] == [("act:ann", "2026-10-09T09:00:00Z"), ("act:bob", "2026-10-09T09:10:00Z")]
    h7 = build("H7")
    assert h7["leak_sample"]["row_count"] == 400
    assert h7["leak_sample"]["newest_record_ts"] == "2026-10-01T00:00:00Z"
    h1 = build("H1")
    assert h7["leak_sample"]["sketches"]["phone"]["hashes"] != h1["leak_sample"]["sketches"]["phone"]["hashes"]


def test_h6_canaries_and_run_b_is_a_mutation():
    sc = build("H6")
    assert sc["params"]["canary_mode"] is True
    assert {c["id"]: c["export_id"] for c in sc["canary_registry"]} == {"can:E1-1": "art:E1", "can:E2-1": "art:E2"}
    assert {a["id"]: a["canary_ids"] for a in sc["artifacts"]} == {"art:E1": ["can:E1-1"], "art:E2": ["can:E2-1"]}
    assert sc["leak_sample"]["canary_hits"] == ["can:E2-1"]
    dl = {e["actor"]: e["object"] for e in sc["events"] if e["action"] == "download"}
    assert dl == {"act:ann": "art:E1", "act:bob": "art:E2"}
    run_b = copy.deepcopy(sc)
    run_b["leak_sample"]["canary_hits"] = []
    assert build("H6")["leak_sample"]["canary_hits"] == ["can:E2-1"]  # builder output not shared/mutated


def test_h8_is_h1_with_ids_renamed():
    h1, h8 = build("H1"), build("H8")
    ren = {"art:E1": "art:E7", "art:E2": "art:E3"}

    def sub(o):
        if isinstance(o, dict):
            return {k: sub(v) for k, v in o.items()}
        if isinstance(o, list):
            return [sub(v) for v in o]
        return ren.get(o, o) if isinstance(o, str) else o

    expected = sub(h1)
    expected["id"] = h8["id"]
    expected["leak_sample"]["id"] = h8["leak_sample"]["id"]
    assert h8 == expected
    assert [a["id"] for a in h8["artifacts"]] == ["art:E7", "art:E3"]
    assert "art:E1" not in json.dumps(h8) and "art:E2" not in json.dumps(h8)
