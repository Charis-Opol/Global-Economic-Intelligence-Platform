"""
Entry point for the Global Economic Intelligence Platform API.

Day 1 scope was proving the container builds, starts, and is reachable.
Day 2, Step 6 adds read-only domain endpoints over the DuckDB warehouse
Day 1, Step 10 populates. ML-backed endpoints (e.g. /predictions) are a
later Day 2 step, added once a model is registered in MLflow.
"""
from fastapi import FastAPI

from app.core.config import settings
from app.routers import crypto, exchange_rate, news, weather, world_bank

app = FastAPI(title=settings.app_name)

app.include_router(world_bank.router)
app.include_router(exchange_rate.router)
app.include_router(weather.router)
app.include_router(crypto.router)
app.include_router(news.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
