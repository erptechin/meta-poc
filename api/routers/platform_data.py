from datetime import date
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from meta_extractor import run_insights_pipeline as run_meta_insights_pipeline
from google_extractor import run_insights_pipeline as run_google_insights_pipeline

router = APIRouter(tags=["platform-data"])


def _row_to_dict(row) -> dict:
    """Serialize PlatformData model to response dict."""
    return {
        "id": row.id,
        "type": getattr(row, "type", None) or "meta",
        "report_date": row.report_date.isoformat() if getattr(row.report_date, "isoformat", None) else str(row.report_date),
        "campaign_name": row.campaign_name,
        "campaign_type": row.campaign_type,
        "source": row.source,
        "impressions": row.impressions,
        "clicks": row.clicks,
        "cpm": float(row.cpm) if row.cpm is not None else None,
        "cpc": float(row.cpc) if row.cpc is not None else None,
        "ctr": float(row.ctr) if row.ctr is not None else None,
        "amount_spent": float(row.amount_spent) if row.amount_spent is not None else None,
        "data": row.data,
    }


def _get_meta_access_and_accounts(db: Session, workspace_id: int) -> tuple[int, str, list[str]]:
    """Get Meta integration id, access token and ad account IDs. Raises HTTPException if missing."""
    integrations = crud.get_integrations_by_workspace(db, workspace_id=workspace_id)
    meta = next((i for i in integrations if i.ad_platform == "META"), None)
    if not meta:
        raise HTTPException(
            status_code=400,
            detail="No Meta integration found for this workspace. Connect Meta in Platform Integration first.",
        )
    tokens = meta.tokens or {}
    access_token = tokens.get("access_token") if isinstance(tokens, dict) else None
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Meta integration has no access token. Reconnect Meta in Platform Integration.",
        )
    ads_accounts = meta.ads_accounts or []
    ad_account_ids = [
        str(a.get("account_id") or a.get("id") or "")
        for a in ads_accounts
        if a.get("account_id") or a.get("id")
    ]
    return meta.id, access_token, ad_account_ids


def _get_google_credentials_and_accounts(db: Session, workspace_id: int):
    """Get Google integration id, refresh_token, client_id, client_secret, customer_ids. Raises HTTPException if missing."""
    import os
    integrations = crud.get_integrations_by_workspace(db, workspace_id=workspace_id)
    google = next((i for i in integrations if i.ad_platform == "GOOGLE"), None)
    if not google:
        raise HTTPException(
            status_code=400,
            detail="No Google Ads integration found for this workspace. Connect Google in Platform Integration first.",
        )
    tokens = google.tokens or {}
    refresh_tokens = google.refresh_tokens or {}
    refresh_token = (tokens.get("refresh_token") or (refresh_tokens.get("refresh_token") if isinstance(refresh_tokens, dict) else None)) if isinstance(tokens, dict) else None
    if not refresh_token and isinstance(refresh_tokens, dict):
        refresh_token = refresh_tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Google integration has no refresh token. Reconnect Google in Platform Integration.",
        )
    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET must be set.",
        )
    ads_accounts = google.ads_accounts or []
    customer_ids = []
    for a in ads_accounts:
        cid = a.get("customer_id") or a.get("id") or a.get("account_id")
        if cid:
            customer_ids.append(str(cid).replace("-", ""))
    return google.id, refresh_token, client_id, client_secret, customer_ids


@router.post("/platform-data")
def platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    Get or set platform_data (date-wise).
    - Get: Body { "workspace_id": N, optional "report_date", "report_date_from", "report_date_to" }.
      Returns { success, workspace_id, data: [ rows ordered by report_date ] }.
    - Set: Body { "workspace_id": N, "data": { "rows": [ { report_date, campaign_name, ... } ] } }.
      Saves rows into platform_data table.
    """
    workspace_id = body.workspace_id
    if body.data is not None and isinstance(body.data, dict) and "rows" in body.data:
        rows = body.data.get("rows") if isinstance(body.data.get("rows"), list) else []
        if not rows:
            return schemas.SetDataResponse(success=True, workspace_id=workspace_id)
        _, _, _ = _get_meta_access_and_accounts(db, workspace_id)
        meta = crud.get_meta_integration_by_workspace(db, workspace_id)
        if not meta:
            raise HTTPException(status_code=400, detail="No Meta integration for this workspace.")
        by_date = {}
        for r in rows:
            if not isinstance(r, dict):
                continue
            rd = r.get("report_date")
            if rd is None:
                continue
            d = rd if isinstance(rd, str) else getattr(rd, "isoformat", lambda: str(rd))()
            by_date.setdefault(d, []).append(r)
        for report_date, date_rows in by_date.items():
            crud.save_platform_data(db, meta.id, report_date, date_rows, type="meta")
        return schemas.SetDataResponse(success=True, workspace_id=workspace_id)
    # Get: filter by report_date / report_date_from / report_date_to
    rows = crud.get_platform_data(
        db,
        workspace_id=workspace_id,
        report_date=body.report_date,
        report_date_from=body.report_date_from,
        report_date_to=body.report_date_to,
        type=body.type,
    )
    return {
        "success": True,
        "workspace_id": workspace_id,
        "data": [_row_to_dict(r) for r in rows],
    }


@router.post("/run-meta-etl")
def run_meta_etl(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    Run Meta insights ETL for a date, save to platform_data table.
    Body: { "workspace_id": N, optional "report_date": "YYYY-MM-DD" } (default: yesterday).
    """
    from datetime import timedelta
    workspace_id = body.workspace_id
    report_date = body.report_date
    integration_id, access_token, ad_account_ids = _get_meta_access_and_accounts(db, workspace_id)
    rows = run_meta_insights_pipeline(
        access_token=access_token,
        ad_account_ids=ad_account_ids or None,
        report_date=report_date,
    )
    report_d = report_date or (date.today() - timedelta(days=1)).isoformat()
    if hasattr(report_d, "isoformat"):
        report_d = report_d.isoformat()
    else:
        report_d = str(report_d)
    crud.save_platform_data(db, integration_id, report_d, rows, type="meta")
    return {"success": True, "workspace_id": workspace_id, "report_date": report_d, "rows_saved": len(rows), "type": "meta"}


@router.post("/run-google-etl")
def run_google_etl(body: schemas.RunEtlRequest, db: Session = Depends(get_db)):
    """
    Run Google Ads insights ETL for a date, save to platform_data table (type=google).
    Body: { "workspace_id": N, optional "report_date": "YYYY-MM-DD" } (default: yesterday).
    """
    from datetime import timedelta
    import os
    workspace_id = body.workspace_id
    report_d = body.report_date or (date.today() - timedelta(days=1)).isoformat()
    if hasattr(report_d, "isoformat"):
        report_d = report_d.isoformat()
    else:
        report_d = str(report_d)

    if not os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"):
        logging.warning("run-google-etl: GOOGLE_ADS_DEVELOPER_TOKEN is not set")
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_ADS_DEVELOPER_TOKEN is not set. Set it in .env for Google Ads API access.",
        )
    try:
        integration_id, refresh_token, client_id, client_secret, customer_ids = _get_google_credentials_and_accounts(db, workspace_id)
        developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        rows = run_google_insights_pipeline(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            customer_ids=customer_ids or None,
            report_date=report_d,
            developer_token=developer_token,
        )
    except (ValueError, ImportError) as e:
        logging.warning("run-google-etl: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    crud.save_platform_data(db, integration_id, report_d, rows, type="google")
    return {"success": True, "workspace_id": workspace_id, "report_date": report_d, "rows_saved": len(rows), "type": "google"}
