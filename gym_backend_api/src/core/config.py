import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables with sensible defaults."""

    # App
    APP_ENV: str = Field(default=os.getenv("APP_ENV", "development"), description="Application environment")
    API_PORT: int = Field(default=int(os.getenv("API_PORT", "3001")), description="Port to run API on")
    FRONTEND_URL: Optional[str] = Field(default=os.getenv("FRONTEND_URL"), description="Frontend base URL")
    CORS_ALLOW_ORIGINS: Optional[str] = Field(
        default=os.getenv("CORS_ALLOW_ORIGINS", ""), description="Comma-separated list of allowed origins"
    )
    DEMO_MODE: bool = Field(
        default=os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"},
        description="Enable demo mode behaviors (seed data, relaxed permissions, mock payments)",
    )

    # Security
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "change_me"), description="JWT secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")), description="Access token expiry in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")), description="Refresh token expiry in days"
    )
    TEST_MODE: bool = Field(
        default=os.getenv("TEST_MODE", "false").strip().lower() in {"1", "true", "yes", "on"},
        description="Enable test mode behaviors (e.g., stubbed payments)",
    )

    # Database
    DATABASE_URL: Optional[str] = Field(default=os.getenv("DATABASE_URL"))
    DATABASE_URL_SQLITE: str = Field(default=os.getenv("DATABASE_URL_SQLITE", "sqlite:///./app.db"))
    DB_ECHO: bool = Field(default=os.getenv("DB_ECHO", "false").strip().lower() in {"1", "true", "yes", "on"})

    # Payments
    PAYMENT_PROVIDER: str = Field(default=os.getenv("PAYMENT_PROVIDER", "stripe"))
    STRIPE_SECRET_KEY: Optional[str] = Field(default=os.getenv("STRIPE_SECRET_KEY"))
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET"))
    CURRENCY: str = Field(default=os.getenv("CURRENCY", "usd"))

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=os.getenv("GOOGLE_CLIENT_ID"), description="Google OAuth Client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=os.getenv("GOOGLE_CLIENT_SECRET"), description="Google OAuth Client Secret")
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = Field(
        default=os.getenv("GOOGLE_OAUTH_REDIRECT_URI"),
        description="Backend redirect URI for Google OAuth (e.g., http://localhost:3001/api/v1/auth/google/callback)",
    )

    # Derived settings
    def cors_origins(self) -> List[str]:
        """Return list of allowed CORS origins based on env settings."""
        origins: List[str] = []
        # Prefer explicit list if provided
        if self.CORS_ALLOW_ORIGINS:
            parts = [p.strip() for p in self.CORS_ALLOW_ORIGINS.split(",") if p.strip()]
            origins.extend(parts)
        # FRONTEND_URL as a fallback allowed origin
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        # Always include localhost:3000 by default for dev
        if "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        # In test or if nothing set, permissive wildcard is allowed by CORS middleware config below
        return origins


# PUBLIC_INTERFACE
@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
