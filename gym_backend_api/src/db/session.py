import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base class for SQLAlchemy models
Base = declarative_base()


def _get_bool(env_value: Optional[str], default: bool = False) -> bool:
    """
    Internal helper to parse boolean-like environment values.
    Accepts: "1", "true", "yes", "on" as True; "0", "false", "no", "off" as False.
    """
    if env_value is None:
        return default
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


# PUBLIC_INTERFACE
def get_engine():
    """Create and return an SQLAlchemy engine.

    Reads configuration from environment variables:
    - DATABASE_URL: Primary database URL (e.g., postgresql+psycopg://user:pass@host:5432/db)
    - DATABASE_URL_SQLITE: SQLite fallback URL (default: sqlite:///./app.db)
    - DB_ECHO: Whether to echo SQL statements (default: false)

    If DATABASE_URL is not provided, falls back to DATABASE_URL_SQLITE (SQLite).
    """
    db_url = os.getenv("DATABASE_URL")
    sqlite_url = os.getenv("DATABASE_URL_SQLITE", "sqlite:///./app.db")
    echo = _get_bool(os.getenv("DB_ECHO"), default=False)

    # Prefer explicit DATABASE_URL; otherwise, use SQLite fallback
    url = db_url if db_url else sqlite_url

    connect_args = {}
    # For SQLite, ensure check_same_thread = False when using with FastAPI/threads
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(url, echo=echo, connect_args=connect_args)
    return engine


# Create engine and SessionLocal for general use
_engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# PUBLIC_INTERFACE
def get_db():
    """FastAPI dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def maybe_create_database_tables():
    """Create all tables in development or when TEST_MODE is true.

    Conditions:
    - APP_ENV == "development"
    - or TEST_MODE == true
    """
    app_env = os.getenv("APP_ENV", "").strip().lower()
    test_mode = _get_bool(os.getenv("TEST_MODE"), default=False)

    if app_env == "development" or test_mode:
        # Import models here to ensure they are registered with Base before create_all
        from src.db import models  # noqa: F401
        from src.db import workout_models  # noqa: F401

        Base.metadata.create_all(bind=_engine)


# Ensure tables are created in dev/test upon import if conditions met.
# Register model events (like updated_at management) before potential create_all to avoid side effects.
try:
    from src.db import _model_events  # noqa: F401
except Exception:
    # Safe to ignore if any import-time issues occur during initial setups
    pass

maybe_create_database_tables()
