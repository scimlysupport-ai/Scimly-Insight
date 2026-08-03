"""
Phase 12 — Authentication.

POST /api/auth/register          -> email/password sign up
POST /api/auth/login             -> email/password log in
GET  /api/auth/me                -> the logged-in user's profile
GET  /api/auth/google/login      -> redirect to Google's consent screen
GET  /api/auth/google/callback   -> Google redirects back here
GET  /api/auth/github/login      -> redirect to GitHub's consent screen
GET  /api/auth/github/callback   -> GitHub redirects back here

The two OAuth callbacks both finish the same way: create/find the User,
issue a JWT, and redirect the browser to
"<FRONTEND_URL>/auth/callback?token=<jwt>" — a plain page in the
frontend whose only job is to read that token, store it, and drop the
user onto /account. Doing it as a redirect (not JSON) is what makes the
"click a button, land back on the site logged in" popup-free flow work.
"""
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import (
    authenticate_user,
    claim_device_data,
    create_access_token,
    get_or_create_oauth_user,
    register_user,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
def register(
    payload: RegisterRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = register_user(db, payload.email, payload.password, payload.name)
    claim_device_data(db, user, x_device_id)

    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    claim_device_data(db, user, x_device_id)

    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/auth/google/login")
def google_login(device_id: str | None = Query(default=None)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google login isn't configured on this server yet.")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": device_id or "",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/google/callback")
def google_callback(code: str, state: str | None = None, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google login isn't configured on this server yet.")

    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google/callback",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Google rejected the login request.")
        access_token = token_resp.json().get("access_token")

        userinfo_resp = client.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not fetch Google profile.")
        info = userinfo_resp.json()

    user = get_or_create_oauth_user(
        db,
        provider="google",
        provider_user_id=info["sub"],
        email=info.get("email"),
        name=info.get("name"),
        avatar_url=info.get("picture"),
    )
    claim_device_data(db, user, state)

    jwt_token = create_access_token(user.id)
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{urlencode({'token': jwt_token})}")


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@router.get("/auth/github/login")
def github_login(device_id: str | None = Query(default=None)):
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub login isn't configured on this server yet.")

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/github/callback",
        "scope": "read:user user:email",
        "state": device_id or "",
    }
    return RedirectResponse(f"{GITHUB_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/github/callback")
def github_callback(code: str, state: str | None = None, db: Session = Depends(get_db)):
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub login isn't configured on this server yet.")

    with httpx.Client(timeout=10.0, headers={"Accept": "application/json"}) as client:
        token_resp = client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.BACKEND_URL}/api/auth/github/callback",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub rejected the login request.")
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="GitHub rejected the login request.")

        auth_header = {"Authorization": f"Bearer {access_token}"}
        user_resp = client.get(GITHUB_USER_URL, headers=auth_header)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not fetch GitHub profile.")
        info = user_resp.json()

        email = info.get("email")
        if not email:
            # Private-email GitHub accounts don't include it on /user —
            # fall back to the emails endpoint and take the primary one.
            emails_resp = client.get(GITHUB_EMAILS_URL, headers=auth_header)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), None)
                email = (primary or (emails[0] if emails else {})).get("email")

    user = get_or_create_oauth_user(
        db,
        provider="github",
        provider_user_id=str(info["id"]),
        email=email,
        name=info.get("name") or info.get("login"),
        avatar_url=info.get("avatar_url"),
    )
    claim_device_data(db, user, state)

    jwt_token = create_access_token(user.id)
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{urlencode({'token': jwt_token})}")
