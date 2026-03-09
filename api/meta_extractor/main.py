"""
meta_extractor – Rivery-style ETL.
Main: orchestrate Extract -> Transform -> Load.
"""
from datetime import date, timedelta
from typing import Any

import httpx

from . import config
from .extractor import extract_all, extract_insights_for_date
from .transformer import transform, transform_insight_rows
from .loader import load_to_dict, load_to_store


def run_pipeline(
    access_token: str,
    ad_account_ids: list[str] | None = None,
    *,
    store: dict[int, Any] | None = None,
    workspace_id: int | None = None,
    load_key: str = "meta_etl",
) -> dict:
    """
    Run full ETL: extract from Meta -> transform -> load.

    - access_token: Meta long-lived access token.
    - ad_account_ids: optional list of ad account IDs (act_XXX or numeric). If None, uses all from /me/adaccounts.
    - store: optional dict to load into (keyed by workspace_id). If None, result is returned only.
    - workspace_id: required if store is provided.
    - load_key: key under workspace_id in store (default "meta_etl").

    Returns the transformed payload (and optionally loads into store).
    """
    client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        raw = extract_all(access_token, ad_account_ids=ad_account_ids, client=client)
    finally:
        client.close()

    transformed = transform(raw)

    if store is not None and workspace_id is not None:
        load_to_store(transformed, store, workspace_id, key=load_key)

    return load_to_dict(transformed)


def run_insights_pipeline(
    access_token: str,
    ad_account_ids: list[str] | None = None,
    report_date: str | None = None,
) -> list[dict]:
    """
    Run insights ETL for a single report_date: extract campaign insights for that date,
    transform to platform_data row format. Returns list of rows ready for save_platform_data.
    report_date: YYYY-MM-DD. Defaults to yesterday.
    """
    if not report_date:
        report_date = (date.today() - timedelta(days=1)).isoformat()
    raw_rows = extract_insights_for_date(
        access_token,
        ad_account_ids=ad_account_ids,
        report_date=report_date,
    )
    return transform_insight_rows(raw_rows, report_date)
