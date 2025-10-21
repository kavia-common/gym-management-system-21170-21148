from typing import List, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..db import workout_models as wm
from ..schemas import workout as ws


def _paginate(query, page: int, page_size: int):
    """Apply pagination to a SQLAlchemy query."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


# PUBLIC_INTERFACE
def ensure_trainer_owns_template(db: Session, trainer_id: int, template_id: int) -> wm.WorkoutTemplate:
    """Ensure that a template is owned by trainer."""
    template = db.query(wm.WorkoutTemplate).filter(
        wm.WorkoutTemplate.id == template_id,
        wm.WorkoutTemplate.trainer_id == trainer_id
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found or not owned by trainer")
    return template


# PUBLIC_INTERFACE
def ensure_trainer_owns_program(db: Session, trainer_id: int, program_id: int) -> wm.Program:
    """Ensure that a program is owned/assigned by trainer."""
    program = db.query(wm.Program).filter(
        wm.Program.id == program_id,
        wm.Program.trainer_id == trainer_id
    ).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found or not owned by trainer")
    return program


# PUBLIC_INTERFACE
def ensure_member_can_view_program(db: Session, member_user_id: int, program_id: int) -> wm.Program:
    """Ensure that a member owns the program."""
    program = db.query(wm.Program).filter(
        wm.Program.id == program_id,
        wm.Program.member_user_id == member_user_id
    ).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


# PUBLIC_INTERFACE
def create_exercise(db: Session, trainer_id: int, payload: ws.ExerciseCreate) -> ws.ExerciseOut:
    """Create an exercise (trainer only)."""
    # If exercises are global, you could drop trainer scope. Here we scope by trainer for ownership.
    ex = wm.Exercise(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        trainer_id=trainer_id
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ws.ExerciseOut.from_orm(ex)


# PUBLIC_INTERFACE
def list_exercises(db: Session, trainer_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[ws.ExerciseOut], int]:
    """List exercises created by the trainer (pagination)."""
    query = db.query(wm.Exercise).filter(wm.Exercise.trainer_id == trainer_id)
    items, total = _paginate(query, page, page_size)
    return [ws.ExerciseOut.from_orm(i) for i in items], total


# PUBLIC_INTERFACE
def create_template(db: Session, trainer_id: int, payload: ws.WorkoutTemplateCreate) -> ws.WorkoutTemplateOut:
    """Create a workout template (trainer only)."""
    tpl = wm.WorkoutTemplate(
        name=payload.name,
        goal=payload.goal,
        trainer_id=trainer_id
    )
    db.add(tpl)
    db.flush()
    # add exercises if provided
    for te in (payload.exercises or []):
        # Validate exercise belongs to trainer
        ex = db.query(wm.Exercise).filter(
            wm.Exercise.id == te.exercise_id,
            wm.Exercise.trainer_id == trainer_id
        ).first()
        if not ex:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Exercise {te.exercise_id} not found for trainer")
        t_ex = wm.TemplateExercise(
            template_id=tpl.id,
            exercise_id=te.exercise_id,
            sets=te.sets,
            reps=te.reps,
            rest_seconds=te.rest_seconds,
            notes=te.notes
        )
        db.add(t_ex)
    db.commit()
    db.refresh(tpl)
    return ws.WorkoutTemplateOut.from_orm(tpl)


# PUBLIC_INTERFACE
def list_templates(db: Session, trainer_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[ws.WorkoutTemplateOut], int]:
    """List templates for trainer."""
    query = db.query(wm.WorkoutTemplate).filter(wm.WorkoutTemplate.trainer_id == trainer_id)
    items, total = _paginate(query, page, page_size)
    return [ws.WorkoutTemplateOut.from_orm(i) for i in items], total


# PUBLIC_INTERFACE
def add_template_exercise(db: Session, trainer_id: int, template_id: int, payload: ws.TemplateExerciseCreate) -> ws.TemplateExerciseOut:
    """Add exercise to template (trainer-only, must own)."""
    template = ensure_trainer_owns_template(db, trainer_id, template_id)
    # Validate exercise
    ex = db.query(wm.Exercise).filter(
        wm.Exercise.id == payload.exercise_id,
        wm.Exercise.trainer_id == trainer_id
    ).first()
    if not ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exercise not found for trainer")

    t_ex = wm.TemplateExercise(
        template_id=template.id,
        exercise_id=payload.exercise_id,
        sets=payload.sets,
        reps=payload.reps,
        rest_seconds=payload.rest_seconds,
        notes=payload.notes
    )
    db.add(t_ex)
    db.commit()
    db.refresh(t_ex)
    return ws.TemplateExerciseOut.from_orm(t_ex)


# PUBLIC_INTERFACE
def delete_template_exercise(db: Session, trainer_id: int, template_id: int, template_exercise_id: int) -> None:
    """Delete a template exercise (trainer-only, must own template)."""
    ensure_trainer_owns_template(db, trainer_id, template_id)
    t_ex = db.query(wm.TemplateExercise).filter(
        wm.TemplateExercise.id == template_exercise_id,
        wm.TemplateExercise.template_id == template_id
    ).first()
    if not t_ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template exercise not found")
    db.delete(t_ex)
    db.commit()


# PUBLIC_INTERFACE
def assign_program(db: Session, trainer_id: int, payload: ws.ProgramCreate) -> ws.ProgramOut:
    """Create and assign a Program to a member user (trainer-only)."""
    program = wm.Program(
        name=payload.name,
        member_user_id=payload.member_user_id,
        trainer_id=trainer_id,
        notes=payload.notes
    )
    db.add(program)
    db.flush()
    # optionally seed from template_id
    if payload.template_id:
        tpl = ensure_trainer_owns_template(db, trainer_id, payload.template_id)
        # create day 1 from the template by default
        day = wm.ProgramDay(program_id=program.id, day_index=1, name=f"{tpl.name} - Day 1")
        db.add(day)
        db.flush()
        # copy template exercises to program day exercises
        t_exs = db.query(wm.TemplateExercise).filter(wm.TemplateExercise.template_id == tpl.id).all()
        for t in t_exs:
            pde = wm.ProgramDayExercise(
                program_day_id=day.id,
                exercise_id=t.exercise_id,
                sets=t.sets,
                reps=t.reps,
                rest_seconds=t.rest_seconds,
                notes=t.notes
            )
            db.add(pde)
    db.commit()
    db.refresh(program)
    return ws.ProgramOut.from_orm(program)


# PUBLIC_INTERFACE
def list_programs_for_trainer(db: Session, trainer_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[ws.ProgramOut], int]:
    """List all programs created by trainer."""
    query = db.query(wm.Program).filter(wm.Program.trainer_id == trainer_id)
    items, total = _paginate(query, page, page_size)
    return [ws.ProgramOut.from_orm(i) for i in items], total


# PUBLIC_INTERFACE
def list_programs_for_member(db: Session, member_user_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[ws.ProgramOut], int]:
    """List programs for a member (own programs)."""
    query = db.query(wm.Program).filter(wm.Program.member_user_id == member_user_id)
    items, total = _paginate(query, page, page_size)
    return [ws.ProgramOut.from_orm(i) for i in items], total


# PUBLIC_INTERFACE
def create_program_day(db: Session, trainer_id: int, program_id: int, payload: ws.ProgramDayCreate) -> ws.ProgramDayOut:
    """Create a day within a program (trainer must own program)."""
    ensure_trainer_owns_program(db, trainer_id, program_id)
    day = wm.ProgramDay(
        program_id=program_id,
        day_index=payload.day_index,
        name=payload.name
    )
    db.add(day)
    db.commit()
    db.refresh(day)
    return ws.ProgramDayOut.from_orm(day)


# PUBLIC_INTERFACE
def list_program_days(db: Session, user_id: int, program_id: int, role: str, page: int = 1, page_size: int = 20) -> Tuple[List[ws.ProgramDayOut], int]:
    """List days for a program (trainer owner or member owner)."""
    base = db.query(wm.ProgramDay).join(wm.Program, wm.ProgramDay.program_id == wm.Program.id).filter(
        wm.ProgramDay.program_id == program_id
    )
    if role == "trainer":
        base = base.filter(wm.Program.trainer_id == user_id)
    else:
        base = base.filter(wm.Program.member_user_id == user_id)
    items, total = _paginate(base, page, page_size)
    return [ws.ProgramDayOut.from_orm(i) for i in items], total


# PUBLIC_INTERFACE
def add_program_day_exercise(db: Session, trainer_id: int, program_id: int, day_id: int, payload: ws.ProgramDayExerciseCreate) -> ws.ProgramDayExerciseOut:
    """Add an exercise to program day (trainer must own program)."""
    ensure_trainer_owns_program(db, trainer_id, program_id)
    day = db.query(wm.ProgramDay).filter(
        wm.ProgramDay.id == day_id,
        wm.ProgramDay.program_id == program_id
    ).first()
    if not day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program day not found")
    # validate exercise belongs to trainer (so trainer knows this exercise)
    ex = db.query(wm.Exercise).filter(
        wm.Exercise.id == payload.exercise_id,
        wm.Exercise.trainer_id == trainer_id
    ).first()
    if not ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exercise not found for trainer")

    pde = wm.ProgramDayExercise(
        program_day_id=day.id,
        exercise_id=payload.exercise_id,
        sets=payload.sets,
        reps=payload.reps,
        rest_seconds=payload.rest_seconds,
        notes=payload.notes
    )
    db.add(pde)
    db.commit()
    db.refresh(pde)
    return ws.ProgramDayExerciseOut.from_orm(pde)


# PUBLIC_INTERFACE
def list_program_day_exercises(db: Session, user_id: int, role: str, program_id: int, day_id: int, page: int = 1, page_size: int = 50) -> Tuple[List[ws.ProgramDayExerciseOut], int]:
    """List exercises for a program day (trainer owner or member owner)."""
    query = db.query(wm.ProgramDayExercise).join(wm.ProgramDay, wm.ProgramDayExercise.program_day_id == wm.ProgramDay.id).join(
        wm.Program, wm.ProgramDay.program_id == wm.Program.id
    ).filter(
        wm.ProgramDayExercise.program_day_id == day_id,
        wm.ProgramDay.program_id == program_id
    )
    if role == "trainer":
        query = query.filter(wm.Program.trainer_id == user_id)
    else:
        query = query.filter(wm.Program.member_user_id == user_id)

    items, total = _paginate(query, page, page_size)
    return [ws.ProgramDayExerciseOut.from_orm(i) for i in items], total
