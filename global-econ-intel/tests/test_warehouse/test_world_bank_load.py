from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country_iso3": ["UGA", "UGA", "KEN"],
            "country_name": ["Uganda", "Uganda", "Kenya"],
            "indicator_id": ["NY.GDP.MKTP.CD"] * 3,
            "year": [2020, 2021, 2021],
            "gdp_usd": [3.7e10, 4.0e10, 1.1e11],
            "gdp_growth_rate": [None, 0.081, 0.05],
        }
    )


def test_loads_countries_and_gdp_facts(loader):
    loader.load_world_bank(_silver())

    # One dimension member per distinct country, not per row.
    countries = loader.con.execute(
        "SELECT country_iso3, country_name FROM dim_country ORDER BY country_iso3"
    ).fetchall()
    assert countries == [("KEN", "Kenya"), ("UGA", "Uganda")]

    # Every silver row becomes a fact, joined back to its country.
    rows = loader.con.execute(
        """
        SELECT c.country_iso3, f.year, f.gdp_usd, f.gdp_growth_rate
        FROM fact_gdp f JOIN dim_country c USING (country_key)
        ORDER BY c.country_iso3, f.year
        """
    ).fetchall()
    assert rows == [
        ("KEN", 2021, 1.1e11, 0.05),
        ("UGA", 2020, 3.7e10, None),
        ("UGA", 2021, 4.0e10, 0.081),
    ]


def test_reload_is_idempotent_and_refreshes_measures(loader):
    loader.load_world_bank(_silver())

    revised = _silver()
    revised.loc[revised["year"] == 2021, "gdp_usd"] = 4.2e10  # a World Bank revision
    loader.load_world_bank(revised)

    # No duplicate countries or facts after the second load.
    assert loader.con.execute("SELECT count(*) FROM dim_country").fetchone()[0] == 2
    assert loader.con.execute("SELECT count(*) FROM fact_gdp").fetchone()[0] == 3

    # The revised value overwrites the grain rather than adding a row.
    updated = loader.con.execute(
        """
        SELECT f.gdp_usd FROM fact_gdp f JOIN dim_country c USING (country_key)
        WHERE c.country_iso3 = 'UGA' AND f.year = 2021
        """
    ).fetchone()[0]
    assert updated == 4.2e10
