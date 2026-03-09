from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from meta_extractor import run_pipeline

router = APIRouter(tags=["platform-data"])


def _campaigns_from_raw(raw: dict | None) -> list:
    """Extract campaigns list from request data or pipeline result."""
    if not isinstance(raw, dict):
        return []
    c = raw.get("campaigns")
    return c if isinstance(c, list) else []


def _get_meta_access_and_accounts(db: Session, workspace_id: int) -> tuple[str, list[str]]:
    """Get Meta access token and ad account IDs for workspace. Raises HTTPException if missing."""
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
    return access_token, ad_account_ids


@router.post("/platform-data")
def platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    Single endpoint: get or set platform_data.
    - Body with `data`: { "workspace_id": N, "data": { "campaigns": [...] } } → set and return success.
    - Body without `data`: { "workspace_id": N } → return stored data { success, workspace_id, data: { campaigns } }.
    """
    workspace_id = body.workspace_id
    if body.data is not None and isinstance(body.data, dict):
        campaigns = _campaigns_from_raw(body.data)
        crud.create_or_update_platform_data(db, workspace_id=workspace_id, campaigns=campaigns)
        return schemas.SetDataResponse(success=True, workspace_id=workspace_id)
    row = crud.get_platform_data(db, workspace_id=workspace_id)
    campaigns = (row.campaigns or []) if row else []
    return {"success": True, "workspace_id": workspace_id, "data": {"campaigns": campaigns}}


@router.post("/run-meta-etl")
def run_meta_etl(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    Run Meta ETL, save to platform_data, return result.
    Body: { "workspace_id": N }.
    """
    workspace_id = body.workspace_id
    access_token, ad_account_ids = _get_meta_access_and_accounts(db, workspace_id)
    result = run_pipeline(
        access_token=access_token,
        ad_account_ids=ad_account_ids or None,
        store=None,
        workspace_id=None,
    )
    campaigns = _campaigns_from_raw(result)
    crud.create_or_update_platform_data(db, workspace_id=workspace_id, campaigns=campaigns)
    return {"success": True, "workspace_id": workspace_id, "data": result}
