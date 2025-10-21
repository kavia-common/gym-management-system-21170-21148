from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Base fields for notifications shared across create/update."""
    user_id: str = Field(..., description="Supabase user id (UUID string) of the recipient")
    type: str = Field(..., description="Type key e.g., workout_reminder, booking_update")
    title: str = Field(..., description="Notification title")
    body: Optional[str] = Field(None, description="Notification body text")
    channel: str = Field("in_app", description="Notification channel; only 'in_app' currently supported")
    scheduled_at: Optional[datetime] = Field(None, description="When to schedule notification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Arbitrary metadata (e.g., deep link)")


class NotificationCreate(NotificationBase):
    """Payload to create a notification."""
    pass


class NotificationOut(BaseModel):
    """Notification response model."""
    id: int = Field(..., description="Notification id")
    user_id: str = Field(..., description="Recipient user id")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Title")
    body: Optional[str] = Field(None, description="Body")
    channel: str = Field(..., description="Channel")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled at")
    sent_at: Optional[datetime] = Field(None, description="Sent/materialized at")
    read_at: Optional[datetime] = Field(None, description="Read at")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        orm_mode = True


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""
    items: List[NotificationOut]
    total: int
    page: int = Field(..., description="Current page (1-based)")
    page_size: int = Field(..., description="Page size")
