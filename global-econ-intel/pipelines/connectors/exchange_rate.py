"""
Exchange rate connector.

Uses open.er-api.com (free, no API key, daily-updated rates against a
base currency). Not paginated - one response contains every rate.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pipelines.connectors.base import BaseConnector


class ExchangeRateResponse(BaseModel):
    result: str
    base_code: str
    time_last_update_utc: str | None = None
    rates: dict[str, float]


class ExchangeRateConnector(BaseConnector[ExchangeRateResponse]):
    name = "exchange_rate"
    base_url = "https://open.er-api.com/v6"

    def __init__(self, base_currency: str = "USD") -> None:
        super().__init__()
        self.base_currency = base_currency

    @property
    def response_model(self) -> type[ExchangeRateResponse]:
        return ExchangeRateResponse

    def _request_page(self, page: int) -> Any:
        response = self.session.get(
            f"{self.base_url}/latest/{self.base_currency}",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
