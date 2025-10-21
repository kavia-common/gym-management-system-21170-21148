from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .session import Base


class Unit(str, Enum):
    """Units for load/metrics."""
    KG = "kg"
    LB = "lb"
    REPS = "reps"
    SECONDS = "seconds"
    MINUTES = "minutes"
    METERS = "meters"
    CALORIES = "calories"


class ProgramStatus(str, Enum):
    """Program lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# PUBLIC_INTERFACE
class Exercise(Base):
    """Catalog of exercises with basic metadata."""
    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("name", name="uq_exercises_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_unit: Mapped[Unit] = mapped_column(SAEnum(Unit), nullable=False, default=Unit.REPS)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    template_exercises: Mapped[list["TemplateExercise"]] = relationship(
        "TemplateExercise", back_populates="exercise", cascade="all, delete-orphan"
    )


# PUBLIC_INTERFACE
class WorkoutTemplate(Base):
    """A reusable workout template consisting of ordered exercises."""
    __tablename__ = "workout_templates"
    __table_args__ = (UniqueConstraint("title", name="uq_workout_templates_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    exercises: Mapped[list["TemplateExercise"]] = relationship(
        "TemplateExercise",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.order_index.asc()",
    )
    program_day_exercises: Mapped[list["ProgramDayExercise"]] = relationship(
        "ProgramDayExercise", back_populates="template"
    )


# PUBLIC_INTERFACE
class TemplateExercise(Base):
    """An exercise within a workout template with prescription details."""
    __tablename__ = "template_exercises"
    __table_args__ = (
        UniqueConstraint("template_id", "order_index", name="uq_template_exercise_order"),
        CheckConstraint("order_index >= 0", name="chk_template_exercise_order_nonneg"),
        CheckConstraint("sets >= 0", name="chk_template_exercise_sets_nonneg"),
        CheckConstraint("reps >= 0", name="chk_template_exercise_reps_nonneg"),
        CheckConstraint("load_value >= 0", name="chk_template_exercise_load_nonneg"),
        CheckConstraint("duration_seconds >= 0", name="chk_template_exercise_dur_nonneg"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True)

    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    load_value: Mapped[int | None] = mapped_column(Integer, nullable=True)  # store as integer (e.g., kg, lb)
    load_unit: Mapped[Unit | None] = mapped_column(SAEnum(Unit), nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    template: Mapped["WorkoutTemplate"] = relationship("WorkoutTemplate", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="template_exercises")


# PUBLIC_INTERFACE
class Program(Base):
    """A multi-day program, optionally assigned to a member or created by a trainer."""
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProgramStatus] = mapped_column(SAEnum(ProgramStatus), nullable=False, default=ProgramStatus.DRAFT)

    # optional ownership references to existing users table to align with session
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    days: Mapped[list["ProgramDay"]] = relationship(
        "ProgramDay", back_populates="program", cascade="all, delete-orphan", order_by="ProgramDay.day_number.asc()"
    )


# PUBLIC_INTERFACE
class ProgramDay(Base):
    """A specific day within a program."""
    __tablename__ = "program_days"
    __table_args__ = (UniqueConstraint("program_id", "day_number", name="uq_program_day_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    program: Mapped["Program"] = relationship("Program", back_populates="days")
    exercises: Mapped[list["ProgramDayExercise"]] = relationship(
        "ProgramDayExercise",
        back_populates="program_day",
        cascade="all, delete-orphan",
        order_by="ProgramDayExercise.order_index.asc()",
    )


# PUBLIC_INTERFACE
class ProgramDayExercise(Base):
    """An exercise entry for a given program day; may optionally be based on a workout template."""
    __tablename__ = "program_day_exercises"
    __table_args__ = (
        UniqueConstraint("program_day_id", "order_index", name="uq_program_day_exercise_order"),
        CheckConstraint("order_index >= 0", name="chk_program_day_exercise_order_nonneg"),
        CheckConstraint("sets >= 0", name="chk_program_day_sets_nonneg"),
        CheckConstraint("reps >= 0", name="chk_program_day_reps_nonneg"),
        CheckConstraint("load_value >= 0", name="chk_program_day_load_nonneg"),
        CheckConstraint("duration_seconds >= 0", name="chk_program_day_dur_nonneg"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_day_id: Mapped[int] = mapped_column(ForeignKey("program_days.id", ondelete="CASCADE"), nullable=False, index=True)

    # Either reference a catalog exercise, or a ready-made template (template takes precedence in UI composition).
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True, index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("workout_templates.id", ondelete="SET NULL"), nullable=True, index=True)

    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    load_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_unit: Mapped[Unit | None] = mapped_column(SAEnum(Unit), nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    program_day: Mapped["ProgramDay"] = relationship("ProgramDay", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise")
    template: Mapped["WorkoutTemplate"] = relationship("WorkoutTemplate", back_populates="program_day_exercises")
