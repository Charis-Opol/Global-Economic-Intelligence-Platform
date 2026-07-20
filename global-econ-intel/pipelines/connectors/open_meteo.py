"""
Open-Meteo weather connector.

Docs: https://open-meteo.com/en/docs

No API key required. Not paginated - one request returns the full daily
series for the requested date range, so `_has_next_page` uses the base
class default (False).

Default coordinates are Kampala, Uganda; override per-country as the
project's location coverage grows.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from pipelines.connectors.base import BaseConnector

KAMPALA_LAT = 0.3476
KAMPALA_LON = 32.5825


class OpenMeteoDaily(BaseModel):
    time: list[str]
    temperature_2m_max: list[float] | None = None
    temperature_2m_min: list[float] | None = None
    precipitation_sum: list[float] | None = None


class OpenMeteoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    latitude: float
    longitude: float
    daily: OpenMeteoDaily


class OpenMeteoConnector(BaseConnector[OpenMeteoResponse]):
    name = "open_meteo"
    base_url = "https://api.open-meteo.com/v1"

    def __init__(
        self,
        latitude: float = KAMPALA_LAT,
        longitude: float = KAMPALA_LON,
        past_days: int = 7,
        forecast_days: int = 7,
    ) -> None:
        super().__init__()
        self.latitude = latitude
        self.longitude = longitude
        self.past_days = past_days
        self.forecast_days = forecast_days

    @property
    def response_model(self) -> type[OpenMeteoResponse]:
        return OpenMeteoResponse

    def _request_page(self, page: int) -> Any:
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
            "timezone": "auto",
        }
        response = self.session.get(
            f"{self.base_url}/forecast", params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()
