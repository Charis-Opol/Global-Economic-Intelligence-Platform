from __future__ import annotations

import httpx
import pytest

from app import superset_client
from app.superset_client import DASHBOARD_UUIDS, UnknownDashboardError, fetch_guest_token


def test_guest_token_endpoint_returns_token_and_dashboard_id(client, monkeypatch):
    monkeypatch.setattr(superset_client, "fetch_guest_token", lambda dashboard: "fake-guest-token")

    resp = client.get("/superset/guest-token", params={"dashboard": "gdp"})
    body = resp.json()

    assert resp.status_code == 200
    assert body["token"] == "fake-guest-token"
    assert body["dashboard_id"] == DASHBOARD_UUIDS["gdp"]


def test_unknown_dashboard_is_400(client):
    resp = client.get("/superset/guest-token", params={"dashboard": "nonsense"})
    assert resp.status_code == 400


def test_superset_unreachable_is_502(client, monkeypatch):
    def _raise(dashboard):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(superset_client, "fetch_guest_token", _raise)

    resp = client.get("/superset/guest-token", params={"dashboard": "gdp"})
    assert resp.status_code == 502


def test_fetch_guest_token_chains_login_csrf_and_guest_token_calls():
    """Exercises the real 3-call chain (login -> csrf -> guest token) against
    a fake transport - no real Superset instance needed, but this is real
    request-building/response-parsing logic, not a router-level stub."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/security/login":
            assert request.method == "POST"
            return httpx.Response(200, json={"access_token": "fake-access-token"})
        if request.url.path == "/api/v1/security/csrf_token/":
            assert request.headers["Authorization"] == "Bearer fake-access-token"
            return httpx.Response(200, json={"result": "fake-csrf-token"})
        if request.url.path == "/api/v1/security/guest_token/":
            assert request.headers["X-CSRFToken"] == "fake-csrf-token"
            body = request.read()
            import json

            payload = json.loads(body)
            assert payload["resources"] == [{"type": "dashboard", "id": DASHBOARD_UUIDS["gdp"]}]
            return httpx.Response(200, json={"token": "fake-guest-token"})
        raise AssertionError(f"unexpected request to {request.url.path}")

    fake_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://superset:8088")

    token = fetch_guest_token("gdp", client=fake_client)

    assert token == "fake-guest-token"


def test_fetch_guest_token_rejects_unknown_dashboard():
    with pytest.raises(UnknownDashboardError):
        fetch_guest_token("nonsense")
