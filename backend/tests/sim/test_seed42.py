import json
from datetime import datetime
from functools import lru_cache
from time import perf_counter

import pytest

from app.sim.generator import generate_scenario, reveal_value, to_summary, warm_cache
from app.sim.leakfile import mask_value
from app.sim.store import get_bundle
from app.sim.styles import format_profile
from scripts.validate import validate_public_scenario


@lru_cache
def demo(loss=0.4):
    return generate_scenario("A1", 42, loss, False, "demo")


def test_seed42_acceptance():
    warm_cache("demo")
    start = perf_counter()
    bundle = demo()
    elapsed = perf_counter() - start
    print(f"seed 42 generation after cache: {elapsed:.3f}s")
    assert elapsed < 3
    public = bundle.public
    validate_public_scenario(public)
    artifacts = {artifact["id"]: artifact for artifact in public["artifacts"]}
    assert set(artifacts) == {f"art:E{i}" for i in range(1, 7)}
    e1 = artifacts["art:E1"]
    assert e1["created_by"] == "act:etl-nightly"
    assert e1["created_ts"] == "2026-10-09T02:10:00Z"
    assert 47_000 <= e1["row_count"] <= 51_000
    assert 0 <= (datetime.fromisoformat(e1["created_ts"]) -
                 datetime.fromisoformat(e1["newest_record_ts"])).total_seconds() <= 5400
    assert all(artifacts[f"art:E{i}"]["row_count"] > e1["row_count"] for i in (4, 5, 6))
    assert artifacts["art:E2"]["created_by"] == "act:arjun-das"
    assert artifacts["art:E2"]["created_ts"] == "2026-10-02T11:00:00Z"
    assert artifacts["art:E3"]["created_by"] == "act:kavya-rao"
    assert artifacts["art:E3"]["created_ts"] == "2026-10-06T09:30:00Z"
    assert [artifacts[f"art:E{i}"]["created_ts"] for i in (4, 5, 6)] == [
        "2026-10-10T02:10:00Z", "2026-10-11T02:10:00Z", "2026-10-12T02:10:00Z"
    ]
    leak = public["leak_sample"]
    assert leak["found_at"] == "ext:telegram-leak-channel"
    assert leak["found_ts"] == "2026-10-12T08:30:00Z"
    assert leak["columns"] == ["full_name", "phone", "policy_no", "created_at"]
    assert 45_000 <= leak["row_count"] <= 49_500
    assert leak["newest_record_ts"] == e1["newest_record_ts"]
    assert leak["format_profile"] == format_profile("ETL", leak["columns"])
    assert artifacts["art:E2"]["created_ts"] < leak["newest_record_ts"]
    assert "phone" not in artifacts["art:E3"]["columns"]
    from app.common.sketch import containment
    assert containment(leak["sketches"]["phone"], e1["sketches"]["phone"]) >= 0.95
    from app.common.sketch import h64, normalize
    from app.sim.leakfile import render_leak_row
    for index in range(0, leak["row_count"], max(1, leak["row_count"] // 200)):
        row = render_leak_row(bundle.private, index)
        source_index = int(bundle.private.indices[index])
        for column in leak["sketches"]:
            assert h64(bundle.private.case_key, normalize(column, row[column])) == int(
                bundle.private.base.hashes[column][source_index]
            )
    assert bundle.truth["origin_artifact"] == "art:E1"
    assert bundle.truth["true_actors"] == ["act:ravi-menon"]
    download = bundle.truth["true_path"][1]["event_id"]
    assert download in {event["id"] for event in public["events"]}
    assert bundle.truth["true_path"][-1]["event_id"] is None
    assert public["discovery"]["platform"] == "telegram-mock"
    assert public["discovery"]["leak_message_id"] in {
        message["id"] for message in public["discovery"]["messages"] if message["attachment"]
    }
    assert to_summary(bundle)["counts"]["artifacts"] == 6
    assert get_bundle(public["id"]) is bundle
    assert reveal_value(bundle, 0, "phone").startswith("+91-")
    for index, preview in enumerate(leak["masked_preview"]):
        for column, masked in preview.items():
            assert mask_value(column, reveal_value(bundle, index, column)) == masked


def test_seed42_loss_and_determinism():
    high_loss = demo(0.6)
    download = high_loss.truth["true_path"][1]["event_id"]
    assert high_loss.truth["true_path"][1]["dropped"] is True
    assert download in high_loss.truth["dropped_event_ids"]
    assert download not in {event["id"] for event in high_loss.public["events"]}
    assert json.dumps(demo().public, sort_keys=True) == json.dumps(
        generate_scenario("A1", 42, 0.4, False, "demo").public, sort_keys=True
    )


@pytest.mark.parametrize("loss", (0.0, 0.2, 0.4))
def test_seed42_phase2_trace_inputs(loss):
    bundle = demo(loss)
    public = bundle.public
    validate_public_scenario(public)
    artifacts = {artifact["id"]: artifact for artifact in public["artifacts"]}
    leak = public["leak_sample"]
    assert artifacts["art:E2"]["newest_record_ts"] < leak["newest_record_ts"]
    assert "phone" not in artifacts["art:E3"]["columns"]
    assert all(artifacts[f"art:E{i}"]["newest_record_ts"] > leak["newest_record_ts"]
               for i in (4, 5, 6))
    assert bundle.truth["origin_artifact"] == "art:E1"
    assert bundle.truth["true_actors"] == ["act:ravi-menon"]
    download = bundle.truth["true_path"][1]
    assert download["dropped"] is False
    assert any(event["id"] == download["event_id"] and
               event["actor"] == "act:ravi-menon" and
               event["action"] == "download" for event in public["events"])


def test_bench_generation_after_cache():
    warm_cache("bench")
    start = perf_counter()
    bundle = generate_scenario("A1", 7, 0.4, False, "bench")
    elapsed = perf_counter() - start
    print(f"bench generation after cache: {elapsed:.3f}s")
    assert elapsed < 0.3
    validate_public_scenario(bundle.public)
