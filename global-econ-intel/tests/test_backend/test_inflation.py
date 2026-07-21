from __future__ import annotations


def test_filters_by_country_and_year(client):
    resp = client.get("/inflation", params={"country": "uga", "year_min": 2021})
    body = resp.json()

    assert body["total"] == 1
    row = body["items"][0]
    assert row["year"] == 2021
    assert row["inflation_pct"] == 5.0
    assert row["inflation_trend"] == 1.0
    assert row["lag1_inflation_pct"] == 4.0  # feature column from view_inflation


def test_no_filters_returns_all_countries(client):
    resp = client.get("/inflation")
    assert resp.json()["total"] == 3
