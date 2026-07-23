"""
MLflow tracking + registry wrapper (Day 2, Step 3).

Thin wrapper so the training pipelines (Step 4) and the nightly DAG (Step 5)
never call the mlflow SDK directly - mirrors this project's existing pattern
of wrapping external services (`BronzeWriter` wraps boto3; this wraps mlflow).

Deployment uses the modern alias API (`champion`) rather than the
now-discouraged stage API (Staging/Production) - a registered model version
is promoted by pointing the "champion" alias at it, only once it beats
whatever version currently holds that alias (see `should_promote`). Fully
testable against a local sqlite-backed tracking URI with no live server
running, the same way the ephemeral GX context and in-memory DuckDB are used
elsewhere in this repo - the Model Registry needs a database-backed store
(sqlite qualifies; a plain local file store does not), which is also exactly
what the real deployment already uses (Postgres).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import mlflow
from mlflow.entities.model_registry import ModelVersion
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from config.settings import shared_settings

CHAMPION_ALIAS = "champion"


@dataclass
class LoggedRun:
    """What the "train" stage hands the "register" stage - an MLflow run id
    and its model URI, small enough to pass through Airflow XCom. Never the
    model object itself."""

    run_id: str
    model_uri: str
    mae: float
    rmse: float


def use_shared_tracking_uri() -> None:
    """Points the mlflow SDK at the shared tracking server. Production
    entrypoints (Airflow tasks, the backend) call this once at process
    start. Tests deliberately never call it - they call
    `mlflow.set_tracking_uri(...)` themselves (see the `mlflow_tracking`
    fixture) to point at a local sqlite file, and this function must not be
    called afterward or it would clobber that override with the real
    server's URL, which doesn't exist in a test environment."""
    mlflow.set_tracking_uri(shared_settings.mlflow_tracking_uri)


def configure_tracking(experiment_name: str) -> None:
    """Selects/creates the experiment that `log_run` will log under.
    Assumes the tracking URI has already been set - either by
    `use_shared_tracking_uri()` in production, or directly by a test."""
    mlflow.set_experiment(experiment_name)


def log_run(
    *, sklearn_model: Any, params: dict[str, Any], metrics: dict[str, float]
) -> LoggedRun:
    """Logs one training run (params, metrics, the sklearn model artifact)
    WITHOUT registering it - registration is `register_model`'s job, kept
    separate so a nightly DAG can observe/retry Train and Register as
    distinct tasks."""
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        # mlflow.sklearn.log_model()'s default serialization_format ("skops")
        # runs a security audit on load that rejects raw numpy ufunc
        # references (np.log1p/np.expm1, used by the log-scale forecast
        # models' TransformedTargetRegressor) as "untrusted types" - these
        # are our own trusted internal models, not third-party artifacts, so
        # cloudpickle (which has no such allowlist to fight) is the right
        # tool here rather than trying to get specific numpy internals onto
        # skops' trust list.
        mlflow.sklearn.log_model(
            sklearn_model, name="model", serialization_format="cloudpickle"
        )
        return LoggedRun(
            run_id=run.info.run_id,
            model_uri=f"runs:/{run.info.run_id}/model",
            mae=metrics["mae"],
            rmse=metrics["rmse"],
        )


def register_model(model_name: str, model_uri: str) -> str:
    """Registers an already-logged run's model artifact as a new version of
    `model_name`. Returns the new version number as a string - MLflow's own
    return type is inconsistent (int here, str elsewhere in the SDK), and a
    string is what's safe to pass through Airflow XCom and compare later."""
    result = mlflow.register_model(model_uri, model_name)
    return str(result.version)


def get_champion_version(model_name: str) -> ModelVersion | None:
    """The registered model version currently aliased `champion`, or None if
    nothing has been promoted for this model yet."""
    client = MlflowClient()
    try:
        return client.get_model_version_by_alias(model_name, CHAMPION_ALIAS)
    except MlflowException:
        return None


def champion_metric(model_name: str, metric_key: str = "mae") -> float | None:
    version = get_champion_version(model_name)
    if version is None:
        return None
    run = MlflowClient().get_run(version.run_id)
    return run.data.metrics.get(metric_key)


def should_promote(model_name: str, candidate_mae: float) -> bool:
    """The deploy gate: promote if there's no champion yet, or the
    candidate beats the current champion's MAE (lower is better)."""
    current_mae = champion_metric(model_name)
    return current_mae is None or candidate_mae < current_mae


def promote_to_champion(model_name: str, version: str) -> None:
    MlflowClient().set_registered_model_alias(model_name, CHAMPION_ALIAS, version)


def load_champion_model(model_name: str):
    """Loads the model currently aliased `champion`, ready for `.predict(...)`."""
    return mlflow.pyfunc.load_model(f"models:/{model_name}@{CHAMPION_ALIAS}")


def list_registered_models() -> list[dict[str, Any]]:
    """One summary row per registered model: name, latest version, whether
    (and which version) is the current champion, and that champion's
    metrics - backs the `/models` endpoint (Day 2, Step 6)."""
    client = MlflowClient()
    summaries = []
    for model in client.search_registered_models():
        versions = client.search_model_versions(f"name='{model.name}'")
        latest = max((int(v.version) for v in versions), default=None)
        champion = get_champion_version(model.name)
        summaries.append(
            {
                "name": model.name,
                "latest_version": str(latest) if latest is not None else None,
                "champion_version": str(champion.version) if champion else None,
                "metrics": (
                    MlflowClient().get_run(champion.run_id).data.metrics if champion else {}
                ),
            }
        )
    return summaries
