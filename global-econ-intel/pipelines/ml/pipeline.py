"""
End-to-end train step for one forecast domain (Day 2, Step 4/5).

Ties `train.train_and_evaluate` (fit + evaluate) to `mlflow_utils.log_run`
(persist), so the Airflow "train" task is one function call. Registration
and deployment are deliberately kept out of this function - see
`airflow/dags/_training_dag_factory.py` for why those stay separate tasks.
"""
from __future__ import annotations

import duckdb

from pipelines.ml import mlflow_utils
from pipelines.ml.models import FORECAST_SPECS
from pipelines.ml.train import train_and_evaluate


def run_training(con: duckdb.DuckDBPyConnection, domain: str) -> mlflow_utils.LoggedRun:
    spec = FORECAST_SPECS[domain]
    mlflow_utils.configure_tracking(spec.model_name)
    result = train_and_evaluate(con, spec)
    return mlflow_utils.log_run(
        sklearn_model=result.model, params=result.params, metrics=result.metrics
    )
