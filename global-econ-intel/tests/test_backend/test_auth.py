from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_login_with_correct_credentials_returns_a_token():
    resp = TestClient(app).post(
        "/auth/login",
        json={"username": settings.auth_admin_username, "password": settings.auth_admin_password},
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_is_401():
    resp = TestClient(app).post(
        "/auth/login",
        json={"username": settings.auth_admin_username, "password": "definitely-wrong"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_without_a_token_is_401():
    resp = TestClient(app).get("/countries")
    assert resp.status_code == 401


def test_protected_endpoint_with_garbage_token_is_401():
    resp = TestClient(app, headers={"Authorization": "Bearer not-a-real-token"}).get("/countries")
    assert resp.status_code == 401


def test_protected_endpoint_with_valid_token_succeeds(client):
    # `client` (from conftest.py) already carries a valid bearer token and a
    # fixture warehouse - this just confirms auth doesn't block a real call.
    resp = client.get("/countries")
    assert resp.status_code == 200


def test_health_check_needs_no_token():
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
