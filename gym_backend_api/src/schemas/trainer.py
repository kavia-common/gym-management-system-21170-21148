from datetime import datetime
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class TrainerCreate(BaseModel):
    """Create trainer."""
    name: str = Field(..., description="Trainer name")
    bio: str | None = Field(default=None, description="Trainer bio")


# PUBLIC_INTERFACE
class TrainerUpdate(BaseModel):
    """Update trainer."""
    name: str | None = None
    bio: str | None = None


# PUBLIC_INTERFACE
class TrainerOut(BaseModel):
    """Trainer response."""
    id: int
    name: str
    bio: str | None

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class TrainerAvailabilityCreate(BaseModel):
    """Create trainer availability slot."""
    trainer_id: int
    start_time: datetime
    end_time: datetime


# PUBLIC_INTERFACE
class TrainerAvailabilityOut(BaseModel):
    """Availability response."""
    id: int
    trainer_id: int
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True
