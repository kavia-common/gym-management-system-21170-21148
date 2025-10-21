from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.progress_models import ExerciseLog, BodyMetrics


# PUBLIC_INTERFACE
def create_exercise_log(db: Session, user_id: str, payload) -> ExerciseLog:
    """Create an exercise log for a user."""
    log = ExerciseLog(
        user_id=user_id,
        date=payload.date,
        exercise_id=payload.exercise_id,
        sets=payload.sets,
        reps=payload.reps,
        weight=payload.weight,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# PUBLIC_INTERFACE
def list_exercise_logs(
    db: Session,
    user_id: str,
    exercise_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ExerciseLog]:
    """List exercise logs for a user with optional filters and pagination."""
    query = db.query(ExerciseLog).filter(ExerciseLog.user_id == user_id)
    if exercise_id is not None:
        query = query.filter(ExerciseLog.exercise_id == exercise_id)
    if start_date is not None:
        query = query.filter(ExerciseLog.date >= start_date)
    if end_date is not None:
        query = query.filter(ExerciseLog.date <= end_date)
    return (
        query.order_by(desc(ExerciseLog.date), desc(ExerciseLog.id))
        .offset(offset)
        .limit(min(max(limit, 1), 200))
        .all()
    )


# PUBLIC_INTERFACE
def create_body_metrics(db: Session, user_id: str, payload) -> BodyMetrics:
    """Create a body metrics snapshot for a user."""
    metrics = BodyMetrics(
        user_id=user_id,
        date=payload.date,
        weight_kg=payload.weight_kg,
        body_fat_pct=payload.body_fat_pct,
        chest_cm=payload.chest_cm,
        waist_cm=payload.waist_cm,
        hips_cm=payload.hips_cm,
        notes=payload.notes,
    )
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics


# PUBLIC_INTERFACE
def list_body_metrics(
    db: Session,
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[BodyMetrics]:
    """List body metrics snapshots for a user with optional date range and pagination."""
    query = db.query(BodyMetrics).filter(BodyMetrics.user_id == user_id)
    if start_date is not None:
        query = query.filter(BodyMetrics.date >= start_date)
    if end_date is not None:
        query = query.filter(BodyMetrics.date <= end_date)
    return (
        query.order_by(desc(BodyMetrics.date), desc(BodyMetrics.id))
        .offset(offset)
        .limit(min(max(limit, 1), 200))
        .all()
    )
