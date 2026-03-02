from sqlalchemy.orm import Session
import models


# ----- Campaign ads / Integration -----
def get_integrations_by_workspace(db: Session, workspace_id: int):
    return (
        db.query(models.Integration)
        .filter(
            models.Integration.workspace_id == workspace_id,
            models.Integration.access_removed == False,
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


def get_workspace(db: Session, workspace_id: int):
    return db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()


def get_meta_integration_by_user_workspace_email(
    db: Session, user_id: int, workspace_id: int, email: str
):
    return (
        db.query(models.Integration)
        .filter(
            models.Integration.user_id == user_id,
            models.Integration.workspace_id == workspace_id,
            models.Integration.ad_platform == "META",
            models.Integration.email == email,
        )
        .first()
    )


def create_or_update_meta_integration(
    db: Session,
    user_id: int,
    workspace_id: int,
    email: str,
    ad_login_userinfo: dict,
    tokens: dict,
    ads_account: list,
    refresh_tokens: dict | None = None,
):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    row = get_meta_integration_by_user_workspace_email(db, user_id, workspace_id, email)
    if row:
        row.ad_login_userinfo = ad_login_userinfo
        row.tokens = tokens
        row.ads_account = ads_account
        row.refresh_tokens = refresh_tokens
        row.access_removed = False
        row.last_authenticated = now
        db.commit()
        db.refresh(row)
        return row
    new_row = models.Integration(
        user_id=user_id,
        workspace_id=workspace_id,
        ad_platform="META",
        status=True,
        email=email,
        ad_login_userinfo=ad_login_userinfo,
        tokens=tokens,
        ads_account=ads_account,
        refresh_tokens=refresh_tokens,
        access_removed=False,
        last_authenticated=now,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row
