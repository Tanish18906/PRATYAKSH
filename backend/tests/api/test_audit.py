import json
import re

from app.privacy import audit


def test_append_assigns_ids_and_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "PATH", tmp_path / "sub" / "audit.jsonl")
    audit.reset()
    a = audit.append("trace", scenario_id="scn:H1", object_id="trc:H1")
    b = audit.append("reveal", scenario_id="scn:H1", object_id="leak:H1", field="phone", reason="legal request 42")
    assert a["id"] == "aud:0001" and b["id"] == "aud:0002"
    assert a["who"] == "investigator-demo" and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", a["ts"])
    assert a["field"] is None and a["reason"] is None and b["reason"] == "legal request 42"
    lines = (tmp_path / "sub" / "audit.jsonl").read_text().splitlines()
    assert [json.loads(x)["id"] for x in lines] == ["aud:0001", "aud:0002"]


def test_entries_filter_by_scenario(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    audit.reset()
    audit.append("trace", scenario_id="scn:A")
    audit.append("trace", scenario_id="scn:B")
    assert len(audit.entries()) == 2 and [e["scenario_id"] for e in audit.entries("scn:B")] == ["scn:B"]


def test_numbering_continues_after_a_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    audit.reset()
    audit.append("trace", scenario_id="scn:A")
    audit.append("trace", scenario_id="scn:A")
    audit.reset()  # same as a new process: memory empty, file kept
    assert audit.append("trace", scenario_id="scn:A")["id"] == "aud:0003"


def test_entries_validate_against_the_contract_model(tmp_path, monkeypatch):
    from app.models import AuditEntry
    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    audit.reset()
    for action in ("scenario_generate", "telegram_export", "trace", "reveal", "report_export", "inject",
                   "canary_alert", "benchmark_run"):
        AuditEntry.model_validate(audit.append(action, scenario_id=None))


def test_concurrent_appends_get_unique_contiguous_ids(tmp_path, monkeypatch):
    """The id is read, incremented, assigned and written as one step: no duplicates, no gaps, no lost lines."""
    import sys
    import threading

    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    audit.reset()
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # make thread switches frequent so an unlocked version fails reliably
    try:
        threads = [threading.Thread(target=lambda: [audit.append("trace", scenario_id="scn:A") for _ in range(40)])
                   for _ in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        sys.setswitchinterval(old)
    ids = [e["id"] for e in audit.entries()]
    lines = [json.loads(x)["id"] for x in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert len(ids) == 1600 and len(set(ids)) == 1600
    assert sorted(int(i.split(":")[1]) for i in ids) == list(range(1, 1601))
    assert lines == ids  # file order equals id order
