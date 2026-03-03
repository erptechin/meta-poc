"""
meta_extractor – Rivery-style ETL.
Load: write transformed data to destination (in-memory store, DB, etc.).
"""
from typing import Any


def load_to_store(
    data: dict,
    store: dict[int, Any],
    workspace_id: int,
    key: str = "meta_etl",
) -> None:
    """
    Load transformed data into an in-memory store keyed by workspace_id.
    Merges under optional key so other keys can coexist.
    """
    if key:
        existing = store.get(workspace_id) or {}
        if not isinstance(existing, dict):
            existing = {"value": existing}
        existing[key] = data
        store[workspace_id] = existing
    else:
        store[workspace_id] = data


def load_to_dict(data: dict) -> dict:
    """
    No-op load that returns the payload (e.g. for API response).
    Use when load destination is the HTTP response itself.
    """
    return data
