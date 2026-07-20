"""
Entry point for the Global Economic Intelligence Platform API.

Day 1 scope: prove the container builds, starts, and is reachable.
Domain endpoints (/countries, /gdp, /predictions, etc.) are added in Day 2.
"""
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
