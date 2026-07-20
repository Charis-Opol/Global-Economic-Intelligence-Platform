from __future__ import annotations

import requests
from pydantic import BaseModel

from pipelines.connectors.base import BaseConnector
from pipelines.connectors.exceptions import ConnectorRequestError, ConnectorValidationError


class _DummyModel(BaseModel):
    value: int


class _DummyConnector(BaseConnector[_DummyModel]):
    name = "dummy"
    base_url = "https://example.invalid"
    max_attempts = 3

    @property
    def response_model(self):
        return _DummyModel

    def _request_page(self, page: int):
        response = self.session.get(self.base_url, params={"page": page}, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()


def test_retries_then_succeeds(patch_session_get):
    from tests.test_connectors.conftest import FakeResponse

    calls = patch_session_get(
        [
            requests.ConnectionError("boom"),
            requests.ConnectionError("boom again"),
            FakeResponse({"value": 42}),
        ]
    )
    connector = _DummyConnector()
    result = connector.fetch_one()

    assert result.value == 42
    assert len(calls) == 3  # two failures + one success


def test_gives_up_after_max_attempts(patch_session_get):
    patch_session_get(
        [
            requests.ConnectionError("boom"),
            requests.ConnectionError("boom"),
            requests.ConnectionError("boom"),
        ]
    )
    connector = _DummyConnector()

    try:
        connector.fetch_one()
        assert False, "expected ConnectorRequestError"
    except ConnectorRequestError:
        pass


def test_validation_error_on_malformed_payload(patch_session_get):
    from tests.test_connectors.conftest import FakeResponse

    patch_session_get([FakeResponse({"value": "not-an-int-and-not-castable"})])
    connector = _DummyConnector()

    try:
        connector.fetch_one()
        assert False, "expected ConnectorValidationError"
    except ConnectorValidationError:
        pass
