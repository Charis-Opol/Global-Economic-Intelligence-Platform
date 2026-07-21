"""
Thin Airflow REST API client (Day 2, Step 6).

Backs `/pipeline-status` - reports the latest run's state for each nightly
training DAG (see `airflow/dags/_training_dag_factory.py`). Talks to
Airflow's own stable REST API over basic auth (the same admin credentials
the webserver login uses) rather than reaching into Airflow's metadata
database directly, which is an internal implementation detail this backend
shouldn't depend on.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

TRAINING_DAG_IDS = [
    "train_gdp_forecast",
    "train_inflation_forecast",
    "train_exchange_rate_forecast",
    "train_crypto_forecast",
]


def get_latest_dag_run(dag_id: str) -> dict[str, Any] | None:
    """The most recent DAG run for `dag_id`, or None if it has never run yet
    (e.g. a fresh docker compose stack before the first nightly schedule)."""
    url = f"{settings.airflow_base_url}/api/v1/dags/{dag_id}/dagRuns"
    params = {"order_by": "-execution_date", "limit": 1}
    response = httpx.get(
        url,
        params=params,
        auth=(settings.airflow_admin_user, settings.airflow_admin_password),
        timeout=5.0,
    )
    response.raise_for_status()
    runs = response.json().get("dag_runs", [])
    return runs[0] if runs else None


def get_pipeline_status() -> list[dict[str, Any]]:
    """One entry per training DAG. A DAG whose Airflow call fails (not yet
    reachable, never run, network hiccup) reports state=None rather than
    failing the whole endpoint - one flaky DAG shouldn't hide the others."""
    statuses = []
    for dag_id in TRAINING_DAG_IDS:
        try:
            run = get_latest_dag_run(dag_id)
        except httpx.HTTPError:
            run = None
        statuses.append(
            {
                "dag_id": dag_id,
                "state": run["state"] if run else None,
                "execution_date": run["execution_date"] if run else None,
                "start_date": run.get("start_date") if run else None,
                "end_date": run.get("end_date") if run else None,
            }
        )
    return statuses
