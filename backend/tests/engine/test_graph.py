from app.engine.trace import trace
from tests.fixtures.mini import build


def test_graph_covers_every_hop_of_every_hypothesis():
    r = trace(build("H2"))
    g = r["graph"]
    nodes = {n["id"]: n for n in g["nodes"]}
    assert len(nodes) == len(g["nodes"]) and len({e["id"] for e in g["edges"]}) == len(g["edges"])
    assert all(e["from"] in nodes and e["to"] in nodes for e in g["edges"])
    for h in r["hypotheses"]:
        for hop in h["hops"]:
            match = [e for e in g["edges"] if e["from"] == hop["from_loc"] and e["to"] == hop["to_loc"]
                     and e["kind"] == hop["kind"] and e["event_id"] == hop["event_id"]
                     and h["path_id"] in e["path_ids"]]
            assert match, hop


def test_node_kinds_and_origin_edge():
    r = trace(build("H1"))
    g = r["graph"]
    nodes = {n["id"]: n for n in g["nodes"]}
    assert nodes["art:E1"]["kind"] == "artifact"
    assert nodes["sys:wh"]["kind"] == "system" and nodes["ep:ann"]["kind"] == "endpoint"
    assert nodes["ext:telegram-leak-channel"]["kind"] == "external"
    origin = next(e for e in g["edges"] if e["from"] == "art:E1")
    assert origin["to"] == "sys:wh" and origin["kind"] == "observed" and origin["label"] == "created by Etl"
    assert "hyp:1" in origin["path_ids"]


def test_edge_labels():
    g = trace(build("H1"))["graph"]
    obs = next(e for e in g["edges"] if e["kind"] == "observed" and e["to"] == "ep:ann")
    assert obs["label"] == "Ann: download, 1828 rows" and obs["event_id"]
    inf = next(e for e in g["edges"] if e["kind"] == "inferred" and e["from"] == "ep:ann")
    assert inf["label"] == "Ann: unlogged channel" and inf["ts"] is None
    logged = next(e for e in g["edges"] if e["kind"] == "inferred" and e["from"] == "sys:wh")
    assert "log missing" in logged["label"] and "5% of" in logged["label"]


def test_shared_edges_merge_path_ids():
    r = trace(build("H5"))
    edges = r["graph"]["edges"]
    assert any(len(e["path_ids"]) > 1 for e in edges)
    assert all(e["path_ids"] == sorted(set(e["path_ids"])) for e in edges)


def test_no_match_gives_empty_graph():
    g = trace(build("H7"))["graph"]
    assert g == {"nodes": [], "edges": []}
