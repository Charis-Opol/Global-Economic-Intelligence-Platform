from __future__ import annotations

from pipelines.ml import mlflow_utils
from pipelines.ml.pipeline import run_training


def test_run_training_logs_a_run_for_every_domain(warehouse, mlflow_tracking):
    logged = run_training(warehouse, "gdp")

    assert logged.run_id
    assert logged.model_uri.endswith("/model")
    assert logged.mae >= 0


def test_register_and_promote_after_training(warehouse, mlflow_tracking):
    logged = run_training(warehouse, "crypto")
    version = mlflow_utils.register_model("crypto_forecast", logged.model_uri)

    assert mlflow_utils.should_promote("crypto_forecast", logged.mae) is True
    mlflow_utils.promote_to_champion("crypto_forecast", version)

    assert mlflow_utils.champion_metric("crypto_forecast") == logged.mae
