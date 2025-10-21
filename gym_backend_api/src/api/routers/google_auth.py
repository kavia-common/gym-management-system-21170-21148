from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.models import User, UserRole
from src.db.session import get_db
from src.services.auth_service import issue_tokens
from src.core.security import get_password_hash

# Google token verification
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import httpx


router = APIRouter(prefix="/auth/google", tags=["Auth"])


class OneTapRequest(BaseModel):
    """Payload from Google Identity Services One Tap."""
    credential: str = Field(..., description="Google ID token credential returned by GIS One Tap")


def _verify_google_id_token(id_token: str, client_id: str) -> dict:
    """
    Verify a Google ID token using google-auth.
    Ensures audience matches client_id, issuer is Google, and email is verified.
    """
    try:
        request = google_requests.Request()
        idinfo = google_id_token.verify_oauth2_token(id_token, request, audience=client_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token") from exc

    # Validate issuer
    iss = idinfo.get("iss")
    if iss not in ("https://accounts.google.com", "accounts.google.com"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    # Validate audience
    aud = idinfo.get("aud")
    if aud != client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

    # Validate email
    if not idinfo.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified by Google")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google token missing email")

    return idinfo


def _find_or_create_user(db: Session, email: str) -> User:
    """
    Find user by email or create a new member user with provider 'google'.
    Since our model requires password_hash, we generate a random hash placeholder.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    # Create a random password hash (not used for Google accounts)
    random_placeholder = get_password_hash(f"google-{email}")
    user = User(email=email, password_hash=random_placeholder, role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/login",
    summary="Google OAuth login",
    description="Build and return the Google OAuth authorization URL for user redirection.",
)
def google_login(state: Optional[str] = Query(default=None, description="Opaque state to be returned by Google")):
    """
    PUBLIC_INTERFACE
    Build the Google OAuth authorization URL using configured GOOGLE_CLIENT_ID and redirect URI.
    """
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_OAUTH_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth not configured")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    if state:
        params["state"] = state

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"authorization_url": auth_url}


@router.get(
    "/callback",
    summary="Google OAuth callback",
    description="Exchange the authorization code for tokens, verify the ID token, find/create user, and issue app JWTs.",
)
def google_callback(code: str = Query(..., description="Authorization code returned by Google"), db: Session = Depends(get_db)):
    """
    PUBLIC_INTERFACE
    Handle Google OAuth server-side callback:
    - Exchange code for tokens at Google's token endpoint.
    - Verify ID token.
    - Find or create a local user by email.
    - Issue application access/refresh tokens.
    """
    settings = get_settings()
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_OAUTH_REDIRECT_URI):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth not configured")

    token_endpoint = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(token_endpoint, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            resp.raise_for_status()
            token_data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code for tokens") from exc

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google did not return an ID token")

    idinfo = _verify_google_id_token(id_token, settings.GOOGLE_CLIENT_ID)
    email = idinfo.get("email")

    user = _find_or_create_user(db, email=email)
    tokens = issue_tokens(user.id)
    return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"], "token_type": "bearer"}


@router.post(
    "/one-tap",
    summary="Google One Tap login",
    description="Accept a Google ID token from the frontend (GIS) to authenticate the user and issue app tokens.",
)
def google_one_tap(payload: OneTapRequest, db: Session = Depends(get_db)):
    """
    PUBLIC_INTERFACE
    Verify the Google One Tap ID token credential and issue application tokens.
    """
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth not configured")

    idinfo = _verify_google_id_token(payload.credential, settings.GOOGLE_CLIENT_ID)
    email = idinfo.get("email")

    user = _find_or_create_user(db, email=email)
    tokens = issue_tokens(user.id)
    return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"], "token_type": "bearer"}
