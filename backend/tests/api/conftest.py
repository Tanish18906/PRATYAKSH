import copy

import pytest
from fastapi.testclient import TestClient

from app import main
from app.privacy import audit
from tests.fixtures.mini import build


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fresh store and audit log per test; fixtures H1..H8 registered; simulator reported as absent."""
    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    audit.reset()
    main.STORE.clear()
    monkeypatch.setattr(main, "_sim", lambda: None)
    for name in ("H1", "H2", "H3", "H6", "H7"):
        main.register(build(name))
    yield TestClient(main.app)
    main.STORE.clear()
    audit.reset()


@pytest.fixture
def fixture_copy():
    return lambda name="H1": copy.deepcopy(build(name))
