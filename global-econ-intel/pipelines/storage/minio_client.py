"""
Thin MinIO (S3-compatible) client for writing raw ingestion output to the
Bronze bucket.

Uses boto3 directly against MinIO's S3-compatible API rather than an
Airflow Connection object, so this module can be imported and unit
tested completely outside of Airflow.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import boto3
from botocore.client import Config as BotoConfig

from config.settings import shared_settings


class BronzeWriter:
    """Writes one JSON object per source per day to the Bronze bucket.

    Using a deterministic key (`{source}/{date}/{source}.json`) means a
    DAG retry or manual rerun for the same logical date overwrites the
    same object instead of creating a duplicate - this is what makes
    ingestion idempotent.
    """

    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket or shared_settings.bronze_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=shared_settings.minio_endpoint,
            aws_access_key_id=shared_settings.minio_root_user,
            aws_secret_access_key=shared_settings.minio_root_password,
            config=BotoConfig(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def _key_for(self, source: str, logical_date: datetime) -> str:
        return f"{source}/{logical_date:%Y-%m-%d}/{source}.json"

    def write_json(self, source: str, logical_date: datetime, payload: dict[str, Any]) -> str:
        key = self._key_for(source, logical_date)
        body = json.dumps(payload, default=str).encode("utf-8")
        self._client.put_object(
            Bucket=self.bucket, Key=key, Body=body, ContentType="application/json"
        )
        return key

    def read_json(self, source: str, logical_date: datetime) -> dict[str, Any]:
        key = self._key_for(source, logical_date)
        obj = self._client.get_object(Bucket=self.bucket, Key=key)
        return json.loads(obj["Body"].read())
