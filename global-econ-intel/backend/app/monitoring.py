"""
Lightweight service-reachability checks (Day 3, Step 6).

"Container health" is deliberately scoped to service reachability, not
literal Docker container introspection - that would need the Docker socket
mounted into this public-facing container, a real security cost for a
monitoring page to carry. Each check is a short-timeout ping; a failure
marks that one service unhealthy without raising, so one flaky dependency
never takes the whole page down.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


def _ping(name: str, url: str, *, timeout: float = 3.0) -> dict[str, Any]:
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return {"service": name, "healthy": True, "detail": None}
    except httpx.HTTPError as exc:
        return {"service": name, "healthy": False, "detail": str(exc)}


def check_all_services() -> list[dict[str, Any]]:
    return [
        _ping("minio", f"{settings.minio_endpoint}/minio/health/live"),
        _ping("mlflow", f"{settings.mlflow_tracking_uri}/health"),
        _ping("airflow", f"{settings.airflow_base_url}/health"),
        # No network hop needed - if this code is running, the backend itself
        # is up.
        {"service": "backend", "healthy": True, "detail": None},
    ]
