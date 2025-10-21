from typing import Optional
from sqlalchemy.orm import Session

from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.db.models import User, UserRole


# PUBLIC_INTERFACE
def signup(db: Session, email: str, password: str) -> User:
    """Create a new user with default member role."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("Email already registered")
    user = User(email=email, password_hash=get_password_hash(password), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# PUBLIC_INTERFACE
def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# PUBLIC_INTERFACE
def issue_tokens(user_id: int) -> dict:
    """Issue access and refresh tokens for a given user id."""
    return {"access_token": create_access_token(user_id), "refresh_token": create_refresh_token(user_id)}
