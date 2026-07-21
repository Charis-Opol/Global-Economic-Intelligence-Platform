from __future__ import annotations

import httpx

from app import monitoring


def test_service_health_endpoint_reports_all_services(client, monkeypatch):
    monkeypatch.setattr(
        monitoring,
        "check_all_services",
        lambda: [
            {"service": "minio", "healthy": True, "detail": None},
            {"service": "mlflow", "healthy": True, "detail": None},
            {"service": "airflow", "healthy": False, "detail": "connection refused"},
            {"service": "backend", "healthy": True, "detail": None},
        ],
    )

    resp = client.get("/monitoring/services")
    body = resp.json()

    assert resp.status_code == 200
    assert len(body) == 4
    by_service = {entry["service"]: entry for entry in body}
    assert by_service["airflow"]["healthy"] is False
    assert by_service["airflow"]["detail"] == "connection refused"
    assert by_service["backend"]["healthy"] is True


def test_ping_failure_is_reported_not_raised(monkeypatch):
    def _raise(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "get", _raise)

    result = monitoring._ping("unreachable", "http://example.invalid/health")

    assert result == {"service": "unreachable", "healthy": False, "detail": "connection refused"}


def test_ping_success_is_reported_healthy(monkeypatch):
    def _fake_get(url, timeout):
        return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", _fake_get)

    result = monitoring._ping("minio", "http://minio:9000/minio/health/live")

    assert result == {"service": "minio", "healthy": True, "detail": None}
