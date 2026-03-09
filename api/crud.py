from sqlalchemy.orm import Session
import models


# ----- Campaign ads / Integration -----
def get_integrations_by_workspace(db: Session, workspace_id: int = 1):
    return (
        db.query(models.Integration)
        .filter(
            models.Integration.workspace_id == workspace_id,
            models.Integration.access_removed.is_(False),
        )
        .all()
    )


def get_integration_by_id(db: Session, integration_id: int):
    return db.query(models.Integration).filter(models.Integration.id == integration_id).first()


def revoke_integration(db: Session, integration_id: int):
    row = db.query(models.Integration).filter(models.Integration.id == integration_id).first()
    if not row:
        return None
    row.access_removed = True
    db.commit()
    db.refresh(row)
    return row


def get_meta_integration_by_workspace(db: Session, workspace_id: int):
    """Return the META integration for the workspace if any (used for update-or-insert)."""
    return (
        db.query(models.Integration)
        .filter(
            models.Integration.workspace_id == workspace_id,
            models.Integration.ad_platform == "META",
        )
        .first()
    )


def create_or_update_meta_integration(
    db: Session,
    workspace_id: int,
    ads_userinfo: dict,
    tokens: dict,
    ads_accounts: list,
    refresh_tokens: dict | None = None,
):
    """If workspace_id already has a META integration row, update it; else insert new row."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    row = get_meta_integration_by_workspace(db, workspace_id)
    if row:
        row.ads_userinfo = ads_userinfo
        row.tokens = tokens
        row.ads_accounts = ads_accounts
        row.refresh_tokens = refresh_tokens
        row.access_removed = False
        row.last_authenticated = now
        db.commit()
        db.refresh(row)
        return row
    new_row = models.Integration(
        workspace_id=workspace_id,
        ad_platform="META",
        status=True,
        ads_userinfo=ads_userinfo,
        tokens=tokens,
        ads_accounts=ads_accounts,
        refresh_tokens=refresh_tokens,
        access_removed=False,
        last_authenticated=now,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row


# ----- Platform Data -----
def get_platform_data(db: Session, workspace_id: int):
    return db.query(models.PlatformData).filter(models.PlatformData.workspace_id == workspace_id).first()


def create_or_update_platform_data(
    db: Session,
    workspace_id: int,
    campaigns: list | None = None,
):
    row = get_platform_data(db, workspace_id)
    if row:
        if campaigns is not None:
            row.campaigns = campaigns
        db.commit()
        db.refresh(row)
        return row
    new_row = models.PlatformData(
        workspace_id=workspace_id,
        campaigns=campaigns or [],
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row
