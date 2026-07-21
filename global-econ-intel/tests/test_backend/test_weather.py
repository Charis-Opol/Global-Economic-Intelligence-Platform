from __future__ import annotations


def test_returns_both_days_ordered_by_date(client):
    resp = client.get("/weather")
    body = resp.json()

    assert body["total"] == 2
    assert [row["date"] for row in body["items"]] == ["2026-07-19", "2026-07-20"]


def test_filters_by_coordinates(client):
    resp = client.get("/weather", params={"latitude": 0.3476, "longitude": 32.5825})
    assert resp.json()["total"] == 2

    resp = client.get("/weather", params={"latitude": 1.0, "longitude": 1.0})
    assert resp.json()["total"] == 0
