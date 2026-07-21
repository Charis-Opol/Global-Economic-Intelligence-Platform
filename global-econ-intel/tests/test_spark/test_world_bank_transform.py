from __future__ import annotations

from transforms.world_bank import transform


def _doc(logical_date: str, fetched_at: str, records: list[dict]) -> dict:
    return {
        "source": "world_bank",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [{"meta": {"page": 1, "pages": 1, "per_page": 1000, "total": len(records)}, "records": records}],
    }


def _record(country_iso3: str, year: str, value):
    return {
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
        "country": {"id": country_iso3[:2], "value": "Testland"},
        "countryiso3code": country_iso3,
        "date": year,
        "value": value,
        "unit": "",
        "obs_status": "",
        "decimal": 0,
    }


def test_normalizes_and_computes_growth_rate(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [_record("UGA", "2022", 100.0), _record("UGA", "2023", 110.0)],
    )
    result = transform(make_bronze_df([doc])).orderBy("year").collect()

    assert len(result) == 2
    assert result[0].gdp_growth_rate is None  # no prior year to compare against
    assert round(result[1].gdp_growth_rate, 4) == 0.1  # (110-100)/100


def test_null_gdp_value_is_kept_not_dropped(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("UGA", "2024", None)])
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 1
    assert result[0].gdp_usd is None


def test_rerun_for_same_year_keeps_most_recently_fetched(make_bronze_df):
    # Simulates the World Bank revising a figure and the DAG re-ingesting.
    stale = _doc("2026-07-19T00:00:00+00:00", "2026-07-19T01:00:00+00:00", [_record("UGA", "2023", 105.0)])
    fresh = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("UGA", "2023", 110.0)])

    result = transform(make_bronze_df([stale, fresh])).collect()

    assert len(result) == 1  # deduped down to one row for (UGA, 2023)
    assert result[0].gdp_usd == 110.0


def test_missing_country_code_is_dropped(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("", "2023", 50.0)])
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 0
