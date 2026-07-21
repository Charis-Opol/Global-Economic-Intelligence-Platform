"""
Entry point for the Global Economic Intelligence Platform API.

Day 1 scope was proving the container builds, starts, and is reachable.
Day 2, Step 6 adds read-only domain endpoints over the DuckDB warehouse
(Day 1, Step 10) plus ML-backed endpoints reading from the MLflow registry
(Day 2, Steps 3-5). Day 2, Step 7 gates every router below except this file's
own `/health` and `auth.router` behind a valid JWT - `/health` stays open so
container healthchecks and load balancers don't need credentials, and
`auth.router` obviously can't require a token to reach the endpoint that
issues one. Day 3 adds Superset embedding and service-health endpoints, and
CORS - the API is now called from a real browser frontend on another origin.
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import mlflow_client
from app.auth import get_current_user
from app.auth import router as auth_router
from app.core.config import settings
from app.routers import (
    crypto,
    exchange_rate,
    models,
    monitoring,
    news,
    pipeline_status,
    predictions,
    superset,
    weather,
    world_bank,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow_client.use_shared_tracking_uri()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_authenticated = [Depends(get_current_user)]

app.include_router(auth_router)
app.include_router(world_bank.router, dependencies=_authenticated)
app.include_router(exchange_rate.router, dependencies=_authenticated)
app.include_router(weather.router, dependencies=_authenticated)
app.include_router(crypto.router, dependencies=_authenticated)
app.include_router(news.router, dependencies=_authenticated)
app.include_router(predictions.router, dependencies=_authenticated)
app.include_router(models.router, dependencies=_authenticated)
app.include_router(pipeline_status.router, dependencies=_authenticated)
app.include_router(superset.router, dependencies=_authenticated)
app.include_router(monitoring.router, dependencies=_authenticated)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
