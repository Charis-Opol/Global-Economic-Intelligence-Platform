"""Superset embedded-dashboard guest-token endpoint (Day 3, Step 5)."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from app import superset_client
from app.superset_client import DASHBOARD_UUIDS, UnknownDashboardError

router = APIRouter(tags=["superset"])


@router.get("/superset/guest-token")
def guest_token(dashboard: str = Query(..., description=f"One of {sorted(DASHBOARD_UUIDS)}")):
    try:
        token = superset_client.fetch_guest_token(dashboard)
    except UnknownDashboardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Superset is unreachable: {exc}") from exc
    return {"token": token, "dashboard_id": DASHBOARD_UUIDS[dashboard]}
