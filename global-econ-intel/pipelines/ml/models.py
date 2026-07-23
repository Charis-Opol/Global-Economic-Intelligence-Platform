"""Registry of the four forecast domain specs (Day 2, Step 4)."""
from __future__ import annotations

from pipelines.ml.train import ForecastSpec
from pipelines.warehouse.repository import (
    get_crypto_features,
    get_exchange_rate_features,
    get_gdp_features,
    get_inflation_features,
)

FORECAST_SPECS: dict[str, ForecastSpec] = {
    "gdp": ForecastSpec(
        domain="gdp",
        feature_fn=get_gdp_features,
        entity_cols=["country_iso3"],
        target_col="gdp_usd",
        lag_col="lag1_gdp_usd",
        rolling_col="gdp_3yr_avg_usd",
        log_scale=True,
    ),
    "inflation": ForecastSpec(
        domain="inflation",
        feature_fn=get_inflation_features,
        entity_cols=["country_iso3"],
        target_col="inflation_pct",
        lag_col="lag1_inflation_pct",
        rolling_col="inflation_3yr_avg_pct",
    ),
    "exchange_rate": ForecastSpec(
        domain="exchange_rate",
        feature_fn=get_exchange_rate_features,
        entity_cols=["base_code", "currency"],
        target_col="rate",
        lag_col="lag1_rate",
        rolling_col="rate_7d_avg",
        log_scale=True,
    ),
    "crypto": ForecastSpec(
        domain="crypto",
        feature_fn=get_crypto_features,
        entity_cols=["coin_id"],
        target_col="price_usd",
        lag_col="lag1_price_usd",
        rolling_col="price_7d_avg_usd",
        log_scale=True,
    ),
}
