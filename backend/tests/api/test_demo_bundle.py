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


def test_cli_without_simulator_or_fixture_fails_clearly(tmp_path, capsys):
    out = tmp_path / "demo.json"
    assert bundle_main(["--out", str(out)]) != 0
    assert "simulator" in capsys.readouterr().err.lower() and not out.exists()
