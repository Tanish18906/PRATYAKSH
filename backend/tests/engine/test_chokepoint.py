import copy

import pytest

from app.engine.chokepoint import chokepoints
from app.engine.index import Index
from app.engine.trace import trace
from tests.fixtures.mini import build

LEAK = "ext:telegram-leak-channel"


def hop(frm, to, actor, kind="inferred"):
    return {"from_loc": frm, "to_loc": to, "actor": actor, "kind": kind, "ts": None, "event_id": None,
            "action": None, "rows": None, "est_loss": None, "note": ""}


def path(prob, *hops, origin="art:E1"):
    return {"origin": origin, "prob": prob, "hops": list(hops)}


@pytest.fixture
def idx():
    sc = build("H2")
    sc["actors"].append({"id": "act:partner-api-key-7", "kind": "service", "name": "Partner key 7",
                         "role": "service", "team": "vendor", "access": ["sys:sftp"]})
    return Index(sc)


def test_greedy_order_and_cumulative_coverage(idx):
    paths = [path(0.4, hop("sys:wh", "ep:ann", "act:ann"), hop("ep:ann", LEAK, "act:ann")),
             path(0.3, hop("sys:wh", "sys:bucket", "act:bob"), hop("sys:bucket", "ep:bob", "act:bob"),
                  hop("ep:bob", LEAK, "act:bob")),
             path(0.3, hop("sys:wh", "sys:bucket", "act:bob"), hop("sys:bucket", LEAK, "act:cat"))]
    out = chokepoints(idx, paths, LEAK)
    # bob's permission on sys:wh sits on 0.6 of the mass, more than ann's 0.4
    assert out[0]["item_id"] == "perm:act:bob@sys:wh" and out[0]["marginal"] == 0.6
    assert out[0]["cumulative_coverage"] == 0.6
    assert out[1]["item_id"] in ("perm:act:ann@egress", "perm:act:ann@sys:wh")
    assert out[1]["marginal"] == 0.4 and out[1]["cumulative_coverage"] == 1.0
    assert [c["rank"] for c in out] == list(range(1, len(out) + 1))
    assert len(out) == 2  # nothing left uncovered


def test_ties_break_on_smaller_item_id(idx):
    paths = [path(1.0, hop("sys:wh", "ep:ann", "act:ann"), hop("ep:ann", LEAK, "act:ann"))]
    assert chokepoints(idx, paths, LEAK)[0]["item_id"] == "perm:act:ann@egress"


def test_marginal_counts_all_paths_but_selection_uses_uncovered(idx):
    paths = [path(0.5, hop("sys:wh", "ep:ann", "act:ann"), hop("ep:ann", LEAK, "act:ann")),
             path(0.25, hop("sys:wh", "ep:ann", "act:ann"), hop("ep:ann", "sys:bucket", "act:ann"),
                  hop("sys:bucket", LEAK, "act:bob")),
             path(0.25, hop("sys:wh", "ep:cat", "act:cat"), hop("ep:cat", LEAK, "act:cat"))]
    out = chokepoints(idx, paths, LEAK)
    assert out[0]["item_id"] == "perm:act:ann@egress" and out[0]["marginal"] == 0.75
    assert out[1]["item_id"] == "perm:act:cat@egress" and out[1]["marginal"] == 0.25
    assert out[1]["cumulative_coverage"] == 1.0


def test_item_types_and_texts(idx):
    paths = [path(0.1, hop("sys:wh", "ep:ann", "act:ann")),
             path(0.1, hop("ep:cat", LEAK, "act:cat")),
             path(0.1, hop("sys:sftp", LEAK, "act:partner-api-key-7")),
             path(0.1, hop("sys:wh", "ep:bob", "act:key1")),
             path(0.1, hop("ext:vendor-x", LEAK, "act:bob"))]
    # CHOKE_MAX limits the output, so ask for each item through its own single path
    singles = {}
    for p in paths:
        c = chokepoints(idx, [p], LEAK)[0]
        singles[c["item_id"]] = c
    a = singles["perm:act:ann@sys:wh"]
    assert a["item_type"] == "permission" and a["action_text"] == "Revoke Ann's access to wh"
    e = singles["perm:act:cat@egress"]
    assert e["item_type"] == "permission" and e["action_text"] == "Block outbound uploads from Cat's laptop"
    k = singles["perm:act:partner-api-key-7@sys:sftp"]
    assert k["item_type"] == "api_key" and k["action_text"] == "Rotate and revoke API key Partner key 7"
    s = singles["perm:act:key1@sys:wh"]
    assert s["item_type"] == "service_account" and s["action_text"] == "Suspend service account Key1 until reviewed"
    c = singles["ch:ext:vendor-x"]
    assert c["item_type"] == "channel" and c["action_text"] == "Block transfers to vendor-x"
    assert all(v["label"] == v["action_text"] for v in singles.values())


def test_service_creator_and_found_at_never_yield_items(idx):
    # art:E1 is created by act:etl (service): its hops produce no item; a hop leaving found_at is ignored
    paths = [path(1.0, hop("sys:wh", "sys:bucket", "act:etl"), hop("sys:bucket", LEAK, "act:etl"),
                  hop(LEAK, "ext:vendor-x", "act:ann"))]
    assert chokepoints(idx, paths, LEAK) == []


def test_choke_max_limits_output(idx):
    paths = [path(0.2, hop("sys:wh", "ep:ann", "act:ann"), hop("ep:ann", LEAK, "act:ann")),
             path(0.2, hop("sys:wh", "ep:bob", "act:bob"), hop("ep:bob", LEAK, "act:bob")),
             path(0.2, hop("sys:wh", "ep:cat", "act:cat"), hop("ep:cat", LEAK, "act:cat")),
             path(0.2, hop("sys:sftp", LEAK, "act:key1")),
             path(0.2, hop("ext:vendor-x", LEAK, "act:ann"))]
    assert len(chokepoints(idx, paths, LEAK)) == 3


def test_trace_h1_first_chokepoint_is_the_leaker():
    r = trace(build("H1"))
    c = r["chokepoints"][0]
    assert c["item_id"] in ("perm:act:ann@egress", "perm:act:ann@sys:wh")
    assert c["marginal"] > 0.9 and c["cumulative_coverage"] >= c["marginal"]
    cov = [x["cumulative_coverage"] for x in r["chokepoints"]]
    assert cov == sorted(cov) and cov[-1] <= 1.0001
    assert "etl" not in " ".join(x["item_id"] for x in r["chokepoints"])


def test_trace_h2_two_insiders_need_two_chokepoints():
    r = trace(build("H2"))
    ids = [c["item_id"] for c in r["chokepoints"][:2]]
    assert {i.split("@")[0] for i in ids} == {"perm:act:bob", "perm:act:cat"}
    assert r["chokepoints"][1]["cumulative_coverage"] > r["chokepoints"][0]["cumulative_coverage"] + 0.3


def test_trace_h7_has_none_and_pinned_works():
    assert trace(build("H7"))["chokepoints"] == []
    r = trace(build("H6"))
    assert r["chokepoints"] and r["chokepoints"][0]["item_id"].startswith("perm:act:bob@")


def test_contract_fields_and_rounding():
    r = trace(build("H5"))
    for c in r["chokepoints"]:
        assert set(c) == {"rank", "item_type", "item_id", "label", "marginal", "cumulative_coverage", "action_text"}
        assert c["marginal"] == round(c["marginal"], 4) and c["cumulative_coverage"] <= 1.0001
    assert trace(copy.deepcopy(build("H5")))["chokepoints"] == r["chokepoints"]
