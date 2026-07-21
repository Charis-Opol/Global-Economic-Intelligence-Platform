from __future__ import annotations

from transforms.coingecko import transform


def _coin(coin_id: str, price: float, change_pct: float) -> dict:
    return {
        "id": coin_id,
        "symbol": coin_id[:3],
        "name": coin_id.capitalize(),
        "current_price": price,
        "market_cap": price * 1_000_000,
        "total_volume": price * 1_000,
        "price_change_percentage_24h": change_pct,
    }


def _doc(logical_date: str, fetched_at: str, coins: list[dict]) -> dict:
    return {
        "source": "coingecko",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [{"coins": coins}],
    }


def test_flattens_coins_into_rows(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [_coin("bitcoin", 65000.0, 1.2), _coin("ethereum", 3400.0, -0.5)],
    )
    result = transform(make_bronze_df([doc])).orderBy("coin_id").collect()

    assert len(result) == 2
    assert result[0].coin_id == "bitcoin"


def test_dedupes_same_day_rerun_keeping_latest(make_bronze_df):
    stale = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_coin("bitcoin", 64000.0, 0.5)])
    fresh = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T05:00:00+00:00", [_coin("bitcoin", 65500.0, 1.5)])

    result = transform(make_bronze_df([stale, fresh])).collect()

    assert len(result) == 1
    assert result[0].price_usd == 65500.0


def test_volatility_reflects_variation_across_days(make_bronze_df):
    docs = [
        _doc(f"2026-07-{d:02d}T00:00:00+00:00", f"2026-07-{d:02d}T01:00:00+00:00", [_coin("bitcoin", 60000.0, pct)])
        for d, pct in zip(range(15, 22), [1.0, -1.0, 2.0, -2.0, 1.0, -1.0, 3.0])
    ]
    result = transform(make_bronze_df(docs)).orderBy("logical_date").collect()

    last_day = result[-1]
    assert last_day.volatility_7d is not None
    assert last_day.volatility_7d > 0
