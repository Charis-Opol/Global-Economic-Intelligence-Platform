"""
Superset embedded-dashboard guest-token client (Day 3, Step 5).

Mints a short-lived guest token scoped to one dashboard, following
Superset's own Embedded Dashboards flow: admin login -> CSRF token -> guest
token. The frontend never sees the admin credential, only the resulting
guest token - and Superset itself only honors that token for the specific
dashboard id it was scoped to.

That "id" is NOT the dashboard's own uuid (the one in
`superset/dashboards/dashboards/*.yaml`). Superset generates a *separate*
random uuid the first time embedding is enabled for a dashboard (via
`POST /api/v1/dashboard/<slug>/embedded`), stored in its own
`embedded_dashboards` table, and that's what both the `@superset-ui/embedded-sdk`
iframe (`GET /embedded/<uuid>`) and the guest token's `resources[].id` need
to match - confirmed by tracing Superset's own
`EmbeddedDashboardDAO.find_by_id()` / `SupersetSecurityManager.has_guest_access()`.
Passing the dashboard's own uuid there 404s the iframe (this repo's original
bug - see git history).

`_ensure_embedded_uuid` calls that POST endpoint itself rather than assuming
embedding was already enabled by some other setup step: Superset's own
`EmbeddedDashboardDAO.upsert()` preserves the existing uuid across repeat
calls (only generates one the first time), so this is safe to call on every
cold cache entry and self-heals if embedding was never enabled at all.
"""
from __future__ import annotations

import httpx

from app.core.config import settings

DASHBOARD_SLUGS: frozenset[str] = frozenset(
    {"gdp", "inflation", "weather", "crypto", "exchange", "forecasts"}
)

# Keyed by slug. Populated lazily; safe to keep for the life of the process
# since Superset's upsert never changes an existing embedded uuid.
_embedded_uuid_cache: dict[str, str] = {}


class UnknownDashboardError(Exception):
    """Raised for a dashboard key not in DASHBOARD_SLUGS."""


def _ensure_embedded_uuid(
    dashboard: str, http: httpx.Client, auth_headers: dict[str, str], csrf_token: str
) -> str:
    if dashboard in _embedded_uuid_cache:
        return _embedded_uuid_cache[dashboard]

    resp = http.post(
        f"/api/v1/dashboard/{dashboard}/embedded",
        headers={**auth_headers, "X-CSRFToken": csrf_token},
        json={"allowed_domains": settings.cors_allowed_origins_list},
    )
    resp.raise_for_status()
    embedded_uuid = resp.json()["result"]["uuid"]
    _embedded_uuid_cache[dashboard] = embedded_uuid
    return embedded_uuid


def fetch_guest_token(
    dashboard: str, *, client: httpx.Client | None = None, username: str = "embedded-viewer"
) -> tuple[str, str]:
    """Runs the login -> CSRF -> (ensure embedded) -> guest-token chain.

    Returns `(guest_token, embedded_dashboard_uuid)` - the caller needs both:
    the token to authenticate the iframe, and the embedded uuid as the SDK's
    `id` (see `app/routers/superset.py`).

    `client` is injectable so tests can pass an `httpx.Client` built on a
    `MockTransport` instead of hitting a real Superset instance.
    """
    if dashboard not in DASHBOARD_SLUGS:
        raise UnknownDashboardError(f"Unknown dashboard '{dashboard}'. Choose one of {sorted(DASHBOARD_SLUGS)}")

    owns_client = client is None
    http = client or httpx.Client(base_url=settings.superset_base_url, timeout=10.0)
    try:
        login_resp = http.post(
            "/api/v1/security/login",
            json={
                "username": settings.superset_admin_user,
                "password": settings.superset_admin_password,
                "provider": "db",
                "refresh": True,
            },
        )
        login_resp.raise_for_status()
        access_token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        csrf_resp = http.get("/api/v1/security/csrf_token/", headers=auth_headers)
        csrf_resp.raise_for_status()
        csrf_token = csrf_resp.json()["result"]

        embedded_uuid = _ensure_embedded_uuid(dashboard, http, auth_headers, csrf_token)

        guest_resp = http.post(
            "/api/v1/security/guest_token/",
            headers={**auth_headers, "X-CSRFToken": csrf_token},
            json={
                "user": {"username": username, "first_name": "Embedded", "last_name": "Viewer"},
                "resources": [{"type": "dashboard", "id": embedded_uuid}],
                "rls": [],
            },
        )
        guest_resp.raise_for_status()
        return guest_resp.json()["token"], embedded_uuid
    finally:
        if owns_client:
            http.close()
