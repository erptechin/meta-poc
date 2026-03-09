"""
google_extractor – Rivery-style ETL.
Extract: pull campaign metrics by date from Google Ads API.
"""
from typing import Any

from . import config


def extract_insights_for_date(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    customer_ids: list[str],
    report_date: str,
    developer_token: str | None = None,
) -> list[dict]:
    """
    Fetch campaign metrics for report_date for the given customer IDs.
    customer_ids: list of Google Ads customer IDs (e.g. "1234567890" or "123-456-7890").
    Returns list of dicts: campaign_id, campaign_name, date, impressions, clicks, cost_micros, ctr, average_cpc, etc.
    """
    token = developer_token or config.GOOGLE_ADS_DEVELOPER_TOKEN
    if not token:
        raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN is not set. Set it in .env for Google Ads API access.")
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError as e:
        raise ImportError("google-ads package is required for run-google-etl. Install with: pip install google-ads") from e

    credentials = {
        "developer_token": token,
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    try:
        client = GoogleAdsClient.load_from_dict(credentials)
    except Exception as e:
        raise ValueError(f"Failed to create Google Ads client: {e}") from e

    # If no customer IDs in integration, fetch accessible customers from API
    if not customer_ids:
        try:
            response = client.get_service("CustomerService").list_accessible_customers()
            resolved = []
            for name in (response.resource_names or []):
                cid = (name.split("/")[-1] if "/" in name else name)
                if cid.isdigit():
                    resolved.append(cid)
            customer_ids = resolved
        except Exception:
            pass
    if not customer_ids:
        raise ValueError(
            "No Google Ads customer IDs. Connect Google in Platform Integration and ensure your account has access to at least one Google Ads customer."
        )

    out = []
    errors = []
    for customer_id in customer_ids or []:
        cid = str(customer_id).replace("-", "")
        if not cid.isdigit():
            continue
        # GAQL: campaign metrics for a single day
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.type,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date = '{report_date}'
              AND campaign.status != 'REMOVED'
        """
        try:
            response = client.get_service("GoogleAdsService").search_stream(
                customer_id=cid,
                query=query,
            )
            for batch in response:
                for row in batch.results:
                    campaign = row.campaign
                    segments = row.segments
                    metrics = row.metrics
                    cost_micros = metrics.cost_micros if metrics.cost_micros else 0
                    out.append({
                        "campaign_id": str(campaign.id) if campaign.id else None,
                        "campaign_name": campaign.name or "",
                        "campaign_type": str(campaign.type).replace("CAMPAIGN_TYPE_", "") if campaign.type else None,
                        "date": segments.date if segments.date else report_date,
                        "impressions": metrics.impressions if metrics.impressions else 0,
                        "clicks": metrics.clicks if metrics.clicks else 0,
                        "cost_micros": cost_micros,
                        "amount_spent": cost_micros / 1_000_000 if cost_micros else None,
                        "ctr": metrics.ctr if metrics.ctr is not None else None,
                        "average_cpc": (metrics.average_cpc / 1_000_000) if metrics.average_cpc else None,
                    })
        except Exception as e:
            errors.append(f"Customer {cid}: {e}")
            continue
    if not out and errors:
        raise ValueError("Google Ads API error(s): " + "; ".join(errors[:3]))
    return out
