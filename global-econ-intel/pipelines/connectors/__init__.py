"""
Connector registry.

Day 1, Step 5 (Airflow ingestion DAGs) imports from here rather than
reaching into each connector module directly, so adding a new source
later means one line here instead of touching DAG code.
"""
from pipelines.connectors.base import BaseConnector
from pipelines.connectors.coingecko import CoinGeckoConnector
from pipelines.connectors.exchange_rate import ExchangeRateConnector
from pipelines.connectors.newsapi import NewsAPIConnector
from pipelines.connectors.open_meteo import OpenMeteoConnector
from pipelines.connectors.world_bank import WorldBankConnector, WorldBankInflationConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "world_bank": WorldBankConnector,
    "world_bank_inflation": WorldBankInflationConnector,
    "open_meteo": OpenMeteoConnector,
    "exchange_rate": ExchangeRateConnector,
    "coingecko": CoinGeckoConnector,
    "newsapi": NewsAPIConnector,
}

__all__ = [
    "CONNECTOR_REGISTRY",
    "BaseConnector",
    "WorldBankConnector",
    "WorldBankInflationConnector",
    "OpenMeteoConnector",
    "ExchangeRateConnector",
    "CoinGeckoConnector",
    "NewsAPIConnector",
]
