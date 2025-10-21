from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.security import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.schemas.payment import CreatePaymentRequest, PaymentOut, PaymentSessionResponse
from src.services.payment_service import create_payment_session, confirm_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/session", response_model=PaymentSessionResponse, summary="Create payment session", description="Create a payment session; returns a mock session id in TEST_MODE.")
def create_payment_session_endpoint(payload: CreatePaymentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        payment, session_id = create_payment_session(
            db, user.id, payload.reference_type, payload.reference_id, payload.amount_cents
        )
        return PaymentSessionResponse(session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/confirm/{payment_id}", response_model=PaymentOut, summary="Confirm payment (TEST_MODE)", description="Confirm a payment in TEST_MODE (or as a simplified confirm).")
def confirm_payment_endpoint(payment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        p = confirm_payment(db, payment_id)
        return p
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/webhook/stripe", summary="Stripe webhook (stub)", description="Stripe webhook endpoint to confirm payments when not in TEST_MODE.")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.TEST_MODE or not settings.STRIPE_WEBHOOK_SECRET:
        return {"detail": "Webhook ignored in TEST_MODE"}
    # Placeholder: implement Stripe signature verification and event handling here.
    await request.body()  # consume body to avoid unused-await warnings
    # TODO: verify payload and update payment status accordingly
    return {"received": True}
