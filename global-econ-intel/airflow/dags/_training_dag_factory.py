"""
Factory for the four near-identical nightly training DAGs (Day 2, Step 5).

Extract+Train+Evaluate happen in one task - they share in-memory objects (a
feature DataFrame, a fitted model) that don't need to round-trip through
Airflow's XCom backend just to get split into separate tasks. Register and
Deploy are their own tasks, each passing only small metadata (a model URI, a
version string, an MAE) through XCom - never the model object itself, which
isn't XCom-safe and doesn't need to be: MLflow's own tracking store is where
the model artifact actually lives once `extract_train_evaluate` logs it.

Note the leading underscore: Airflow scans every .py file in `dags/` but
only registers objects that are actual DAG instances. This file defines none
at module level, so Airflow parses it harmlessly and moves on (same
convention as `_ingestion_dag_factory.py`).
"""
from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.decorators import task

from pipelines.ml import mlflow_utils
from pipelines.ml.models import FORECAST_SPECS
from pipelines.ml.pipeline import run_training
from pipelines.warehouse.schema import connect

DEFAULT_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def build_training_dag(domain: str) -> DAG:
    spec = FORECAST_SPECS[domain]

    with DAG(
        dag_id=f"train_{domain}_forecast",
        description=f"Nightly retrain of the {domain} forecast model.",
        schedule="@daily",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        default_args=DEFAULT_ARGS,
        tags=["ml", "training", domain],
    ) as dag:

        @task(task_id="extract_train_evaluate")
        def extract_train_evaluate() -> dict:
            mlflow_utils.use_shared_tracking_uri()
            con = connect(read_only=True)
            try:
                logged = run_training(con, domain)
            finally:
                con.close()
            return {"run_id": logged.run_id, "model_uri": logged.model_uri, "mae": logged.mae}

        @task(task_id="register")
        def register(logged: dict) -> dict:
            mlflow_utils.use_shared_tracking_uri()
            version = mlflow_utils.register_model(spec.model_name, logged["model_uri"])
            return {"version": version, "mae": logged["mae"]}

        @task(task_id="deploy")
        def deploy(registered: dict) -> None:
            mlflow_utils.use_shared_tracking_uri()
            if mlflow_utils.should_promote(spec.model_name, registered["mae"]):
                mlflow_utils.promote_to_champion(spec.model_name, registered["version"])

        deploy(register(extract_train_evaluate()))

    return dag
