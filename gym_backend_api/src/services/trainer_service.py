from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.db.models import Trainer, TrainerAvailability, TrainerBooking, BookingStatus


# PUBLIC_INTERFACE
def create_trainer(db: Session, name: str, bio: str | None) -> Trainer:
    """Create trainer."""
    t = Trainer(name=name, bio=bio)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# PUBLIC_INTERFACE
def update_trainer(db: Session, trainer_id: int, **fields) -> Trainer:
    """Update trainer."""
    t = db.query(Trainer).get(trainer_id)
    if not t:
        raise ValueError("Trainer not found")
    for k, v in fields.items():
        if v is not None:
            setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


# PUBLIC_INTERFACE
def delete_trainer(db: Session, trainer_id: int) -> None:
    """Delete trainer."""
    t = db.query(Trainer).get(trainer_id)
    if not t:
        raise ValueError("Trainer not found")
    db.delete(t)
    db.commit()


# PUBLIC_INTERFACE
def list_trainers(db: Session) -> list[Trainer]:
    """List trainers."""
    return db.query(Trainer).all()


# PUBLIC_INTERFACE
def add_availability(db: Session, trainer_id: int, start_time: datetime, end_time: datetime) -> TrainerAvailability:
    """Add availability slot for trainer."""
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    t = db.query(Trainer).get(trainer_id)
    if not t:
        raise ValueError("Trainer not found")
    slot = TrainerAvailability(trainer_id=trainer_id, start_time=start_time, end_time=end_time)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


# PUBLIC_INTERFACE
def list_availability(db: Session, trainer_id: int) -> list[TrainerAvailability]:
    """List availability slots for a trainer."""
    return (
        db.query(TrainerAvailability)
        .filter(TrainerAvailability.trainer_id == trainer_id)
        .order_by(TrainerAvailability.start_time.asc())
        .all()
    )


# PUBLIC_INTERFACE
def create_trainer_booking(db: Session, user_id: int, trainer_id: int, start_time: datetime, end_time: datetime) -> TrainerBooking:
    """Create trainer booking ensuring availability and no conflicts."""
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")

    # Ensure within an availability window
    avail = (
        db.query(TrainerAvailability)
        .filter(
            TrainerAvailability.trainer_id == trainer_id,
            TrainerAvailability.start_time <= start_time,
            TrainerAvailability.end_time >= end_time,
        )
        .first()
    )
    if not avail:
        raise ValueError("Requested time outside trainer availability")

    # Check for overlap with existing bookings
    overlap = (
        db.query(TrainerBooking)
        .filter(
            TrainerBooking.trainer_id == trainer_id,
            TrainerBooking.status == BookingStatus.BOOKED,
            or_(
                and_(TrainerBooking.start_time < end_time, TrainerBooking.end_time > start_time),
            ),
        )
        .first()
    )
    if overlap:
        raise ValueError("Time slot already booked")

    b = TrainerBooking(user_id=user_id, trainer_id=trainer_id, start_time=start_time, end_time=end_time, status=BookingStatus.BOOKED)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# PUBLIC_INTERFACE
def cancel_trainer_booking(db: Session, user_id: int, booking_id: int, is_admin: bool = False) -> TrainerBooking:
    """Cancel trainer booking; only owner or admin can cancel."""
    b = db.query(TrainerBooking).get(booking_id)
    if not b:
        raise ValueError("Booking not found")
    if not is_admin and b.user_id != user_id:
        raise PermissionError("Not allowed")
    b.status = BookingStatus.CANCELED
    db.add(b)
    db.commit()
    db.refresh(b)
    return b
