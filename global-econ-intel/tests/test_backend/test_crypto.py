from __future__ import annotations


def test_filters_by_coin_id(client):
    resp = client.get("/crypto", params={"coin_id": "bitcoin"})
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["symbol"] == "btc"
    assert body["items"][0]["price_usd"] == 65000.0


def test_no_filter_returns_all_coins(client):
    resp = client.get("/crypto")
    assert resp.json()["total"] == 2
