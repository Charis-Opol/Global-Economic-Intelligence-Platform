"""
Predictions domain endpoint (Day 2, Step 6).

Loads the champion model for a forecast domain from MLflow and applies it to
that entity's latest feature row from the warehouse (the same `view_*` views
`pipelines/ml/train.py` trains against, via `app/repository.py`).

The domain -> (lag column, rolling-average column) mapping below mirrors
`pipelines/ml/models.py`'s `FORECAST_SPECS`, duplicated rather than imported:
the backend's Docker image has no dependency on `pipelines/` (see
`app/db.py`, `app/repository.py`), and this is a few short tuples of column
names, not business logic - the real shared truth both sides agree on is the
warehouse view itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from mlflow.exceptions import MlflowException

from app import mlflow_client, repository
from app.db import get_connection
from app.schemas import PredictionResponse

router = APIRouter(tags=["predictions"])


@dataclass(frozen=True)
class _DomainSpec:
    lag_col: str
    rolling_col: str
    required_params: tuple[str, ...]
    entity_fn: Callable[[dict[str, str]], dict[str, str]]
    row_fn: Callable[[Any, dict[str, str]], dict[str, Any] | None]


_DOMAIN_SPECS: dict[str, _DomainSpec] = {
    "gdp": _DomainSpec(
        lag_col="lag1_gdp_usd",
        rolling_col="gdp_3yr_avg_usd",
        required_params=("country",),
        entity_fn=lambda p: {"country": p["country"].upper()},
        row_fn=lambda con, p: repository.latest_gdp_row(con, p["country"]),
    ),
    "inflation": _DomainSpec(
        lag_col="lag1_inflation_pct",
        rolling_col="inflation_3yr_avg_pct",
        required_params=("country",),
        entity_fn=lambda p: {"country": p["country"].upper()},
        row_fn=lambda con, p: repository.latest_inflation_row(con, p["country"]),
    ),
    "exchange_rate": _DomainSpec(
        lag_col="lag1_rate",
        rolling_col="rate_7d_avg",
        required_params=("base", "quote"),
        entity_fn=lambda p: {"base": p["base"].upper(), "quote": p["quote"].upper()},
        row_fn=lambda con, p: repository.latest_exchange_rate_row(con, p["base"], p["quote"]),
    ),
    "crypto": _DomainSpec(
        lag_col="lag1_price_usd",
        rolling_col="price_7d_avg_usd",
        required_params=("coin_id",),
        entity_fn=lambda p: {"coin_id": p["coin_id"].lower()},
        row_fn=lambda con, p: repository.latest_crypto_row(con, p["coin_id"]),
    ),
}


@router.get("/predictions", response_model=PredictionResponse)
def predict(
    domain: str = Query(..., description=f"One of {sorted(_DOMAIN_SPECS)}"),
    country: str | None = None,
    base: str | None = None,
    quote: str | None = None,
    coin_id: str | None = None,
    con=Depends(get_connection),
):
    spec = _DOMAIN_SPECS.get(domain)
    if spec is None:
        raise HTTPException(
            status_code=400, detail=f"Unknown domain '{domain}'. Choose one of {sorted(_DOMAIN_SPECS)}"
        )

    params = {"country": country, "base": base, "quote": quote, "coin_id": coin_id}
    missing = [name for name in spec.required_params if not params.get(name)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"domain={domain} requires query param(s): {', '.join(missing)}",
        )

    entity = spec.entity_fn(params)
    row = spec.row_fn(con, params)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No warehouse data found for {entity}")

    lag_value, rolling_value = row.get(spec.lag_col), row.get(spec.rolling_col)
    if lag_value is None or rolling_value is None:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough history for {entity} yet to build forecast features",
        )

    try:
        model = mlflow_client.load_champion_model(domain)
    except MlflowException:
        raise HTTPException(
            status_code=404, detail=f"No champion model deployed yet for domain '{domain}'"
        )

    features = pd.DataFrame([{spec.lag_col: lag_value, spec.rolling_col: rolling_value}])
    prediction = model.predict(features)[0]

    return PredictionResponse(
        domain=domain,
        entity=entity,
        predicted_value=float(prediction),
        based_on={spec.lag_col: lag_value, spec.rolling_col: rolling_value},
    )
