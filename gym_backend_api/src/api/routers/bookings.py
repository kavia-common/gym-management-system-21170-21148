from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.models import User, UserRole
from src.db.session import get_db
from src.schemas.booking import ClassBookingCreate, TrainerBookingCreate, BookingOut
from src.services.booking_service import create_class_booking, cancel_class_booking
from src.services.trainer_service import create_trainer_booking, cancel_trainer_booking

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/classes", response_model=BookingOut, summary="Book class session", description="Create booking for a class session.")
def book_class(payload: ClassBookingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return create_class_booking(db, user.id, payload.class_session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/classes/{booking_id}", response_model=BookingOut, summary="Cancel class booking", description="Cancel a class booking (owner or admin).")
def cancel_class(booking_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        is_admin = user.role in (UserRole.ADMIN, )
        return cancel_class_booking(db, user.id, booking_id, is_admin=is_admin)
    except (ValueError, PermissionError) as e:
        status_code = status.HTTP_403_FORBIDDEN if isinstance(e, PermissionError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post("/trainers", response_model=BookingOut, summary="Book trainer", description="Create a trainer booking.")
def book_trainer(payload: TrainerBookingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return create_trainer_booking(db, user.id, payload.trainer_id, payload.start_time, payload.end_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/trainers/{booking_id}", response_model=BookingOut, summary="Cancel trainer booking", description="Cancel a trainer booking (owner or admin).")
def cancel_trainer(booking_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        is_admin = user.role in (UserRole.ADMIN, )
        return cancel_trainer_booking(db, user.id, booking_id, is_admin=is_admin)
    except (ValueError, PermissionError) as e:
        status_code = status.HTTP_403_FORBIDDEN if isinstance(e, PermissionError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e)) from e
