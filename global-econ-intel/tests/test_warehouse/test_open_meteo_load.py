from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    # Two calendar days at one location (Kampala).
    return pd.DataFrame(
        {
            "date": ["2026-07-19", "2026-07-20"],
            "latitude": [0.3476, 0.3476],
            "longitude": [32.5825, 32.5825],
            "temp_max_c": [27.1, 26.4],
            "temp_min_c": [17.0, 16.8],
            "precipitation_mm": [2.5, 0.0],
            "precip_30d_avg_mm": [3.1, 3.0],
            "rainfall_anomaly_mm": [-0.6, -3.0],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )


def test_one_location_member_and_a_fact_per_day(loader):
    loader.load_open_meteo(_silver())

    assert loader.con.execute("SELECT count(*) FROM dim_location").fetchone()[0] == 1

    rows = loader.con.execute(
        """
        SELECT d.full_date, f.precipitation_mm, f.rainfall_anomaly_mm
        FROM fact_weather f JOIN dim_date d USING (date_key)
        ORDER BY d.full_date
        """
    ).fetchall()
    assert rows == [
        (pd.Timestamp("2026-07-19").date(), 2.5, -0.6),
        (pd.Timestamp("2026-07-20").date(), 0.0, -3.0),
    ]


def test_dim_date_carries_calendar_attributes(loader):
    loader.load_open_meteo(_silver())

    # 2026-07-19 is a Sunday - exercises day_of_week and is_weekend.
    sunday = loader.con.execute(
        "SELECT day_name, day_of_week, is_weekend FROM dim_date WHERE full_date = DATE '2026-07-19'"
    ).fetchone()
    assert sunday == ("Sunday", 0, True)


def test_overlapping_reload_keeps_one_row_per_day(loader):
    loader.load_open_meteo(_silver())
    loader.load_open_meteo(_silver())  # rolling window re-pulls the same days

    assert loader.con.execute("SELECT count(*) FROM fact_weather").fetchone()[0] == 2
    assert loader.con.execute("SELECT count(*) FROM dim_location").fetchone()[0] == 1
