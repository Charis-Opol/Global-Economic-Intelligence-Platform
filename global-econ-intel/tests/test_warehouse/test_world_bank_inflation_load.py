from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country_iso3": ["UGA", "UGA", "KEN"],
            "country_name": ["Uganda", "Uganda", "Kenya"],
            "indicator_id": ["FP.CPI.TOTL.ZG"] * 3,
            "year": [2022, 2023, 2023],
            "inflation_pct": [5.0, 7.5, 6.1],
            "inflation_trend": [None, 2.5, None],
        }
    )


def test_loads_countries_and_inflation_facts(loader):
    loader.load_world_bank_inflation(_silver())

    countries = loader.con.execute(
        "SELECT country_iso3, country_name FROM dim_country ORDER BY country_iso3"
    ).fetchall()
    assert countries == [("KEN", "Kenya"), ("UGA", "Uganda")]

    rows = loader.con.execute(
        """
        SELECT c.country_iso3, f.year, f.inflation_pct, f.inflation_trend
        FROM fact_inflation f JOIN dim_country c USING (country_key)
        ORDER BY c.country_iso3, f.year
        """
    ).fetchall()
    assert rows == [
        ("KEN", 2023, 6.1, None),
        ("UGA", 2022, 5.0, None),
        ("UGA", 2023, 7.5, 2.5),
    ]


def test_reload_is_idempotent_and_refreshes_measures(loader):
    loader.load_world_bank_inflation(_silver())

    revised = _silver()
    revised.loc[revised["year"] == 2023, "inflation_pct"] = 8.0  # UGA and KEN both 2023 rows
    loader.load_world_bank_inflation(revised)

    assert loader.con.execute("SELECT count(*) FROM dim_country").fetchone()[0] == 2
    assert loader.con.execute("SELECT count(*) FROM fact_inflation").fetchone()[0] == 3

    updated = loader.con.execute(
        """
        SELECT f.inflation_pct FROM fact_inflation f JOIN dim_country c USING (country_key)
        WHERE c.country_iso3 = 'UGA' AND f.year = 2023
        """
    ).fetchone()[0]
    assert updated == 8.0


def test_shares_dim_country_with_gdp(loader):
    # A country already loaded by GDP shouldn't get a second dim_country row
    # when inflation data for the same country arrives.
    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA"],
                "country_name": ["Uganda"],
                "indicator_id": ["NY.GDP.MKTP.CD"],
                "year": [2023],
                "gdp_usd": [4.0e10],
                "gdp_growth_rate": [0.05],
            }
        )
    )
    loader.load_world_bank_inflation(_silver())

    assert loader.con.execute(
        "SELECT count(*) FROM dim_country WHERE country_iso3 = 'UGA'"
    ).fetchone()[0] == 1
