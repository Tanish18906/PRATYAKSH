import json

from app.models import DemoBundle
from scripts.make_demo_bundle import main as bundle_main
from scripts.make_demo_bundle import make_bundle


def test_bundle_from_a_fixture_is_a_valid_demo_bundle():
    b = make_bundle(fixture="H1")
    DemoBundle.model_validate(b)
    assert b["contract_version"] == "1.0" and b["scenario"]["id"] == "scn:H1"
    assert b["trace"]["origin_ranking"][0]["artifact_id"] == "art:E1"
    assert [e["action"] for e in b["audit"]] == ["telegram_export", "trace", "report_export"]
    assert "Verify current legal timelines with counsel." in b["report_html"]
    assert b["benchmark"] is None
    assert '"truth"' not in json.dumps(b) and "case_key" not in json.dumps(b)


def test_bundle_does_not_write_the_real_audit_log(tmp_path, monkeypatch):
    from app.privacy import audit
    before = audit.PATH
    make_bundle(fixture="H1")
    assert audit.PATH == before and not (before.exists() and "scn:H1" in before.read_text())


def test_cli_writes_the_file(tmp_path):
    out = tmp_path / "demo.json"
    assert bundle_main(["--fixture", "H1", "--out", str(out)]) == 0
    DemoBundle.model_validate(json.loads(out.read_text()))


def test_bundle_script_works_on_the_real_simulator(tmp_path):
    """Seed 42, A1, demo scale, loss 0.4, canary mode on, straight from the simulator (no fixture)."""
    from app import main as api
    assert api._sim() is not None, "the simulator must be importable in an integrated checkout"
    out = tmp_path / "demo.json"
    assert bundle_main(["--out", str(out)]) == 0
    b = json.loads(out.read_text())
    DemoBundle.model_validate(b)  # strict contract validation
    assert b["scenario"]["id"] == "scn:A1-42-L40-C"
    assert b["scenario"]["params"] == {"log_loss": 0.4, "canary_mode": True, "scale": "demo"}
    assert b["trace"]["origin_pinned"] is True and b["trace"]["origin_ranking"][0]["artifact_id"] == "art:E1"
    assert "act:ravi-menon" in b["trace"]["hypotheses"][0]["actors"]
    assert [e["action"] for e in b["audit"]] == ["scenario_generate", "telegram_export", "trace", "report_export"]
    assert "Verify current legal timelines with counsel." in b["report_html"]
    assert '"truth"' not in json.dumps(b) and "case_key" not in json.dumps(b)


def test_cli_without_a_simulator_and_without_a_fixture_fails_clearly(tmp_path, capsys, monkeypatch):
    from app import main as api
    monkeypatch.setattr(api, "_sim", lambda: None)
    out = tmp_path / "demo.json"
    assert bundle_main(["--out", str(out)]) != 0
    assert "simulator" in capsys.readouterr().err.lower() and not out.exists()


def test_bundle_embeds_a_saved_benchmark(tmp_path):
    from app.bench import run as bench_run
    from tests.api.test_benchmark import fake_generate

    res = bench_run.run_benchmark(fake_generate, (50, 52), [0.0, 0.2], ["A1"])
    saved = tmp_path / "bench.json"
    saved.write_text(json.dumps({"benchmark_id": "bench:0001", **res}))
    out = tmp_path / "demo.json"
    assert bundle_main(["--fixture", "H1", "--benchmark", str(saved), "--out", str(out)]) == 0
    b = json.loads(out.read_text())
    DemoBundle.model_validate(b)
    assert b["benchmark"]["benchmark_id"] == "bench:0001" and b["benchmark"]["reported_on"] == "seeds 50-52"


def test_bundle_rejects_a_bad_benchmark_file(tmp_path, capsys):
    bad = tmp_path / "bench.json"
    bad.write_text('{"nope": 1}')
    assert bundle_main(["--fixture", "H1", "--benchmark", str(bad), "--out", str(tmp_path / "d.json")]) != 0
    assert "benchmark" in capsys.readouterr().err.lower()
