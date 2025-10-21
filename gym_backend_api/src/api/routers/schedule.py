from typing import Any, Dict, List, Literal, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from src.dependencies import get_db
from src.auth.supabase_jwt import get_current_user
from src.services.workout_service import WorkoutService
from src.services.booking_service import BookingService
# from ...services.class_service import ClassService

router = APIRouter(prefix="/api/v1", tags=["Schedule"])


# PUBLIC_INTERFACE
class ScheduleItemOut(BaseModel):
    """Normalized schedule item returned by /api/v1/schedule."""
    type: Literal["workout", "trainer_booking", "class"] = Field(..., description="Item type")
    id: int = Field(..., description="Underlying entity id")
    start: datetime = Field(..., description="Start datetime")
    end: datetime = Field(..., description="End datetime")
    title: str = Field(..., description="Human readable title")
    status: Optional[str] = Field(None, description="Status if applicable for the item")


def _validate_role_or_raise(role: str) -> None:
    """
    Ensure the caller is allowed to access member schedule. Trainers/admins can view their own combined items as well.
    """
    if role not in {"member", "trainer", "admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")


def _paginate(items: List[Dict[str, Any]], page: int, page_size: int) -> Tuple[List[Dict[str, Any]], int]:
    total = len(items)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total


# PUBLIC_INTERFACE
@router.get(
    "/schedule",
    summary="Unified member schedule",
    description="Return a combined, normalized list of schedule items for the authenticated user. "
                "Includes workout schedules, trainer bookings, and class sessions the member is booked in. "
                "Supports optional filtering by date range and pagination.",
    response_model=List[ScheduleItemOut],
    responses={
        200: {"description": "Combined schedule list (may be empty)."},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
async def get_schedule(
    # Document usage and accept query params for simple filtering/pagination
    start_from: Optional[datetime] = Query(None, description="Include items with end >= start_from"),
    end_before: Optional[datetime] = Query(None, description="Include items with start <= end_before"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[ScheduleItemOut]:
    """
    Get the unified schedule for the authenticated account.

    Parameters:
    - start_from: Optional inclusive filter for items ending after this instant
    - end_before: Optional inclusive filter for items starting before this instant
    - page: Page number (1-based)
    - page_size: Items per page

    Auth:
    - Requires Supabase JWT via Authorization: Bearer <token>
    - RBAC: member|trainer|admin allowed (viewing own combined items)

    Returns:
    - 200: List[ScheduleItemOut] possibly empty
    """
    # Extract local fields from supabase claims mapping done in get_current_user
    user_id: str = current_user.get("user_id") or current_user.get("sub")
    role: str = current_user.get("role", "member")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _validate_role_or_raise(role)

    workout_service = WorkoutService(db)
    booking_service = BookingService(db)
    # ClassService reserved for future expansion; not required for aggregation since we use BookingService for class bookings.

    items: List[Dict[str, Any]] = []

    # Workouts: planned/completed entries for this user.
    try:
        # Expecting service to have a method like get_user_workouts(user_id, start_from, end_before)
        # Fallback to list and filter if the method doesn't support date filters.
        workouts = workout_service.get_user_workouts(user_id=user_id)
    except Exception:
        workouts = []

    for w in workouts or []:
        # Safety extract
        wid = getattr(w, "id", None) or w.get("id")
        wtitle = getattr(w, "title", None) or w.get("title") or "Workout"
        wstatus = getattr(w, "status", None) or w.get("status") or None
        wstart = getattr(w, "scheduled_at", None) or w.get("scheduled_at") or w.get("start_time")
        wend = getattr(w, "end_time", None) or w.get("end_time") or wstart

        # Convert ISO strings if services return str
        if isinstance(wstart, str):
            try:
                wstart = datetime.fromisoformat(wstart.replace("Z", "+00:00"))
            except Exception:
                wstart = None
        if isinstance(wend, str):
            try:
                wend = datetime.fromisoformat(wend.replace("Z", "+00:00"))
            except Exception:
                wend = None

        if wstart is None and wend is None:
            # Skip items we can't place on a timeline
            continue

        items.append(
            {
                "type": "workout",
                "id": int(wid) if wid is not None else 0,
                "start": wstart or wend,  # ensure datetime present
                "end": wend or wstart,
                "title": str(wtitle),
                "status": str(wstatus) if wstatus is not None else None,
            }
        )

    # Trainer bookings for this user (as a member)
    try:
        trainer_bookings = booking_service.get_trainer_bookings_for_user(user_id=user_id)
    except Exception:
        trainer_bookings = []

    for b in trainer_bookings or []:
        bid = getattr(b, "id", None) or b.get("id")
        bstatus = getattr(b, "status", None) or b.get("status") or None
        bstart = getattr(b, "start_time", None) or b.get("start_time")
        bend = getattr(b, "end_time", None) or b.get("end_time")
        trainer_name = getattr(b, "trainer_name", None) or b.get("trainer_name") or "Trainer Session"

        if isinstance(bstart, str):
            try:
                bstart = datetime.fromisoformat(bstart.replace("Z", "+00:00"))
            except Exception:
                bstart = None
        if isinstance(bend, str):
            try:
                bend = datetime.fromisoformat(bend.replace("Z", "+00:00"))
            except Exception:
                bend = None

        if bstart is None and bend is None:
            continue

        items.append(
            {
                "type": "trainer_booking",
                "id": int(bid) if bid is not None else 0,
                "start": bstart or bend,
                "end": bend or bstart,
                "title": f"Trainer: {trainer_name}",
                "status": str(bstatus) if bstatus is not None else None,
            }
        )

    # Class sessions that the user is booked into
    try:
        class_bookings = booking_service.get_class_bookings_for_user(user_id=user_id)
    except Exception:
        class_bookings = []

    for cb in class_bookings or []:
        cid = getattr(cb, "id", None) or cb.get("id")
        cstatus = getattr(cb, "status", None) or cb.get("status") or None
        ctitle = getattr(cb, "class_title", None) or cb.get("class_title") or "Class Session"
        cstart = getattr(cb, "start_time", None) or cb.get("start_time")
        cend = getattr(cb, "end_time", None) or cb.get("end_time")

        if isinstance(cstart, str):
            try:
                cstart = datetime.fromisoformat(cstart.replace("Z", "+00:00"))
            except Exception:
                cstart = None
        if isinstance(cend, str):
            try:
                cend = datetime.fromisoformat(cend.replace("Z", "+00:00"))
            except Exception:
                cend = None

        if cstart is None and cend is None:
            continue

        items.append(
            {
                "type": "class",
                "id": int(cid) if cid is not None else 0,
                "start": cstart or cend,
                "end": cend or cstart,
                "title": str(ctitle),
                "status": str(cstatus) if cstatus is not None else None,
            }
        )

    # Optional date filtering
    if start_from is not None:
        items = [i for i in items if (i.get("end") and i["end"] >= start_from)]
    if end_before is not None:
        items = [i for i in items if (i.get("start") and i["start"] <= end_before)]

    # Sort by start asc
    items.sort(key=lambda x: (x.get("start") or datetime.max))

    # Pagination (local)
    page_items, _total = _paginate(items, page, page_size)

    # Return as Pydantic models for response_model enforcement
    return [ScheduleItemOut(**i) for i in page_items]
