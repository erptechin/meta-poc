"""
meta_extractor – Rivery-style ETL.
Transform: normalize raw Meta API responses to a consistent schema.
"""
from datetime import datetime
from typing import Any


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    s = str(value).strip()
    return s if s else None


def transform_ad_accounts(raw: list[dict]) -> list[dict]:
    """Transform raw ad account objects to normalized records."""
    out = []
    for a in raw or []:
        out.append({
            "id": a.get("id"),
            "account_id": a.get("account_id"),
            "name": a.get("name"),
            "account_status": a.get("account_status"),
            "currency": a.get("currency"),
            "timezone_name": a.get("timezone_name"),
        })
    return out


def transform_campaigns(raw: list[dict]) -> list[dict]:
    """Transform raw campaign objects to normalized records."""
    out = []
    for c in raw or []:
        out.append({
            "id": c.get("id"),
            "ad_account_id": c.get("ad_account_id"),
            "name": c.get("name"),
            "status": c.get("status"),
            "objective": c.get("objective"),
            "daily_budget": c.get("daily_budget"),
            "lifetime_budget": c.get("lifetime_budget"),
            "created_time": _normalize_date(c.get("created_time")),
            "updated_time": _normalize_date(c.get("updated_time")),
        })
    return out


def transform_adsets(raw: list[dict]) -> list[dict]:
    """Transform raw ad set objects to normalized records."""
    out = []
    for a in raw or []:
        out.append({
            "id": a.get("id"),
            "ad_account_id": a.get("ad_account_id"),
            "name": a.get("name"),
            "status": a.get("status"),
            "daily_budget": a.get("daily_budget"),
            "lifetime_budget": a.get("lifetime_budget"),
            "targeting": a.get("targeting"),
            "created_time": _normalize_date(a.get("created_time")),
            "updated_time": _normalize_date(a.get("updated_time")),
        })
    return out


def transform_ads(raw: list[dict]) -> list[dict]:
    """Transform raw ad objects to normalized records."""
    out = []
    for a in raw or []:
        creative = a.get("creative") or {}
        out.append({
            "id": a.get("id"),
            "ad_account_id": a.get("ad_account_id"),
            "name": a.get("name"),
            "status": a.get("status"),
            "creative_id": creative.get("id") if isinstance(creative, dict) else None,
            "creative_name": creative.get("name") if isinstance(creative, dict) else None,
            "created_time": _normalize_date(a.get("created_time")),
            "updated_time": _normalize_date(a.get("updated_time")),
        })
    return out


def transform(extracted: dict) -> dict:
    """
    Transform full extracted payload to normalized schema.
    Input: { ad_accounts, campaigns, adsets, ads }
    Output: { ad_accounts, campaigns, adsets, ads } with normalized records.
    """
    return {
        "ad_accounts": transform_ad_accounts(extracted.get("ad_accounts")),
        "campaigns": transform_campaigns(extracted.get("campaigns")),
        "adsets": transform_adsets(extracted.get("adsets")),
        "ads": transform_ads(extracted.get("ads")),
    }


def _num(value: Any) -> int | None:
    """Parse int from string or number."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _decimal(value: Any) -> float | None:
    """Parse float for decimal fields."""
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
    Transform raw insight records (from extract_insights_for_date) to platform_data row format.
    Each output row: report_date, campaign_name, campaign_type, source, impressions, clicks, cpm, cpc, ctr, amount_spent, data.
    """
    out = []
    for r in raw_rows or []:
        date_start = r.get("date_start") or report_date
        out.append({
            "report_date": date_start,
            "campaign_name": r.get("campaign_name"),
            "campaign_type": None,
            "source": "META",
            "impressions": _num(r.get("impressions")),
            "clicks": _num(r.get("clicks")),
            "cpm": _decimal(r.get("cpm")),
            "cpc": _decimal(r.get("cpc")),
            "ctr": _decimal(r.get("ctr")),
            "amount_spent": _decimal(r.get("spend") or r.get("amount_spent")),
            "data": {"campaign_id": r.get("campaign_id")},
        })
    return out
