# FastAPI Scalable Backend Boilerplate

This boilerplate provides a highly maintainable, production-ready structure for FastAPI applications. It enforces a clean separation of concerns using a pragmatic 3-tier architecture while providing built-in tools for both ORM and optimized raw SQL performance.

## 🏗 Architecture & Layers

This project follows a strict **Layered Architecture** to ensure maintainability and testability:

```mermaid
graph TD
    API[api/ - Routers] --> Service[services/ - Logic]
    Service --> Repo[infrastructure/repositories/ - Data Access]
    Repo --> Table[infrastructure/tables/ - Entities]
    Table <--> DB[(PostgreSQL)]

    API .-> Common[common/ - Shared Utils & Models]
    Service .-> Common
    Repo .-> Common
```

### Module Responsibilities
- **`app/api/` (Presentation)**: HTTP routing, request parsing, and response formatting.
  - `dependencies.py`: FastAPI Dependency Injection (get_db, current_user, etc).
  - `decorators.py`: Advanced auth/rate-limiting wrappers.
- **`app/services/` (Business Logic)**: Orchestrates infrastructure calls and contains core domain workflows. Decoupled from HTTP objects.
- **`app/infrastructure/` (Technical implementation)**: 
  - `repositories/`: Data Access Layer. Abstraction over database operations.
  - `tables/`: Database Entities (SQLAlchemy models mapped to relational tables).
  - `db.py`, `security.py`, `sql_helpers.py`: Persistence and technical cross-cutting concerns.
- **`app/common/` (Shared Layer)**: 
  - `models/`: Pydantic v2 schemas for API validation and serialization.
  - `config.py`: Configuration management using **Pydantic Settings** (env validation, secret management).
  - `constants.py`, `exceptions.py`, `utils.py`: Generic utilities, logging setup, and error definitions that all other layers can depend on.

---

## 🛠 Features

### 1. Database Agnostic Core
The system defaults to **PostgreSQL** but remains fully compatible with MySQL or SQLite via SQLAlchemy. It uses the `pg8000` driver for efficient, pure-python communication.

### 2. High-Performance Testing
The testing suite leverages **Testcontainers** to spin up real PostgreSQL instances automatically:
- **Zero Pollution**: Every test run starts with a clean database.
- **Blazing Fast**: Uses a **Transaction Rollback** pattern. Tables are created once per session, and every individual test is rolled back upon completion, ensuring 100% independence in milliseconds.
- **Mocks Included**: Pre-configured `unittest.mock` examples for external services (like Email/S3).

### 3. Visual & Developer Experience
- **VS Code Ready**: Comprehensive `.vscode/settings.json` and `pytest.ini` ensure tests are discoverable and run immediately from the IDE.
- **Lifespan Management**: Database initialization is handled via FastAPI `lifespan`, preventing connection errors during background test discovery.
- **Built-In Auth Flow**: The boilerplate includes cookie-based JWT auth endpoints for register, login, current-user lookup, and logout.
- **Rate Limiting**: Built-in `SlowAPI` integration with guest-cookie support.
- **Protected Route Helpers**: `@authenticated()` and `get_current_user()` share the same token and active-user validation path.
- **Enhanced Health Checks**: The `/api/health-check` verify both API and Database connectivity.
- **Structured Logging**: Standardized, timestamped logging for all layers via a central utility.

---

## 🚀 Quick Start

### 1. Environment Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Secrets Management
Copy `.env.example` to `.env` and configure your database credentials.

### 3. Run Development Server
```powershell
# With auto-reload
$env:PYTHONPATH='.'; uvicorn app.main:app --reload
```

### 4. Execute Tests
```powershell
# Run unit tests (Mocks only)
$env:PYTHONPATH='.'; pytest -m unit

# Run integration tests (Uses Testcontainers)
$env:PYTHONPATH='.'; pytest -m integration
```

### 5. Running with Docker
```powershell
docker compose up -d --build
```

### Auth Endpoints
- `POST /api/auth/register` creates a user.
- `POST /api/auth/login` sets the HTTP-only `token` cookie and is rate limited more tightly than the default guest limit.
- `GET /api/auth/me` is a protected example endpoint that returns the authenticated user.
- `POST /api/auth/logout` clears the auth cookie.

---

## 🤝 Module Dependencies Summary

| Module | Level | Dependencies | Upstream Caller |
| :--- | :--- | :--- | :--- |
| **Routers** | Presentation | `Service`, `Common`, `Infrastructure` | `FastAPI` (HTTP Request) |
| **Services** | Business | `Infrastructure`, `Common` | `Routers` |
| **Infrastructure** | Technical | `Tables`, `DB`, `Common` | `Services` |
| **Common** | Shared | `Pydantic`, `SlowAPI` | All Layers |

---

## 🧑‍💻 Coding Conventions
- **Naming**: Database classes end in `Table`, Pydantic classes (Models) have no specific suffix.
- **Injection**: Always use FastAPI `Depends()` for services and repositories.
- **Exceptions**: Raise `CustomHTTPException` (from `app.common.exceptions`) in any layer; the middleware converts them to JSON responses automatically.
