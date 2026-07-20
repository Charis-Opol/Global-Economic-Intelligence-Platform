"""
Shared, service-agnostic settings — importable by Airflow DAGs, Spark jobs,
and anything else that needs to know where MinIO/DuckDB live without
duplicating connection strings everywhere.

Kept intentionally minimal for Day 1, Step 1: no business config yet.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"

    bronze_bucket: str = "bronze"
    silver_bucket: str = "silver"
    gold_bucket: str = "gold"

    duckdb_path: str = "/opt/warehouse/warehouse.duckdb"


shared_settings = SharedSettings()
