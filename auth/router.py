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

from fastapi.responses import RedirectResponse

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