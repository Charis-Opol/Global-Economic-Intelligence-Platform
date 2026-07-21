from __future__ import annotations

from pipelines.connectors.world_bank import WorldBankInflationConnector
from tests.test_connectors.conftest import FakeResponse


def _page(values: list[float]) -> list:
    meta = {"page": 1, "pages": 1, "per_page": 1000, "total": len(values)}
    records = [
        {
            "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
            "country": {"id": "UG", "value": "Uganda"},
            "countryiso3code": "UGA",
            "date": "2023",
            "value": v,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        }
        for v in values
    ]
    return [meta, records]


def test_requests_the_inflation_indicator_not_gdp(patch_session_get):
    calls = patch_session_get([FakeResponse(_page([5.2]))])
    connector = WorldBankInflationConnector()

    result = connector.fetch_one()

    assert "FP.CPI.TOTL.ZG" in calls[0]["url"]
    assert result.records[0].indicator.id == "FP.CPI.TOTL.ZG"
    assert result.records[0].value == 5.2
