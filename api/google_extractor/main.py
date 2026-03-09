"""
google_extractor – Rivery-style ETL.
Main: orchestrate Extract -> Transform (insights by date).
"""
from datetime import date, timedelta

from . import config
from .extractor import extract_insights_for_date
from .transformer import transform_insight_rows


def run_insights_pipeline(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    customer_ids: list[str] | None = None,
    report_date: str | None = None,
    developer_token: str | None = None,
) -> list[dict]:
    """
    Run insights ETL for a single report_date: extract campaign metrics from Google Ads,
    transform to platform_data row format. Returns list of rows ready for save_platform_data.
    report_date: YYYY-MM-DD. Defaults to yesterday.
    """
    if not report_date:
        report_date = (date.today() - timedelta(days=1)).isoformat()
    raw_rows = extract_insights_for_date(
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        customer_ids=customer_ids or [],
        report_date=report_date,
        developer_token=developer_token or config.GOOGLE_ADS_DEVELOPER_TOKEN,
    )
    return transform_insight_rows(raw_rows, report_date)
