"""Nightly training pipeline status endpoint (Day 2, Step 6)."""
from __future__ import annotations

from fastapi import APIRouter

from app import airflow_client
from app.schemas import PipelineStatusEntry

router = APIRouter(tags=["pipeline-status"])


@router.get("/pipeline-status", response_model=list[PipelineStatusEntry])
def pipeline_status():
    return airflow_client.get_pipeline_status()
