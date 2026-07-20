"""
Shared connector infrastructure.

Every source-specific connector (World Bank, Open-Meteo, ExchangeRate,
CoinGecko, NewsAPI) subclasses BaseConnector and only implements:

  - `response_model`   : the Pydantic schema a page of data must satisfy
  - `_request_page`    : fetch one raw (unvalidated) page of JSON
  - `_has_next_page`   : whether to keep paginating (default: no)

Retries, structured JSON logging, and schema validation are handled once,
here, so every connector behaves consistently.

Scope note: this module produces validated Python objects only. Writing
fetched data to MinIO's Bronze bucket is Day 1, Step 5 (Airflow DAGs) —
deliberately not this file's job.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Iterator, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipelines.connectors.exceptions import ConnectorRequestError, ConnectorValidationError

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class _JsonFormatter(logging.Formatter):
    """Emits one JSON object per log line so logs are machine-parseable
    once they land in Airflow's task logs / a log aggregator."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


class BaseConnector(ABC, Generic[ResponseModel]):
    """Generic HTTP source connector with retries, logging, and validation."""

    name: str = "base"
    base_url: str = ""
    timeout_seconds: float = 15.0
    max_attempts: int = 5

    def __init__(self) -> None:
        self.logger = _configure_logger(f"connectors.{self.name}")
        self.session = requests.Session()

    # ---- required overrides -------------------------------------------------
    @property
    @abstractmethod
    def response_model(self) -> type[ResponseModel]:
        """Pydantic model each page of data is validated against."""

    @abstractmethod
    def _request_page(self, page: int) -> Any:
        """Return raw (unvalidated) JSON for the given 1-indexed page."""

    def _has_next_page(self, payload: Any, page: int) -> bool:
        """Override for paginated sources. Default: single page only."""
        return False

    # ---- shared machinery -----------------------------------------------------
    def _fetch_with_retry(self, page: int) -> Any:
        @retry(
            reraise=True,
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception_type(requests.RequestException),
        )
        def _do_fetch() -> Any:
            self.logger.info(f"Fetching {self.name} page {page}")
            try:
                return self._request_page(page)
            except requests.RequestException as exc:
                self.logger.warning(f"{self.name} page {page} request failed: {exc}")
                raise

        try:
            return _do_fetch()
        except requests.RequestException as exc:
            self.logger.error(
                f"{self.name} page {page} failed after {self.max_attempts} attempts"
            )
            raise ConnectorRequestError(
                f"{self.name} failed after {self.max_attempts} attempts on page {page}"
            ) from exc

    def _validate(self, payload: Any) -> ResponseModel:
        try:
            return self.response_model.model_validate(payload)
        except ValidationError as exc:
            self.logger.error(f"{self.name} response failed validation: {exc}")
            raise ConnectorValidationError(str(exc)) from exc

    def fetch_all(self) -> Iterator[ResponseModel]:
        """Yield one validated ResponseModel per page until pagination ends."""
        page = 1
        while True:
            raw = self._fetch_with_retry(page)
            validated = self._validate(raw)
            yield validated
            if not self._has_next_page(raw, page):
                break
            page += 1

    def fetch_one(self) -> ResponseModel:
        """Convenience for non-paginated sources: fetch just the first page."""
        raw = self._fetch_with_retry(page=1)
        return self._validate(raw)
