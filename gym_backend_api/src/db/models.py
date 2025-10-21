from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .session import Base
# Import workout models module to ensure metadata includes these tables when Base.metadata.create_all runs.
# This is a safe, optional import for side-effect registration; individual classes are defined in workout_models.py
try:
    from . import workout_models  # noqa: F401
except Exception:
    # Avoid hard failure if module not yet available during certain tooling phases
    pass


class UserRole(str, Enum):
    MEMBER = "member"
    TRAINER = "trainer"
    ADMIN = "admin"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PENDING = "pending"


class BookingStatus(str, Enum):
    BOOKED = "booked"
    CANCELED = "canceled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


# PUBLIC_INTERFACE
class User(Base):
    """User accounts: gym members, trainers, and admins.

    Persisted mapping between local user and Supabase identity:
    - supabase_user_id: UUID (string) from Supabase JWT 'sub', unique when present
    - email: used for legacy/local auth and for mapping when Supabase provides email
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("supabase_user_id", name="uq_users_supabase_user_id"),
        Index("ix_users_supabase_user_id", "supabase_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Supabase subject (UUID as string). Nullable to maintain compatibility with existing local users.
    supabase_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.MEMBER)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    trainer_bookings: Mapped[list["TrainerBooking"]] = relationship("TrainerBooking", back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class MembershipPlan(Base):
    """Subscription plans available to users."""

    __tablename__ = "membership_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # store in cents to avoid FP issues
    interval: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., monthly, yearly
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="plan")


# PUBLIC_INTERFACE
class Membership(Base):
    """User's subscription instance for a given plan."""

    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("membership_plans.id"), nullable=False, index=True)
    status: Mapped[MembershipStatus] = mapped_column(SAEnum(MembershipStatus), nullable=False, default=MembershipStatus.PENDING)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    plan: Mapped["MembershipPlan"] = relationship("MembershipPlan", back_populates="memberships")


# PUBLIC_INTERFACE
class Class(Base):
    """A type of class (e.g., Yoga, HIIT)."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    sessions: Mapped[list["ClassSession"]] = relationship("ClassSession", back_populates="class_", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class ClassSession(Base):
    """A particular scheduled instance of a class."""

    __tablename__ = "class_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    spots_remaining: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("spots_remaining >= 0", name="chk_spots_remaining_non_negative"),
        CheckConstraint("capacity >= 0", name="chk_capacity_non_negative"),
    )

    class_: Mapped["Class"] = relationship("Class", back_populates="sessions")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="class_session", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class Trainer(Base):
    """Trainer profile information."""

    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=True)

    availability: Mapped[list["TrainerAvailability"]] = relationship("TrainerAvailability", back_populates="trainer", cascade="all, delete-orphan")
    bookings: Mapped[list["TrainerBooking"]] = relationship("TrainerBooking", back_populates="trainer", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class TrainerAvailability(Base):
    """Time slots when a trainer is available."""

    __tablename__ = "trainer_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    trainer: Mapped["Trainer"] = relationship("Trainer", back_populates="availability")


# PUBLIC_INTERFACE
class Booking(Base):
    """Member booking for a class session."""

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "class_session_id", name="uq_user_class_session"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_session_id: Mapped[int] = mapped_column(ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), nullable=False, default=BookingStatus.BOOKED)

    user: Mapped["User"] = relationship("User", back_populates="bookings")
    class_session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="bookings")


# PUBLIC_INTERFACE
class TrainerBooking(Base):
    """Member booking for a trainer one-on-one session."""

    __tablename__ = "trainer_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), nullable=False, default=BookingStatus.BOOKED)

    user: Mapped["User"] = relationship("User", back_populates="trainer_bookings")
    trainer: Mapped["Trainer"] = relationship("Trainer", back_populates="bookings")


# PUBLIC_INTERFACE
class Payment(Base):
    """Payments associated with various references, e.g., membership, class booking, trainer booking."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="usd")
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="stripe")
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "membership", "class_booking", "trainer_booking"
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False)  # id of the referenced entity
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="payments")
