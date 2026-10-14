import math
from statistics import mean

from app.config import ENGINE as CFG
from app.engine.anomaly import Anomaly
from app.engine.index import Index
from tests.fixtures.mini import build


def add_event(sc, **kw):
    n = len(sc["events"]) + 1000
    e = {"id": f"evt:{n:06d}", "ts": "2026-10-09T09:00:00Z", "seq": 10_000 + n, "source": "src:wh",
         "actor": "act:ann", "action": "download", "object": "art:E1", "from_loc": "sys:wh",
         "to_loc": "ep:ann", "rows": 1000, "meta": {}}
    e.update(kw)
    sc["events"].append(e)
    return e


def score(sc, e):
    return Anomaly(Index(sc)).event(e)


def test_h1_download_vs_own_baseline():
    sc = build("H1")
    e = next(x for x in sc["events"] if x["action"] == "download")
    r = score(sc, e)
    ann_x = [math.log(1 + x["rows"]) for x in sc["events"] if x["actor"] == "act:ann" and x["action"] == "query"]
    assert r["n_baseline"] == 12 and abs(r["mu"] - mean(ann_x)) < 1e-9
    assert r["z"] == CFG["Z_CAP"] and r["off"] == 0 and r["first"] == 1 and r["priv"] == 0
    assert abs(r["score"] - (CFG["Z_CAP"] + CFG["FIRST_TIME_W"])) < 1e-9


def test_leave_one_out_and_window():
    sc = build("H1")
    e = next(x for x in sc["events"] if x["actor"] == "act:ann" and x["ts"] == "2026-10-06T10:00:00Z")
    r = score(sc, e)
    # ann queries on 09-14 .. 10-04 are in the 30 day window before 10-06; the event itself is not
    assert r["n_baseline"] == 11
    assert r["first"] == 0  # same action and from_loc earlier


def test_fallback_to_role_peers_then_default():
    sc = build("H1")
    sc["events"] = [x for x in sc["events"] if x["actor"] != "act:bob"]
    e = add_event(sc, actor="act:bob", from_loc="sys:wh", to_loc="ep:bob", rows=5000)
    r = score(sc, e)  # bob has no history: role "analyst" peers (ann) are used
    peers = [math.log(1 + x["rows"]) for x in sc["events"]
             if x["actor"] == "act:ann" and x["rows"] > 0 and "2026-09-09T09:00:00Z" <= x["ts"] < e["ts"]]
    assert r["n_baseline"] == len(peers) and abs(r["mu"] - mean(peers)) < 1e-9
    sc2 = build("H1")
    e2 = add_event(sc2, actor="act:key1", rows=5000, from_loc="sys:wh", to_loc="sys:sftp")
    r2 = score(sc2, e2)  # service peers: only etl's single export, below the minimum
    assert r2["mu"] == CFG["DEFAULT_MU"] and r2["sigma"] == CFG["DEFAULT_SIGMA"]


def test_sigma_floor():
    sc = build("H1")
    r = score(sc, next(x for x in sc["events"] if x["action"] == "download"))
    assert r["sigma"] >= CFG["SIGMA_FLOOR"]


def test_off_hours_users_only():
    sc = build("H1")
    user = add_event(sc, ts="2026-10-09T23:00:00Z")
    svc = add_event(sc, ts="2026-10-09T23:00:00Z", actor="act:etl", from_loc="sys:db", to_loc="sys:wh")
    early = add_event(sc, ts="2026-10-09T04:59:59Z")
    sat = add_event(sc, ts="2026-10-10T12:00:00Z")  # Saturday
    day = add_event(sc, ts="2026-10-09T05:00:00Z")
    a = Anomaly(Index(sc))
    assert [a.event(x)["off"] for x in (user, svc, early, sat, day)] == [1, 0, 1, 1, 0]


def test_first_time_flag():
    sc = build("H1")
    first = add_event(sc, ts="2026-10-09T09:00:00Z", rows=100)
    second = add_event(sc, ts="2026-10-09T10:00:00Z", rows=100)
    a = Anomaly(Index(sc))
    assert a.event(first)["first"] == 1 and a.event(second)["first"] == 0


def test_privilege_grant_flag():
    def priv(meta, ts="2026-10-05T09:00:00Z"):
        sc = build("H1")
        add_event(sc, ts=ts, actor="act:cat", action="permission_change", object="ds:cust",
                  from_loc=None, to_loc=None, rows=0, meta=meta, source="src:wh")
        e = add_event(sc, ts="2026-10-09T09:00:00Z", rows=100)
        return score(sc, e)["priv"]

    base = {"grantee": "act:ann", "change": "grant"}
    assert priv({**base, "scope": "sys:wh"}) == 1
    assert priv(base) == 1                                  # scope null counts
    assert priv({**base, "scope": "sys:bucket"}) == 0
    assert priv({**base, "scope": "sys:wh", "change": "revoke"}) == 0
    assert priv({**base, "scope": "sys:wh"}, ts="2026-09-30T09:00:00Z") == 0  # outside 7 days
    assert priv({"grantee": "act:bob", "change": "grant", "scope": "sys:wh"}) == 0
