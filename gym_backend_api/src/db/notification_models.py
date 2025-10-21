from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.types import JSON as SQLITE_JSON

from .session import Base

# Choose JSON type compatible with SQLite and Postgres
try:
    from sqlalchemy.dialects.postgresql import JSONB as PG_JSON
    JSONType = PG_JSON  # type: ignore
except Exception:  # pragma: no cover
    JSONType = SQLITE_JSON  # type: ignore


class Notification(Base):
    """
    Notification ORM model to store in-app notifications.

    Fields:
    - id: PK
    - user_id: string (Supabase UUID string) of the recipient
    - type: string describing notification type (e.g., workout_reminder, booking_update)
    - title: short title
    - body: long text body
    - channel: notification channel (only 'in_app' supported at the moment)
    - scheduled_at: when it is scheduled to be materialized/sent
    - sent_at: when it was materialized
    - read_at: when user marked as read
    - metadata: JSON metadata for deep links or context
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=False)  # Supabase UUID string
    type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    channel = Column(String(32), nullable=False, default="in_app")
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True, index=True)
    metadata = Column(JSONType, nullable=True)

    # convenience flags (not strictly required)
    # computed via sent_at/read_at in queries
