"""Registered-model listing endpoint (Day 2, Step 6)."""
from __future__ import annotations

from fastapi import APIRouter

from app import mlflow_client
from app.schemas import RegisteredModel

router = APIRouter(tags=["models"])


@router.get("/models", response_model=list[RegisteredModel])
def list_models():
    return mlflow_client.list_registered_models()
