"""Response models for the Day 2, Step 6 domain endpoints.

One flat module rather than one file per domain (the Step 9/10 convention)
because each domain model here is a handful of fields with no shared
validation logic between them - splitting them out would be five near-empty
files for no readability gain.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Common pagination envelope every list endpoint returns."""

    items: list[T]
    total: int
    limit: int
    offset: int


class Country(BaseModel):
    country_iso3: str
    country_name: str | None = None


class GDPRecord(BaseModel):
    country_iso3: str
    country_name: str | None = None
    indicator_id: str
    year: int
    gdp_usd: float | None = None
    gdp_growth_rate: float | None = None
    lag1_gdp_usd: float | None = None
    gdp_3yr_avg_usd: float | None = None


class Inflation(BaseModel):
    country_iso3: str
    country_name: str | None = None
    indicator_id: str
    year: int
    inflation_pct: float | None = None
    inflation_trend: float | None = None
    lag1_inflation_pct: float | None = None
    inflation_3yr_avg_pct: float | None = None


class ExchangeRate(BaseModel):
    base_code: str
    currency: str
    date: date
    rate: float | None = None
    exchange_momentum: float | None = None
    lag1_rate: float | None = None
    rate_7d_avg: float | None = None


class Weather(BaseModel):
    latitude: float
    longitude: float
    date: date
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    precipitation_mm: float | None = None
    precip_30d_avg_mm: float | None = None
    rainfall_anomaly_mm: float | None = None
    temp_max_7d_avg_c: float | None = None


class Crypto(BaseModel):
    coin_id: str
    symbol: str | None = None
    name: str | None = None
    date: date
    price_usd: float | None = None
    market_cap_usd: float | None = None
    volume_usd: float | None = None
    price_change_pct_24h: float | None = None
    volatility_7d: float | None = None
    lag1_price_usd: float | None = None
    price_7d_avg_usd: float | None = None


class NewsArticle(BaseModel):
    url: str
    source_name: str | None = None
    title: str | None = None
    author: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    date: date
    articles_that_day: int | None = None


class PredictionResponse(BaseModel):
    domain: str
    entity: dict[str, str]
    predicted_value: float
    based_on: dict[str, float | None]
    model_version: str | None = None


class RegisteredModel(BaseModel):
    name: str
    latest_version: str | None = None
    champion_version: str | None = None
    metrics: dict[str, float]


class PipelineStatusEntry(BaseModel):
    dag_id: str
    state: str | None = None
    execution_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None
