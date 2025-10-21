from typing import Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .db.session import SessionLocal
from .services.auth_service import get_current_user as _get_current_user


def get_db():
    """Yield a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_current_user() -> Any:
    """Proxy to auth service to retrieve current user object with role and id."""
    return _get_current_user()


# PUBLIC_INTERFACE
def require_trainer(current_user: Any = Depends(get_current_user)) -> Any:
    """Require the current user to have trainer role."""
    # current_user is expected to have 'role' and 'id'
    if not current_user or getattr(current_user, "role", None) != "trainer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer role required")
    return current_user
