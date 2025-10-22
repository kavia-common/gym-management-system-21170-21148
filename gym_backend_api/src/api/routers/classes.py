from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import get_current_user, require_roles, require_roles_demo_aware
from src.db.models import User, UserRole
from src.db.session import get_db
from src.schemas.classes import ClassCreate, ClassUpdate, ClassOut, ClassSessionCreate, ClassSessionOut
from src.services.class_service import create_class, update_class, delete_class, list_classes, create_session, list_sessions

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.post("", response_model=ClassOut, summary="Create class", description="Create a new class (admin or staff).")
def create_class_endpoint(payload: ClassCreate, db: Session = Depends(get_db), _: User = Depends(require_roles_demo_aware([UserRole.ADMIN, UserRole.TRAINER]))):
    return create_class(db, **payload.model_dump())


@router.get("", response_model=list[ClassOut], summary="List classes", description="List all classes.")
def list_classes_endpoint(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_classes(db)


@router.patch("/{class_id}", response_model=ClassOut, summary="Update class", description="Update a class (admin or staff).")
def update_class_endpoint(class_id: int, payload: ClassUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles_demo_aware([UserRole.ADMIN, UserRole.TRAINER]))):
    try:
        return update_class(db, class_id, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{class_id}", summary="Delete class", description="Delete a class (admin or staff).")
def delete_class_endpoint(class_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles_demo_aware([UserRole.ADMIN, UserRole.TRAINER]))):
    try:
        delete_class(db, class_id)
        return {"detail": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/sessions", response_model=ClassSessionOut, summary="Create class session", description="Create a class session (admin or staff).")
def create_session_endpoint(payload: ClassSessionCreate, db: Session = Depends(get_db), _: User = Depends(require_roles_demo_aware([UserRole.ADMIN, UserRole.TRAINER]))):
    try:
        return create_session(db, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/sessions", response_model=list[ClassSessionOut], summary="List class sessions", description="List class sessions; optionally filter by class_id.")
def list_sessions_endpoint(class_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_sessions(db, class_id=class_id)
