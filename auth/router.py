from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.oauth import oauth
from auth.service import AuthService

from auth.token_service import TokenService
from database.session import get_db

from fastapi import Depends, HTTPException
from model.user import User
from schema.auth import RefreshRequest
from fastapi import Query, Form
from fastapi.responses import RedirectResponse
import hashlib
import base64
import secrets
from store import oauth_store, client_store
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/auth")

@router.get("/google/login")
async def login(request: Request,redirect_uri: str):

    request.session["extension_redirect_uri"] = redirect_uri

    callback_url = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
        request,
        callback_url,
    )

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):

    token = await oauth.google.authorize_access_token(request)

    google_user  = token["userinfo"]

    user = AuthService.save_google_user(
        db=db,
        google_user=google_user,
    )

    access_token = create_access_token(user.id)

    refresh_token, expires_at = create_refresh_token(user.id)

    TokenService.save_refresh_token(
        db=db,
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )

    extension_redirect = request.session.get(
        "extension_redirect_uri"
    )

    if not extension_redirect:
        raise HTTPException(
            status_code=400,
            detail="Missing extension redirect URI",
        )

    if extension_redirect == "mcp_oauth":
        request.session["user_id"] = str(user.id)
        request.session.pop("extension_redirect_uri", None)
        return RedirectResponse(url="/auth/oauth/authorize")

    return RedirectResponse(
        url=(
            f"{extension_redirect}"
            f"#access_token={access_token}"
            f"&refresh_token={refresh_token}"
        )
    )

@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):

    try:

        payload = verify_token(
            body.refresh_token
        )

    except Exception as e:

        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    db_token = TokenService.get_refresh_token(
        db,
        body.refresh_token,
    )

    if db_token is None:

        raise HTTPException(
            status_code=401,
            detail="Refresh token not found",
        )

    user = (
        db.query(User)
        .filter(User.id == db_token.user_id)
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    TokenService.revoke_refresh_token(
        db,
        body.refresh_token,
    )

    access_token = create_access_token(
        user.id,
    )

    refresh_token, expires_at = create_refresh_token(
        user.id,
    )

    TokenService.save_refresh_token(
        db,
        user.id,
        refresh_token,
        expires_at,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):

    try:
        verify_token(body.refresh_token)

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    revoked = TokenService.revoke_refresh_token(
        db,
        body.refresh_token,
    )

    if not revoked:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    return {
        "message": "Logged out successfully"
    }

# New APIRouter for metadata routes (unprefixed)
metadata_router = APIRouter()

def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method == "plain":
        return code_verifier == code_challenge
    elif method == "S256":
        sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        encoded = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
        return encoded == code_challenge
    return False

@router.get("/oauth/authorize")
async def oauth_authorize(
    request: Request,
    response_type: str = Query(None),
    client_id: str = Query(None),
    redirect_uri: str = Query(None),
    scope: str = Query(None),
    state: str = Query(None),
    code_challenge: str = Query(None),
    code_challenge_method: str = Query("plain"),
):
    oauth_params = request.session.get("oauth_params")
    
    if response_type and client_id and redirect_uri:
        # Validate client redirect_uri if client is registered in the store
        client = client_store.get(client_id)
        if client and redirect_uri not in client["redirect_uris"]:
            raise HTTPException(status_code=400, detail="Invalid redirect_uri for this client.")
            
        oauth_params = {
            "response_type": response_type,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }
        request.session["oauth_params"] = oauth_params
        
    if not oauth_params:
        raise HTTPException(status_code=400, detail="Missing authorization parameters.")
        
    user_id = request.session.get("user_id")
    user_exists = False
    if user_id:
        from uuid import UUID
        from database.session import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if user:
                user_exists = True
        except Exception:
            pass
        finally:
            db.close()

    if not user_id or not user_exists:
        request.session.pop("user_id", None)
        return RedirectResponse(
            url="/auth/google/login?redirect_uri=mcp_oauth"
        )
        
    code = secrets.token_urlsafe(32)
    oauth_store[code] = {
        "user_id": user_id,
        "client_id": oauth_params["client_id"],
        "redirect_uri": oauth_params["redirect_uri"],
        "code_challenge": oauth_params["code_challenge"],
        "code_challenge_method": oauth_params["code_challenge_method"],
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    
    request.session.pop("oauth_params", None)
    
    redirect_url = f"{oauth_params['redirect_uri']}?code={code}"
    if oauth_params.get("state"):
        redirect_url += f"&state={oauth_params['state']}"
        
    return RedirectResponse(url=redirect_url)

@router.post("/oauth/token")
async def oauth_token(
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    code_verifier: str = Form(None),
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type. Only 'authorization_code' is supported.")
        
    code_data = oauth_store.get(code)
    if not code_data:
        raise HTTPException(status_code=400, detail="Invalid or expired authorization code.")
        
    if code_data["expires_at"] < datetime.now(timezone.utc):
        oauth_store.pop(code, None)
        raise HTTPException(status_code=400, detail="Authorization code has expired.")
        
    if code_data["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="client_id mismatch.")
        
    if code_data["redirect_uri"] != redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri mismatch.")
        
    challenge = code_data["code_challenge"]
    method = code_data["code_challenge_method"] or "plain"
    
    if challenge:
        if not code_verifier:
            raise HTTPException(status_code=400, detail="code_verifier is required for PKCE.")
        if not verify_pkce(code_verifier, challenge, method):
            raise HTTPException(status_code=400, detail="PKCE verification failed.")
            
    oauth_store.pop(code, None)
    
    from uuid import UUID
    from config import settings
    from database.session import SessionLocal
    
    user_uuid = UUID(code_data["user_id"])
    
    access_token = create_access_token(user_uuid)
    refresh_token, expires_at = create_refresh_token(user_uuid)
    
    db = SessionLocal()
    try:
        TokenService.save_refresh_token(
            db=db,
            user_id=user_uuid,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
    finally:
        db.close()
        
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
    }

@metadata_router.get("/.well-known/oauth-authorization-server")
@metadata_router.get("/auth/oauth/.well-known/oauth-authorization-server")
@metadata_router.get("/.well-known/openid-configuration")
@metadata_router.get("/auth/oauth/.well-known/openid-configuration")
async def oauth_metadata(request: Request):
    base_url = str(request.base_url).rstrip('/')
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/auth/oauth/authorize",
        "token_endpoint": f"{base_url}/auth/oauth/token",
        "registration_endpoint": f"{base_url}/auth/oauth/register",
        "token_endpoint_auth_methods_supported": ["none"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }

@router.post("/oauth/register")
async def oauth_register(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    client_name = data.get("client_name", "Unknown MCP Client")
    redirect_uris = data.get("redirect_uris", [])
    
    if not redirect_uris:
        raise HTTPException(status_code=400, detail="redirect_uris is required")
        
    import time
    client_id = f"mcp-client-{secrets.token_hex(8)}"
    
    # Cache client details
    client_store[client_id] = {
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"]
    }
    
    return {
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "client_id_issued_at": int(time.time())
    }