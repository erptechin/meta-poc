"""
meta_extractor – Rivery-style ETL.
Extract: pull data from Meta Graph API.
"""
import httpx

from . import config


def extract_ad_accounts(access_token: str, client: httpx.Client | None = None) -> list[dict]:
    """Extract ad accounts for the authenticated user."""
    url = f"{config.GRAPH_BASE_URL}/me/adaccounts"
    params = {"access_token": access_token, "fields": "id,account_id,name,account_status,currency,timezone_name"}
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        r = client.get(url, params=params)
        r.raise_for_status()
        return (r.json().get("data") or [])
    finally:
        if own:
            client.close()


def extract_campaigns(
    access_token: str,
    ad_account_id: str,
    client: httpx.Client | None = None,
) -> list[dict]:
    """Extract campaigns for an ad account. ad_account_id must be act_XXXXX."""
    aid = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
    url = f"{config.GRAPH_BASE_URL}/{aid}/campaigns"
    params = {"access_token": access_token, "fields": config.CAMPAIGN_FIELDS}
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        r = client.get(url, params=params)
        r.raise_for_status()
        return (r.json().get("data") or [])
    finally:
        if own:
            client.close()


def extract_ad_sets(
    access_token: str,
    ad_account_id: str,
    client: httpx.Client | None = None,
) -> list[dict]:
    """Extract ad sets for an ad account."""
    aid = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
    url = f"{config.GRAPH_BASE_URL}/{aid}/adsets"
    params = {"access_token": access_token, "fields": "id,name,status,daily_budget,lifetime_budget,targeting,created_time,updated_time"}
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        r = client.get(url, params=params)
        r.raise_for_status()
        return (r.json().get("data") or [])
    finally:
        if own:
            client.close()


def extract_ads(
    access_token: str,
    ad_account_id: str,
    client: httpx.Client | None = None,
) -> list[dict]:
    """Extract ads for an ad account."""
    aid = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
    url = f"{config.GRAPH_BASE_URL}/{aid}/ads"
    params = {"access_token": access_token, "fields": "id,name,status,creative{id,name},created_time,updated_time"}
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        r = client.get(url, params=params)
        r.raise_for_status()
        return (r.json().get("data") or [])
    finally:
        if own:
            client.close()


def extract_campaign_insights(
    access_token: str,
    campaign_id: str,
    date_since: str,
    date_until: str,
    client: httpx.Client | None = None,
) -> list[dict]:
    """
    Extract insights for a single campaign for a date range.
    campaign_id can be numeric or with act_ prefix; insights are at campaign level.
    time_range: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
    """
    import json
    cid = campaign_id if str(campaign_id).startswith("act_") else str(campaign_id)
    url = f"{config.GRAPH_BASE_URL}/{cid}/insights"
    time_range = json.dumps({"since": date_since, "until": date_until})
    params = {
        "access_token": access_token,
        "fields": config.INSIGHTS_FIELDS,
        "time_range": time_range,
        "time_increment": 1,
    }
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        r = client.get(url, params=params)
        r.raise_for_status()
        return (r.json().get("data") or [])
    finally:
        if own:
            client.close()


def extract_insights_for_date(
    access_token: str,
    ad_account_ids: list[str] | None = None,
    report_date: str | None = None,
    client: httpx.Client | None = None,
) -> list[dict]:
    """
    For a single report_date, get all campaigns from ad accounts, then insights for that date per campaign.
    Returns list of raw insight records (each has date_start, impressions, clicks, spend, cpm, cpc, ctr)
    with campaign_id and campaign_name attached.
    """
    raw = extract_all(access_token, ad_account_ids=ad_account_ids, client=client)
    campaigns = raw.get("campaigns") or []
    out = []
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        for c in campaigns:
            cid = c.get("id")
            if not cid:
                continue
            insights = extract_campaign_insights(
                access_token, cid, report_date, report_date, client=client
            )
            name = c.get("name") or ""
            for ins in insights:
                out.append({"campaign_id": cid, "campaign_name": name, **ins})
    finally:
        if own:
            client.close()
    return out


def extract_all(
    access_token: str,
    ad_account_ids: list[str] | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """
    Extract ad accounts (and optionally campaigns/adsets/ads per account).
    If ad_account_ids is None, uses all accounts from /me/adaccounts.
    """
    own = client is None
    if own:
        client = httpx.Client(timeout=config.REQUEST_TIMEOUT)
    try:
        raw_accounts = extract_ad_accounts(access_token, client=client)
        if not ad_account_ids:
            ad_account_ids = [
                (a.get("id") or a.get("account_id") or "").replace("act_", "")
                for a in raw_accounts
                if a.get("id") or a.get("account_id")
            ]
        result = {"ad_accounts": raw_accounts, "campaigns": [], "adsets": [], "ads": []}
        for aid in ad_account_ids:
            if not aid:
                continue
            act_id = aid if str(aid).startswith("act_") else f"act_{aid}"
            result["campaigns"].extend(
                [{"ad_account_id": act_id, **c} for c in extract_campaigns(access_token, act_id, client=client)]
            )
            result["adsets"].extend(
                [{"ad_account_id": act_id, **a} for a in extract_ad_sets(access_token, act_id, client=client)]
            )
            result["ads"].extend(
                [{"ad_account_id": act_id, **a} for a in extract_ads(access_token, act_id, client=client)]
            )
        return result
    finally:
        if own:
            client.close()
