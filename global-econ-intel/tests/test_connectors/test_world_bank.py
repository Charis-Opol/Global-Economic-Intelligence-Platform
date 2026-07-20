from __future__ import annotations

from pipelines.connectors.world_bank import WorldBankConnector
from tests.test_connectors.conftest import FakeResponse


def _page(page: int, pages: int, values: list[float]) -> list:
    meta = {"page": page, "pages": pages, "per_page": 1000, "total": pages * len(values)}
    records = [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
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


def test_single_page(patch_session_get):
    patch_session_get([FakeResponse(_page(1, 1, [48_000_000_000.0]))])
    connector = WorldBankConnector()

    pages = list(connector.fetch_all())

    assert len(pages) == 1
    assert pages[0].meta.pages == 1
    assert pages[0].records[0].countryiso3code == "UGA"
    assert pages[0].records[0].value == 48_000_000_000.0


def test_multi_page_pagination(patch_session_get):
    calls = patch_session_get(
        [
            FakeResponse(_page(1, 2, [1.0])),
            FakeResponse(_page(2, 2, [2.0])),
        ]
    )
    connector = WorldBankConnector()

    pages = list(connector.fetch_all())

    assert len(pages) == 2
    assert [p.records[0].value for p in pages] == [1.0, 2.0]
    assert calls[0]["params"]["page"] == 1
    assert calls[1]["params"]["page"] == 2


def test_null_value_is_allowed(patch_session_get):
    # World Bank returns null for years/countries with no reported data.
    patch_session_get([FakeResponse(_page(1, 1, [None]))])  # type: ignore[list-item]
    connector = WorldBankConnector()

    result = connector.fetch_one()

    assert result.records[0].value is None
