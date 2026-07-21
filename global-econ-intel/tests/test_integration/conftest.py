from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import mlflow
import pandas as pd
import pytest

# Self-contained even if this package runs in isolation from
# tests/test_backend/ (whose conftest also does this) - `app.*` is only
# importable with backend/ on sys.path, since the backend's own Dockerfile
# copies just `app/`, not the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from pipelines.warehouse.loader import WarehouseLoader  # noqa: E402
from pipelines.warehouse.schema import connect, create_schema  # noqa: E402


@pytest.fixture
def mlflow_tracking():
    """Local sqlite-backed tracking store - see tests/test_ml/conftest.py
    for why sqlite (not a plain file store) is required for the Model
    Registry to work at all."""
    d = Path(tempfile.mkdtemp())
    mlflow.set_tracking_uri(f"sqlite:///{d / 'mlflow.db'}")
    yield d


@pytest.fixture
def warehouse():
    """An in-memory warehouse with enough GDP history (2 countries x 4
    years) to clear the trainer's MIN_TRAINING_ROWS after the
    first-observation-per-country row is dropped for its null lag feature."""
    con = connect(":memory:")
    create_schema(con)
    loader = WarehouseLoader(con)

    years = [2020, 2021, 2022, 2023]
    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA"] * 4 + ["KEN"] * 4,
                "country_name": ["Uganda"] * 4 + ["Kenya"] * 4,
                "indicator_id": ["NY.GDP.MKTP.CD"] * 8,
                "year": years * 2,
                "gdp_usd": [37e9, 40e9, 44e9, 47e9, 90e9, 95e9, 99e9, 103e9],
                "gdp_growth_rate": [None, 0.08, 0.10, 0.07] * 2,
            }
        )
    )

    try:
        yield con
    finally:
        con.close()
