"""
Central application settings.

All configuration is pulled from environment variables (populated by
docker-compose.yml / .env). No secrets are hardcoded here - defaults exist
only so the app can boot locally without a .env file.
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

    # Day 2, Step 3/6 - model registry + inference
    mlflow_tracking_uri: str = "http://mlflow:5000"

    # Day 2, Step 6 - /pipeline-status reads the Airflow REST API
    airflow_base_url: str = "http://airflow-webserver:8080"
    airflow_admin_user: str = "admin"
    airflow_admin_password: str = "admin"

    # Day 2, Step 7 - simple JWT auth
    jwt_secret_key: str = "change_me_generate_a_long_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    auth_admin_username: str = "admin"
    auth_admin_password: str = "change_me"


settings = Settings()
