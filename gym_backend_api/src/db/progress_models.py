from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, Float
from sqlalchemy.orm import declarative_mixin
from .models import Base  # Reuse same Base to share metadata across models


@declarative_mixin
class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ExerciseLog(Base, TimestampMixin):
    """
    Exercise log entry for a user.
    Links to a workout/exercise id optionally (exercise_id), records sets, reps, weight, and notes.
    """
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Supabase user id (uuid string)
    exercise_id = Column(Integer, index=True, nullable=True)  # optional linkage to exercise catalog
    date = Column(Date, nullable=False, index=True)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    notes = Column(String, nullable=True)


class BodyMetrics(Base, TimestampMixin):
    """
    Body metrics snapshot for a user.
    Records weight, body fat percentage, and circumferences, etc.
    """
    __tablename__ = "body_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Supabase user id (uuid string)
    date = Column(Date, nullable=False, index=True)
    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
