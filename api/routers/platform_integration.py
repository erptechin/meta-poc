import asyncio
import os
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter(tags=["campaign-ads"])

META_API_VERSION = os.getenv("META_API_VERSION", "v23.0")
APP_ID = os.getenv("META_ADS_CLIENT_ID")
APP_SECRET = os.getenv("META_ADS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("META_ADS_REDIRECT_URI")
BASE_APP_UI_URL = os.getenv("BASE_APP_UI_URL")

# Google Ads OAuth (ref: nyx-api googleAdsRoutes.js, .env)
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REDIRECT_URI = os.getenv("GOOGLE_ADS_AUTH_REDIRECT_URI", "http://localhost:5005/v1/campaign-ads/google/auth/callback")
GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/content",
]


def _integration_result_redirect(outcome: str, message: str = "") -> RedirectResponse:
    base = (BASE_APP_UI_URL or "").rstrip("/")
    q = f"outcome={quote(outcome)}"
    if message:
        q += f"&message={quote(message)}"
    return RedirectResponse(url=f"{base}/integration-result?{q}", status_code=302)


def _get_httpx_client(request: Request):
    return request.app.state.httpx_client


def _format_status_row(integration):
    return {
        "id": integration.id,
        "workspace_id": 1,
        "status": integration.status,
        "ad_platform": integration.ad_platform,
        "ads_userinfo": integration.ads_userinfo,
        "ads_accounts": integration.ads_accounts or [],
        "refresh_tokens": integration.refresh_tokens,
        "last_authenticated": integration.last_authenticated.isoformat() if integration.last_authenticated else None,
        "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
    }


@router.get("/status", response_model=list[dict])
def get_platform_integration_status(db: Session = Depends(get_db)):
    """
    GET /v1/campaign-ads/status
    List all integrations for the default workspace (workspace_id=1).
    Returns list of integration objects with id, workspace_id, status, ad_platform, ads_userinfo, ads_accounts, refresh_tokens, last_authenticated, updated_at.
    """
    rows = crud.get_integrations_by_workspace(db)
    return [_format_status_row(r) for r in rows]


@router.post("/meta/auth", response_model=schemas.MetaAuthResponse)
def meta_auth(body: schemas.MetaAuthRequest | None = Body(None)):
    """
    POST /v1/campaign-ads/meta/auth
    Returns the Meta (Facebook) OAuth URL. Client should open this URL in a popup; after user authorizes, Meta redirects to /meta/auth/callback.
    Response: { "authUrl": "https://www.facebook.com/..." }.
    """
    state = quote("{}")
    scope = "public_profile,email,ads_management,ads_read,pages_show_list,business_management,pages_read_engagement,catalog_management,instagram_manage_insights,instagram_basic"
    auth_url = (
        f"https://www.facebook.com/{META_API_VERSION}/dialog/oauth"
        f"?client_id={APP_ID}"
        f"&redirect_uri={quote(REDIRECT_URI or '')}"
        f"&state={state}"
        f"&scope={quote(scope)}"
    )
    return schemas.MetaAuthResponse(authUrl=auth_url)


