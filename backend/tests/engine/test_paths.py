from app.config import ENGINE as CFG
from app.engine.index import Index
from app.engine.loss import estimate_loss
from app.engine.paths import find_paths
from tests.fixtures.mini import build

FOUND_AT = "ext:telegram-leak-channel"


def paths_for(sc, art_id="art:E1"):
    idx = Index(sc)
    leak = sc["leak_sample"]
    return find_paths(idx, idx.artifact[art_id], estimate_loss(sc), leak["found_at"], leak["found_ts"])


def sig(p):
    return [(h["kind"], h["from_loc"], h["to_loc"], h["actor"]) for h in p["hops"]]


def test_all_paths_reach_leak_and_respect_limits():
    for name in ("H1", "H2", "H5"):
        out, _ = paths_for(build(name))
        assert out
        for p in out:
            hops = p["hops"]
            assert hops[-1]["to_loc"] == FOUND_AT
            assert sum(h["kind"] == "inferred" for h in hops) <= CFG["MAX_HIDDEN"]
            assert len(hops) <= CFG["MAX_DEPTH"]
            locs = [hops[0]["from_loc"]] + [h["to_loc"] for h in hops]
            assert len(set(locs)) == len(locs)  # no revisits
            for a, b in zip(hops, hops[1:]):
                assert a["to_loc"] == b["from_loc"]
                if a["ts"] and b["ts"]:
                    assert a["ts"] <= b["ts"]


def test_observed_move_suppresses_matching_hidden_download():
    out, _ = paths_for(build("H1"))
    sigs = [sig(p) for p in out]
    assert [("observed", "sys:wh", "ep:ann", "act:ann"), ("inferred", "ep:ann", FOUND_AT, "act:ann")] in sigs
    # M3 hidden download by ann from sys:wh would duplicate the observed one
    assert not any(s[0] == ("inferred", "sys:wh", "ep:ann", "act:ann") for s in sigs)
    # but other holders of wh access get hidden downloads
    assert [("inferred", "sys:wh", "ep:bob", "act:bob"), ("inferred", "ep:bob", FOUND_AT, "act:bob")] in sigs


def test_observed_moves_follow_time_order():
    sc = build("H1")
    dl = next(e for e in sc["events"] if e["action"] == "download")
    dl["ts"] = "2026-10-09T02:00:00Z"  # before E1 existed
    out, _ = paths_for(sc)
    assert not any(h["kind"] == "observed" for p in out for h in p["hops"])


def test_observed_move_after_found_is_ignored():
    sc = build("H1")
    dl = next(e for e in sc["events"] if e["action"] == "download")
    dl["ts"] = "2026-10-12T09:00:00Z"
    out, _ = paths_for(sc)
    assert not any(h["kind"] == "observed" for p in out for h in p["hops"])


def test_hidden_hop_cost_uses_loss_estimate():
    out, _ = paths_for(build("H1"))
    p = next(p for p in out if sig(p)[0] == ("inferred", "sys:wh", "ep:bob", "act:bob"))
    # sys:wh is a well observed source: -ln(0.05) + 1.0, then endpoint 0.5
    assert abs(p["cost"] - (3.9957 + 0.5)) < 1e-3
    assert p["hops"][0]["est_loss"] == 0.05 and p["hops"][1]["est_loss"] is None
    assert all(h["ts"] is None for h in p["hops"])


def test_m4_hidden_copy_between_systems():
    out, _ = paths_for(build("H1"))
    assert any(h["kind"] == "inferred" and h["from_loc"] == "sys:wh" and h["to_loc"] == "sys:bucket"
               for p in out for h in p["hops"])


def test_m4_not_used_when_observed_copy_exists():
    out, _ = paths_for(build("H2"))
    assert not any(h["kind"] == "inferred" and h["from_loc"] == "sys:wh" and h["to_loc"] == "sys:bucket"
                   for p in out for h in p["hops"])


def test_fallback_when_no_path_exists():
    sc = build("H1")
    sc["actors"] = [a for a in sc["actors"] if a["id"] == "act:etl"]  # nobody else can touch the file
    sc["events"] = [e for e in sc["events"] if e["actor"] == "act:etl"]
    for loc in sc["locations"]:
        loc["egress_capable"] = False
    out, notes = paths_for(sc)
    assert len(out) == 1 and len(out[0]["hops"]) == 1
    hop = out[0]["hops"][0]
    assert (hop["kind"], hop["from_loc"], hop["to_loc"], hop["actor"]) == ("inferred", "sys:wh", FOUND_AT, "act:etl")
    assert abs(out[0]["cost"] - (CFG["UNKNOWN_CHANNEL"] + CFG["H_BASE"])) < 1e-9
    assert any("No custody path found" in n for n in notes)


def test_zero_events_scenario_returns_fallback():
    sc = build("H1")
    sc["events"] = []
    out, notes = paths_for(sc)
    assert out and notes is not None
