from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.schemas.auth import SignupRequest, LoginRequest, TokenPair, RefreshRequest, UserOut
from src.services.auth_service import signup as signup_service, authenticate, issue_tokens
from src.core.security import decode_token, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserOut, summary="User signup", description="Create a new user account.")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        user = signup_service(db, email=payload.email, password=payload.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/login", response_model=TokenPair, summary="Login", description="Authenticate user and obtain tokens.")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = issue_tokens(user.id)
    return TokenPair(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])


@router.post("/refresh", response_model=TokenPair, summary="Refresh tokens", description="Refresh access and refresh tokens using a refresh token.")
def refresh(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    sub = data.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")
    return TokenPair(access_token=create_access_token(int(sub)), refresh_token=create_refresh_token(int(sub)))


@router.post("/logout", summary="Logout", description="Stateless logout acknowledgement. If token store exists, invalidate there.")
def logout():
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut, summary="Get current user", description="Return the profile of the authenticated user.")
def me(current_user: User = Depends(get_current_user)):
    return current_user
