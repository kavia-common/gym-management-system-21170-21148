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
allow_origins = settings.cors_origins()
# Include Kavia/Vercel-style preview wildcard note:
# If you deploy previews on custom subdomains, set CORS_ALLOW_ORIGINS to a comma-separated list.
# Example:
# CORS_ALLOW_ORIGINS=http://localhost:3000,https://*.beta01.cloud.kavia.ai,https://*.vercel.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
