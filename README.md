# FastAPI Scalable Backend Boilerplate

This boilerplate takes inspiration from real-world backend architectures to provide a highly maintainable structure that enforces a clean separation of concerns without falling into over-engineered "clean architecture" traps. It embraces pragmatism by offering tools for both ORM operations and optimized raw SQL.

## Architecture & Layers
This project follows a pragmatic 3-tier structure (`API -> Service -> Repository`).

```text
app/
├── api/             # API layer. Only deals with HTTP, parsing requests, and routing.
│   ├── decorators.py# Reusable auth and rate-limiting wrappers (@authenticated)
│   ├── deps.py      # FastAPI Dependency Injection (get_db, current_user, etc)
│   └── routers/     # HTTP API Endpoints (e.g., auth, health)
├── core/            # App-wide foundational systems and configurations.
│   ├── config.py    # Environment variables mapping (Settings)
│   ├── constants.py # Global Enums and Strings (Roles, Environments, QueryResult)
│   ├── db.py        # SQLAlchemy engine and session generation
│   ├── exceptions.py# Standardized HTTP Error hierarchy
│   ├── middlewares.py # Global interceptors (Exceptions, Rate Limits, Guest Cookies, CORS)
│   ├── security.py  # Password hashing and JWT encoding/decoding
│   ├── sql_helpers.py # Generic utilities for bulk_inserts and raw SQL execution
│   └── utils.py     # Background helpers (Emails, S3 uploads, limiters)
├── dtos/            # Pydantic schemas (Data Transfer Objects for network payloads)
├── repositories/    # Data Access Layer. Exclusively handles DB queries (ORM & Raw SQL)
├── services/        # Business Logic Layer. Orchestrates repos and contains core domain logic
└── tables/          # SQLAlchemy ORM entities (Database Model definitions)
```

## Key Capabilities

### Data Access (ORM & Raw SQL)
The boilerplate contains robust data access patterns. Inside the `UserRepository`, you'll find side-by-side examples demonstrating both:
1. **ORM Execution:** Standard SQLAlchemy `.filter()` queries and `bulk_insert` helpers.
2. **Raw SQL Helper:** An injected utility (`execute_raw_query`) that natively handles tuple-packing for `IN` clauses, standardizes output types (Dictionaries, Scalars, Lists) via `QueryResult` enums, and seamlessly corrects localized database time objects formatting issues.

### Naming Conventions
To eliminate the ambiguity of having `User` represent both a database schema and a validation schema:
- **`app/tables/`**: Suffixed with `Table` (e.g., `UserTable`). These are pure SQLAlchemy database mapped objects.
- **`app/dtos/`**: Suffixed with `Dto` (e.g., `UserRegisterDto`, `UserResponseDto`). These are pure Pydantic validation objects tracking network ingress/egress.

### Included Middlewares & Decorators
- **Middlewares**: Custom standardized HTTP Exception Catchers ensuring 500-level tracebacks are handled gracefully, `GuestCookieMiddleware` to assign unique tokens for untracked browsers, and full `SlowAPI` rate-limiting configs.
- **Decorators**: Found in `app/api/decorators.py`, you can bypass native `Depends` workflows and wrap endpoints in `@authenticated(roles=[...])`, `@optional_authentication()`, or `@rate_limit("10/minute")`. 

---

## Testing Patterns

The testing framework leverages `pytest` and the `FastAPI TestClient`.
The included `tests/conftest.py` configures a highly stable testing environment by intercepting the `get_db` FastAPI Dependency and replacing it with a transactional SQLite `db_session` fixture that auto-creates and auto-drops your tables before and after execution.

The boilerplate showcases three types of tests:
- **E2E API Tests (`test_auth_api.py`)**: Fires full `TestClient` HTTP requests ensuring cookies are attached and routers map to logic gracefully.
- **Repository Tests (`test_user_repository.py`)**: Tests raw SQL vs ORM mapping behavior dynamically connecting to the `db_session`.
- **Isolated Service Tests (`test_auth_service.py`)**: Pure Python testing by injecting a mock Repository inside the Service constructor to instantly validate internal logic (like throwing `ConflictExceptions`) without a database connection.

---

## Quick Start

### 1. Setup Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Setup Secrets
Copy `.env.example` to `.env` and fill out your specific values.

### 4. Run Development Server
```bash
# Starts the server via uvicorn wrapper
fastapi dev app/main.py
```

### Run Tests
Make sure the environment can find the `app` module by running pytest from the root:
```bash
# Windows
$env:PYTHONPATH='.'; pytest tests/

# Linux/Mac
PYTHONPATH='.' pytest tests/
```

### Run with Docker Compose
```bash
docker-compose up --build
```
