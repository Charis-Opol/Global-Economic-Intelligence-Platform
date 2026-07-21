"""
Thin MLflow client wrapper for the backend (Day 2, Step 6).

The backend only ever *reads* the registry - it loads whichever model
version is aliased "champion" for inference, and lists registered models'
metadata. It never trains or registers anything (that's
`pipelines/ml/mlflow_utils.py`'s job, run from Airflow) - a separate thin
wrapper around the same MLflow concepts because the backend's Docker image
has no dependency on `pipelines/`, the same reason `app/db.py` doesn't reuse
`pipelines/warehouse/schema.py`.
"""
from __future__ import annotations

from typing import Any

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from app.core.config import settings

CHAMPION_ALIAS = "champion"


def use_shared_tracking_uri() -> None:
    """Points the mlflow SDK at the shared tracking server. Called once at
    FastAPI startup (see app/main.py) - tests never call this, they set
    their own local tracking URI directly instead (see
    tests/test_backend/conftest.py), for the same reason
    `pipelines/ml/mlflow_utils.use_shared_tracking_uri` is split out
    identically: calling it after a test has pointed mlflow at a local
    sqlite file would clobber that with a server URL that doesn't exist in
    a test environment."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)


def load_champion_model(domain: str):
    """Loads the current champion model for `domain` (e.g. "gdp" resolves to
    "gdp_forecast@champion"). Raises MlflowException if none is deployed
    yet - the /predictions route turns that into a 404."""
    model_name = f"{domain}_forecast"
    return mlflow.pyfunc.load_model(f"models:/{model_name}@{CHAMPION_ALIAS}")


def get_champion_version(domain: str) -> str | None:
    """The version number currently aliased `champion` for `domain`, or None
    if nothing's been promoted yet - lets /predictions report which model
    version produced a forecast."""
    model_name = f"{domain}_forecast"
    try:
        version = MlflowClient().get_model_version_by_alias(model_name, CHAMPION_ALIAS)
    except MlflowException:
        return None
    return str(version.version)


def list_registered_models() -> list[dict[str, Any]]:
    """One summary row per registered model: name, latest version, whether
    (and which version) is the current champion, and that champion's
    metrics - backs the `/models` endpoint."""
    client = MlflowClient()
    summaries = []
    for model in client.search_registered_models():
        versions = client.search_model_versions(f"name='{model.name}'")
        latest = max((int(v.version) for v in versions), default=None)
        try:
            champion = client.get_model_version_by_alias(model.name, CHAMPION_ALIAS)
        except MlflowException:
            champion = None
        summaries.append(
            {
                "name": model.name,
                "latest_version": str(latest) if latest is not None else None,
                "champion_version": str(champion.version) if champion else None,
                "metrics": client.get_run(champion.run_id).data.metrics if champion else {},
            }
        )
    return summaries
