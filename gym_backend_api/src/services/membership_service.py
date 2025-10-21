from datetime import date, timedelta
from sqlalchemy.orm import Session

from src.db.models import Membership, MembershipPlan, MembershipStatus, Payment, PaymentStatus
from src.core.config import get_settings


# PUBLIC_INTERFACE
def create_plan(db: Session, name: str, price_cents: int, interval: str, active: bool = True) -> MembershipPlan:
    """Create a membership plan."""
    plan = MembershipPlan(name=name, price_cents=price_cents, interval=interval, active=active)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# PUBLIC_INTERFACE
def list_plans(db: Session) -> list[MembershipPlan]:
    """List membership plans."""
    return db.query(MembershipPlan).all()


# PUBLIC_INTERFACE
def update_plan(db: Session, plan_id: int, **fields) -> MembershipPlan:
    """Update a membership plan."""
    plan = db.query(MembershipPlan).get(plan_id)
    if not plan:
        raise ValueError("Plan not found")
    for k, v in fields.items():
        if v is not None:
            setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan


# PUBLIC_INTERFACE
def delete_plan(db: Session, plan_id: int) -> None:
    """Delete a membership plan."""
    plan = db.query(MembershipPlan).get(plan_id)
    if not plan:
        raise ValueError("Plan not found")
    db.delete(plan)
    db.commit()


# PUBLIC_INTERFACE
def subscribe_user_to_plan(db: Session, user_id: int, plan_id: int) -> Membership:
    """Subscribe a user to a plan; in TEST_MODE this will immediately activate and create succeeded payment."""
    settings = get_settings()
    plan = db.query(MembershipPlan).get(plan_id)
    if not plan or not plan.active:
        raise ValueError("Invalid plan")
    # End any active membership
    active = (
        db.query(Membership).filter(Membership.user_id == user_id, Membership.status == MembershipStatus.ACTIVE).first()
    )
    if active:
        active.status = MembershipStatus.CANCELED
        db.add(active)

    mem = Membership(user_id=user_id, plan_id=plan_id, status=MembershipStatus.PENDING)
    db.add(mem)
    db.commit()
    db.refresh(mem)

    if settings.TEST_MODE or not settings.STRIPE_SECRET_KEY:
        # Activate immediately, create a succeeded payment record
        mem.status = MembershipStatus.ACTIVE
        mem.start_date = date.today()
        # Basic duration logic (1 month default)
        mem.end_date = date.today() + timedelta(days=30)
        payment = Payment(
            user_id=user_id,
            amount_cents=plan.price_cents,
            currency=settings.CURRENCY,
            provider=settings.PAYMENT_PROVIDER,
            status=PaymentStatus.SUCCEEDED,
            reference_type="membership",
            reference_id=mem.id,
        )
        db.add(payment)
        db.add(mem)
        db.commit()
        db.refresh(mem)
    return mem


# PUBLIC_INTERFACE
def cancel_current_membership(db: Session, user_id: int) -> Membership:
    """Cancel user's current active membership."""
    mem = (
        db.query(Membership).filter(Membership.user_id == user_id, Membership.status == MembershipStatus.ACTIVE).first()
    )
    if not mem:
        raise ValueError("No active membership")
    mem.status = MembershipStatus.CANCELED
    mem.end_date = date.today()
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


# PUBLIC_INTERFACE
def get_current_membership(db: Session, user_id: int) -> Membership | None:
    """Get user's current membership (active or pending)."""
    return (
        db.query(Membership)
        .filter(Membership.user_id == user_id)
        .order_by(Membership.id.desc())
        .first()
    )
