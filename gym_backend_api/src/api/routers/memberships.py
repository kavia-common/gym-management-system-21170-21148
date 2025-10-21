from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import require_roles, get_current_user
from src.db.models import User, UserRole
from src.db.session import get_db
from src.schemas.membership import (
    MembershipPlanCreate,
    MembershipPlanUpdate,
    MembershipPlanOut,
    SubscribeRequest,
    MembershipOut,
)
from src.services.membership_service import (
    create_plan,
    list_plans,
    update_plan,
    delete_plan,
    subscribe_user_to_plan,
    cancel_current_membership,
    get_current_membership,
)

router = APIRouter(prefix="/memberships", tags=["Memberships"])


@router.post("/plans", response_model=MembershipPlanOut, summary="Create plan", description="Create a membership plan (admin only).")
def create_membership_plan(payload: MembershipPlanCreate, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    return create_plan(db, **payload.model_dump())


@router.get("/plans", response_model=list[MembershipPlanOut], summary="List plans", description="List all membership plans.")
def list_membership_plans(db: Session = Depends(get_db)):
    return list_plans(db)


@router.patch("/plans/{plan_id}", response_model=MembershipPlanOut, summary="Update plan", description="Update a membership plan (admin only).")
def update_membership_plan(plan_id: int, payload: MembershipPlanUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    try:
        return update_plan(db, plan_id, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/plans/{plan_id}", summary="Delete plan", description="Delete a membership plan (admin only).")
def delete_membership_plan(plan_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles([UserRole.ADMIN]))):
    try:
        delete_plan(db, plan_id)
        return {"detail": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/subscribe", response_model=MembershipOut, summary="Subscribe", description="Subscribe the current user to a plan (may trigger payment).")
def subscribe(payload: SubscribeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return subscribe_user_to_plan(db, user.id, payload.plan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/cancel", response_model=MembershipOut, summary="Cancel membership", description="Cancel the current user's active membership.")
def cancel(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return cancel_current_membership(db, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/current", response_model=MembershipOut | None, summary="Current membership", description="Get current user's membership.")
def current_membership(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_current_membership(db, user.id)
