"""
Central application settings.

All configuration is pulled from environment variables (populated by
docker-compose.yml / .env). No secrets or business logic live here -
this is scaffolding only, wired up in later steps.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Global Economic Intelligence Platform API"
    environment: str = "development"

    duckdb_path: str = "/opt/warehouse/warehouse.duckdb"

    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"


settings = Settings()
