"""
Superset embedded-dashboard guest-token client (Day 3, Step 5).

Mints a short-lived guest token scoped to one dashboard, following
Superset's own Embedded Dashboards flow: admin login -> CSRF token -> guest
token. The frontend never sees the admin credential, only the resulting
guest token - and Superset itself only honors that token for the specific
dashboard id it was scoped to.

The six dashboard UUIDs below are fixed identifiers this repo controls -
they're referenced identically in `superset/dashboards/*.yaml` (the
declarative dashboard definitions meant to be imported into a running
Superset instance) so the frontend, this client, and the YAML all agree on
which dashboard is which without a live lookup.

Caveat: these UUIDs and this whole flow are unverified against a real
Superset instance in this environment (no live Superset here to import the
YAML into and click through) - see docs/DEPLOYMENT.md for what to check
first.
"""
from __future__ import annotations

import httpx

from app.core.config import settings

DASHBOARD_UUIDS: dict[str, str] = {
    "gdp": "fdbf5d8b-5077-4ba7-8421-3f0be46f14d8",
    "inflation": "8259bc55-e18d-4198-b68e-27c89029b54e",
    "weather": "b7cbc5fc-a0cf-4a5f-88f9-749a4ac9478c",
    "crypto": "778e0eb8-3168-4b4b-99fd-59899b3e7c58",
    "exchange": "7950e4cc-2853-4334-ab19-aa5e50005f6b",
    "forecasts": "2366b86b-7c92-441a-b33f-596ae1d7b56e",
}


class UnknownDashboardError(Exception):
    """Raised for a dashboard key not in DASHBOARD_UUIDS."""


def fetch_guest_token(
    dashboard: str, *, client: httpx.Client | None = None, username: str = "embedded-viewer"
) -> str:
    """Runs the three-call Superset flow and returns the guest token.

    `client` is injectable so tests can pass an `httpx.Client` built on a
    `MockTransport` instead of hitting a real Superset instance.
    """
    if dashboard not in DASHBOARD_UUIDS:
        raise UnknownDashboardError(f"Unknown dashboard '{dashboard}'. Choose one of {sorted(DASHBOARD_UUIDS)}")

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

        guest_resp = http.post(
            "/api/v1/security/guest_token/",
            headers={**auth_headers, "X-CSRFToken": csrf_token},
            json={
                "user": {"username": username, "first_name": "Embedded", "last_name": "Viewer"},
                "resources": [{"type": "dashboard", "id": DASHBOARD_UUIDS[dashboard]}],
                "rls": [],
            },
        )
        guest_resp.raise_for_status()
        return guest_resp.json()["token"]
    finally:
        if owns_client:
            http.close()
