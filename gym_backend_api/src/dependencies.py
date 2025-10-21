"""
Shared FastAPI dependencies.

Exposes:
- auth_required: FastAPI dependency that validates a Supabase JWT and returns claims.
"""

from typing import Dict, Any

from fastapi import Depends

from src.auth.supabase_jwt import get_current_user as _supabase_get_current_user, get_supabase_url  # noqa: F401

# Validate SUPABASE_URL at import-time to provide clear startup error early.
# This will raise a RuntimeError if not set.
get_supabase_url()

# PUBLIC_INTERFACE
def auth_required(claims: Dict[str, Any] = Depends(_supabase_get_current_user)) -> Dict[str, Any]:
    """Dependency alias for routes to require Supabase-authenticated user, returning JWT claims."""
    return claims
