from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .session import Base


class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    trainer_id = Column(Integer, nullable=False)  # assuming user table uses int ids


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    goal = Column(Text, nullable=True)
    trainer_id = Column(Integer, nullable=False)

    exercises = relationship("TemplateExercise", backref="template", cascade="all, delete-orphan")


class TemplateExercise(Base):
    __tablename__ = "template_exercises"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    rest_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)


class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    member_user_id = Column(Integer, nullable=False, index=True)
    trainer_id = Column(Integer, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    days = relationship("ProgramDay", backref="program", cascade="all, delete-orphan")


class ProgramDay(Base):
    __tablename__ = "program_days"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    day_index = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)

    exercises = relationship("ProgramDayExercise", backref="day", cascade="all, delete-orphan")


class ProgramDayExercise(Base):
    __tablename__ = "program_day_exercises"
    id = Column(Integer, primary_key=True, index=True)
    program_day_id = Column(Integer, ForeignKey("program_days.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    rest_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
