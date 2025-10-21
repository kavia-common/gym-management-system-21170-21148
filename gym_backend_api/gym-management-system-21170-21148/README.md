# gym-management-system-21170-21148

Backend supports Google Sign-In (OAuth and One Tap). Configure in `gym_backend_api/.env`:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_OAUTH_REDIRECT_URI (e.g., http://localhost:3001/api/v1/auth/google/callback)
See backend README for full setup and endpoints.

This repository contains a full-stack gym management system. The backend is built with FastAPI and includes a database layer using SQLAlchemy with an SQLite default and optional PostgreSQL support.

## Backend: API Overview

- Base URL: `http://localhost:3001`
- API prefix: `/api/v1`
- OpenAPI docs: `http://localhost:3001/docs`
- Health check (readiness): `GET /healthz` returns `{"status":"ok"}`

### Domains
- Auth: `/api/v1/auth/*` (signup, login, refresh, logout, me)
- Memberships: `/api/v1/memberships/*` (plans CRUD [admin], subscribe/cancel/current)
- Classes: `/api/v1/classes/*` (classes CRUD, sessions CRUD/list)
- Trainers: `/api/v1/trainers/*` (trainers CRUD, availability)
- Bookings: `/api/v1/bookings/*` (class/trainer bookings)
- Payments: `/api/v1/payments/*` (create session, confirm [TEST_MODE], stripe webhook stub)

## Supabase JWT Authentication (Backend)

The backend can validate Supabase-issued JWTs using the JWKS from your Supabase project.

- Required environment variable:
  - SUPABASE_URL (e.g., https://your-project.supabase.co)

At startup, the app ensures SUPABASE_URL is set. Incoming requests can use Authorization: Bearer <supabase-access-token>. The dependency will:

- Fetch JWKS from `${SUPABASE_URL}/auth/v1/keys` and cache it with TTL.
- Verify signature and standard claims (issuer; audience if present).
- Expose claims (including `sub` and `email` if present).

Usage in routes:
- Import the dependency alias: `from src.dependencies import auth_required`
- Add to route parameters: `claims: dict = Depends(auth_required)`
- `claims["sub"]` is the Supabase user id (UUID). `claims.get("email")` may be present.

Note: Existing username/password endpoints remain for the local user system. You can migrate protected routes to Supabase by switching dependency from `get_current_user` to `auth_required`.

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
- SUPABASE_URL=https://your-project.supabase.co  <-- required for Supabase JWT validation

#### Google Sign-In (OAuth and One Tap)
To enable Google authentication:

1. In Google Cloud Console, create OAuth 2.0 Client ID (Web application).
2. Authorized JavaScript origins: include your frontend URL(s), e.g.
   - http://localhost:3000
3. Authorized redirect URIs: include your backend callback URL, e.g.
   - http://localhost:3001/api/v1/auth/google/callback
4. Set the env vars in `gym_backend_api/.env`:
   - GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   - GOOGLE_CLIENT_SECRET=your_client_secret
   - GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3001/api/v1/auth/google/callback

Endpoints:
- GET /api/v1/auth/google/login
  - Returns { authorization_url } to redirect the user to Google.
- GET /api/v1/auth/google/callback?code=...
  - Server-side exchange of code for tokens, verifies the ID token, finds/creates user, then returns app tokens.
- POST /api/v1/auth/google/one-tap
  - Body: { "credential": "<Google ID token from GIS>" }
  - Verifies token and returns app tokens.

Notes:
- We use google-auth to verify ID tokens and validate audience equals your GOOGLE_CLIENT_ID and email_verified is true.
- A local user is created by email if none exists, with role=member and a generated password hash (not used for Google login).
- The app issues access and refresh JWTs using existing security utilities.

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
   - In `gym_backend_api/requirements.txt`, SQLAlchemy, Alembic, psycopg[binary], passlib[bcrypt], PyJWT, stripe, python-jose[cryptography], httpx are included.
2. Create `.env` in `gym_backend_api` (copy from `.env.example`).
3. Start the backend using one of:
   - `python -m src.api` (recommended; binds 0.0.0.0 and port from API_PORT)
   - `uvicorn src.api.main:app --host 0.0.0.0 --port 3001`

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
- Run entry: `python -m src.api` -> `src/api/__main__.py`
- Routers: `gym_backend_api/src/api/routers/*`
- Settings: `gym_backend_api/src/core/config.py`
- Security: `gym_backend_api/src/core/security.py`
- Services: `gym_backend_api/src/services/*`
- Schemas: `gym_backend_api/src/schemas/*`
- Database session and engine: `gym_backend_api/src/db/session.py`
- Models: `gym_backend_api/src/db/models.py`
- Exports: `gym_backend_api/src/db/__init__.py`

These modules are designed to be import-safe and not disrupt existing app startup.
