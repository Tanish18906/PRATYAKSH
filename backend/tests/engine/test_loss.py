from app.engine.loss import estimate_loss


def scen(seqs_by_src, extra_sources=()):
    events = [{"source": s, "seq": q} for s, seqs in seqs_by_src.items() for q in seqs]
    srcs = list(seqs_by_src) + list(extra_sources)
    return {"events": events, "log_sources": [{"id": s} for s in srcs]}


def test_seq_gaps_give_fraction():
    # 40 events observed out of seq 1..50 (first and last present) -> 10/50 = 0.2
    seqs = [q for q in range(1, 51) if q % 5 != 4]
    assert estimate_loss(scen({"src:a": seqs})) == {"src:a": 0.2}


def test_no_gaps_clips_to_floor():
    assert estimate_loss(scen({"src:a": list(range(1, 41))})) == {"src:a": 0.05}


def test_fewer_than_20_events_uses_default():
    assert estimate_loss(scen({"src:a": [1, 5, 9]})) == {"src:a": 0.4}


def test_exactly_20_events_is_estimated():
    seqs = list(range(1, 21))
    assert estimate_loss(scen({"src:a": seqs})) == {"src:a": 0.05}


def test_clips_to_ceiling():
    seqs = list(range(1, 100, 5))  # 20 events over seq 1..96 -> 0.7917
    assert estimate_loss(scen({"src:a": seqs})) == {"src:a": 0.7917}
    seqs = [1 + 200 * i for i in range(20)]  # ~0.9 area, then beyond ceiling
    assert estimate_loss(scen({"src:a": seqs}))["src:a"] == 0.9


def test_source_without_events_defaults_and_is_listed():
    out = estimate_loss(scen({"src:a": list(range(1, 41))}, extra_sources=["src:empty"]))
    assert out == {"src:a": 0.05, "src:empty": 0.4}
