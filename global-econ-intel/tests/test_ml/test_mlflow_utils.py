from __future__ import annotations

from sklearn.linear_model import LinearRegression

from pipelines.ml import mlflow_utils


def _fit_dummy_model():
    import numpy as np

    return LinearRegression().fit(np.array([[1.0], [2.0], [3.0]]), np.array([2.0, 4.0, 6.0]))


def _log_and_register(model_name: str, mae: float, rmse: float) -> str:
    logged = mlflow_utils.log_run(
        sklearn_model=_fit_dummy_model(), params={"model_type": "linear_regression"},
        metrics={"mae": mae, "rmse": rmse},
    )
    return mlflow_utils.register_model(model_name, logged.model_uri)


def test_log_run_returns_run_id_and_model_uri(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")

    logged = mlflow_utils.log_run(
        sklearn_model=_fit_dummy_model(),
        params={"model_type": "linear_regression"},
        metrics={"mae": 1.5, "rmse": 2.0},
    )

    assert logged.run_id
    assert logged.model_uri == f"runs:/{logged.run_id}/model"
    assert logged.mae == 1.5


def test_register_model_creates_version_one_on_first_call(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")
    version = _log_and_register("gdp_forecast", mae=1.5, rmse=2.0)

    assert version == "1"


def test_no_champion_before_first_promotion(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")
    _log_and_register("gdp_forecast", mae=1.5, rmse=2.0)

    assert mlflow_utils.get_champion_version("gdp_forecast") is None
    assert mlflow_utils.champion_metric("gdp_forecast") is None
    # No champion yet - the very first trained version should always promote.
    assert mlflow_utils.should_promote("gdp_forecast", candidate_mae=999.0) is True


def test_should_promote_only_when_candidate_beats_champion(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")
    version = _log_and_register("gdp_forecast", mae=2.0, rmse=3.0)
    mlflow_utils.promote_to_champion("gdp_forecast", version)

    assert mlflow_utils.champion_metric("gdp_forecast") == 2.0
    assert mlflow_utils.should_promote("gdp_forecast", candidate_mae=1.5) is True   # better
    assert mlflow_utils.should_promote("gdp_forecast", candidate_mae=2.5) is False  # worse


def test_load_champion_model_predicts(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")
    version = _log_and_register("gdp_forecast", mae=1.0, rmse=1.0)
    mlflow_utils.promote_to_champion("gdp_forecast", version)

    model = mlflow_utils.load_champion_model("gdp_forecast")
    import numpy as np

    prediction = model.predict(np.array([[4.0]]))
    assert round(float(prediction[0]), 1) == 8.0  # y = 2x


def test_list_registered_models_reports_champion_and_metrics(mlflow_tracking):
    mlflow_utils.configure_tracking("test_experiment")
    version = _log_and_register("gdp_forecast", mae=1.2, rmse=1.8)
    mlflow_utils.promote_to_champion("gdp_forecast", version)

    models = mlflow_utils.list_registered_models()

    assert len(models) == 1
    assert models[0]["name"] == "gdp_forecast"
    assert models[0]["champion_version"] == version
    assert models[0]["metrics"]["mae"] == 1.2
