from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from meta_extractor import run_pipeline

router = APIRouter(prefix="/platform-data", tags=["platform-data"])


def _etl_result_to_row(result: dict) -> tuple[list, list, list, list]:
    """Convert run_pipeline result to (ad_accounts, campaigns, adsets, ads)."""
    return (
        result.get("ad_accounts") or [],
        result.get("campaigns") or [],
        result.get("adsets") or [],
        result.get("ads") or [],
    )


@router.post("/set-platform-data", response_model=schemas.SetDataResponse)
def set_platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/set-platform-data - insert/update platform_data in DB.
    Body: {"workspace_id": N, "data": { "ad_accounts", "campaigns", "adsets", "ads" }}.
    On click (e.g. after ETL), call this to persist.
    """
    workspace_id = body.workspace_id
    raw = body.data
    if isinstance(raw, dict):
        ad_accounts = raw.get("ad_accounts")
        campaigns = raw.get("campaigns")
        adsets = raw.get("adsets")
        ads = raw.get("ads")
        if ad_accounts is None and campaigns is None and adsets is None and ads is None:
            ad_accounts = campaigns = adsets = ads = []
    else:
        ad_accounts = campaigns = adsets = ads = []
    crud.create_or_update_platform_data(
        db,
        workspace_id=workspace_id,
        ad_accounts=ad_accounts if isinstance(ad_accounts, list) else None,
        campaigns=campaigns if isinstance(campaigns, list) else None,
        adsets=adsets if isinstance(adsets, list) else None,
        ads=ads if isinstance(ads, list) else None,
    )
    return schemas.SetDataResponse(success=True, workspace_id=workspace_id)


@router.post("/get-platform-data")
def get_platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/get-platform-data - get platform_data from DB for workspace.
    Body: {"workspace_id": N}. Returns { success, workspace_id, data: { ad_accounts, campaigns, adsets, ads } }.
    """
    workspace_id = body.workspace_id
    row = crud.get_platform_data(db, workspace_id=workspace_id)
    if not row:
        return {
            "success": True,
            "workspace_id": workspace_id,
            "data": {"ad_accounts": [], "campaigns": [], "adsets": [], "ads": []},
        }
    data = {
        "ad_accounts": row.ad_accounts or [],
        "campaigns": row.campaigns or [],
        "adsets": row.adsets or [],
        "ads": row.ads or [],
    }
    return {"success": True, "workspace_id": workspace_id, "data": data}


@router.post("/run-meta-etl")
def run_meta_etl(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/run-meta-etl - run Meta ETL, insert into DB, return data.
    Body: {"workspace_id": N}. Uses Meta integration token; saves to platform_data table.
    """
    workspace_id = body.workspace_id
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
    ads_account = meta.ads_account or []
    ad_account_ids = [
        str(a.get("account_id") or a.get("id") or "")
        for a in ads_account
        if a.get("account_id") or a.get("id")
    ]
    result = run_pipeline(
        access_token=access_token,
        ad_account_ids=ad_account_ids if ad_account_ids else None,
        store=None,
        workspace_id=None,
    )
    ad_accounts, campaigns, adsets, ads = _etl_result_to_row(result)
    crud.create_or_update_platform_data(
        db,
        workspace_id=workspace_id,
        ad_accounts=ad_accounts,
        campaigns=campaigns,
        adsets=adsets,
        ads=ads,
    )
    return {"success": True, "workspace_id": workspace_id, "data": result}
