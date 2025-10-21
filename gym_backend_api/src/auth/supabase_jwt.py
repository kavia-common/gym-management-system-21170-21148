import os
import time
from typing import Any, Dict, Optional, Tuple, List

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt


# PUBLIC_INTERFACE
def get_supabase_url() -> str:
    """Return SUPABASE_URL from environment or raise a clear error if missing."""
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise RuntimeError(
            "Missing SUPABASE_URL environment variable. "
            "Set SUPABASE_URL to your Supabase project URL (e.g., https://xyzcompany.supabase.co)"
        )
    return supabase_url.rstrip("/")


# Simple in-memory JWKS cache with TTL
_JWKS_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
_JWKS_TTL_SECONDS = 60 * 60  # 1 hour


def _jwks_url() -> str:
    """Build Supabase JWKS URL based on SUPABASE_URL."""
    base = get_supabase_url()
    return f"{base}/auth/v1/keys"


def _get_cached_jwks(cache_key: str) -> Optional[Dict[str, Any]]:
    entry = _JWKS_CACHE.get(cache_key)
    if not entry:
        return None
    data, expiry = entry
    if time.time() > expiry:
        # expired
        _JWKS_CACHE.pop(cache_key, None)
        return None
    return data


def _set_cached_jwks(cache_key: str, jwks: Dict[str, Any], ttl_seconds: int = _JWKS_TTL_SECONDS) -> None:
    _JWKS_CACHE[cache_key] = (jwks, time.time() + ttl_seconds)


def _fetch_jwks() -> Dict[str, Any]:
    """Fetch JWKS from Supabase and cache."""
    url = _jwks_url()
    cache_key = url
    cached = _get_cached_jwks(cache_key)
    if cached:
        return cached

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            jwks = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Supabase JWKS"
        ) from exc

    if not isinstance(jwks, dict) or "keys" not in jwks:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid JWKS format returned by Supabase"
        )

    _set_cached_jwks(cache_key, jwks)
    return jwks


def _get_kid(token: str) -> str:
    """Extract 'kid' from JWT header without verification."""
    try:
        # jose provides parsing to get the unverified header which contains 'kid'
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT header") from exc

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT header missing kid")
    return kid


def _find_jwk_for_kid(jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None


def _expected_issuers() -> List[str]:
    """Return allowed issuer values for Supabase tokens."""
    base = get_supabase_url()
    # Supabase jwt iss is typically the project URL; sometimes includes /auth/v1
    return [base, f"{base}/auth/v1"]


# PUBLIC_INTERFACE
def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a Supabase JWT using the project's JWKS.

    - Validates signature using the correct JWK (by kid).
    - Validates issuer (iss) against SUPABASE_URL (and /auth/v1 variant).
    - If 'aud' present, ensure non-empty; optionally you can compare against expected audience(s) if configured.
    - Returns decoded claims dict on success; raises HTTPException otherwise.
    """
    if not token or token.count(".") != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT format")

    # Load JWKS and select JWK by kid
    kid = _get_kid(token)
    jwks = _fetch_jwks()
    jwk = _find_jwk_for_kid(jwks, kid)
    if jwk is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown JWT key id (kid)")

    # Verify signature and claims (issuer, expiry etc.)
    try:
        claims = jwt.decode(
            token,
            jwk,
            algorithms=[jwk.get("alg", "RS256"), "RS256", "ES256"],  # allow typical algorithms
            options={
                "verify_aud": False,  # We'll validate aud manually if present
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT") from exc

    # Validate issuer
    iss = claims.get("iss")
    if not iss or iss not in _expected_issuers():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    # Validate audience if present (Supabase may include aud like 'authenticated')
    aud = claims.get("aud")
    if aud is not None and isinstance(aud, str) and not aud.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

    return claims


_bearer_scheme = HTTPBearer(auto_error=False)

# PUBLIC_INTERFACE
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and verifies a Supabase JWT from Authorization header.

    Returns a claims dict containing at least:
    - sub: the user id (UUID string)
    - email: if present in token (optional)

    Raises 401 on missing or invalid token.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")

    token = credentials.credentials
    claims = verify_jwt(token)

    # Normalize known fields
    if "sub" not in claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing sub")
    # Email might live under 'email' or 'user_metadata' depending on Supabase settings
    email = claims.get("email")
    if not email:
        user_meta = claims.get("user_metadata") or {}
        if isinstance(user_meta, dict):
            email = user_meta.get("email")
        if email:
            claims["email"] = email

    return claims
