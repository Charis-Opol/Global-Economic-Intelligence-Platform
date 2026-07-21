"""Service-reachability monitoring endpoint (Day 3, Step 6)."""
from __future__ import annotations

from fastapi import APIRouter

from app import monitoring
from app.schemas import ServiceHealthEntry

router = APIRouter(tags=["monitoring"])


@router.get("/monitoring/services", response_model=list[ServiceHealthEntry])
def service_health():
    return monitoring.check_all_services()
