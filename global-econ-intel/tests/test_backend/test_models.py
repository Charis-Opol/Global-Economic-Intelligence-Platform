from __future__ import annotations

from app import mlflow_client


def test_lists_registered_models(client, monkeypatch):
    monkeypatch.setattr(
        mlflow_client,
        "list_registered_models",
        lambda: [
            {
                "name": "gdp_forecast",
                "latest_version": "2",
                "champion_version": "1",
                "metrics": {"mae": 1.2, "rmse": 1.8},
            }
        ],
    )

    resp = client.get("/models")
    body = resp.json()

    assert resp.status_code == 200
    assert body == [
        {
            "name": "gdp_forecast",
            "latest_version": "2",
            "champion_version": "1",
            "metrics": {"mae": 1.2, "rmse": 1.8},
        }
    ]


def test_empty_registry_returns_empty_list(client, monkeypatch):
    monkeypatch.setattr(mlflow_client, "list_registered_models", lambda: [])

    resp = client.get("/models")
    assert resp.json() == []
