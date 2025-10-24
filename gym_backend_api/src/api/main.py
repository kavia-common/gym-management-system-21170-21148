from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.api.routers import auth as auth_router
from src.api.routers import memberships as memberships_router
from src.api.routers import classes as classes_router
from src.api.routers import trainers as trainers_router
from src.api.routers import bookings as bookings_router
from src.api.routers import payments as payments_router
from src.api.routers import google_auth as google_auth_router
from src.api.routers import supabase_protected as supabase_protected_router
from src.api.routers import workouts as workouts_router  # new
from src.api.routers import progress as progress_router
from src.api.routers import notifications as notifications_router
from src.api.routers import schedule as schedule_router
from src.api.routers import demo as demo_router

# Import dependencies to ensure SUPABASE_URL is validated at startup
# and to make `auth_required` available for routers.
from src import dependencies as shared_dependencies  # noqa: F401

settings = get_settings()

openapi_tags = [
    {"name": "Auth", "description": "User authentication and token management"},
    {"name": "Memberships", "description": "Membership plans and subscriptions"},
    {"name": "Classes", "description": "Gym classes and sessions"},
    {"name": "Trainers", "description": "Trainers and availability"},
    {"name": "Bookings", "description": "Class and trainer bookings"},
    {"name": "Payments", "description": "Payment sessions and confirmations"},
    {"name": "Workouts", "description": "Exercises, templates, and training programs"},
    {"name": "Progress", "description": "Exercise logs and body metrics tracking"},
    {"name": "Notifications", "description": "In-app notifications and reminders"},
    {"name": "Schedule", "description": "Unified per-user schedule"},
]

app = FastAPI(
    title="Gym Management API",
    description="Backend API for a gym management system (memberships, classes, trainers, bookings, payments, progress tracking).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS setup
# Ensure Authorization header is allowed and include frontend origin.
# You can configure CORS origins via env (see src/core/config.get_settings().cors_origins()).
# Example:
# CORS_ALLOW_ORIGINS=http://localhost:3000,https://*.beta01.cloud.kavia.ai,https://*.vercel.app
allow_origins = settings.cors_origins() or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    # Explicitly allow Authorization header used by the frontend
    allow_headers=["*"],
)


@app.get("/", tags=["Auth"], summary="Health Check", description="Return basic health status.")
def health_check():
    return {"message": "Healthy", "env": settings.APP_ENV}


# Mount routers under /api/v1
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(memberships_router.router, prefix="/api/v1")
app.include_router(classes_router.router, prefix="/api/v1")
app.include_router(trainers_router.router, prefix="/api/v1")
app.include_router(bookings_router.router, prefix="/api/v1")
app.include_router(payments_router.router, prefix="/api/v1")
app.include_router(google_auth_router.router, prefix="/api/v1")
# Workouts router mounted at its own full prefix inside the module
app.include_router(workouts_router.router)  # workouts has prefix="/api/v1/workouts"
# Supabase-protected endpoints (JWT required via src.dependencies.auth_required)
app.include_router(supabase_protected_router.router)
# Progress tracking endpoints (exercise logs, body metrics)
app.include_router(progress_router.router)
# Notifications endpoints (in-app notifications and scheduler)
app.include_router(notifications_router.router)
# Schedule endpoint (unified per-user schedule)
app.include_router(schedule_router.router)

# Optional startup seeding when DEMO_MODE and DEMO_AUTO_SEED are enabled
@app.on_event("startup")
async def _maybe_seed_on_startup():
    import os
    if not settings.DEMO_MODE:
        return
    auto = os.getenv("DEMO_AUTO_SEED", "").strip().lower() in {"1", "true", "yes", "on"}
    if not auto:
        return
    # Run seeding using a short-lived DB session
    from src.db.session import SessionLocal
    from src.api.routers.demo import seed_demo as _seed_fn
    db = SessionLocal()
    try:
        # No authenticated user context here; will create demo users and default membership for member.demo
        _seed_fn.__wrapped__(db=db, current_user=None)  # Call underlying function bypassing dependency injection
    except Exception:
        # Best-effort: do not crash startup on seed errors
        pass
    finally:
        db.close()
# Demo endpoints (seed/reset/mock payments)
app.include_router(demo_router.router)
