from datetime import date
from pydantic import BaseModel, Field
from src.db.models import MembershipStatus


# PUBLIC_INTERFACE
class MembershipPlanCreate(BaseModel):
    """Create a membership plan."""
    name: str = Field(..., description="Plan name")
    price_cents: int = Field(..., description="Price in cents")
    interval: str = Field(..., description="Billing interval (e.g., monthly, yearly)")
    active: bool = Field(default=True, description="Is plan active")


# PUBLIC_INTERFACE
class MembershipPlanUpdate(BaseModel):
    """Update fields for a membership plan."""
    name: str | None = Field(default=None)
    price_cents: int | None = Field(default=None)
    interval: str | None = Field(default=None)
    active: bool | None = Field(default=None)


# PUBLIC_INTERFACE
class MembershipPlanOut(BaseModel):
    """Response model for membership plan."""
    id: int
    name: str
    price_cents: int
    interval: str
    active: bool

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class MembershipOut(BaseModel):
    """Details of a user's membership."""
    id: int
    plan_id: int
    status: MembershipStatus
    start_date: date | None
    end_date: date | None

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class SubscribeRequest(BaseModel):
    """Subscribe to a plan (may initiate a payment)."""
    plan_id: int = Field(..., description="ID of the membership plan to subscribe to")
