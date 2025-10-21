from datetime import datetime
from pydantic import BaseModel, EmailStr
from src.db.models import UserRole


# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    role: UserRole


# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """User create payload (internal)."""
    email: EmailStr
    password: str


# PUBLIC_INTERFACE
class UserRead(BaseModel):
    """User read response."""
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