async def _fetch_instagram_accounts(client: httpx.AsyncClient, business_id: str, access_token: str) -> list:
    try:
        r = await client.get(
            f"https://graph.facebook.com/{META_API_VERSION}/{business_id}/instagram_accounts",
            params={"fields": "id,username"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        r.raise_for_status()
        return r.json().get("data") or []
    except Exception:
        return []


@router.get("/meta/auth/callback")
async def meta_auth_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(_get_httpx_client),
):
    """
    GET /v1/campaign-ads/meta/auth/callback
    OAuth callback: Meta redirects here after user authorizes. Exchanges code for short- then long-lived token, fetches user/ad accounts, upserts META integration for workspace_id=1, then redirects to app integration-result page.
    """
    if not code or not state:
        return _integration_result_redirect("failure", "Invalid callback parameters.")
    try:
        workspace_id = 1
        tr = await client.get(
            f"https://graph.facebook.com/{META_API_VERSION}/oauth/access_token",
            params={"client_id": APP_ID, "redirect_uri": REDIRECT_URI, "client_secret": APP_SECRET, "code": code},
        )
        tr.raise_for_status()
        short_lived = tr.json().get("access_token")
        if not short_lived:
            raise ValueError("No access_token in token response")
        lr = await client.get(
            f"https://graph.facebook.com/{META_API_VERSION}/oauth/access_token",
            params={"grant_type": "fb_exchange_token", "client_id": APP_ID, "client_secret": APP_SECRET, "fb_exchange_token": short_lived},
        )
        lr.raise_for_status()
        long_lived_resp = lr.json()
        long_lived = long_lived_resp.get("access_token")
        if not long_lived:
            raise ValueError("No access_token in long-lived response")
        tokens = {"access_token": long_lived}
        # Meta does not return a separate refresh_token. Long-lived response includes token_type, expires_in (seconds).
        # To refresh: call same endpoint with grant_type=fb_exchange_token and fb_exchange_token=<current long-lived token>.
        refresh_tokens = {k: v for k, v in long_lived_resp.items() if k != "access_token"} or None

        me_r = await client.get(
            f"https://graph.facebook.com/{META_API_VERSION}/me",
            params={"access_token": short_lived, "fields": "id,name,email,picture,businesses,adaccounts{id,account_id,name,business,currency,timezone_id,timezone_name}"},
        )
        me_r.raise_for_status()
        user_info = me_r.json()
        adaccounts_data = (user_info.get("adaccounts") or {}).get("data") or []
        user_detail = {
            "userInfo": user_info,
            "adaccounts": user_info.get("adaccounts"),
            "accounts": {"data": []},
            "instagramAccounts": {"data": []},
            "businesses": user_info.get("businesses"),
        }
        page_ok = False
        insta_ok = False

        async def _empty_insta():
            return []

        async def _fetch_pages_and_insta(acc):
            pid = acc.get("id")
            biz = acc.get("business")
            bid = biz.get("id") if isinstance(biz, dict) else None
            pr_task = client.get(
                f"https://graph.facebook.com/{META_API_VERSION}/{pid}/promote_pages",
                params={"access_token": short_lived},
            )
            insta_task = _fetch_instagram_accounts(client, bid, long_lived) if bid else _empty_insta()
            pr, il = await asyncio.gather(pr_task, insta_task)
            il = il if isinstance(il, list) else []
            return acc, pr, il

        if adaccounts_data:
            results = await asyncio.gather(
                *[_fetch_pages_and_insta(acc) for acc in adaccounts_data],
                return_exceptions=True,
            )
            for item in results:
                if isinstance(item, Exception):
                    continue
                acc, pr, il = item
                data = (pr.json() if pr.is_success else {}).get("data") or []
                for p in data:
                    user_detail["accounts"]["data"].append({**p, "account_id": acc.get("account_id")})
                if data:
                    page_ok = True
                for i in il:
                    user_detail["instagramAccounts"]["data"].append({**i, "account_id": acc.get("account_id")})
                if il:
                    insta_ok = True

        if not user_detail["accounts"]["data"]:
            page_ok = False
            ar = await client.get(
                f"https://graph.facebook.com/{META_API_VERSION}/me/accounts",
                params={"access_token": short_lived, "fields": "id,name,access_token"},
            )
            if ar.is_success:
                alist = (ar.json() or {}).get("data") or []
                for p in alist:
                    user_detail["accounts"]["data"].append({"id": p.get("id"), "name": p.get("name")})
                if not user_detail["instagramAccounts"]["data"] and alist:
                    for pg in alist:
                        pt = pg.get("access_token")
                        if not pt:
                            continue
                        rr = await client.get(
                            f"https://graph.facebook.com/{META_API_VERSION}/{pg.get('id')}",
                            params={"access_token": pt, "fields": "name,instagram_accounts{name}"},
                        )
                        if rr.is_success:
                            ia = (rr.json() or {}).get("instagram_accounts") or {}
                            for i in (ia.get("data") or []):
                                user_detail["instagramAccounts"]["data"].append({**i, "page_id": pg.get("id")})

        msg = ""
        if not user_detail["instagramAccounts"]["data"] and not user_detail["accounts"]["data"]:
            return _integration_result_redirect("failure", "No page Ids and no instagram accounts found.")
        if not user_detail["instagramAccounts"]["data"]:
            msg = "No instagram accounts are found for any ad account."
            if page_ok:
                msg = f"For some ad accounts pageId are not found AND {msg}"
        elif not user_detail["accounts"]["data"]:
            msg = "No page Ids are found for any ad account."
            if insta_ok:
                msg = f"For some ad accounts instagram accounts are not found AND {msg}"
        elif not page_ok or not insta_ok:
            msg = "For some ad accounts pageId or instagram accounts are not found"

        ads_list = [
            {"id": a.get("id"), "account_id": a.get("account_id"), "account_name": a.get("name"), "currency_code": a.get("currency"), "timezone_id": a.get("timezone_id"), "time_zone": a.get("timezone_name")}
            for a in adaccounts_data if a.get("account_id")
        ]
        # If workspace_id already has a META integration in DB, update it; else insert new row.
        crud.create_or_update_meta_integration(db=db, workspace_id=workspace_id, ads_userinfo=user_detail, tokens=tokens, ads_accounts=ads_list, refresh_tokens=refresh_tokens)
        return _integration_result_redirect("success", msg)
    except Exception as ex:
        return _integration_result_redirect("failure", str(ex) or "Unexpected error integrating META.")


# ----- Google Ads OAuth (ref: nyx-api routes/campaignAds/googleAdsRoutes.js) -----
@router.post("/google/auth", response_model=schemas.MetaAuthResponse)
def google_auth(body: schemas.MetaAuthRequest | None = Body(None)):
    """
    POST /v1/campaign-ads/google/auth
    Returns the Google Ads OAuth URL. Client should open this URL in a popup; after user authorizes, Google redirects to /google/auth/callback.
    Response: { "authUrl": "https://accounts.google.com/..." }. Uses GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_AUTH_REDIRECT_URI.
    """
    state = quote("{}")
    scope = " ".join(GOOGLE_OAUTH_SCOPES)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={quote(GOOGLE_ADS_CLIENT_ID or '')}"
        f"&redirect_uri={quote(GOOGLE_ADS_REDIRECT_URI or '')}"
        "&response_type=code"
        f"&scope={quote(scope)}"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    return schemas.MetaAuthResponse(authUrl=auth_url)


@router.get("/google/auth/callback")
async def google_auth_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(_get_httpx_client),
):
    """
    GET /v1/campaign-ads/google/auth/callback
    OAuth callback: Google redirects here after user authorizes. Exchanges code for tokens, fetches userinfo, upserts GOOGLE integration for workspace_id=1, then redirects to app integration-result page.
    """
    if not code or not state:
        return _integration_result_redirect("failure", "Invalid callback parameters.")
    try:
        workspace_id = 1
        # Exchange code for tokens (ref: nyx-api oauth2Client.getToken)
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_ADS_CLIENT_ID,
                "client_secret": GOOGLE_ADS_CLIENT_SECRET,
                "redirect_uri": GOOGLE_ADS_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        tokens_data = token_resp.json()
        access_token = tokens_data.get("access_token")
        if not access_token:
            raise ValueError("No access_token in token response")
        tokens = {"access_token": access_token}
        if tokens_data.get("refresh_token"):
            tokens["refresh_token"] = tokens_data["refresh_token"]
        refresh_tokens = {k: v for k, v in tokens_data.items() if k != "access_token"} or None

        # Fetch user info (ref: nyx-api axios.get userinfo)
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_resp.raise_for_status()
        user_info = userinfo_resp.json()

        user_detail = {
            "userInfo": user_info,
            "accounts": {"data": []},
            "adaccounts": None,
        }
        ads_list = []

        # If workspace_id already has a GOOGLE integration in DB, update it; else insert new row.
        crud.create_or_update_google_integration(
            db=db,
            workspace_id=workspace_id,
            ads_userinfo=user_detail,
            tokens=tokens,
            ads_accounts=ads_list,
            refresh_tokens=refresh_tokens,
        )
        return _integration_result_redirect("success", "")
    except Exception as ex:
        return _integration_result_redirect("failure", str(ex) or "Unexpected error integrating Google.")


# ----- Revoke integration -----
@router.post("/revoke-access", response_model=schemas.RevokeAccessResponse)
def revoke_access(body: schemas.RevokeAccessRequest, db: Session = Depends(get_db)):
    """
    POST /v1/campaign-ads/revoke-access
    Revoke (soft-delete) an integration by integration_id. Body: { "integration_id": N }.
    Sets access_removed=True for the integration. Returns { "status": "success", "message": "Access revoked" }.
    """
    row = crud.revoke_integration(db, integration_id=body.integration_id)
    if not row:
        raise HTTPException(status_code=400, detail="Error revoking access")
    return schemas.RevokeAccessResponse(status="success", message="Access revoked")
