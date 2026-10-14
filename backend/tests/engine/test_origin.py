import copy

from app.engine.origin import candidate_table, pin_canary
from tests.fixtures.mini import build


def table(sc):
    return {c["artifact_id"]: c for c in candidate_table(sc)}


def art(sc, aid):
    return next(a for a in sc["artifacts"] if a["id"] == aid)


def test_format_sim_exact_values():
    assert table(build("H1"))["art:E1"]["format_sim"] == 1.0
    assert table(build("H1"))["art:E2"]["format_sim"] == 0.1111
    assert table(build("H3"))["art:E1"]["format_sim"] == 0.6667


def test_h1_table_values_and_order():
    rows = candidate_table(build("H1"))
    assert [r["artifact_id"] for r in rows] == ["art:E1", "art:E2"]
    e1, e2 = rows
    assert e1["verdict"] == e2["verdict"] == "candidate"
    assert e1["containment"] >= 0.95
    assert e1["watermark_term"] == -0.3333 and e2["watermark_term"] == -1.3333
    assert e1["origin_fit"] - e2["origin_fit"] >= 1.5


def test_rule_schema_leaves_numbers_null():
    sc = build("H1")
    art(sc, "art:E2")["columns"].remove("policy_no")
    c = table(sc)["art:E2"]
    assert c["verdict"] == "excluded" and c["exclusion_rule"] == "schema"
    assert all(c[k] is None for k in ("containment", "specificity", "format_sim", "watermark_term", "origin_fit"))
    assert c["notes"]


def test_rule_watermark_before_keeps_containment():
    c = table(build("H3"))["art:E2"]
    assert c["verdict"] == "excluded" and c["exclusion_rule"] == "watermark_before"
    assert c["containment"] is not None and c["origin_fit"] is None
    assert [r["artifact_id"] for r in candidate_table(build("H3"))][-1] == "art:E2"  # excluded last


def test_watermark_tolerance_is_five_minutes():
    sc = build("H1")  # leak newest record is 2026-10-09T02:00:00Z
    art(sc, "art:E2")["created_ts"] = "2026-10-09T01:55:00Z"
    assert table(sc)["art:E2"]["verdict"] == "candidate"
    art(sc, "art:E2")["created_ts"] = "2026-10-09T01:54:59Z"
    assert table(sc)["art:E2"]["exclusion_rule"] == "watermark_before"


def test_rule_after_found():
    sc = build("H1")
    art(sc, "art:E2")["created_ts"] = "2026-10-13T00:00:00Z"
    c = table(sc)["art:E2"]
    assert c["verdict"] == "excluded" and c["exclusion_rule"] == "after_found"


def test_first_violated_rule_wins():
    sc = build("H3")  # E2 is watermark_before
    art(sc, "art:E2")["columns"].remove("phone")
    assert table(sc)["art:E2"]["exclusion_rule"] == "schema"


def test_wm_only_when_ratio_at_least_point_nine():
    t = table(build("H4"))  # ratio about 0.1
    assert t["art:E1"]["watermark_term"] == 0 and t["art:E5"]["watermark_term"] == 0
    assert t["art:E1"]["containment"] >= 0.7 and t["art:E5"]["containment"] >= 0.7


def test_wm_is_capped():
    sc = build("H1")
    art(sc, "art:E2")["arrivals_per_hour"] = 100.0
    assert table(sc)["art:E2"]["watermark_term"] == -8.0


def test_no_shared_identifier_columns():
    sc = build("H1")
    art(sc, "art:E2")["sketches"] = {}
    c = table(sc)["art:E2"]
    assert c["containment"] == 0.05
    assert any("no shared identifier columns" in n for n in c["notes"])


def test_pin_canary_picks_most_hits_and_ignores_unknown():
    sc = build("H6")
    pinned, notes = pin_canary(sc)
    assert pinned == "art:E2" and any("canary" in n for n in notes)
    sc2 = copy.deepcopy(sc)
    sc2["leak_sample"]["canary_hits"] = ["can:ghost"]
    pinned, notes = pin_canary(sc2)
    assert pinned is None and notes
    sc2["leak_sample"]["canary_hits"] = []
    assert pin_canary(sc2) == (None, [])


def test_empty_export_does_not_divide_by_zero():
    from app.engine.trace import trace
    sc = build("H1")
    art(sc, "art:E2")["row_count"] = 0
    c = table(sc)["art:E2"]
    assert c["specificity"] == 0.01  # least specific, same as the clip floor
    r = trace(sc)
    assert r["origin_candidates"][0]["artifact_id"] == "art:E1"
