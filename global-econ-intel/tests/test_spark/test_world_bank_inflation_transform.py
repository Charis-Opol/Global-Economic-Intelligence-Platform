from __future__ import annotations

from transforms.world_bank_inflation import transform


def _doc(logical_date: str, fetched_at: str, records: list[dict]) -> dict:
    return {
        "source": "world_bank_inflation",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [{"meta": {"page": 1, "pages": 1, "per_page": 1000, "total": len(records)}, "records": records}],
    }


def _record(country_iso3: str, year: str, value):
    return {
        "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
        "country": {"id": country_iso3[:2], "value": "Testland"},
        "countryiso3code": country_iso3,
        "date": year,
        "value": value,
        "unit": "",
        "obs_status": "",
        "decimal": 0,
    }


def test_computes_year_over_year_percentage_point_trend(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [_record("UGA", "2022", 5.0), _record("UGA", "2023", 7.5)],
    )
    result = transform(make_bronze_df([doc])).orderBy("year").collect()

    assert len(result) == 2
    assert result[0].inflation_trend is None  # no prior year to compare against
    assert round(result[1].inflation_trend, 4) == 2.5  # 7.5 - 5.0 points, not a ratio


def test_null_inflation_value_is_kept_not_dropped(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("UGA", "2024", None)])
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 1
    assert result[0].inflation_pct is None


def test_rerun_for_same_year_keeps_most_recently_fetched(make_bronze_df):
    stale = _doc("2026-07-19T00:00:00+00:00", "2026-07-19T01:00:00+00:00", [_record("UGA", "2023", 6.0)])
    fresh = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("UGA", "2023", 7.5)])

    result = transform(make_bronze_df([stale, fresh])).collect()

    assert len(result) == 1
    assert result[0].inflation_pct == 7.5


def test_missing_country_code_is_dropped(make_bronze_df):
    doc = _doc("2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", [_record("", "2023", 5.0)])
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 0
