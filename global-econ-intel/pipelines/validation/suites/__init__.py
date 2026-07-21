"""Registry mapping source name to its Great Expectations suite builder."""
from pipelines.validation.suites import (
    coingecko,
    exchange_rate,
    newsapi,
    open_meteo,
    world_bank,
    world_bank_inflation,
)

SUITE_BUILDERS = {
    "world_bank": world_bank.build_suite,
    "world_bank_inflation": world_bank_inflation.build_suite,
    "open_meteo": open_meteo.build_suite,
    "exchange_rate": exchange_rate.build_suite,
    "coingecko": coingecko.build_suite,
    "newsapi": newsapi.build_suite,
}

__all__ = ["SUITE_BUILDERS"]
