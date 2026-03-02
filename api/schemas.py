from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ----- User -----
class UserBase(BaseModel):
    email: str
    name: str | None = None
    phone: str | None = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


# ----- Integration (campaign-ads) -----
class IntegrationStatusResponse(BaseModel):
    id: int
    user_id: int
    workspace_id: int
    status: bool
    ad_platform: str
    email: str | None
    ad_login_userinfo: dict[str, Any] | None
    ads_account: list[dict[str, Any]] | None
    last_authenticated: datetime | None
    updated_at: datetime | None
    user: dict  # { name, email, phone }

    class Config:
        from_attributes = True


class MetaAuthRequest(BaseModel):
    workspace_id: int


class MetaAuthResponse(BaseModel):
    authUrl: str


class RevokeAccessRequest(BaseModel):
    workspace_id: int
    tokenRecord_id: int


class RevokeAccessResponse(BaseModel):
    status: str = "success"
    message: str = "Access revoked"
