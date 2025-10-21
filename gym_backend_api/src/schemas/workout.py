from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from src.db.workout_models import Unit, ProgramStatus


# PUBLIC_INTERFACE
class ExerciseCreate(BaseModel):
    """Create a catalog exercise."""
    name: str = Field(..., description="Exercise name")
    description: str | None = Field(default=None, description="Exercise description")
    default_unit: Unit = Field(default=Unit.REPS, description="Default measurement unit")


# PUBLIC_INTERFACE
class ExerciseOut(BaseModel):
    """Exercise response."""
    id: int
    name: str
    description: str | None
    default_unit: Unit
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class TemplateExerciseCreate(BaseModel):
    """Exercise prescription inside a workout template."""
    exercise_id: int = Field(..., description="Exercise ID from catalog")
    order_index: int = Field(default=0, ge=0)
    sets: int | None = Field(default=None, ge=0)
    reps: int | None = Field(default=None, ge=0)
    load_value: int | None = Field(default=None, ge=0)
    load_unit: Unit | None = Field(default=None)
    duration_seconds: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None)


# PUBLIC_INTERFACE
class TemplateExerciseOut(BaseModel):
    """Template exercise response."""
    id: int
    template_id: int
    exercise_id: int
    order_index: int
    sets: int | None
    reps: int | None
    load_value: int | None
    load_unit: Unit | None
    duration_seconds: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class WorkoutTemplateCreate(BaseModel):
    """Create workout template."""
    title: str = Field(..., description="Template title")
    description: str | None = Field(default=None, description="Template description")


# PUBLIC_INTERFACE
class WorkoutTemplateOut(BaseModel):
    """Workout template response."""
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class ProgramCreate(BaseModel):
    """Create a training program."""
    title: str = Field(..., description="Program title")
    description: str | None = Field(default=None)
    status: ProgramStatus = Field(default=ProgramStatus.DRAFT)
    assigned_to_user_id: int | None = Field(default=None, description="Assign to member user id")


# PUBLIC_INTERFACE
class ProgramOut(BaseModel):
    """Program response."""
    id: int
    title: str
    description: str | None
    status: ProgramStatus
    created_by_user_id: int | None
    assigned_to_user_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class ProgramDayCreate(BaseModel):
    """Create a day for a program."""
    program_id: int
    day_number: int = Field(default=1, ge=1)
    title: str | None = None
    notes: str | None = None


# PUBLIC_INTERFACE
class ProgramDayOut(BaseModel):
    """Program day response."""
    id: int
    program_id: int
    day_number: int
    title: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class ProgramDayExerciseCreate(BaseModel):
    """Create exercise entry for a program day."""
    program_day_id: int
    order_index: int = Field(default=0, ge=0)
    exercise_id: int | None = Field(default=None, description="Catalog exercise id")
    template_id: int | None = Field(default=None, description="Workout template id")
    sets: int | None = Field(default=None, ge=0)
    reps: int | None = Field(default=None, ge=0)
    load_value: int | None = Field(default=None, ge=0)
    load_unit: Unit | None = Field(default=None)
    duration_seconds: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None)


# PUBLIC_INTERFACE
class ProgramDayExerciseOut(BaseModel):
    """Program day exercise response."""
    id: int
    program_day_id: int
    order_index: int
    exercise_id: int | None
    template_id: int | None
    sets: int | None
    reps: int | None
    load_value: int | None
    load_unit: Unit | None
    duration_seconds: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
