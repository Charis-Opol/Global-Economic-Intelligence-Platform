from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from pipelines.tasks.ingestion import run_ingestion


class _FakePage(BaseModel):
    value: int


class _FakeConnector:
    def __init__(self) -> None:
        pass

    def fetch_all(self):
        yield _FakePage(value=1)
        yield _FakePage(value=2)


def test_run_ingestion_writes_expected_document_shape():
    logical_date = datetime(2026, 7, 20, tzinfo=timezone.utc)

    with patch("pipelines.tasks.ingestion.CONNECTOR_REGISTRY", {"fake_source": _FakeConnector}), \
         patch("pipelines.tasks.ingestion.BronzeWriter") as mock_writer_cls:
        mock_writer = MagicMock()
        mock_writer.write_json.return_value = "fake_source/2026-07-20/fake_source.json"
        mock_writer_cls.return_value = mock_writer

        key = run_ingestion("fake_source", logical_date=logical_date)

    assert key == "fake_source/2026-07-20/fake_source.json"
    written_kwargs = mock_writer.write_json.call_args.kwargs
    document = written_kwargs["payload"]

    assert document["source"] == "fake_source"
    assert document["page_count"] == 2
    assert document["pages"] == [{"value": 1}, {"value": 2}]
    assert written_kwargs["logical_date"] == logical_date


def test_unknown_source_raises_before_any_network_or_storage_call():
    with patch("pipelines.tasks.ingestion.BronzeWriter") as mock_writer_cls:
        with pytest.raises(ValueError, match="Unknown source"):
            run_ingestion("not_a_real_source", logical_date=datetime.now(timezone.utc))
        mock_writer_cls.assert_not_called()
