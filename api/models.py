from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
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
    """Stored Meta ETL result per workspace (campaigns only)."""
    __tablename__ = "platform_data"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, nullable=False, index=True, unique=True)
    campaigns = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
