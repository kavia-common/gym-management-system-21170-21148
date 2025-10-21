from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class ExerciseLogCreate(BaseModel):
    """Payload to create a new exercise log for the current user."""
    date: date = Field(..., description="Log date (YYYY-MM-DD)")
    exercise_id: Optional[int] = Field(None, description="Optional exercise id reference")
    sets: Optional[int] = Field(None, description="Number of sets")
    reps: Optional[int] = Field(None, description="Number of reps per set (avg)")
    weight: Optional[float] = Field(None, description="Weight used (kg)")
    duration_minutes: Optional[float] = Field(None, description="Duration in minutes")
    notes: Optional[str] = Field(None, description="Notes")


# PUBLIC_INTERFACE
class ExerciseLogOut(BaseModel):
    """Exercise log response model."""
    id: int
    user_id: str
    date: date
    exercise_id: Optional[int]
    sets: Optional[int]
    reps: Optional[int]
    weight: Optional[float]
    duration_minutes: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# PUBLIC_INTERFACE
class BodyMetricsCreate(BaseModel):
    """Payload to create a body metrics snapshot for the current user."""
    date: date = Field(..., description="Metrics date (YYYY-MM-DD)")
    weight_kg: Optional[float] = Field(None, description="Weight in kg")
    body_fat_pct: Optional[float] = Field(None, description="Body fat percentage")
    chest_cm: Optional[float] = Field(None, description="Chest circumference in cm")
    waist_cm: Optional[float] = Field(None, description="Waist circumference in cm")
    hips_cm: Optional[float] = Field(None, description="Hips circumference in cm")
    notes: Optional[str] = Field(None, description="Notes")


# PUBLIC_INTERFACE
class BodyMetricsOut(BaseModel):
    """Body metrics response model."""
    id: int
    user_id: str
    date: date
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    chest_cm: Optional[float]
    waist_cm: Optional[float]
    hips_cm: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
