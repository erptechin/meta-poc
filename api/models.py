from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)


class Workspace(Base):
    __tablename__ = "workspace"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    workspace_name = Column(String(255), nullable=False)

    user = relationship("User", backref="workspaces")


class Integration(Base):
    __tablename__ = "integration"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    workspace_id = Column(Integer, nullable=False, index=True)
    ad_platform = Column(String(64), nullable=False, index=True)  # META, GOOGLE, LINKEDIN, etc.
    status = Column(Boolean, default=True, nullable=False)
    email = Column(String(255), nullable=True)  # platform user id (e.g. Meta id)
    ad_login_userinfo = Column(JSON, nullable=True)  # userInfo, accounts, adaccounts, etc.
    ads_account = Column(JSON, nullable=True)  # list of { id, account_id, account_name }
    tokens = Column(JSON, nullable=True)  # { access_token: long_lived_token }
    refresh_tokens = Column(JSON, nullable=True)  # token metadata: expires_in, token_type, refresh_token (if any)
    access_removed = Column(Boolean, default=False, nullable=False)
    last_authenticated = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="integrations")


class PlatformData(Base):
    """Stored Meta ETL result per workspace (campaigns only)."""
    __tablename__ = "platform_data"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, nullable=False, index=True, unique=True)
    campaigns = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
