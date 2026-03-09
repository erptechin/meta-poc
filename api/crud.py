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


def get_google_integration_by_workspace(db: Session, workspace_id: int):
    """Return the GOOGLE integration for the workspace if any (used for update-or-insert)."""
    return (
        db.query(models.Integration)
        .filter(
            models.Integration.workspace_id == workspace_id,
            models.Integration.ad_platform == "GOOGLE",
        )
        .first()
    )


def create_or_update_google_integration(
    db: Session,
    workspace_id: int,
    ads_userinfo: dict,
    tokens: dict,
    ads_accounts: list,
    refresh_tokens: dict | None = None,
):
    """If workspace_id already has a GOOGLE integration row, update it; else insert new row."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    row = get_google_integration_by_workspace(db, workspace_id)
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
        ad_platform="GOOGLE",
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
def get_platform_data(
    db: Session,
    workspace_id: int,
    report_date: str | None = None,
    report_date_from: str | None = None,
    report_date_to: str | None = None,
    type: str | None = None,
):
    """
    Get platform_data rows for workspace (all integrations), optionally filtered by report_date and type.
    type: 'meta' | 'google' | 'linkedin' | None (all).
    Returns list of PlatformData ordered by report_date.
    """
    integration_ids = [
        i.id for i in db.query(models.Integration).filter(
            models.Integration.workspace_id == workspace_id,
            models.Integration.access_removed.is_(False),
        ).all()
    ]
    if not integration_ids:
        return []
    q = db.query(models.PlatformData).filter(models.PlatformData.integration_id.in_(integration_ids))
    if type:
        q = q.filter(models.PlatformData.type == type)
    if report_date:
        q = q.filter(models.PlatformData.report_date == report_date)
    if report_date_from:
        q = q.filter(models.PlatformData.report_date >= report_date_from)
    if report_date_to:
        q = q.filter(models.PlatformData.report_date <= report_date_to)
    return q.order_by(models.PlatformData.report_date).all()


def save_platform_data(
    db: Session,
    integration_id: int,
    report_date: str,
    rows: list[dict],
    type: str = "meta",
) -> int:
    """
    Replace platform_data for (integration_id, report_date, type) with the given rows.
    type: 'meta' | 'google' | 'linkedin'.
    Each row: campaign_name, campaign_type?, source?, impressions?, clicks?, cpm?, cpc?, ctr?, amount_spent?, data?
    Returns count of rows saved.
    """
    from datetime import date
    db.query(models.PlatformData).filter(
        models.PlatformData.integration_id == integration_id,
        models.PlatformData.report_date == report_date,
        models.PlatformData.type == type,
    ).delete()
    report_d = date.fromisoformat(report_date) if isinstance(report_date, str) else report_date
    for r in rows or []:
        row = models.PlatformData(
            integration_id=integration_id,
            type=type,
            report_date=report_d,
            campaign_name=r.get("campaign_name"),
            campaign_type=r.get("campaign_type"),
            source=r.get("source"),
            impressions=r.get("impressions"),
            clicks=r.get("clicks"),
            cpm=r.get("cpm"),
            cpc=r.get("cpc"),
            ctr=r.get("ctr"),
            amount_spent=r.get("amount_spent"),
            data=r.get("data"),
        )
        db.add(row)
    db.commit()
    return len(rows or [])
