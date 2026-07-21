"""Day 2, Step 8 - end-to-end auth flow: real login -> real token -> real protected call."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import get_connection
from app.main import app


def test_login_then_use_the_returned_token_on_a_protected_endpoint(warehouse):
    login_resp = TestClient(app).post(
        "/auth/login",
        json={"username": settings.auth_admin_username, "password": settings.auth_admin_password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    app.dependency_overrides[get_connection] = lambda: warehouse
    try:
        resp = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/countries")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.pop(get_connection, None)


def test_wrong_login_never_yields_a_usable_token():
    login_resp = TestClient(app).post(
        "/auth/login", json={"username": settings.auth_admin_username, "password": "wrong"}
    )
    assert login_resp.status_code == 401
    assert "access_token" not in login_resp.json()
