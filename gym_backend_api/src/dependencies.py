"""
Shared FastAPI dependencies.

Exposes:
- auth_required: Validates a Supabase JWT and returns claims.
- get_current_local_user: Resolves/creates a local User mapped by Supabase sub/email.
- require_member / require_trainer: Role-based access control helpers using local user mapping.
"""

from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.supabase_jwt import get_current_user as _supabase_get_current_user, get_supabase_url  # noqa: F401
from src.db.session import get_db
from src.db.models import User, UserRole
from src.core.security import get_password_hash

# Validate SUPABASE_URL at import-time to provide clear startup error early.
# This will raise a RuntimeError if not set.
get_supabase_url()


# PUBLIC_INTERFACE
def auth_required(claims: Dict[str, Any] = Depends(_supabase_get_current_user)) -> Dict[str, Any]:
    """Dependency alias for routes to require Supabase-authenticated user, returning JWT claims."""
    return claims


# PUBLIC_INTERFACE
def get_current_local_user(
    claims: Dict[str, Any] = Depends(auth_required),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the local User from Supabase claims. If not exists, create as member.

    Behavior:
    - Uses claims['sub'] as supabase_user_id (UUID string).
    - If user with this supabase_user_id exists: return it.
    - Else, try find by email if provided and not already linked; if found, link supabase_user_id.
    - Else, create a new local user with role=member; email may be None -> fallback to placeholder.
      Password hash is a random placeholder; not used for Supabase auth.
    """
    supabase_sub = str(claims.get("sub"))
    if not supabase_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing sub")

    email = claims.get("email")

    # 1) by supabase_user_id
    user = db.query(User).filter(User.supabase_user_id == supabase_sub).first()
    if user:
        return user

    # 2) link by email if exists
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.supabase_user_id = supabase_sub
            # ensure updated_at maintained if present
            try:
                from datetime import datetime as _dt
                existing.updated_at = _dt.utcnow()
            except Exception:
                pass
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

    # 3) create new user (member default)
    placeholder_email = email or f"{supabase_sub}@example.local"
    ph_pwd = get_password_hash(f"supabase-{supabase_sub}")
    new_user = User(
        supabase_user_id=supabase_sub,
        email=placeholder_email,
        password_hash=ph_pwd,
        role=UserRole.MEMBER,
    )
    # set created/updated timestamp if model supports it (created_at default already)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def _role_guard(required_roles: tuple[UserRole, ...]):
    """Internal factory to enforce required roles against local user."""

    # PUBLIC_INTERFACE
    def _dep(user: User = Depends(get_current_local_user)) -> User:
        if user.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _dep


# PUBLIC_INTERFACE
def require_member(user: User = Depends(get_current_local_user)) -> User:
    """Require that current local user is at least a member (always true if exists)."""
    # All users are at least members; this wrapper provides explicit dependency for readability.
    return user


# PUBLIC_INTERFACE
def require_trainer(user: User = Depends(_role_guard((UserRole.TRAINER, UserRole.ADMIN)))) -> User:
    """Require that the current local user has trainer or admin role."""
    return user
