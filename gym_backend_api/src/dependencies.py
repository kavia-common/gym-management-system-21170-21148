from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# Use canonical absolute imports for consistency across the codebase
from src.db.session import get_db as _get_db
from src.core.security import get_current_user as _security_get_current_user
from src.db.models import User, UserRole


# PUBLIC_INTERFACE
def get_db() -> Session:
    """FastAPI dependency that yields a SQLAlchemy session from the shared SessionLocal.

    Delegates to src.db.session.get_db to avoid duplication and ensure engine configuration is centralized.
    """
    # This function simply re-exports the generator from src.db.session to keep import paths stable.
    yield from _get_db()


# PUBLIC_INTERFACE
async def get_current_user(db: Session = Depends(get_db)) -> User:
    """Return the currently authenticated local User using the app JWT.

    Delegates to security.get_current_user for token validation and user lookup.
    """
    return await _security_get_current_user(db=db)


# PUBLIC_INTERFACE
def require_trainer(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has the trainer role."""
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer role required")
    return current_user
