from pydantic import BaseModel, Field
from src.db.models import PaymentStatus


# PUBLIC_INTERFACE
class CreatePaymentRequest(BaseModel):
    """Request to create a payment session for a reference object."""
    reference_type: str = Field(..., description="membership | class_booking | trainer_booking")
    reference_id: int = Field(..., description="ID of the referenced entity")
    amount_cents: int = Field(..., description="Amount in cents")


# PUBLIC_INTERFACE
class PaymentOut(BaseModel):
    """Payment response."""
    id: int
    status: PaymentStatus
    amount_cents: int
    currency: str
    provider: str
    reference_type: str
    reference_id: int

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class PaymentSessionResponse(BaseModel):
    """Response for creating a payment session."""
    session_id: str = Field(..., description="Mock or provider session id")
