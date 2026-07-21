"""
Entry point for the Global Economic Intelligence Platform API.

Day 1 scope was proving the container builds, starts, and is reachable.
Day 2, Step 6 adds read-only domain endpoints over the DuckDB warehouse
(Day 1, Step 10) plus ML-backed endpoints reading from the MLflow registry
(Day 2, Steps 3-5). Day 2, Step 7 gates everything below behind a JWT.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import mlflow_client
from app.core.config import settings
from app.routers import (
    crypto,
    exchange_rate,
    models,
    news,
    pipeline_status,
    predictions,
    weather,
    world_bank,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow_client.use_shared_tracking_uri()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(world_bank.router)
app.include_router(exchange_rate.router)
app.include_router(weather.router)
app.include_router(crypto.router)
app.include_router(news.router)
app.include_router(predictions.router)
app.include_router(models.router)
app.include_router(pipeline_status.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
