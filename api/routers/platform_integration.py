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
    rows = crud.get_integrations_by_workspace(db)
    return [_format_status_row(r) for r in rows]


@router.post("/meta/auth", response_model=schemas.MetaAuthResponse)
def meta_auth(body: schemas.MetaAuthRequest | None = Body(None)):
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


@router.post("/revoke-access", response_model=schemas.RevokeAccessResponse)
def revoke_access(body: schemas.RevokeAccessRequest, db: Session = Depends(get_db)):
    row = crud.revoke_integration(db, integration_id=body.integration_id)
    if not row:
        raise HTTPException(status_code=400, detail="Error revoking access")
    return schemas.RevokeAccessResponse(status="success", message="Access revoked")
