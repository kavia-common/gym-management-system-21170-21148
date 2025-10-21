from sqlalchemy.orm import Session

from src.db.models import Booking, BookingStatus, ClassSession


# PUBLIC_INTERFACE
def create_class_booking(db: Session, user_id: int, class_session_id: int) -> Booking:
    """Create a booking for a class session if there is availability and not already booked."""
    session = db.query(ClassSession).get(class_session_id)
    if not session:
        raise ValueError("Class session not found")
    if session.spots_remaining <= 0:
        raise ValueError("No spots remaining")

    existing = (
        db.query(Booking)
        .filter(Booking.user_id == user_id, Booking.class_session_id == class_session_id)
        .first()
    )
    if existing:
        raise ValueError("Already booked")

    booking = Booking(user_id=user_id, class_session_id=class_session_id, status=BookingStatus.BOOKED)
    session.spots_remaining -= 1

    db.add(booking)
    db.add(session)
    db.commit()
    db.refresh(booking)
    return booking


# PUBLIC_INTERFACE
def cancel_class_booking(db: Session, user_id: int, booking_id: int, is_admin: bool = False) -> Booking:
    """Cancel class booking; ensure ownership or admin override and update spots."""
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise ValueError("Booking not found")
    if not is_admin and booking.user_id != user_id:
        raise PermissionError("Not allowed")
    if booking.status != BookingStatus.BOOKED:
        return booking
    session = db.query(ClassSession).get(booking.class_session_id)
    booking.status = BookingStatus.CANCELED
    if session:
        session.spots_remaining += 1
        db.add(session)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
