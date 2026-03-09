from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ----- Integration (platform-integration) -----
class IntegrationStatusResponse(BaseModel):
    id: int
    workspace_id: int
    status: bool
    ad_platform: str
    ads_userinfo: dict[str, Any] | None
    ads_accounts: list[dict[str, Any]] | None
    last_authenticated: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class MetaAuthRequest(BaseModel):
    workspace_id: int | None = None


class MetaAuthResponse(BaseModel):
    authUrl: str


class RevokeAccessRequest(BaseModel):
    workspace_id: int = 1
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
