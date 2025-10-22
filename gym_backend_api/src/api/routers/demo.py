from datetime import datetime, timedelta, date
import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.session import get_db
from src.db.models import (
    User, UserRole,
    MembershipPlan, Membership, MembershipStatus,
    Class, ClassSession,
    Trainer, TrainerAvailability,
    Booking, BookingStatus,
    Payment, PaymentStatus,
)
from src.core.security import get_current_user

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])

# PUBLIC_INTERFACE
class SeedResponse(BaseModel):
    """Summary of seeded entities counts."""
    users: int = Field(..., description="Users created or ensured")
    trainers: int = Field(..., description="Trainer records")
    classes: int = Field(..., description="Class types")
    sessions: int = Field(..., description="Class sessions")
    plans: int = Field(..., description="Membership plans")
    memberships: int = Field(..., description="Memberships created")
    bookings: int = Field(..., description="Class bookings created")

def _ensure_user(db: Session, email: str, role: UserRole) -> User:
    u = db.query(User).filter(User.email == email).first()
    if u:
        if u.role != role:
            u.role = role
            db.add(u)
            db.commit()
            db.refresh(u)
        return u
    from src.core.security import get_password_hash
    u = User(email=email, password_hash=get_password_hash("demo-password"), role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def _wipe_demo_data(db: Session) -> None:
    # Order is important due to FKs
    db.query(Booking).delete()
    db.query(Membership).delete()
    db.query(ClassSession).delete()
    db.query(Class).delete()
    db.query(TrainerAvailability).delete()
    db.query(Trainer).delete()
    db.query(MembershipPlan).delete()
    db.query(Payment).delete()
    db.commit()

def _seed_plans(db: Session) -> list[MembershipPlan]:
    plans = [
        ("Basic", 2999, "monthly"),
        ("Plus", 4999, "monthly"),
        ("Pro Annual", 39999, "yearly"),
    ]
    created: list[MembershipPlan] = []
    for name, price, interval in plans:
        existing = db.query(MembershipPlan).filter(MembershipPlan.name == name).first()
        if existing:
            existing.price_cents = price
            existing.interval = interval
            existing.active = True
            db.add(existing)
            created.append(existing)
        else:
            p = MembershipPlan(name=name, price_cents=price, interval=interval, active=True)
            db.add(p)
            created.append(p)
    db.commit()
    for p in created:
        db.refresh(p)
    return created

def _seed_trainers(db: Session) -> list[Trainer]:
    names = ["Alex Strong", "Jamie Flex", "Taylor Swiftlift"]
    out: list[Trainer] = []
    for n in names:
        t = db.query(Trainer).filter(Trainer.name == n).first()
        if not t:
            t = Trainer(name=n, bio="Certified trainer with 5+ years experience.")
            db.add(t)
            db.commit()
            db.refresh(t)
        out.append(t)
        # Ensure availability blocks for next 5 days
        today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        for d in range(0, 5):
            start = today + timedelta(days=d)
            end = start + timedelta(hours=2)
            exists = (
                db.query(TrainerAvailability)
                .filter(
                    TrainerAvailability.trainer_id == t.id,
                    TrainerAvailability.start_time == start,
                    TrainerAvailability.end_time == end,
                )
                .first()
            )
            if not exists:
                db.add(TrainerAvailability(trainer_id=t.id, start_time=start, end_time=end))
        db.commit()
    return out

def _seed_classes_and_sessions(db: Session) -> tuple[list[Class], list[ClassSession]]:
    class_defs = [
        ("Yoga Flow", "Relaxing yoga session", 20),
        ("HIIT Blast", "High intensity interval training", 15),
        ("Spin Class", "Cardio cycling", 18),
    ]
    classes: list[Class] = []
    for title, desc, cap in class_defs:
        c = db.query(Class).filter(Class.title == title).first()
        if not c:
            c = Class(title=title, description=desc, capacity=cap)
            db.add(c)
            db.commit()
            db.refresh(c)
        else:
            c.description = desc
            c.capacity = cap
            db.add(c)
            db.commit()
        classes.append(c)

    sessions: list[ClassSession] = []
    base = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
    for c in classes:
        # Create 3 upcoming sessions each
        for i in range(3):
            start = base + timedelta(days=i, hours=random.choice([0, 2, 4]))
            end = start + timedelta(hours=1)
            exists = (
                db.query(ClassSession)
                .filter(ClassSession.class_id == c.id, ClassSession.start_time == start)
                .first()
            )
            if not exists:
                s = ClassSession(class_id=c.id, start_time=start, end_time=end, capacity=c.capacity, spots_remaining=c.capacity)
                db.add(s)
                db.commit()
                db.refresh(s)
                sessions.append(s)
            else:
                sessions.append(exists)
    return classes, sessions

def _seed_memberships(db: Session, user: User, plan: MembershipPlan) -> Membership:
    # End previous
    prev = db.query(Membership).filter(Membership.user_id == user.id, Membership.status == MembershipStatus.ACTIVE).first()
    if prev:
        prev.status = MembershipStatus.CANCELED
        prev.end_date = date.today()
        db.add(prev)
        db.commit()
    mem = Membership(user_id=user.id, plan_id=plan.id, status=MembershipStatus.ACTIVE, start_date=date.today(), end_date=date.today() + timedelta(days=30))
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem

def _seed_bookings(db: Session, user: User, sessions: list[ClassSession]) -> int:
    count = 0
    for s in sessions[:2]:
        exists = db.query(Booking).filter(Booking.user_id == user.id, Booking.class_session_id == s.id).first()
        if not exists and s.spots_remaining > 0:
            b = Booking(user_id=user.id, class_session_id=s.id, status=BookingStatus.BOOKED)
            s.spots_remaining -= 1
            db.add(s)
            db.add(b)
            count += 1
    db.commit()
    return count

@router.post(
    "/seed",
    summary="Seed demo data",
    description="Populate demo data (plans, trainers, classes, sessions, a demo user and membership). Requires DEMO_MODE enabled.",
    response_model=SeedResponse,
)
def seed_demo(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo mode is disabled")

    # Create/ensure demo users (admin/trainer/member) for easy switching if local auth used
    u_admin = _ensure_user(db, "admin.demo@example.com", UserRole.ADMIN)
    u_trainer = _ensure_user(db, "trainer.demo@example.com", UserRole.TRAINER)
    u_member = _ensure_user(db, "member.demo@example.com", UserRole.MEMBER)

    plans = _seed_plans(db)
    trainers = _seed_trainers(db)
    classes, sessions = _seed_classes_and_sessions(db)

    # Give the current user or demo member a membership and a few bookings
    target = current_user or u_member
    mem = _seed_memberships(db, target, plans[0])
    bcount = _seed_bookings(db, target, sessions)

    return SeedResponse(
        users=3,
        trainers=len(trainers),
        classes=len(classes),
        sessions=len(sessions),
        plans=len(plans),
        memberships=1 if mem else 0,
        bookings=bcount,
    )

@router.post(
    "/reset",
    summary="Reset demo data",
    description="Clear demo-related tables and reseed a fresh set of demo data.",
    response_model=SeedResponse,
)
def reset_demo(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo mode is disabled")
    _wipe_demo_data(db)
    return seed_demo(db=db, current_user=current_user)

# ---- Mock payments for demo ----

# PUBLIC_INTERFACE
class MockCheckoutRequest(BaseModel):
    """Request to start a mock checkout for demo."""
    amount_cents: int = Field(..., description="Amount in cents")
    reference_type: str = Field(..., description="membership | class_booking | trainer_booking")
    reference_id: int = Field(..., description="Reference id")

# PUBLIC_INTERFACE
class MockCheckoutResponse(BaseModel):
    """Response containing a simulated checkout session id."""
    session_id: str = Field(..., description="Simulated session id")

# PUBLIC_INTERFACE
class MockStatusResponse(BaseModel):
    """Result of a mock payment indicating success or failure."""
    status: str = Field(..., description="succeeded | failed")
    payment_id: Optional[int] = Field(None, description="Payment record id, if created")

@router.post(
    "/payments/checkout",
    summary="Mock checkout (demo)",
    description="Create a simulated checkout session and a Payment row in pending status.",
    response_model=MockCheckoutResponse,
)
def demo_payments_checkout(payload: MockCheckoutRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo mode is disabled")

    # Create a Payment row pending
    p = Payment(
        user_id=user.id,
        amount_cents=payload.amount_cents,
        currency=settings.CURRENCY,
        provider="demo",
        status=PaymentStatus.PENDING,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    session_id = f"demo_{p.id}_{random.randint(1000,9999)}"
    return MockCheckoutResponse(session_id=session_id)

@router.get(
    "/payments/status",
    summary="Mock payment status (demo)",
    description="Return a simulated payment result. Randomly marks a pending Payment as succeeded or failed.",
    response_model=MockStatusResponse,
)
def demo_payments_status(payment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo mode is disabled")

    p = db.query(Payment).get(payment_id)
    if not p or p.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if p.status == PaymentStatus.PENDING:
        p.status = PaymentStatus.SUCCEEDED if random.random() > 0.2 else PaymentStatus.FAILED
        db.add(p)
        db.commit()
        db.refresh(p)
    return MockStatusResponse(status=p.status.value, payment_id=p.id)
