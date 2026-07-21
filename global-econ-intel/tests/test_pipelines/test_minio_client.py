from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from pipelines.storage.minio_client import BronzeWriter


def test_key_format_is_deterministic_per_source_per_day():
    with patch("pipelines.storage.minio_client.boto3.client") as mock_boto:
        mock_boto.return_value = MagicMock()
        writer = BronzeWriter(bucket="bronze")

        logical_date = datetime(2026, 7, 20, tzinfo=timezone.utc)
        key = writer.write_json("world_bank", logical_date, {"hello": "world"})

        assert key == "world_bank/2026-07-20/world_bank.json"


def test_rerun_overwrites_same_key_rather_than_duplicating():
    with patch("pipelines.storage.minio_client.boto3.client") as mock_boto:
        fake_s3 = MagicMock()
        mock_boto.return_value = fake_s3
        writer = BronzeWriter(bucket="bronze")
        logical_date = datetime(2026, 7, 20, tzinfo=timezone.utc)

        writer.write_json("newsapi", logical_date, {"run": 1})
        writer.write_json("newsapi", logical_date, {"run": 2})  # simulated rerun

        assert fake_s3.put_object.call_count == 2
        first_key = fake_s3.put_object.call_args_list[0].kwargs["Key"]
        second_key = fake_s3.put_object.call_args_list[1].kwargs["Key"]
        assert first_key == second_key == "newsapi/2026-07-20/newsapi.json"

        second_body = json.loads(fake_s3.put_object.call_args_list[1].kwargs["Body"])
        assert second_body == {"run": 2}  # latest write wins


def test_put_object_uses_correct_bucket_and_content_type():
    with patch("pipelines.storage.minio_client.boto3.client") as mock_boto:
        fake_s3 = MagicMock()
        mock_boto.return_value = fake_s3
        writer = BronzeWriter(bucket="bronze")

        writer.write_json("coingecko", datetime(2026, 7, 20, tzinfo=timezone.utc), {"a": 1})

        kwargs = fake_s3.put_object.call_args.kwargs
        assert kwargs["Bucket"] == "bronze"
        assert kwargs["ContentType"] == "application/json"
