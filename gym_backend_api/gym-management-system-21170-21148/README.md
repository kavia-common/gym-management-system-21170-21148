# gym-management-system-21170-21148

This repository contains a full-stack gym management system. The backend is built with FastAPI and includes a database layer using SQLAlchemy with an SQLite default and optional PostgreSQL support.

## Backend: API Overview

- Base URL: `http://localhost:3001`
- API prefix: `/api/v1`
- OpenAPI docs: `http://localhost:3001/docs`
- Health check: `GET /`

### Domains
- Auth: `/api/v1/auth/*` (signup, login, refresh, logout, me)
- Memberships: `/api/v1/memberships/*` (plans CRUD [admin], subscribe/cancel/current)
- Classes: `/api/v1/classes/*` (classes CRUD, sessions CRUD/list)
- Trainers: `/api/v1/trainers/*` (trainers CRUD, availability)
- Bookings: `/api/v1/bookings/*` (class/trainer bookings)
- Payments: `/api/v1/payments/*` (create session, confirm [TEST_MODE], stripe webhook stub)

## Backend: Database Setup

- Default: SQLite (no external service required). A local `app.db` file will be created in the `gym_backend_api` directory.
- Optional: PostgreSQL using `psycopg`.

### Environment Variables

Copy `.env.example` to `.env` inside `gym_backend_api` and adjust values as needed:

- APP_ENV=development
- API_PORT=3001
- FRONTEND_URL=http://localhost:3000
- CORS_ALLOW_ORIGINS=http://localhost:3000
  - Tip: Add preview domains if applicable, e.g.
    `CORS_ALLOW_ORIGINS=http://localhost:3000,https://*.beta01.cloud.kavia.ai,https://*.vercel.app`
- SECRET_KEY=change_me
- ACCESS_TOKEN_EXPIRE_MINUTES=60
- REFRESH_TOKEN_EXPIRE_DAYS=7
- TEST_MODE=true
  - When true and no Stripe keys are provided, payment flows use mock sessions and simplified confirms.
- DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/gymdb
- DATABASE_URL_SQLITE=sqlite:///./app.db
- DB_ECHO=false
- PAYMENT_PROVIDER=stripe
- STRIPE_SECRET_KEY=sk_test_xxx
- STRIPE_WEBHOOK_SECRET=whsec_xxx
- CURRENCY=usd

Notes:
- If `DATABASE_URL` is not set, the backend falls back to `DATABASE_URL_SQLITE` (defaults to `sqlite:///./app.db`).
- When `APP_ENV=development` or `TEST_MODE=true`, tables are auto-created at startup, so you can run locally without manual migrations.

### Regenerate OpenAPI
To regenerate the OpenAPI schema after modifying routes, run from the `gym_backend_api` folder:
```
python -m src.api.generate_openapi
```
This writes to `interfaces/openapi.json`.

### Running the Backend with SQLite (default)

1. Ensure dependencies are installed:
   - In `gym_backend_api/requirements.txt`, SQLAlchemy, Alembic, psycopg[binary], passlib[bcrypt], PyJWT, stripe are included.
2. Create `.env` in `gym_backend_api` (copy from `.env.example`).
3. Start the backend (e.g., via `uvicorn src.api.main:app --host 0.0.0.0 --port 3001` or your existing run command).

You should see a local `app.db` created upon first start. OpenAPI docs: `http://localhost:3001/docs`.

### Switching to PostgreSQL

1. Set `DATABASE_URL` in `.env`, for example:
   ```
   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/gymdb
   ```
2. Ensure your Postgres server is running and the database exists.
3. Restart the backend; it will connect to Postgres. If running in development/TEST_MODE, tables are auto-created.

### Migrations (Optional)

Alembic is included in the dependencies for future schema migrations. You can initialize Alembic later:
```
alembic init alembic
```
Then configure the `sqlalchemy.url` in `alembic.ini` or load from environment.

## Code Pointers

- App entry: `gym_backend_api/src/api/main.py`
- Routers: `gym_backend_api/src/api/routers/*`
- Settings: `gym_backend_api/src/core/config.py`
- Security: `gym_backend_api/src/core/security.py`
- Services: `gym_backend_api/src/services/*`
- Schemas: `gym_backend_api/src/schemas/*`
- Database session and engine: `gym_backend_api/src/db/session.py`
- Models: `gym_backend_api/src/db/models.py`
- Exports: `gym_backend_api/src/db/__init__.py`

These modules are designed to be import-safe and not disrupt existing app startup.
