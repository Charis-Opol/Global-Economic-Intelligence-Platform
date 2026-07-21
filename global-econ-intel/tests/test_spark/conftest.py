import json
import sys
from pathlib import Path

import pytest
from pyspark.sql import functions as F
from pyspark.sql import SparkSession

# spark-submit adds the script's own directory to sys.path automatically;
# pytest doesn't, so do it explicitly to import common.py / transforms/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spark" / "jobs"))


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("test-etl")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def make_bronze_df(spark):
    """Builds a bronze-shaped DataFrame from plain Python dicts, matching
    what pipelines.tasks.ingestion.run_ingestion actually writes."""

    def _make(docs: list[dict]):
        json_lines = [json.dumps(d) for d in docs]
        rdd = spark.sparkContext.parallelize(json_lines)
        df = spark.read.json(rdd)
        return df.withColumn(
            "logical_date", F.substring(F.col("logical_date"), 1, 10).cast("date")
        )

    return _make
