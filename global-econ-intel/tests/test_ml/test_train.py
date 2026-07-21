from __future__ import annotations

import pandas as pd
import pytest

from pipelines.ml.models import FORECAST_SPECS
from pipelines.ml.train import InsufficientTrainingDataError, train_and_evaluate


@pytest.mark.parametrize("domain", list(FORECAST_SPECS))
def test_trains_and_evaluates_every_domain(warehouse, domain):
    result = train_and_evaluate(warehouse, FORECAST_SPECS[domain])

    assert result.train_rows > 0
    assert result.test_rows > 0
    assert result.metrics["mae"] >= 0
    assert result.metrics["rmse"] >= 0
    assert result.model.coef_.shape == (2,)  # [lag, rolling_avg] -> one coefficient each


def test_holdout_is_the_last_row_per_entity_not_a_random_split(warehouse):
    spec = FORECAST_SPECS["gdp"]
    result = train_and_evaluate(warehouse, spec)

    # 2 countries x 4 years -> 1 row per country dropped (null lag), leaving
    # 6 usable rows; 1 per country held out -> 4 train, 2 test.
    assert result.train_rows == 4
    assert result.test_rows == 2


def test_raises_when_too_few_usable_rows():
    from pipelines.warehouse.loader import WarehouseLoader
    from pipelines.warehouse.schema import connect, create_schema

    con = connect(":memory:")
    create_schema(con)
    WarehouseLoader(con).load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA"],
                "country_name": ["Uganda", "Uganda"],
                "indicator_id": ["NY.GDP.MKTP.CD"] * 2,
                "year": [2022, 2023],
                "gdp_usd": [40e9, 44e9],
                "gdp_growth_rate": [None, 0.1],
            }
        )
    )

    with pytest.raises(InsufficientTrainingDataError):
        train_and_evaluate(con, FORECAST_SPECS["gdp"])
    con.close()
