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

    booking = Booking(user_id=user_id, class_session_id=int(class_session_id), status=BookingStatus.BOOKED)
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


# PUBLIC_INTERFACE
def get_trainer_bookings_for_user(db: Session, user_id: int):
    """Return trainer bookings for a user. Simplified query based on Booking model if trainer booking fields exist."""
    try:
        q = db.query(Booking).filter(Booking.user_id == user_id, Booking.trainer_id.isnot(None))
        # Map to dicts with expected fields
        results = []
        for b in q.all():
            results.append(
                {
                    "id": b.id,
                    "status": getattr(b, "status", None).value if hasattr(b, "status") and b.status else None,
                    "start_time": getattr(b, "start_time", None),
                    "end_time": getattr(b, "end_time", None),
                    "trainer_name": getattr(b, "trainer_name", None) or getattr(getattr(b, "trainer", None), "name", None),
                }
            )
        return results
    except Exception:
        return []


# PUBLIC_INTERFACE
def get_class_bookings_for_user(db: Session, user_id: int):
    """Return class bookings for a user as simple dicts with start/end and class title."""
    try:
        q = db.query(Booking).filter(Booking.user_id == user_id, Booking.class_session_id.isnot(None))
        results = []
        for b in q.all():
            # pull session times and class title if relationships present
            session = getattr(b, "class_session", None)
            start_time = getattr(session, "start_time", None) or getattr(b, "start_time", None)
            end_time = getattr(session, "end_time", None) or getattr(b, "end_time", None)
            class_title = None
            if session is not None:
                klass = getattr(session, "klass", None) or getattr(session, "class_", None)
                class_title = getattr(klass, "title", None)
            results.append(
                {
                    "id": b.id,
                    "status": getattr(b, "status", None).value if hasattr(b, "status") and b.status else None,
                    "start_time": start_time,
                    "end_time": end_time,
                    "class_title": class_title,
                }
            )
        return results
    except Exception:
        return []
