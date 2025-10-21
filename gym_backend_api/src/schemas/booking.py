from datetime import datetime
from pydantic import BaseModel, Field
from src.db.models import BookingStatus


# PUBLIC_INTERFACE
class ClassBookingCreate(BaseModel):
    """Create class booking."""
    class_session_id: int = Field(..., description="Class session ID")


# PUBLIC_INTERFACE
class TrainerBookingCreate(BaseModel):
    """Create trainer booking."""
    trainer_id: int
    start_time: datetime
    end_time: datetime


# PUBLIC_INTERFACE
class BookingOut(BaseModel):
    """Booking response."""
    id: int
    status: BookingStatus

    class Config:
        from_attributes = True
