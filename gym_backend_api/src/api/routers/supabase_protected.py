from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.dependencies import auth_required

router = APIRouter(prefix="/api", tags=["Auth"])


class MeResponse(BaseModel):
    """Response model for /api/me with user_id and email from Supabase JWT."""
    user_id: str = Field(..., description="Supabase user id (sub in JWT, UUID string)")
    email: str | None = Field(default=None, description="Email from JWT claims if present")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user (Supabase)",
    description="Return the current user information parsed from Supabase JWT claims.",
)
# PUBLIC_INTERFACE
def me(claims: Dict[str, Any] = Depends(auth_required)) -> MeResponse:
    """Protected endpoint returning the current user info from Supabase JWT claims (sub and email)."""
    return MeResponse(user_id=str(claims["sub"]), email=claims.get("email"))


class ProtectedResponse(BaseModel):
    """Simple response for /api/protected."""
    message: str = Field(..., description='Always "ok" on success')
    user_id: str = Field(..., description="Supabase user id (sub in JWT, UUID string)")


@router.get(
    "/protected",
    response_model=ProtectedResponse,
    summary="Protected ping (Supabase)",
    description='Simple protected endpoint requiring Authorization: Bearer <supabase-access-token> that returns {"message": "ok", "user_id"}.',
)
# PUBLIC_INTERFACE
def protected(claims: Dict[str, Any] = Depends(auth_required)) -> ProtectedResponse:
    """Protected endpoint returning a simple ok message with user id from Supabase JWT."""
    return ProtectedResponse(message="ok", user_id=str(claims["sub"]))
