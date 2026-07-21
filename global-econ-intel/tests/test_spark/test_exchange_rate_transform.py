from __future__ import annotations

from transforms.exchange_rate import transform


def _doc(logical_date: str, fetched_at: str, rates: dict) -> dict:
    return {
        "source": "exchange_rate",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [
            {
                "result": "success",
                "base_code": "USD",
                "time_last_update_utc": fetched_at,
                "rates": rates,
            }
        ],
    }


def test_explodes_rates_map_into_rows(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", {"UGX": 3700.0, "EUR": 0.92})
    result = transform(make_bronze_df([doc])).orderBy("currency").collect()

    assert len(result) == 2
    assert {r.currency for r in result} == {"UGX", "EUR"}


def test_zero_or_negative_rates_are_dropped(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", {"UGX": 3700.0, "BAD": 0.0})
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 1
    assert result[0].currency == "UGX"


def test_momentum_feature_across_days(make_bronze_df):
    day1 = _doc("2026-07-19T00:00:00+00:00", "2026-07-19T01:00:00+00:00", {"UGX": 3700.0})
    day2 = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", {"UGX": 3737.0})

    result = transform(make_bronze_df([day1, day2])).orderBy("logical_date").collect()

    assert result[0].exchange_momentum is None
    assert round(result[1].exchange_momentum, 4) == 0.01  # (3737-3700)/3700
