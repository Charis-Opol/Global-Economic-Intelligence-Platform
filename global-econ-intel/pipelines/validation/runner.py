"""
Great Expectations validation runner (Day 1, Step 9).

Runs a source's expectation suite against its Silver DataFrame using an
ephemeral (in-memory) GX context - no persistent GX project, store, or
config file needed - so this is just as easy to unit test as the Spark
transforms it checks.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import great_expectations as gx
import pandas as pd

logger = logging.getLogger("pipelines.validation")


@dataclass
class ValidationOutcome:
    asset_name: str
    success: bool
    failed_expectations: list[str] = field(default_factory=list)
    total_expectations: int = 0


class ValidationFailedError(Exception):
    """Raised by `validate_and_raise` when one or more expectations fail."""


def validate_dataframe(
    df: pd.DataFrame,
    suite_builder: Callable[[], "gx.ExpectationSuite"],
    asset_name: str,
) -> ValidationOutcome:
    """Validates `df` against the suite `suite_builder()` produces."""
    context = gx.get_context(mode="ephemeral")
    suite = suite_builder()

    data_source = context.data_sources.add_pandas(f"{asset_name}_source")
    asset = data_source.add_dataframe_asset(name=asset_name)
    batch_definition = asset.add_batch_definition_whole_dataframe(f"{asset_name}_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    result = batch.validate(suite)

    failed = [r.expectation_config.type for r in result.results if not r.success]
    outcome = ValidationOutcome(
        asset_name=asset_name,
        success=result.success,
        failed_expectations=failed,
        total_expectations=len(result.results),
    )

    if outcome.success:
        logger.info(f"{asset_name}: passed all {outcome.total_expectations} expectations")
    else:
        logger.warning(f"{asset_name}: failed expectations {failed}")

    return outcome


def validate_and_raise(
    df: pd.DataFrame,
    suite_builder: Callable[[], "gx.ExpectationSuite"],
    asset_name: str,
) -> ValidationOutcome:
    """Same as `validate_dataframe`, but raises if validation fails - for
    use as a hard gate in a pipeline that should stop on bad data."""
    outcome = validate_dataframe(df, suite_builder, asset_name)
    if not outcome.success:
        raise ValidationFailedError(
            f"{asset_name} failed Great Expectations validation: {outcome.failed_expectations}"
        )
    return outcome
