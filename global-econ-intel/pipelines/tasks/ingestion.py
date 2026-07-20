"""
Shared ingestion task logic, used by every Step 5 DAG.

Kept out of the DAG files themselves so DAGs stay thin (schedule + retry
policy only) and this logic can be unit tested without spinning up
Airflow at all.

Design note: fetch and write happen in a single task rather than two
Airflow tasks connected by XCom. Passing full API payloads through XCom
(which is backed by the metadata database) doesn't scale once responses
get larger than a few KB - writing straight to object storage avoids
that ceiling entirely.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from pipelines.connectors import CONNECTOR_REGISTRY
from pipelines.storage.minio_client import BronzeWriter

logger = logging.getLogger("pipelines.ingestion")


def run_ingestion(source_name: str, logical_date: datetime) -> str:
    """
    Fetch every page for `source_name`, wrap it with run metadata, and
    write one JSON object to the Bronze bucket keyed by `logical_date`.

    Returns the object key that was written (useful for logging / XCom,
    since it's a short string rather than the payload itself).
    """
    if source_name not in CONNECTOR_REGISTRY:
        raise ValueError(f"Unknown source '{source_name}'. Known: {list(CONNECTOR_REGISTRY)}")

    connector_cls = CONNECTOR_REGISTRY[source_name]
    connector = connector_cls()

    pages = [page.model_dump(mode="json") for page in connector.fetch_all()]

    document = {
        "source": source_name,
        "logical_date": logical_date.isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "pages": pages,
    }

    writer = BronzeWriter()
    key = writer.write_json(source=source_name, logical_date=logical_date, payload=document)
    logger.info(f"Wrote {len(pages)} page(s) for '{source_name}' to bronze/{key}")
    return key
