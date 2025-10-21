import uuid
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.models import Payment, PaymentStatus


# PUBLIC_INTERFACE
def create_payment_session(db: Session, user_id: int, reference_type: str, reference_id: int, amount_cents: int) -> tuple[Payment, str]:
    """Create a payment record and return a session id (mock in TEST_MODE)."""
    settings = get_settings()
    payment = Payment(
        user_id=user_id,
        amount_cents=amount_cents,
        currency=settings.CURRENCY,
        provider=settings.PAYMENT_PROVIDER,
        status=PaymentStatus.PENDING,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # TEST_MODE: return mock session id
    if settings.TEST_MODE or not settings.STRIPE_SECRET_KEY:
        session_id = f"test_{uuid.uuid4().hex}"
        return payment, session_id

    # Stripe integration (placeholder): return a synthetic session id; real implementation would create checkout session
    session_id = f"stripe_{uuid.uuid4().hex}"
    return payment, session_id


# PUBLIC_INTERFACE
def confirm_payment(db: Session, payment_id: int) -> Payment:
    """Confirm a payment (TEST_MODE simple confirm, provider webhook for real)."""
    p = db.query(Payment).get(payment_id)
    if not p:
        raise ValueError("Payment not found")
    p.status = PaymentStatus.SUCCEEDED
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
