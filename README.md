# Backend Boilerplate

FastAPI backend boilerplate for teams that want clean layering, predictable conventions, and production-oriented defaults.

## Scope

This boilerplate includes:

- Email/password registration and login with JWT in HTTP-only cookies
- Email verification, resend code, forgot password, verify reset code, and reset password flows
- Route-level authentication decorators and dependency-based current-user resolution
- Layered architecture with routers, services, repositories, SQLAlchemy tables, and shared schemas
- Alembic-based schema evolution workflow
- Rate limiting with composable identity keys for auth-sensitive routes
- Integration and unit test setup using Testcontainers + transaction rollback isolation

## Runtime Notes

- On startup, the app validates database connectivity with a lightweight `SELECT 1` check.
- Schema is not auto-created at runtime; use Alembic migrations.
- CORS origins are read from `ALLOWED_ORIGINS`, and credentials are enabled.
- `POST /api/auth/register` creates an inactive user and sends a 4-digit verification code.
- `POST /api/auth/login` sets an HTTP-only cookie named `token`.
- Verification and reset codes are 4 digits, expire after `AUTH_CODE_EXPIRE_MINUTES`, and only the latest code is valid.
- Password reset is a two-step flow: verify code first, then reset using a short-lived reset token.
- Protected routes rely on the auth cookie and active-user checks.
- Default limiter is `10` requests per second per IP outside pytest.
- Auth routes use tighter limits and can compose keys like `IP + EMAIL` or `IP + RESET_TOKEN`.

## Configuration

Copy `.env.example` to `.env` and update values.

Required settings:

- `ENVIRONMENT`
- `DEBUG`
- `ALLOWED_ORIGINS`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `ISOLATION_LEVEL`
- `DB_POOL_SIZE`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_DAYS`
- `AUTH_CODE_EXPIRE_MINUTES`
- `PASSWORD_RESET_SESSION_EXPIRE_MINUTES`

Optional email settings:

- `EMAIL_FROM_ADDRESS`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`

## Project Structure

- `app/api/` handles HTTP routing and dependency wiring.
- `app/services/` contains business workflows.
- `app/infrastructure/repositories/` contains data access.
- `app/infrastructure/tables/` defines SQLAlchemy tables.
- `app/common/models/` defines request and response schemas.
- `app/infrastructure/alembic/` contains migration config and revisions.

## Local Run

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
Copy-Item .env.example .env
$env:PYTHONPATH='.'
alembic upgrade head
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

## Database Migrations

- Use Alembic for every schema change.
- Create a revision with `alembic revision --autogenerate -m "describe change"`.
- Keep revisions under `app/infrastructure/alembic/versions/`.
- Review generated revisions before applying.
- Apply latest schema with `alembic upgrade head`.

## Tests

```powershell
$env:PYTHONPATH='.'
pytest -m unit
pytest -m integration
pytest -m migration
```

- Integration tests run against PostgreSQL Testcontainers.
- Test isolation uses transaction rollback per test.
- Migration tests validate Alembic upgrades on a clean database.

## Auth Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification-code`
- `POST /api/auth/forgot-password`
- `POST /api/auth/verify-reset-code`
- `POST /api/auth/reset-password`
