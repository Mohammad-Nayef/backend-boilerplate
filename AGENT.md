# Agent Instructions

FastAPI backend boilerplate using layered architecture: Routers -> Services -> Repositories -> Tables.

## Core Directives
- **Layers**: Keep routing, business rules, and persistence strictly separated.
- **Portability**: Use standard SQLAlchemy and generic SQL where possible.
- **Schema**: Use Alembic for all schema changes (`app/infrastructure/alembic/versions/`).
- **Docs**: Keep `README.md` and API flow docs in sync with code changes.

## Layering Rules
1. **`app/api/`**: Presentation only (parsing, wiring, formatting). No business logic.
2. **`app/services/`**: Business workflows, independent from FastAPI request objects.
3. **`app/infrastructure/`**: Repositories, SQLAlchemy tables, DB/runtime technical concerns.
4. **`app/common/`**: Shared schemas, constants, config, and utilities.

## Conventions
- **Validation**: Pydantic v2 for request/response models.
- **Queries**: No `SELECT *`; enumerate required columns.
- **Raw SQL helpers**: Use `sql(...)` with explicit `QueryResult` types.
- **Auth style**: Use HTTP-only cookie token auth for protected routes.
- **Rate limits**: Prefer composable key strategies for auth endpoints (IP + email/token).

## Testing & Verification
- Use **pytest** markers (`unit`, `integration`, `migration`).
- Keep integration tests isolated through transaction rollback fixtures.
- Add tests for all behavior changes, including auth edge cases.
- Validate Alembic migration upgrades when schema changes are introduced.

## Change Workflow
1. Update table models and request/response schemas.
2. Add or update Alembic revisions.
3. Update repositories, then services, then routers.
4. Register routers in `app/main.py` and run tests.
5. Update docs and environment examples when behavior/config changes.
