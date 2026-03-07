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


# ----- Integration (platform-integration) -----
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
    workspace_id: int | None = None


class MetaAuthResponse(BaseModel):
    authUrl: str


class RevokeAccessRequest(BaseModel):
    workspace_id: int
    integration_id: int


class RevokeAccessResponse(BaseModel):
    status: str = "success"
    message: str = "Access revoked"


# ----- Platform Data -----
class SetDataRequest(BaseModel):
    workspace_id: int
    data: dict[str, Any] | list | str | int | float | bool | None = None


class SetDataResponse(BaseModel):
    success: bool = True
    workspace_id: int


class GetDataResponse(BaseModel):
    data: dict[str, Any] | list[Any] | None
    workspace_id: int
