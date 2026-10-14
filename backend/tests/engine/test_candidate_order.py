"""Candidate list order (docs/DECISIONS.md, engine override): score desc, then created_ts asc, row_count desc,
creator asc, artifact id asc as the very last resort. The id may order exact ties; it never moves a score."""
import copy
import json
import random

import pytest

from app.engine.origin import candidate_table, tie_key
from app.engine.trace import trace
from tests.fixtures.mini import build


def art(i, ts="2026-10-09T02:10:00Z", rows=100, by="act:etl"):
    return {"id": i, "created_ts": ts, "row_count": rows, "created_by": by}


def test_tie_key_precedence():
    items = [art("art:B"), art("art:W", by="act:ann"), art("art:X"), art("art:Y", rows=900),
             art("art:A"), art("art:V", by="act:bob"), art("art:Z", ts="2026-10-09T01:00:00Z")]
    random.Random(3).shuffle(items)
    # creation time first (Z), then more rows (Y), then creator ascending (ann, bob, etl), id only among equals
    assert [a["id"] for a in sorted(items, key=tie_key)] == [
        "art:Z", "art:Y", "art:W", "art:V", "art:A", "art:B", "art:X"]


def with_tied_copy(ids=("art:A", "art:B"), ts2="2026-10-09T02:10:00Z", by2="act:etl"):
    """H4-like (leak is 10 percent of the file so no watermark term): a copy of E1 that scores exactly the same."""
    sc = build("H4")
    e1 = next(a for a in sc["artifacts"] if a["id"] == "art:E1")
    sc["artifacts"] = [e1]
    twin = copy.deepcopy(e1)
    twin["created_ts"], twin["created_by"] = ts2, by2
    e1["id"], twin["id"] = ids
    sc["artifacts"].append(twin)
    for e in sc["events"]:
        if e["object"] == "art:E1":
            e["object"] = ids[0]
            e["meta"] = {"artifact_id": ids[0]}
    return sc


def order(sc):
    return [c["artifact_id"] for c in candidate_table(sc)]


def test_exact_ties_are_ordered_by_creation_time_then_creator_then_id():
    # same score, A created later than B -> B first even though A sorts first by id
    sc = with_tied_copy(ts2="2026-10-09T01:30:00Z")  # twin (id art:B) is earlier; it also has the sketches of E1
    fits = {c["artifact_id"]: c["origin_fit"] for c in candidate_table(sc)}
    assert fits["art:A"] == fits["art:B"] or abs(fits["art:A"] - fits["art:B"]) < 1e-9
    assert order(sc) == ["art:B", "art:A"]
    # same time, creators differ -> creator ascending beats id
    sc = with_tied_copy(by2="act:ann")  # E1 is by act:etl, twin by act:ann
    assert order(sc) == ["art:B", "art:A"]
    # everything equal -> id ascending
    assert order(with_tied_copy()) == ["art:A", "art:B"]
    assert order(with_tied_copy(ids=("art:Q", "art:P"))) == ["art:P", "art:Q"]


def test_ids_never_change_a_score_or_a_probability():
    r1 = trace(with_tied_copy(ids=("art:A", "art:B")))
    r2 = trace(with_tied_copy(ids=("art:Q", "art:P")))
    probs = lambda r: sorted(h["probability"] for h in r["hypotheses"])  # noqa: E731
    assert probs(r1) == probs(r2)
    assert sorted(c["origin_fit"] for c in r1["origin_candidates"]) == sorted(
        c["origin_fit"] for c in r2["origin_candidates"])
    assert sorted(x["probability"] for x in r1["origin_ranking"]) == sorted(
        x["probability"] for x in r2["origin_ranking"])


@pytest.mark.parametrize("name", ["H1", "H2", "H3", "H4", "H5", "H6", "H7"])
def test_input_order_and_ids_do_not_change_candidate_order_or_probabilities(name):
    sc = build(name)
    base = trace(sc)
    rnd = random.Random(11)
    shuffled = copy.deepcopy(sc)
    for k in ("events", "artifacts", "actors", "locations", "log_sources", "canary_registry"):
        rnd.shuffle(shuffled[k])
    assert json.dumps(trace(shuffled), sort_keys=True) == json.dumps(base, sort_keys=True)
    # rename every artifact to ids in a different alphabetical order, keep the content
    text = json.dumps(sc)
    mapping = {a["id"]: f"art:{chr(ord('Z') - i)}{i}" for i, a in enumerate(sc["artifacts"])}
    for old, new in mapping.items():
        text = text.replace(json.dumps(old)[1:-1], json.dumps(new)[1:-1])
    renamed = trace(json.loads(text))
    inv = {v: k for k, v in mapping.items()}
    assert [inv[c["artifact_id"]] for c in renamed["origin_candidates"]] == [
        c["artifact_id"] for c in base["origin_candidates"]]
    assert [h["probability"] for h in renamed["hypotheses"]] == [h["probability"] for h in base["hypotheses"]]
    assert [(inv[x["artifact_id"]], x["probability"]) for x in renamed["origin_ranking"]] == [
        (x["artifact_id"], x["probability"]) for x in base["origin_ranking"]]
