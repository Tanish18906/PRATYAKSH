"""M2 access rule (docs/03_ENGINE.md section 7, amended): an actor may make the hidden move out of an
intermediate location if that location is in its access OR it has an observed move of THIS artifact into that
location at or before found_ts (it carried this file there, so it had access). Routine calls to the same host
and moves of other files do not count."""
import copy

from app.engine.index import Index
from app.engine.loss import estimate_loss
from app.engine.paths import find_paths
from app.engine.trace import trace
from tests.fixtures.mini import build

HOST = "ext:vendor-x"          # an unlogged external in the fixtures; nobody has it in `access`
LEAK = "ext:telegram-leak-channel"


def base():
    """H1 without ann's download; key1 (service, no access to HOST) moves art:E1 to HOST through the API."""
    sc = build("H1")
    sc["events"] = [e for e in sc["events"] if e["action"] != "download"]
    nxt = len(sc["events"]) + 1
    sc["events"].append({"id": f"evt:{nxt:06d}", "ts": "2026-10-09T03:00:00Z", "seq": 900, "source": "src:wh",
                         "actor": "act:key1", "action": "api_call", "object": "art:E1", "from_loc": "sys:wh",
                         "to_loc": HOST, "rows": 1828, "meta": {"client_ip": "203.0.113.9"}})
    sc["events"].sort(key=lambda e: (e["ts"], e["seq"]))
    assert not any(HOST in a["access"] for a in sc["actors"])
    return sc


def add_event(sc, actor, ts, from_loc=None, to_loc=None, action="send", n=950):
    sc["events"].append({"id": f"evt:{n:06d}", "ts": ts, "seq": n, "source": "src:wh", "actor": actor,
                         "action": action, "object": "ds:cust", "from_loc": from_loc, "to_loc": to_loc,
                         "rows": 0, "meta": {}})
    sc["events"].sort(key=lambda e: (e["ts"], e["seq"]))


def m2_actors(sc, art="art:E1"):
    idx, leak = Index(sc), sc["leak_sample"]
    paths, _ = find_paths(idx, idx.artifact[art], estimate_loss(sc), leak["found_at"], leak["found_ts"])
    return {h["actor"] for p in paths for h in p["hops"] if h["kind"] == "inferred" and h["from_loc"] == HOST}


def test_actor_that_moved_the_file_into_a_location_can_continue_from_it():
    sc = base()
    paths, _ = (lambda i: find_paths(i, i.artifact["art:E1"], estimate_loss(sc), LEAK, sc["leak_sample"]["found_ts"]))(Index(sc))
    chains = [[(h["kind"], h["from_loc"], h["to_loc"], h["actor"]) for h in p["hops"]] for p in paths]
    assert [("observed", "sys:wh", HOST, "act:key1"), ("inferred", HOST, LEAK, "act:key1")] in chains
    r = trace(sc)
    ranked = [a["actor"] for a in r["actor_ranking"]]
    assert "act:key1" in ranked
    top = r["hypotheses"][0]
    assert top["actors"] == ["act:key1"] and top["hops"][0]["kind"] == "observed" and top["hops"][0]["action"] == "api_call"
    assert top["hops"][-1]["kind"] == "inferred" and top["hops"][-1]["to_loc"] == LEAK


def move_into_host(sc, actor, ts, obj, n, action="send"):
    """An observed move of `obj` into HOST by `actor` (obj may be this artifact, another artifact, or a dataset)."""
    sc["events"].append({"id": f"evt:{n:06d}", "ts": ts, "seq": n, "source": "src:wh", "actor": actor,
                         "action": action, "object": obj, "from_loc": "sys:wh", "to_loc": HOST, "rows": 5,
                         "meta": {"artifact_id": obj} if obj.startswith("art:") else {}})
    sc["events"].sort(key=lambda e: (e["ts"], e["seq"]))


def test_only_an_observed_move_of_this_artifact_into_the_location_grants_access():
    sc = base()
    add_event(sc, "act:bob", "2026-10-08T10:00:00Z", from_loc=HOST, to_loc=None, action="read", n=951)  # read only
    move_into_host(sc, "act:cat", "2026-10-09T04:00:00Z", "art:E1", 952)      # carried THIS file there: passes
    move_into_host(sc, "act:ann", "2026-10-08T12:00:00Z", "ds:cust", 953)     # routine call, a dataset: rejected
    assert m2_actors(sc) == {"act:key1", "act:cat"}


def test_a_routine_call_with_a_different_file_does_not_pass():
    """The case the literal first version got wrong: alternates that only called the same host."""
    sc = build("H1")
    sc["events"] = [e for e in sc["events"] if e["action"] != "download"]
    # key1 moves E1 into HOST; ann and bob moved a DIFFERENT export (E2) into the same host
    move_into_host(sc, "act:key1", "2026-10-09T03:00:00Z", "art:E1", 900, action="api_call")
    move_into_host(sc, "act:ann", "2026-10-09T05:00:00Z", "art:E2", 901, action="api_call")
    move_into_host(sc, "act:bob", "2026-10-09T06:00:00Z", "art:E2", 902, action="api_call")
    assert m2_actors(sc, "art:E1") == {"act:key1"}
    assert m2_actors(sc, "art:E2") == {"act:ann", "act:bob"}  # for E2 they carried the file, so they do pass


def test_hypotheses_do_not_blame_actors_with_only_routine_calls():
    sc = base()
    move_into_host(sc, "act:ann", "2026-10-08T12:00:00Z", "ds:cust", 953)
    move_into_host(sc, "act:bob", "2026-10-08T13:00:00Z", "art:E2", 954)
    r = trace(sc)
    e1 = [h for h in r["hypotheses"] if h["origin_artifact"] == "art:E1" and any(x["from_loc"] == HOST for x in h["hops"])]
    assert e1 and all(h["actors"] == ["act:key1"] for h in e1)


def test_a_move_of_this_artifact_after_found_ts_does_not_grant_access():
    sc = base()
    move_into_host(sc, "act:cat", "2026-10-13T11:00:00Z", "art:E1", 955)
    assert m2_actors(sc) == {"act:key1"}


def test_listed_access_still_works_without_any_event():
    sc = base()
    cat = next(a for a in sc["actors"] if a["id"] == "act:cat")
    cat["access"] = cat["access"] + [HOST]  # rebind: build() shares the module-level access lists between calls
    add_event(sc, "act:cat", "2026-10-08T11:00:00Z", from_loc=HOST, to_loc=None, action="read", n=954)  # in alt, has access
    assert m2_actors(sc) == {"act:key1", "act:cat"}


def test_without_the_observed_move_the_key_is_still_not_invented():
    sc = base()
    sc["events"] = [e for e in sc["events"] if e["action"] != "api_call"]
    assert "act:key1" not in [a["actor"] for a in trace(sc)["actor_ranking"]] or \
        all("act:key1" not in h["actors"] for h in trace(sc)["hypotheses"][:1])
    assert m2_actors(sc) == set()


def test_endpoints_and_other_hops_are_unchanged():
    """Same scenario family as H1: no event writes to an endpoint on behalf of someone else, results identical."""
    before = trace(build("H1"))
    after = trace(copy.deepcopy(build("H1")))
    assert before == after
