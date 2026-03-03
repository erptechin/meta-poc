from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from meta_extractor import run_pipeline

router = APIRouter(prefix="/platform-data", tags=["platform-data"])

# In-memory store keyed by workspace_id (replace with DB model if needed)
_platform_data_store: dict[int, dict[str, Any]] = {}


@router.post("/set-platform-data", response_model=schemas.SetDataResponse)
def set_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """POST /v1/platform-data/set-platform-data - store data for a workspace."""
    data = body.data if isinstance(body.data, dict) else {"value": body.data}
    _platform_data_store[body.workspace_id] = data
    return schemas.SetDataResponse(success=True, workspace_id=body.workspace_id)


@router.post("/get-platform-data")
def get_platform_data(body: schemas.SetDataRequest, db: Session = Depends(get_db)):
    """
    POST /v1/platform-data/get-platform-data - run Meta ETL for workspace and return data.
    Body: {"workspace_id": N}. Uses Meta integration token and ad accounts; loads result into store and returns it.
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
        store=_platform_data_store,
        workspace_id=workspace_id,
        load_key="meta_etl",
    )
    return {"success": True, "workspace_id": workspace_id, "data": result}
