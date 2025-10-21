from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from ...dependencies import get_db, require_trainer, get_current_user
from ...schemas import workout as ws
from ...services import workout_service as svc

router = APIRouter(
    prefix="/api/v1/workouts",
    tags=["Workouts"]
)


# PUBLIC_INTERFACE
@router.post(
    "/exercises",
    response_model=ws.ExerciseOut,
    summary="Create exercise",
    description="Create an exercise owned by the trainer.",
    responses={403: {"description": "Not a trainer"}},
)
def create_exercise_endpoint(
    payload: ws.ExerciseCreate,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Create a new exercise (trainer only). Returns the created exercise."""
    return svc.create_exercise(db, trainer_id=trainer.id, payload=payload)


# PUBLIC_INTERFACE
@router.get(
    "/exercises",
    response_model=ws.PaginatedExercises,
    summary="List exercises",
    description="List exercises owned by the authenticated trainer.",
)
def list_exercises_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """List exercises for trainer with pagination."""
    items, total = svc.list_exercises(db, trainer_id=trainer.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/templates",
    response_model=ws.WorkoutTemplateOut,
    summary="Create workout template",
    description="Create a workout template owned by the trainer. Can include initial exercises.",
)
def create_template_endpoint(
    payload: ws.WorkoutTemplateCreate,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Create a template (trainer only)."""
    return svc.create_template(db, trainer_id=trainer.id, payload=payload)


# PUBLIC_INTERFACE
@router.get(
    "/templates",
    response_model=ws.PaginatedTemplates,
    summary="List workout templates",
    description="List workout templates owned by the trainer.",
)
def list_templates_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """List templates for trainer."""
    items, total = svc.list_templates(db, trainer_id=trainer.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/templates/{template_id}/exercises",
    response_model=ws.TemplateExerciseOut,
    summary="Add exercise to template",
    description="Add an exercise to a workout template (trainer must own template and exercise).",
)
def add_template_exercise_endpoint(
    template_id: int = Path(..., description="Template ID"),
    payload: ws.TemplateExerciseCreate = None,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Add exercise to a template (trainer-only)."""
    return svc.add_template_exercise(db, trainer_id=trainer.id, template_id=template_id, payload=payload)


# PUBLIC_INTERFACE
@router.delete(
    "/templates/{template_id}/exercises/{template_exercise_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete exercise from template",
    description="Remove an exercise from a workout template (trainer-only).",
)
def delete_template_exercise_endpoint(
    template_id: int = Path(..., description="Template ID"),
    template_exercise_id: int = Path(..., description="Template exercise ID"),
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Delete template exercise."""
    svc.delete_template_exercise(db, trainer_id=trainer.id, template_id=template_id, template_exercise_id=template_exercise_id)
    return {"status": "ok"}


# PUBLIC_INTERFACE
@router.post(
    "/programs",
    response_model=ws.ProgramOut,
    summary="Assign program",
    description="Create and assign a program to a member user. Optionally seed from a template.",
)
def assign_program_endpoint(
    payload: ws.ProgramCreate,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Create a member program (trainer-only)."""
    return svc.assign_program(db, trainer_id=trainer.id, payload=payload)


# PUBLIC_INTERFACE
@router.get(
    "/programs/my",
    response_model=ws.PaginatedPrograms,
    summary="List my programs (member)",
    description="Members can view their own programs.",
)
def list_my_programs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List programs for the current member."""
    items, total = svc.list_programs_for_member(db, member_user_id=current_user.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.get(
    "/programs",
    response_model=ws.PaginatedPrograms,
    summary="List programs I manage (trainer)",
    description="Trainers can list programs they created for their clients.",
)
def list_programs_for_trainer_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """List programs for trainer."""
    items, total = svc.list_programs_for_trainer(db, trainer_id=trainer.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/programs/{program_id}/days",
    response_model=ws.ProgramDayOut,
    summary="Create program day",
    description="Create a day in a program (trainer must own program).",
)
def create_program_day_endpoint(
    program_id: int = Path(..., description="Program ID"),
    payload: ws.ProgramDayCreate = None,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Add a day to a program (trainer-only)."""
    return svc.create_program_day(db, trainer_id=trainer.id, program_id=program_id, payload=payload)


# PUBLIC_INTERFACE
@router.get(
    "/programs/{program_id}/days",
    response_model=ws.PaginatedProgramDays,
    summary="List program days",
    description="List days for a program. Trainer must own program, member must be the assignee.",
)
def list_program_days_endpoint(
    program_id: int = Path(..., description="Program ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List days for a given program."""
    items, total = svc.list_program_days(db, user_id=current_user.id, program_id=program_id, role=current_user.role)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/programs/{program_id}/days/{day_id}/exercises",
    response_model=ws.ProgramDayExerciseOut,
    summary="Add exercise to program day",
    description="Add an exercise to a program day (trainer must own program).",
)
def add_program_day_exercise_endpoint(
    program_id: int = Path(..., description="Program ID"),
    day_id: int = Path(..., description="Program Day ID"),
    payload: ws.ProgramDayExerciseCreate = None,
    db: Session = Depends(get_db),
    trainer=Depends(require_trainer),
):
    """Add exercise to a specific program day (trainer-only)."""
    return svc.add_program_day_exercise(db, trainer_id=trainer.id, program_id=program_id, day_id=day_id, payload=payload)


# PUBLIC_INTERFACE
@router.get(
    "/programs/{program_id}/days/{day_id}/exercises",
    response_model=ws.PaginatedProgramDayExercises,
    summary="List program day exercises",
    description="List exercises for a program day. Trainer must own program, member must be the assignee.",
)
def list_program_day_exercises_endpoint(
    program_id: int = Path(..., description="Program ID"),
    day_id: int = Path(..., description="Program Day ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List exercises within a program day for trainer/member visibility constraints."""
    items, total = svc.list_program_day_exercises(db, user_id=current_user.id, role=current_user.role, program_id=program_id, day_id=day_id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
