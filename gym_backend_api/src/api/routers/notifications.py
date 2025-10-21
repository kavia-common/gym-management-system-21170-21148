from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...auth.supabase_jwt import get_current_user  # provides user dict with id, email, role
from ...db import get_db
from ...schemas.notification import NotificationCreate, NotificationListResponse, NotificationOut
from ...services import notification_service

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)


class _UserContext(BaseModel):
    user_id: str
    role: str


def _require_user(user=Depends(get_current_user)) -> _UserContext:
    """Extract user context from Supabase JWT claims.

    Raises when unauthenticated.
    """
    if not user or "user_id" not in user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    role = user.get("role") or "member"
    return _UserContext(user_id=user["user_id"], role=role)


def _require_trainer_or_admin(ctx: _UserContext = Depends(_require_user)) -> _UserContext:
    """Ensure the current user is trainer or admin."""
    if ctx.role not in {"trainer", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx


# PUBLIC_INTERFACE
@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications",
    description="List notifications for the current user. Supports unread filter and pagination.",
)
def list_notifications(
    unread: bool = Query(False, description="If true, return only unread notifications"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    ctx: _UserContext = Depends(_require_user),
    db: Session = Depends(get_db),
):
    """List notifications for the authenticated user with pagination."""
    items, total = notification_service.list_for_user(db, user_id=ctx.user_id, unread_only=unread, page=page, page_size=page_size)
    return NotificationListResponse(items=[NotificationOut.from_orm(it) for it in items], total=total, page=page, page_size=page_size)


# PUBLIC_INTERFACE
@router.patch(
    "/{notification_id}/read",
    response_model=NotificationOut,
    summary="Mark notification as read",
    description="Mark a specific notification as read for the current user.",
)
def mark_notification_read(
    notification_id: int,
    ctx: _UserContext = Depends(_require_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read for the current user."""
    updated = notification_service.mark_read(db, notif_id=notification_id, user_id=ctx.user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationOut.from_orm(updated)


# PUBLIC_INTERFACE
@router.post(
    "/test",
    response_model=NotificationOut,
    summary="Create test notification",
    description="Create a sample notification for the current user (development convenience).",
)
def create_test_notification(
    ctx: _UserContext = Depends(_require_user),
    db: Session = Depends(get_db),
):
    """Create a simple test notification for the authenticated user."""
    payload = NotificationCreate(
        user_id=ctx.user_id,
        type="test",
        title="Test Notification",
        body="This is a test notification.",
        channel="in_app",
        metadata={"source": "test_endpoint"},
    )
    notif = notification_service.create_notification(db, payload)
    return NotificationOut.from_orm(notif)


class MaterializeResponse(BaseModel):
    materialized: int = Field(..., description="Number of notifications materialized/updated")


# PUBLIC_INTERFACE
@router.post(
    "/materialize",
    response_model=MaterializeResponse,
    summary="Materialize due reminders",
    description="Scheduler stub to materialize due reminders into notifications. Requires trainer or admin.",
)
def materialize_notifications(
    ctx: _UserContext = Depends(_require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    """Materialize due reminders from schedules into notifications (stub)."""
    count = notification_service.materialize_due_reminders(db)
    return MaterializeResponse(materialized=count)
