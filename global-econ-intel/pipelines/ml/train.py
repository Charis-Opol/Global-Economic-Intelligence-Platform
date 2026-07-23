"""
Generic pooled-regression forecaster (Day 2, Step 4).

All four forecast domains (GDP, inflation, exchange rate, crypto) reduce to
the same shape once their warehouse view is pulled into a DataFrame: predict
the next period's value from [lag1 value, rolling average]. Rather than
writing four near-identical training scripts, the shared logic lives once
here; `pipelines/ml/models.py` provides one `ForecastSpec` per domain
describing which view/columns/entity key apply.

Holdout: the *last* chronological row per entity (country / currency pair /
coin) is held out for evaluation, everything else trains. This needs no
fallback split, because rows only reach the split once they already have a
non-null lag/rolling feature - meaning every remaining row is at least an
entity's second observation, so a per-entity holdout can never leak an
entity's first-ever data point into the test set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import duckdb
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

MIN_TRAINING_ROWS = 4


class InsufficientTrainingDataError(Exception):
    """Raised when a domain doesn't have enough history yet to train on."""


@dataclass(frozen=True)
class ForecastSpec:
    domain: str
    feature_fn: Callable[[duckdb.DuckDBPyConnection], pd.DataFrame]
    entity_cols: list[str]
    target_col: str
    lag_col: str
    rolling_col: str
    # True for strictly-positive, multiplicative-scale targets (GDP, exchange
    # rates, crypto prices) that span many orders of magnitude across
    # entities pooled into the same regression (e.g. exchange_rate pools 166
    # currency pairs from ~0.0001 to ~24,000). A plain pooled linear
    # regression gets dominated by the largest-scale entities and produces
    # nonsensical predictions - even negative ones - for smaller-scale
    # entities. Fitting in log-space instead makes a 10% move look like a
    # 10% move regardless of an entity's absolute scale. Inflation is a
    # signed percentage that can go negative (deflation), so log-space
    # doesn't apply there and it stays a plain linear fit.
    log_scale: bool = False

    @property
    def model_name(self) -> str:
        return f"{self.domain}_forecast"

    @property
    def feature_cols(self) -> list[str]:
        return [self.lag_col, self.rolling_col]


def _build_model(log_scale: bool):
    if not log_scale:
        return LinearRegression()
    # log1p/expm1 (not log/exp) so an entity whose lag/rolling feature is
    # legitimately 0 doesn't blow up - safe here since every log_scale
    # domain's values are >= 0 by construction (rates, prices, GDP).
    regressor = Pipeline(
        [
            ("log_features", FunctionTransformer(np.log1p, inverse_func=np.expm1)),
            ("linreg", LinearRegression()),
        ]
    )
    return TransformedTargetRegressor(regressor=regressor, func=np.log1p, inverse_func=np.expm1)


@dataclass
class TrainingResult:
    model: LinearRegression | TransformedTargetRegressor
    params: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    train_rows: int = 0
    test_rows: int = 0


def train_and_evaluate(con: duckdb.DuckDBPyConnection, spec: ForecastSpec) -> TrainingResult:
    df = spec.feature_fn(con)
    usable = df.dropna(subset=[*spec.feature_cols, spec.target_col])

    if len(usable) < MIN_TRAINING_ROWS:
        raise InsufficientTrainingDataError(
            f"{spec.domain}: only {len(usable)} usable rows (need >= {MIN_TRAINING_ROWS})"
        )

    test_idx = usable.groupby(spec.entity_cols, group_keys=False).tail(1).index
    train_df = usable.drop(test_idx)
    test_df = usable.loc[test_idx]

    if train_df.empty or test_df.empty:
        raise InsufficientTrainingDataError(
            f"{spec.domain}: empty train ({len(train_df)}) or test ({len(test_df)}) split"
        )

    model = _build_model(spec.log_scale)
    model.fit(train_df[spec.feature_cols], train_df[spec.target_col])
    predictions = model.predict(test_df[spec.feature_cols])

    mae = mean_absolute_error(test_df[spec.target_col], predictions)
    rmse = root_mean_squared_error(test_df[spec.target_col], predictions)

    return TrainingResult(
        model=model,
        params={
            "model_type": "log_linear_regression" if spec.log_scale else "linear_regression",
            "features": ",".join(spec.feature_cols),
        },
        metrics={"mae": float(mae), "rmse": float(rmse)},
        train_rows=len(train_df),
        test_rows=len(test_df),
    )
