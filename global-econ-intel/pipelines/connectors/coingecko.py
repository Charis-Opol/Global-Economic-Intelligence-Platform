"""
CoinGecko connector.

Docs: https://docs.coingecko.com/reference/coins-markets

Public endpoint, no API key required (rate-limited). Paginated via
`page`/`per_page`; capped at `max_pages` since the project only needs
the top few hundred coins by market cap, not the entire long tail.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pipelines.connectors.base import BaseConnector


class CoinGeckoCoin(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float | None = None
    market_cap: float | None = None
    total_volume: float | None = None
    price_change_percentage_24h: float | None = None


class CoinGeckoResponse(BaseModel):
    coins: list[CoinGeckoCoin]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "CoinGeckoResponse":
        # The API returns a bare JSON array, not an object - wrap it so the
        # rest of the codebase can treat every connector's response the
        # same way (a model with named fields).
        if isinstance(obj, list):
            obj = {"coins": obj}
        return super().model_validate(obj, *args, **kwargs)


class CoinGeckoConnector(BaseConnector[CoinGeckoResponse]):
    name = "coingecko"
    base_url = "https://api.coingecko.com/api/v3"
    per_page = 100
    max_pages = 3

    @property
    def response_model(self) -> type[CoinGeckoResponse]:
        return CoinGeckoResponse

    def _request_page(self, page: int) -> Any:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.per_page,
            "page": page,
            "sparkline": "false",
        }
        response = self.session.get(
            f"{self.base_url}/coins/markets", params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def _has_next_page(self, payload: Any, page: int) -> bool:
        coins = payload if isinstance(payload, list) else []
        return len(coins) == self.per_page and page < self.max_pages
