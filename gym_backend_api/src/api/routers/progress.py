from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth.supabase_jwt import get_current_user as get_supabase_user  # returns dict with user_id, email, role
from src.db.session import get_db
from src.schemas.progress import (
    ExerciseLogCreate,
    ExerciseLogOut,
    BodyMetricsCreate,
    BodyMetricsOut,
)
from ...services.progress_service import (
    create_exercise_log,
    list_exercise_logs,
    create_body_metrics,
    list_body_metrics,
)

router = APIRouter(
    prefix="/api/v1/progress",
    tags=["Progress"],
)


def _resolve_target_user_id(
    current_user: dict,
    target_user_id: Optional[str],
) -> str:
    """
    RBAC helper:
    - Members can only act on themselves (ignore target_user_id).
    - Trainers can read their clients; for now, allow provided target_user_id or self if none.
      Note: Integrate with trainer_service if client mapping exists; keeping permissive read for trainers for now for MVP.
    - Admins can act on any user_id.
    """
    role = current_user.get("role")
    if role == "member":
        return current_user["user_id"]
    if role in ("trainer", "admin"):
        return target_user_id or current_user["user_id"]
    # default deny
    return current_user["user_id"]


@router.post(
    "/exercise-logs",
    response_model=ExerciseLogOut,
    summary="Create exercise log",
    description="Create an exercise log for the authenticated user. Trainers/Admins can create for a target user via query param user_id.",
)
def create_exercise_log_endpoint(
    payload: ExerciseLogCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_supabase_user),
    user_id: Optional[str] = Query(
        None, description="Target user id (Supabase UUID). Trainers/Admins only."
    ),
):
    """
    Create exercise log entry.

    Security:
    - Member: creates for self.
    - Trainer/Admin: may create for another user by passing user_id.
    """
    role = current_user.get("role")
    target_user = current_user["user_id"] if role == "member" else (user_id or current_user["user_id"])
    if role == "member" and user_id and user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Members can only create their own logs.")
    log = create_exercise_log(db, target_user, payload)
    return log


@router.get(
    "/exercise-logs",
    response_model=List[ExerciseLogOut],
    summary="List exercise logs",
    description="List exercise logs for the current user. Trainers/Admins can query another user's logs with user_id.",
)
def list_exercise_logs_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_supabase_user),
    user_id: Optional[str] = Query(None, description="Target user id (Trainer/Admin)"),
    exercise_id: Optional[int] = Query(None, description="Filter by exercise id"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
):
    """
    List exercise logs.

    RBAC:
    - Members: self only.
    - Trainers/Admins: may specify user_id to read others (clients).
    """
    target_user = _resolve_target_user_id(current_user, user_id)
    if current_user.get("role") == "member" and user_id and user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Members can only view their own logs.")

    logs = list_exercise_logs(
        db=db,
        user_id=target_user,
        exercise_id=exercise_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return logs


@router.post(
    "/body-metrics",
    response_model=BodyMetricsOut,
    summary="Create body metrics",
    description="Create body metrics entry for the authenticated user. Trainers/Admins can create for a target user via query param user_id.",
)
def create_body_metrics_endpoint(
    payload: BodyMetricsCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_supabase_user),
    user_id: Optional[str] = Query(
        None, description="Target user id (Supabase UUID). Trainers/Admins only."
    ),
):
    """
    Create body metrics.

    Security:
    - Member: creates for self.
    - Trainer/Admin: may create for another user by passing user_id.
    """
    role = current_user.get("role")
    target_user = current_user["user_id"] if role == "member" else (user_id or current_user["user_id"])
    if role == "member" and user_id and user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Members can only create their own body metrics.")
    metrics = create_body_metrics(db, target_user, payload)
    return metrics


@router.get(
    "/body-metrics",
    response_model=List[BodyMetricsOut],
    summary="List body metrics",
    description="List body metrics for the current user. Trainers/Admins can query another user's metrics with user_id.",
)
def list_body_metrics_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_supabase_user),
    user_id: Optional[str] = Query(None, description="Target user id (Trainer/Admin)"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
):
    """
    List body metrics.

    RBAC:
    - Members: self only.
    - Trainers/Admins: may specify user_id to read others (clients).
    """
    target_user = _resolve_target_user_id(current_user, user_id)
    if current_user.get("role") == "member" and user_id and user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Members can only view their own body metrics.")
    metrics = list_body_metrics(
        db=db,
        user_id=target_user,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return metrics
