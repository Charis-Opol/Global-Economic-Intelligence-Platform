"""
Shared test helpers.

Tests never hit real APIs - `patch_session_get` swaps `requests.Session.get`
for a stub that returns pre-built FakeResponse objects (or raises) in
sequence, so connector logic can be tested deterministically and offline.
"""
from __future__ import annotations

from typing import Any, Callable

import pytest
import requests


class FakeResponse:
    def __init__(self, json_body: Any, status_code: int = 200) -> None:
        self._json_body = json_body
        self.status_code = status_code

    def json(self) -> Any:
        return self._json_body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def patch_session_get(monkeypatch: pytest.MonkeyPatch) -> Callable:
    """
    Usage:
        patch_session_get([FakeResponse({...}), FakeResponse({...})])
    Each call to session.get() pops the next item off the list. Items can
    also be exceptions, which will be raised instead of returned.
    """

    def _apply(responses: list[Any]) -> list[dict]:
        calls: list[dict] = []
        remaining = list(responses)

        def fake_get(self, url: str, params: dict | None = None, timeout: float | None = None):
            calls.append({"url": url, "params": params, "timeout": timeout})
            if not remaining:
                raise AssertionError("No more fake responses queued")
            item = remaining.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        monkeypatch.setattr(requests.Session, "get", fake_get)
        return calls

    return _apply
