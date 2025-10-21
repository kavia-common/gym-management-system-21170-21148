from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..db.notification_models import Notification
from ..schemas.notification import NotificationCreate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# PUBLIC_INTERFACE
def list_for_user(db: Session, user_id: str, unread_only: bool = False, page: int = 1, page_size: int = 20) -> Tuple[List[Notification], int]:
    """List notifications for a user with optional unread filter and pagination.

    Args:
        db: SQLAlchemy session
        user_id: Supabase user id (UUID string)
        unread_only: If true, only return notifications where read_at is null
        page: 1-based page number
        page_size: number of items per page

    Returns:
        (items, total_count)
    """
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.read_at.is_(None))
    total = db.execute(
        select(func.count()).select_from(q.subquery())
    ).scalar_one()
    q = q.order_by(Notification.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(q).scalars().all()
    return items, total


# PUBLIC_INTERFACE
def mark_read(db: Session, notif_id: int, user_id: str) -> Optional[Notification]:
    """Mark a notification as read for the given user.

    Args:
        db: session
        notif_id: notification id
        user_id: owner user id

    Returns:
        Updated notification or None if not found/unauthorized
    """
    notif = db.get(Notification, notif_id)
    if not notif or notif.user_id != user_id:
        return None
    if notif.read_at is None:
        notif.read_at = _utcnow()
        db.add(notif)
        db.commit()
        db.refresh(notif)
    return notif


# PUBLIC_INTERFACE
def create_notification(db: Session, payload: NotificationCreate, mark_sent_if_past: bool = True) -> Notification:
    """Create a new notification row.

    If scheduled_at <= now and channel is in_app, mark sent_at now.
    """
    notif = Notification(
        user_id=payload.user_id,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        channel=payload.channel or "in_app",
        scheduled_at=payload.scheduled_at,
        metadata=payload.metadata or {},
    )
    now = _utcnow()
    if mark_sent_if_past and (notif.scheduled_at is None or notif.scheduled_at <= now):
        notif.sent_at = now
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


# PUBLIC_INTERFACE
def materialize_due_reminders(db: Session, now: Optional[datetime] = None) -> int:
    """Materialize due reminders into Notification rows.

    This is a stub that demonstrates how workout schedules or bookings could create notifications.
    For now, it simply marks existing scheduled notifications whose scheduled_at <= now and sent_at is null as sent.

    Returns:
        number of notifications materialized/updated
    """
    if now is None:
        now = _utcnow()
    q = select(Notification).where(
        and_(Notification.scheduled_at.is_not(None), Notification.scheduled_at <= now, Notification.sent_at.is_(None))
    )
    items: List[Notification] = db.execute(q).scalars().all()
    count = 0
    for notif in items:
        notif.sent_at = now
        db.add(notif)
        count += 1
    if count:
        db.commit()
    return count
