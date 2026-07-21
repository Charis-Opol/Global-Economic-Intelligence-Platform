from __future__ import annotations

import numpy as np
import pytest
from mlflow.exceptions import MlflowException

from app import mlflow_client


class _FakeModel:
    """Deterministic stand-in for a loaded MLflow pyfunc model - these tests
    are about the router's request/response handling, not MLflow's own
    correctness (that's covered for real in tests/test_ml)."""

    def predict(self, df):
        return np.array([df.iloc[0].sum()])


def test_predicts_gdp_from_latest_feature_row(client, monkeypatch):
    monkeypatch.setattr(mlflow_client, "load_champion_model", lambda domain: _FakeModel())

    resp = client.get("/predictions", params={"domain": "gdp", "country": "uga"})
    body = resp.json()

    assert resp.status_code == 200
    assert body["domain"] == "gdp"
    assert body["entity"] == {"country": "UGA"}
    assert "lag1_gdp_usd" in body["based_on"]
    assert body["predicted_value"] == pytest.approx(
        body["based_on"]["lag1_gdp_usd"] + body["based_on"]["gdp_3yr_avg_usd"]
    )


def test_missing_required_param_is_400(client):
    resp = client.get("/predictions", params={"domain": "exchange_rate", "base": "usd"})  # no quote
    assert resp.status_code == 400


def test_unknown_domain_is_400(client):
    resp = client.get("/predictions", params={"domain": "nonsense"})
    assert resp.status_code == 400


def test_unknown_entity_is_404(client, monkeypatch):
    monkeypatch.setattr(mlflow_client, "load_champion_model", lambda domain: _FakeModel())
    resp = client.get("/predictions", params={"domain": "gdp", "country": "zzz"})
    assert resp.status_code == 404


def test_no_champion_model_deployed_is_404(client, monkeypatch):
    def _raise(domain):
        raise MlflowException("no champion alias")

    monkeypatch.setattr(mlflow_client, "load_champion_model", _raise)

    resp = client.get("/predictions", params={"domain": "gdp", "country": "uga"})
    assert resp.status_code == 404
