from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app


def test_health_check_does_not_need_the_warehouse():
    # /health has no DB dependency, so it must work with no override at all.
    resp = TestClient(app).get("/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_missing_warehouse_file_returns_503(monkeypatch):
    from app.core.config import settings

    # tempfile.mkdtemp rather than pytest's tmp_path fixture - the latter
    # shares one base temp dir across the whole session, which this Windows
    # environment sometimes locks with denied access between test runs.
    missing_path = Path(tempfile.mkdtemp()) / "does_not_exist.duckdb"
    monkeypatch.setattr(settings, "duckdb_path", str(missing_path))
    app.dependency_overrides.pop(get_connection, None)  # exercise the real dependency

    resp = TestClient(app).get("/countries")

    assert resp.status_code == 503
