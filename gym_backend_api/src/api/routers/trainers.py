from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import get_current_user, require_roles
from src.db.models import User, UserRole
from src.db.session import get_db
from src.schemas.trainer import TrainerCreate, TrainerUpdate, TrainerOut, TrainerAvailabilityCreate, TrainerAvailabilityOut
from src.services.trainer_service import create_trainer, update_trainer, delete_trainer, list_trainers, add_availability, list_availability

router = APIRouter(prefix="/trainers", tags=["Trainers"])


@router.post("", response_model=TrainerOut, summary="Create trainer", description="Create trainer (admin only).")
def create_trainer_endpoint(payload: TrainerCreate, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    return create_trainer(db, **payload.model_dump())


@router.get("", response_model=list[TrainerOut], summary="List trainers", description="List trainers.")
def list_trainers_endpoint(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_trainers(db)


@router.patch("/{trainer_id}", response_model=TrainerOut, summary="Update trainer", description="Update trainer (admin only).")
def update_trainer_endpoint(trainer_id: int, payload: TrainerUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    try:
        return update_trainer(db, trainer_id, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{trainer_id}", summary="Delete trainer", description="Delete trainer (admin only).")
def delete_trainer_endpoint(trainer_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    try:
        delete_trainer(db, trainer_id)
        return {"detail": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/availability", response_model=TrainerAvailabilityOut, summary="Add availability", description="Add availability slot for a trainer (admin or staff).")
def add_availability_endpoint(payload: TrainerAvailabilityCreate, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN, UserRole.TRAINER]))):
    try:
        return add_availability(db, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{trainer_id}/availability", response_model=list[TrainerAvailabilityOut], summary="List availability", description="List availability for a trainer.")
def list_availability_endpoint(trainer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_availability(db, trainer_id)
