from __future__ import annotations

import pandas as pd


def test_view_gdp_carries_lag_and_rolling_average(loader):
    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA", "UGA"],
                "country_name": ["Uganda"] * 3,
                "indicator_id": ["NY.GDP.MKTP.CD"] * 3,
                "year": [2020, 2021, 2022],
                "gdp_usd": [3.7e10, 4.0e10, 4.4e10],
                "gdp_growth_rate": [None, 0.081, 0.10],
            }
        )
    )
    rows = loader.con.execute(
        "SELECT year, gdp_usd, lag1_gdp_usd, gdp_3yr_avg_usd FROM view_gdp ORDER BY year"
    ).fetchall()

    assert rows[0] == (2020, 3.7e10, None, 3.7e10)  # no prior year -> lag null, avg = itself
    assert rows[1] == (2021, 4.0e10, 3.7e10, 38.5e9)
    assert round(rows[2][3], 2) == round((3.7e10 + 4.0e10 + 4.4e10) / 3, 2)


def test_agg_gdp_by_country_computes_cagr():
    from pipelines.warehouse.loader import WarehouseLoader
    from pipelines.warehouse.schema import connect, create_schema

    con = connect(":memory:")
    create_schema(con)
    loader = WarehouseLoader(con)
    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA"],
                "country_name": ["Uganda", "Uganda"],
                "indicator_id": ["NY.GDP.MKTP.CD"] * 2,
                "year": [2020, 2022],
                "gdp_usd": [100.0, 121.0],  # 10% CAGR over 2 years
                "gdp_growth_rate": [None, 0.21],
            }
        )
    )
    row = con.execute(
        "SELECT first_year, latest_year, first_year_gdp_usd, latest_gdp_usd, gdp_cagr "
        "FROM agg_gdp_by_country WHERE country_iso3 = 'UGA'"
    ).fetchone()
    con.close()

    assert row[:4] == (2020, 2022, 100.0, 121.0)
    assert round(row[4], 4) == 0.1  # (121/100)^(1/2) - 1


def test_view_exchange_rate_rolling_average_window(loader):
    loader.load_exchange_rate(
        pd.DataFrame(
            {
                "base_code": ["USD", "USD", "USD"],
                "currency": ["UGX", "UGX", "UGX"],
                "rate": [3700.0, 3710.0, 3720.0],
                "exchange_momentum": [None, 0.0027, 0.0027],
                "logical_date": ["2026-07-18", "2026-07-19", "2026-07-20"],
            }
        )
    )
    rows = loader.con.execute(
        "SELECT date, rate, lag1_rate, rate_7d_avg FROM view_exchange_rate ORDER BY date"
    ).fetchall()

    assert rows[0][2] is None  # first day has no prior rate
    assert rows[2][2] == 3710.0
    assert round(rows[2][3], 4) == round((3700.0 + 3710.0 + 3720.0) / 3, 4)


def test_agg_exchange_rate_monthly_rolls_up_by_month(loader):
    loader.load_exchange_rate(
        pd.DataFrame(
            {
                "base_code": ["USD", "USD", "USD"],
                "currency": ["UGX", "UGX", "UGX"],
                "rate": [3700.0, 3710.0, 3720.0],
                "exchange_momentum": [None, 0.0027, 0.0027],
                "logical_date": ["2026-07-18", "2026-07-19", "2026-07-20"],
            }
        )
    )
    row = loader.con.execute(
        "SELECT year, month, avg_rate, min_rate, max_rate, days_observed "
        "FROM agg_exchange_rate_monthly WHERE base_code = 'USD' AND currency = 'UGX'"
    ).fetchone()

    assert row == (2026, 7, 3710.0, 3700.0, 3720.0, 3)


def test_view_crypto_and_view_inflation_carry_lag_features(loader):
    loader.load_coingecko(
        pd.DataFrame(
            {
                "coin_id": ["bitcoin", "bitcoin"],
                "symbol": ["btc", "btc"],
                "name": ["Bitcoin", "Bitcoin"],
                "price_usd": [65000.0, 66000.0],
                "market_cap_usd": [1.28e12, 1.29e12],
                "volume_usd": [2.5e10, 2.6e10],
                "price_change_pct_24h": [1.5, 1.2],
                "volatility_7d": [2.1, 2.0],
                "logical_date": ["2026-07-20", "2026-07-21"],
            }
        )
    )
    loader.load_world_bank_inflation(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA"],
                "country_name": ["Uganda", "Uganda"],
                "indicator_id": ["FP.CPI.TOTL.ZG"] * 2,
                "year": [2021, 2022],
                "inflation_pct": [5.0, 7.5],
                "inflation_trend": [None, 2.5],
            }
        )
    )

    crypto_rows = loader.con.execute(
        "SELECT date, price_usd, lag1_price_usd FROM view_crypto ORDER BY date"
    ).fetchall()
    assert crypto_rows[1][2] == 65000.0

    inflation_rows = loader.con.execute(
        "SELECT year, inflation_pct, lag1_inflation_pct FROM view_inflation ORDER BY year"
    ).fetchall()
    assert inflation_rows[1] == (2022, 7.5, 5.0)
