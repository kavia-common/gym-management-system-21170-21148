from typing import Optional, List
from pydantic import BaseModel, Field


class ExerciseBase(BaseModel):
    name: str = Field(..., description="Exercise name")
    description: Optional[str] = Field(None, description="Optional description")
    category: Optional[str] = Field(None, description="Category or body part")


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseOut(ExerciseBase):
    id: int

    class Config:
        orm_mode = True


class PaginatedExercises(BaseModel):
    items: List[ExerciseOut]
    total: int
    page: int
    page_size: int


class TemplateExerciseBase(BaseModel):
    exercise_id: int = Field(..., description="Exercise ID")
    sets: int = Field(..., description="Number of sets")
    reps: int = Field(..., description="Target reps")
    rest_seconds: Optional[int] = Field(None, description="Rest in seconds between sets")
    notes: Optional[str] = Field(None, description="Coach notes")


class TemplateExerciseCreate(TemplateExerciseBase):
    pass


class TemplateExerciseOut(TemplateExerciseBase):
    id: int
    template_id: int

    class Config:
        orm_mode = True


class WorkoutTemplateBase(BaseModel):
    name: str = Field(..., description="Template name")
    goal: Optional[str] = Field(None, description="Intended goal (e.g., strength, hypertrophy)")


class WorkoutTemplateCreate(WorkoutTemplateBase):
    exercises: Optional[List[TemplateExerciseCreate]] = Field(default=None, description="Optional exercises to add")


class WorkoutTemplateOut(WorkoutTemplateBase):
    id: int
    trainer_id: int

    class Config:
        orm_mode = True


class PaginatedTemplates(BaseModel):
    items: List[WorkoutTemplateOut]
    total: int
    page: int
    page_size: int


class ProgramCreate(BaseModel):
    name: str = Field(..., description="Program name")
    member_user_id: int = Field(..., description="Assignee member user id")
    template_id: Optional[int] = Field(None, description="Optional template to seed from")
    notes: Optional[str] = Field(None, description="Notes for the program")


class ProgramOut(BaseModel):
    id: int
    name: str
    member_user_id: int
    trainer_id: int
    notes: Optional[str]

    class Config:
        orm_mode = True


class PaginatedPrograms(BaseModel):
    items: List[ProgramOut]
    total: int
    page: int
    page_size: int


class ProgramDayCreate(BaseModel):
    day_index: int = Field(..., description="Order of the day within the program (1-based)")
    name: str = Field(..., description="Name for the day")


class ProgramDayOut(BaseModel):
    id: int
    program_id: int
    day_index: int
    name: str

    class Config:
        orm_mode = True


class PaginatedProgramDays(BaseModel):
    items: List[ProgramDayOut]
    total: int
    page: int
    page_size: int


class ProgramDayExerciseCreate(BaseModel):
    exercise_id: int = Field(..., description="Exercise id")
    sets: int = Field(..., description="Sets")
    reps: int = Field(..., description="Reps")
    rest_seconds: Optional[int] = Field(None, description="Rest seconds")
    notes: Optional[str] = Field(None, description="Notes")


class ProgramDayExerciseOut(ProgramDayExerciseCreate):
    id: int
    program_day_id: int

    class Config:
        orm_mode = True


class PaginatedProgramDayExercises(BaseModel):
    items: List[ProgramDayExerciseOut]
    total: int
    page: int
    page_size: int
