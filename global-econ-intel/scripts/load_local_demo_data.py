"""
One-off: populate a local warehouse.duckdb with real data for a quick demo,
without standing up Bronze/Spark/Silver.

Fetches directly from each source's free, no-API-key endpoint via the
existing connectors, applies the same clean/dedupe/feature logic the Spark
transforms use (in pandas instead of PySpark, since there's no cluster
here), and loads through the real `WarehouseLoader` - so the resulting
warehouse is structurally identical to what the full pipeline would produce,
just for a single snapshot in time rather than an accumulated history.

News is skipped - NEWSAPI_KEY isn't set in this environment.

Usage (from the repo root - global-econ-intel/):
    python scripts/load_local_demo_data.py [--duckdb-path PATH]

Requires requirements-dev.txt installed (`pip install -r requirements-dev.txt`).
`--duckdb-path` defaults to `warehouse/warehouse.duckdb`, resolved relative
to wherever you run this from - matches what the local-dev backend
(`backend/.env.example`'s DUCKDB_PATH) reads from by default. See the root
README's "Running locally without Docker" section for the full local-dev
walkthrough this script is meant to be one step of.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

# Run directly (`python scripts/load_local_demo_data.py`), Python only puts
# scripts/ itself on sys.path, not the repo root - so `pipelines` wouldn't
# otherwise be importable. Insert the repo root explicitly instead of
# requiring callers to remember `PYTHONPATH=.` (the same reason
# tests/test_backend/conftest.py inserts backend/ onto sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.connectors.coingecko import CoinGeckoConnector  # noqa: E402
from pipelines.connectors.exchange_rate import ExchangeRateConnector  # noqa: E402
from pipelines.connectors.open_meteo import OpenMeteoConnector  # noqa: E402
from pipelines.connectors.world_bank import WorldBankConnector, WorldBankInflationConnector  # noqa: E402
from pipelines.warehouse.loader import WarehouseLoader  # noqa: E402
from pipelines.warehouse.schema import connect, create_schema  # noqa: E402

TODAY = date.today().isoformat()


def load_world_bank(loader: WarehouseLoader) -> int:
    records = WorldBankConnector().fetch_one().records
    rows = [
        {
            "country_iso3": r.countryiso3code,
            "country_name": r.country.value,
            "indicator_id": r.indicator.id,
            "year": int(r.date) if r.date else None,
            "gdp_usd": r.value,
        }
        for r in records
    ]
    df = pd.DataFrame(rows)
    df = df[df["country_iso3"].notna() & (df["country_iso3"] != "") & df["year"].notna()]
    df = df.drop_duplicates(subset=["country_iso3", "indicator_id", "year"]).sort_values(
        ["country_iso3", "year"]
    )
    df["gdp_growth_rate"] = df.groupby("country_iso3")["gdp_usd"].pct_change()
    loader.load_world_bank(df)
    return len(df)


def load_world_bank_inflation(loader: WarehouseLoader) -> int:
    records = WorldBankInflationConnector().fetch_one().records
    rows = [
        {
            "country_iso3": r.countryiso3code,
            "country_name": r.country.value,
            "indicator_id": r.indicator.id,
            "year": int(r.date) if r.date else None,
            "inflation_pct": r.value,
        }
        for r in records
    ]
    df = pd.DataFrame(rows)
    df = df[df["country_iso3"].notna() & (df["country_iso3"] != "") & df["year"].notna()]
    df = df.drop_duplicates(subset=["country_iso3", "indicator_id", "year"]).sort_values(
        ["country_iso3", "year"]
    )
    df["inflation_trend"] = df.groupby("country_iso3")["inflation_pct"].diff()
    loader.load_world_bank_inflation(df)
    return len(df)


def load_open_meteo(loader: WarehouseLoader) -> int:
    resp = OpenMeteoConnector().fetch_one()
    daily = resp.daily
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(daily.time).date,
            "latitude": resp.latitude,
            "longitude": resp.longitude,
            "temp_max_c": daily.temperature_2m_max,
            "temp_min_c": daily.temperature_2m_min,
            "precipitation_mm": daily.precipitation_sum,
        }
    ).sort_values("date")
    df["precip_30d_avg_mm"] = df["precipitation_mm"].rolling(30, min_periods=1).mean()
    df["rainfall_anomaly_mm"] = df["precipitation_mm"] - df["precip_30d_avg_mm"]
    loader.load_open_meteo(df)
    return len(df)


def load_exchange_rate(loader: WarehouseLoader) -> int:
    resp = ExchangeRateConnector().fetch_one()
    rows = [
        {"base_code": resp.base_code, "currency": code, "rate": rate}
        for code, rate in resp.rates.items()
        if rate and rate > 0
    ]
    df = pd.DataFrame(rows)
    df["exchange_momentum"] = None  # single snapshot - no prior day to compare against
    df["logical_date"] = TODAY
    loader.load_exchange_rate(df)
    return len(df)


def load_coingecko(loader: WarehouseLoader) -> int:
    coins = CoinGeckoConnector().fetch_one().coins
    rows = [
        {
            "coin_id": c.id,
            "symbol": c.symbol,
            "name": c.name,
            "price_usd": c.current_price,
            "market_cap_usd": c.market_cap,
            "volume_usd": c.total_volume,
            "price_change_pct_24h": c.price_change_percentage_24h,
        }
        for c in coins
        if c.id and c.current_price is not None
    ]
    df = pd.DataFrame(rows)
    df["volatility_7d"] = None  # single snapshot - no rolling history yet
    df["logical_date"] = TODAY
    loader.load_coingecko(df)
    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duckdb-path", default="warehouse/warehouse.duckdb")
    args = parser.parse_args()

    con = connect(args.duckdb_path)
    create_schema(con)
    loader = WarehouseLoader(con)

    print(f"[{datetime.now(timezone.utc).isoformat()}] fetching real data...")
    for label, fn in [
        ("World Bank GDP", load_world_bank),
        ("World Bank inflation", load_world_bank_inflation),
        ("Open-Meteo weather", load_open_meteo),
        ("Exchange rates", load_exchange_rate),
        ("CoinGecko crypto", load_coingecko),
    ]:
        try:
            count = fn(loader)
            print(f"  {label}: loaded {count} rows")
        except Exception as exc:  # noqa: BLE001 - best-effort demo populate, keep going
            print(f"  {label}: FAILED ({exc})")

    con.close()
    print("done")


if __name__ == "__main__":
    main()
