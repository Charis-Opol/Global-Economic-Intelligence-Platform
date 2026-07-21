"""
World Bank indicator connector.

Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581

The World Bank API returns a 2-element list: [metadata, records], where
metadata carries page/pages/per_page/total. That shape is unusual enough
that it's normalized inside WorldBankResponse.model_validate.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pipelines.connectors.base import BaseConnector


class WorldBankMeta(BaseModel):
    page: int
    pages: int
    per_page: int
    total: int


class WorldBankIndicator(BaseModel):
    id: str
    value: str


class WorldBankCountry(BaseModel):
    id: str
    value: str


class WorldBankRecord(BaseModel):
    indicator: WorldBankIndicator
    country: WorldBankCountry
    countryiso3code: str
    date: str
    value: float | None = None
    unit: str = ""
    obs_status: str = ""
    decimal: int = 0


class WorldBankResponse(BaseModel):
    meta: WorldBankMeta
    records: list[WorldBankRecord]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "WorldBankResponse":
        # Normalize the API's [metadata, records] list shape into a dict
        # before handing off to standard Pydantic validation.
        if isinstance(obj, list) and len(obj) == 2:
            meta, records = obj
            obj = {"meta": meta, "records": records or []}
        return super().model_validate(obj, *args, **kwargs)


class WorldBankConnector(BaseConnector[WorldBankResponse]):
    """Fetches a single indicator (default: GDP, current US$) for all countries."""

    name = "world_bank"
    base_url = "https://api.worldbank.org/v2"
    indicator = "NY.GDP.MKTP.CD"
    per_page = 1000

    @property
    def response_model(self) -> type[WorldBankResponse]:
        return WorldBankResponse

    def _request_page(self, page: int) -> Any:
        url = f"{self.base_url}/country/all/indicator/{self.indicator}"
        params = {"format": "json", "page": page, "per_page": self.per_page}
        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _has_next_page(self, payload: Any, page: int) -> bool:
        meta = payload[0] if isinstance(payload, list) else {}
        return page < meta.get("pages", 1)


class WorldBankInflationConnector(WorldBankConnector):
    """Fetches inflation (consumer prices, annual %) for all countries.

    Day 2, Step 1/2 needs a real inflation series to build the `/inflation`
    endpoint and an "inflation trend" feature on top of - reuses every bit of
    WorldBankConnector's machinery (same API shape, same pagination), just a
    different indicator and source name.
    """

    name = "world_bank_inflation"
    indicator = "FP.CPI.TOTL.ZG"
