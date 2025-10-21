from datetime import datetime

from sqlalchemy import event
from sqlalchemy.orm import Mapper

from .models import User


def _set_updated_at(mapper: Mapper, connection, target):
    """Set updated_at to utcnow on insert/update for models that have it."""
    if hasattr(target, "updated_at"):
        setattr(target, "updated_at", datetime.utcnow())


# Register events for User timestamps
event.listen(User, "before_insert", _set_updated_at)
event.listen(User, "before_update", _set_updated_at)
