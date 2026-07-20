from __future__ import annotations

from pipelines.connectors.coingecko import CoinGeckoConnector
from tests.test_connectors.conftest import FakeResponse


def _coin(coin_id: str) -> dict:
    return {
        "id": coin_id,
        "symbol": coin_id[:3],
        "name": coin_id.capitalize(),
        "current_price": 100.0,
        "market_cap": 1_000_000.0,
        "total_volume": 50_000.0,
        "price_change_percentage_24h": 1.5,
    }


def test_bare_array_response_is_normalized(patch_session_get):
    patch_session_get([FakeResponse([_coin("bitcoin"), _coin("ethereum")])])
    connector = CoinGeckoConnector()

    result = connector.fetch_one()

    assert len(result.coins) == 2
    assert result.coins[0].id == "bitcoin"


def test_stops_paginating_once_page_is_short(patch_session_get):
    connector = CoinGeckoConnector()
    connector.per_page = 2  # small page size so the test doesn't need 100 fake coins
    patch_session_get(
        [
            FakeResponse([_coin("bitcoin"), _coin("ethereum")]),  # full page -> keep going
            FakeResponse([_coin("solana")]),  # short page -> stop
        ]
    )

    pages = list(connector.fetch_all())

    assert len(pages) == 2
    assert [c.id for p in pages for c in p.coins] == ["bitcoin", "ethereum", "solana"]


def test_respects_max_pages_cap(patch_session_get):
    connector = CoinGeckoConnector()
    connector.per_page = 1
    connector.max_pages = 2
    patch_session_get(
        [
            FakeResponse([_coin("bitcoin")]),
            FakeResponse([_coin("ethereum")]),
        ]
    )

    pages = list(connector.fetch_all())

    assert len(pages) == 2  # capped even though each page was "full"
