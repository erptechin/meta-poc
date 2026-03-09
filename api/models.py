from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Date, Numeric, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Integration(Base):
    __tablename__ = "integration"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, nullable=False, index=True, default=1)
    ad_platform = Column(String(64), nullable=False, index=True)  # META, GOOGLE, LINKEDIN, etc.
    status = Column(Boolean, default=True, nullable=False)
    ads_userinfo = Column(JSON, nullable=True)  # userInfo, accounts, adaccounts, etc.
    ads_accounts = Column(JSON, nullable=True)  # list of { id, account_id, account_name }
    tokens = Column(JSON, nullable=True)  # { access_token: long_lived_token }
    refresh_tokens = Column(JSON, nullable=True)  # token metadata: expires_in, token_type, refresh_token (if any)
    access_removed = Column(Boolean, default=False, nullable=False)
    last_authenticated = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlatformData(Base):
    """One row per integration per report_date per campaign (metrics). type = meta | google | linkedin."""
    __tablename__ = "platform_data"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integration.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(32), nullable=False, default="meta", index=True)  # meta, google, linkedin
    report_date = Column(Date, nullable=True, index=True)
    campaign_name = Column(String(512), nullable=True)
    campaign_type = Column(String(128), nullable=True)
    source = Column(String(128), nullable=True)
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    cpm = Column(Numeric(14, 4), nullable=True)
    cpc = Column(Numeric(14, 4), nullable=True)
    ctr = Column(Numeric(14, 4), nullable=True)
    amount_spent = Column(Numeric(14, 4), nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
