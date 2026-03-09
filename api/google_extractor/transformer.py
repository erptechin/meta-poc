"""
google_extractor – Rivery-style ETL.
Transform: normalize raw Google Ads API responses to platform_data row format.
"""
from typing import Any


def _num(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _decimal(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def transform_insight_rows(raw_rows: list[dict], report_date: str) -> list[dict]:
    """
    Transform raw insight records from Google Ads to platform_data row format.
    Same shape as meta_extractor: campaign_name, impressions, clicks, cpm, cpc, ctr, amount_spent, source=GOOGLE.
    """
    out = []
    for r in raw_rows or []:
        date_start = r.get("date") or r.get("date_start") or report_date
        impressions = _num(r.get("impressions"))
        clicks = _num(r.get("clicks"))
        amount_spent = _decimal(r.get("amount_spent")) or (_decimal(r.get("cost_micros") / 1_000_000) if r.get("cost_micros") is not None else None)
        ctr = _decimal(r.get("ctr"))
        cpc = _decimal(r.get("cpc") or r.get("average_cpc"))
        cpm = _decimal(r.get("cpm"))
        if cpm is None and amount_spent is not None and impressions and impressions > 0:
            cpm = amount_spent / impressions * 1000
        out.append({
            "report_date": date_start,
            "campaign_name": r.get("campaign_name"),
            "campaign_type": r.get("campaign_type"),
            "source": "GOOGLE",
            "impressions": impressions,
            "clicks": clicks,
            "cpm": cpm,
            "cpc": cpc,
            "ctr": ctr,
            "amount_spent": amount_spent,
            "data": {"campaign_id": r.get("campaign_id")},
        })
    return out
