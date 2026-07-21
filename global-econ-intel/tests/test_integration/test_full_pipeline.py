"""
Day 2, Step 8 - full pipeline integration test.

No mocking anywhere in this chain: a real in-memory warehouse, a real
sklearn model trained against it, a real (sqlite-backed) MLflow tracking
store and Model Registry, and a real FastAPI app serving predictions from
whatever ends up aliased "champion" - exactly the path a nightly Airflow
training DAG and a live backend would each take independently, just against
a local sqlite store instead of the real Postgres-backed one.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.db import get_connection
from app.main import app
from pipelines.ml import mlflow_utils
from pipelines.ml.pipeline import run_training


def test_train_register_promote_then_serve_a_real_prediction(warehouse, mlflow_tracking):
    logged = run_training(warehouse, "gdp")
    version = mlflow_utils.register_model("gdp_forecast", logged.model_uri)
    mlflow_utils.promote_to_champion("gdp_forecast", version)

    # pipelines.ml and the backend both call the plain mlflow SDK, which
    # keeps its tracking URI as process-global state - pointing it at the
    # sqlite fixture above (done by the `mlflow_tracking` fixture) is enough
    # for the backend's own mlflow_client calls to see the same registry.
    app.dependency_overrides[get_connection] = lambda: warehouse
    token = create_access_token(subject="integration-test")
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})

    try:
        predict_resp = client.get("/predictions", params={"domain": "gdp", "country": "UGA"})
        assert predict_resp.status_code == 200
        body = predict_resp.json()
        assert isinstance(body["predicted_value"], float)
        assert body["model_version"] == version

        models_resp = client.get("/models")
        assert models_resp.status_code == 200
        models = {m["name"]: m for m in models_resp.json()}
        assert models["gdp_forecast"]["champion_version"] == version
        assert models["gdp_forecast"]["metrics"]["mae"] == logged.mae
    finally:
        app.dependency_overrides.pop(get_connection, None)


def test_predictions_without_a_champion_yet_is_404(warehouse, mlflow_tracking):
    # A fresh mlflow store with no training run yet - the champion alias
    # genuinely doesn't exist, which must surface as 404, not a 500.
    app.dependency_overrides[get_connection] = lambda: warehouse
    token = create_access_token(subject="integration-test")
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})

    try:
        resp = client.get("/predictions", params={"domain": "gdp", "country": "UGA"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_connection, None)


def test_registering_a_new_version_does_not_auto_promote_it(warehouse, mlflow_tracking):
    # Register/deploy are deliberately separate steps (see
    # _training_dag_factory.py) - registering version 2 must not silently
    # move the champion alias off version 1 without an explicit promotion.
    first = run_training(warehouse, "gdp")
    v1 = mlflow_utils.register_model("gdp_forecast", first.model_uri)
    mlflow_utils.promote_to_champion("gdp_forecast", v1)

    second = run_training(warehouse, "gdp")
    v2 = mlflow_utils.register_model("gdp_forecast", second.model_uri)

    assert v2 != v1
    assert str(mlflow_utils.get_champion_version("gdp_forecast").version) == v1
