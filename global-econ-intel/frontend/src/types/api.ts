/**
 * Mirrors backend/app/schemas.py field-for-field. Keep in sync by hand -
 * the backend has no dependency on this frontend, so nothing generates
 * these automatically (FastAPI's own /docs is the source of truth if this
 * ever drifts).
 */

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Country {
  country_iso3: string;
  country_name: string | null;
}

export interface GDPRecord {
  country_iso3: string;
  country_name: string | null;
  indicator_id: string;
  year: number;
  gdp_usd: number | null;
  gdp_growth_rate: number | null;
  lag1_gdp_usd: number | null;
  gdp_3yr_avg_usd: number | null;
}

export interface Inflation {
  country_iso3: string;
  country_name: string | null;
  indicator_id: string;
  year: number;
  inflation_pct: number | null;
  inflation_trend: number | null;
  lag1_inflation_pct: number | null;
  inflation_3yr_avg_pct: number | null;
}

export interface ExchangeRate {
  base_code: string;
  currency: string;
  date: string;
  rate: number | null;
  exchange_momentum: number | null;
  lag1_rate: number | null;
  rate_7d_avg: number | null;
}

export interface Weather {
  latitude: number;
  longitude: number;
  date: string;
  temp_max_c: number | null;
  temp_min_c: number | null;
  precipitation_mm: number | null;
  precip_30d_avg_mm: number | null;
  rainfall_anomaly_mm: number | null;
  temp_max_7d_avg_c: number | null;
}

export interface Crypto {
  coin_id: string;
  symbol: string | null;
  name: string | null;
  date: string;
  price_usd: number | null;
  market_cap_usd: number | null;
  volume_usd: number | null;
  price_change_pct_24h: number | null;
  volatility_7d: number | null;
  lag1_price_usd: number | null;
  price_7d_avg_usd: number | null;
}

export interface NewsArticle {
  url: string;
  source_name: string | null;
  title: string | null;
  author: string | null;
  description: string | null;
  published_at: string | null;
  date: string;
  articles_that_day: number | null;
}

export const FORECAST_DOMAINS = ["gdp", "inflation", "exchange_rate", "crypto"] as const;
export type ForecastDomain = (typeof FORECAST_DOMAINS)[number];

export interface PredictionResponse {
  domain: string;
  entity: Record<string, string>;
  predicted_value: number;
  based_on: Record<string, number | null>;
  model_version: string | null;
}

export interface RegisteredModel {
  name: string;
  latest_version: string | null;
  champion_version: string | null;
  metrics: Record<string, number>;
}

export interface PipelineStatusEntry {
  dag_id: string;
  state: string | null;
  execution_date: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface ServiceHealthEntry {
  service: string;
  healthy: boolean;
  detail: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
