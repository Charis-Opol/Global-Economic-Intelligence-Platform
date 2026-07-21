from __future__ import annotations


def test_filters_by_base_and_quote(client):
    resp = client.get("/exchange", params={"base": "usd", "quote": "eur"})
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["rate"] == 0.92


def test_date_range_excludes_out_of_range_rows(client):
    resp = client.get("/exchange", params={"date_from": "2026-07-21"})
    assert resp.json()["total"] == 0


def test_no_filters_returns_both_pairs(client):
    resp = client.get("/exchange")
    body = resp.json()

    assert body["total"] == 2
    assert {row["currency"] for row in body["items"]} == {"UGX", "EUR"}
