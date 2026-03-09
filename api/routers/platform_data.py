from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from meta_extractor import run_pipeline

router = APIRouter(tags=["platform-data"])


def _etl_result_to_campaigns(result: dict) -> list:
    """Extract campaigns from run_pipeline result."""
    return result.get("campaigns") or []


@router.post("/set-platform-data", response_model=schemas.SetDataResponse)
def set_platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/set-platform-data - insert/update platform_data in DB.
    Body: {"workspace_id": N, "data": { "campaigns": [...] }}.
    """
    workspace_id = body.workspace_id
    raw = body.data
    campaigns = []
    if isinstance(raw, dict) and isinstance(raw.get("campaigns"), list):
        campaigns = raw["campaigns"]
    crud.create_or_update_platform_data(db, workspace_id=workspace_id, campaigns=campaigns)
    return schemas.SetDataResponse(success=True, workspace_id=workspace_id)


@router.post("/get-platform-data")
def get_platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/get-platform-data - get platform_data from DB for workspace.
    Body: {"workspace_id": N}. Returns { success, workspace_id, data: { campaigns } }.
    """
    workspace_id = body.workspace_id
    row = crud.get_platform_data(db, workspace_id=workspace_id)
    if not row:
        return {"success": True, "workspace_id": workspace_id, "data": {"campaigns": []}}
    return {
        "success": True,
        "workspace_id": workspace_id,
        "data": {"campaigns": row.campaigns or []},
    }


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
    ads_accounts = meta.ads_accounts or []
    ad_account_ids = [
        str(a.get("account_id") or a.get("id") or "")
        for a in ads_accounts
        if a.get("account_id") or a.get("id")
    ]
    result = run_pipeline(
        access_token=access_token,
        ad_account_ids=ad_account_ids if ad_account_ids else None,
        store=None,
        workspace_id=None,
    )
    campaigns = _etl_result_to_campaigns(result)
    crud.create_or_update_platform_data(db, workspace_id=workspace_id, campaigns=campaigns)
    return {"success": True, "workspace_id": workspace_id, "data": result}
