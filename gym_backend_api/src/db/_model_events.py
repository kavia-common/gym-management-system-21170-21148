from datetime import datetime

from sqlalchemy import event
from sqlalchemy.orm import Mapper

from .models import User
from .workout_models import (
    Exercise,
    WorkoutTemplate,
    TemplateExercise,
    Program,
    ProgramDay,
    ProgramDayExercise,
)


def _set_updated_at(mapper: Mapper, connection, target):
    """Set updated_at to utcnow on insert/update for models that have it."""
    if hasattr(target, "updated_at"):
        setattr(target, "updated_at", datetime.utcnow())


# Register events for User timestamps
event.listen(User, "before_insert", _set_updated_at)
event.listen(User, "before_update", _set_updated_at)

# Register events for workout programming models
for _model in (Exercise, WorkoutTemplate, TemplateExercise, Program, ProgramDay, ProgramDayExercise):
    event.listen(_model, "before_insert", _set_updated_at)
    event.listen(_model, "before_update", _set_updated_at)
