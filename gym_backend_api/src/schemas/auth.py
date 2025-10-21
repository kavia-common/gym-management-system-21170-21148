from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from src.db.models import UserRole


# PUBLIC_INTERFACE
class SignupRequest(BaseModel):
    """Request payload for user signup."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")


# PUBLIC_INTERFACE
class LoginRequest(BaseModel):
    """Request payload for user login."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


# PUBLIC_INTERFACE
class TokenPair(BaseModel):
    """Response with access and refresh tokens."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


# PUBLIC_INTERFACE
class RefreshRequest(BaseModel):
    """Request payload to refresh tokens."""
    refresh_token: str = Field(..., description="Refresh token")


# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """Public view of a user."""
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
