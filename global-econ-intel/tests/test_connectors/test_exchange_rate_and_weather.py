from __future__ import annotations

from pipelines.connectors.exchange_rate import ExchangeRateConnector
from pipelines.connectors.open_meteo import OpenMeteoConnector
from tests.test_connectors.conftest import FakeResponse


def test_exchange_rate_fetch(patch_session_get):
    calls = patch_session_get(
        [
            FakeResponse(
                {
                    "result": "success",
                    "base_code": "USD",
                    "time_last_update_utc": "Mon, 20 Jul 2026 00:00:00 +0000",
                    "rates": {"UGX": 3700.5, "EUR": 0.92},
                }
            )
        ]
    )
    connector = ExchangeRateConnector(base_currency="USD")

    result = connector.fetch_one()

    assert result.rates["UGX"] == 3700.5
    assert "USD" in calls[0]["url"]


def test_open_meteo_fetch(patch_session_get):
    patch_session_get(
        [
            FakeResponse(
                {
                    "latitude": 0.3476,
                    "longitude": 32.5825,
                    "daily": {
                        "time": ["2026-07-19", "2026-07-20"],
                        "temperature_2m_max": [27.1, 26.8],
                        "temperature_2m_min": [17.0, 16.5],
                        "precipitation_sum": [0.0, 4.2],
                    },
                }
            )
        ]
    )
    connector = OpenMeteoConnector()

    result = connector.fetch_one()

    assert result.daily.precipitation_sum == [0.0, 4.2]
    assert len(result.daily.time) == 2
