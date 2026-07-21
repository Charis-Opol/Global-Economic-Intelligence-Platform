from __future__ import annotations

import httpx

from app import airflow_client


def test_reports_state_for_every_training_dag(client, monkeypatch):
    def _fake_latest(dag_id):
        return {
            "state": "success",
            "execution_date": "2026-07-20T00:00:00+00:00",
            "start_date": "2026-07-20T00:00:01+00:00",
            "end_date": "2026-07-20T00:05:00+00:00",
        }

    monkeypatch.setattr(airflow_client, "get_latest_dag_run", _fake_latest)

    resp = client.get("/pipeline-status")
    body = resp.json()

    assert resp.status_code == 200
    assert len(body) == len(airflow_client.TRAINING_DAG_IDS)
    assert {entry["dag_id"] for entry in body} == set(airflow_client.TRAINING_DAG_IDS)
    assert all(entry["state"] == "success" for entry in body)


def test_a_dag_that_has_never_run_reports_null_state(client, monkeypatch):
    monkeypatch.setattr(airflow_client, "get_latest_dag_run", lambda dag_id: None)

    resp = client.get("/pipeline-status")
    body = resp.json()

    assert all(entry["state"] is None for entry in body)


def test_one_unreachable_dag_does_not_break_the_others(client, monkeypatch):
    def _flaky(dag_id):
        if dag_id == airflow_client.TRAINING_DAG_IDS[0]:
            raise httpx.ConnectError("connection refused")
        return {"state": "success", "execution_date": None, "start_date": None, "end_date": None}

    monkeypatch.setattr(airflow_client, "get_latest_dag_run", _flaky)

    resp = client.get("/pipeline-status")
    body = {entry["dag_id"]: entry["state"] for entry in resp.json()}

    assert body[airflow_client.TRAINING_DAG_IDS[0]] is None
    assert body[airflow_client.TRAINING_DAG_IDS[1]] == "success"
