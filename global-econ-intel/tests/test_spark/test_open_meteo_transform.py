from __future__ import annotations

from transforms.open_meteo import transform


def _doc(logical_date: str, fetched_at: str, dates: list[str], precip: list[float]) -> dict:
    return {
        "source": "open_meteo",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [
            {
                "latitude": 0.3476,
                "longitude": 32.5825,
                "daily": {
                    "time": dates,
                    "temperature_2m_max": [27.0] * len(dates),
                    "temperature_2m_min": [17.0] * len(dates),
                    "precipitation_sum": precip,
                },
            }
        ],
    }


def test_explodes_daily_arrays_into_rows(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        ["2026-07-19", "2026-07-20"],
        [0.0, 4.2],
    )
    result = transform(make_bronze_df([doc])).orderBy("date").collect()

    assert len(result) == 2
    assert result[1].precipitation_mm == 4.2


def test_overlapping_ingestion_windows_dedupe_by_date(make_bronze_df):
    # Each run re-fetches a rolling past_days window, so the same date
    # legitimately appears in two different bronze documents.
    run1 = _doc(
        "2026-07-19T00:00:00+00:00", "2026-07-19T01:00:00+00:00", ["2026-07-18", "2026-07-19"], [1.0, 2.0]
    )
    run2 = _doc(
        "2026-07-20T00:00:00+00:00", "2026-07-20T01:00:00+00:00", ["2026-07-19", "2026-07-20"], [2.5, 3.0]
    )
    result = transform(make_bronze_df([run1, run2])).orderBy("date").collect()

    dates = [row.date.isoformat() for row in result]
    assert dates == ["2026-07-18", "2026-07-19", "2026-07-20"]
    # 2026-07-19 appeared in both runs; the more recently fetched value (from run2) should win.
    july_19 = next(r for r in result if r.date.isoformat() == "2026-07-19")
    assert july_19.precipitation_mm == 2.5


def test_rainfall_anomaly_is_deviation_from_rolling_average(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        ["2026-07-18", "2026-07-19", "2026-07-20"],
        [0.0, 0.0, 30.0],
    )
    result = transform(make_bronze_df([doc])).orderBy("date").collect()

    last_day = result[-1]
    # rolling avg over all 3 days = 10.0, so anomaly = 30 - 10 = 20
    assert round(last_day.precip_30d_avg_mm, 2) == 10.0
    assert round(last_day.rainfall_anomaly_mm, 2) == 20.0
