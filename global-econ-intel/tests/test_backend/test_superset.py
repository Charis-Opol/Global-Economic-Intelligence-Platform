from __future__ import annotations

import httpx
import pytest

from app import superset_client
from app.superset_client import UnknownDashboardError, fetch_guest_token


@pytest.fixture(autouse=True)
def _clear_embedded_uuid_cache():
    # fetch_guest_token caches the embedded uuid per dashboard slug for the
    # life of the process (Superset's upsert never changes an existing one) -
    # tests calling the real function need a clean cache each time, or an
    # earlier test's fake uuid leaks into a later assertion.
    superset_client._embedded_uuid_cache.clear()
    yield
    superset_client._embedded_uuid_cache.clear()


def test_guest_token_endpoint_returns_token_and_dashboard_id(client, monkeypatch):
    monkeypatch.setattr(
        superset_client, "fetch_guest_token", lambda dashboard: ("fake-guest-token", "fake-embedded-uuid")
    )

    resp = client.get("/superset/guest-token", params={"dashboard": "gdp"})
    body = resp.json()

    assert resp.status_code == 200
    assert body["token"] == "fake-guest-token"
    assert body["dashboard_id"] == "fake-embedded-uuid"


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
    """Exercises the real 4-call chain (login -> csrf -> ensure embedded ->
    guest token) against a fake transport - no real Superset instance
    needed, but this is real request-building/response-parsing logic, not a
    router-level stub."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/security/login":
            assert request.method == "POST"
            return httpx.Response(200, json={"access_token": "fake-access-token"})
        if request.url.path == "/api/v1/security/csrf_token/":
            assert request.headers["Authorization"] == "Bearer fake-access-token"
            return httpx.Response(200, json={"result": "fake-csrf-token"})
        if request.url.path == "/api/v1/dashboard/gdp/embedded":
            assert request.method == "POST"
            assert request.headers["X-CSRFToken"] == "fake-csrf-token"
            return httpx.Response(200, json={"result": {"uuid": "fake-embedded-uuid", "allowed_domains": []}})
        if request.url.path == "/api/v1/security/guest_token/":
            assert request.headers["X-CSRFToken"] == "fake-csrf-token"
            body = request.read()
            import json

            payload = json.loads(body)
            assert payload["resources"] == [{"type": "dashboard", "id": "fake-embedded-uuid"}]
            return httpx.Response(200, json={"token": "fake-guest-token"})
        raise AssertionError(f"unexpected request to {request.url.path}")

    fake_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://superset:8088")

    token, embedded_uuid = fetch_guest_token("gdp", client=fake_client)

    assert token == "fake-guest-token"
    assert embedded_uuid == "fake-embedded-uuid"


def test_fetch_guest_token_rejects_unknown_dashboard():
    with pytest.raises(UnknownDashboardError):
        fetch_guest_token("nonsense")
