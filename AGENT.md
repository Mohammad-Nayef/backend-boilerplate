# Agent Instructions

This repository is a **FastAPI Backend Boilerplate** with a clean, layered architecture. It serves as a strong foundation for developing scalable RESTful APIs backed by a generic relational database.

## 🎯 Primary Directives

- **Database Agnostic Core**: The system is designed for **any** relational database supported by SQLAlchemy. **Never write raw, dialect-specific SQL (like MySQL syntax)** unless absolutely necessary. Rely on standard, generic SQLAlchemy ORM constructs to ensure portability.
- **Maintain Boilerplate Principles**: Keep features generalized and highly reusable. Avoid over-engineering or introducing hyper-specific domain complexities unless requested. Focus on clean separation and testable layers.

## 🏗 Architecture & Separation of Concerns

Follow these layering rules strictly:

1. **`app/api/` (Presentation)**
   - Responsible for HTTP routing, request parsing, and response formatting.
   - Depends on `services` and `common`.
   - Must contain **no** business logic or raw database access.

2. **`app/services/` (Business Logic)**
   - Core application logic lives here. Orchestrates domain workflows.
   - Depends on `infrastructure` and `common`.
   - Must be decoupled from HTTP objects, HTTP exceptions, and database session lifecycles.

3. **`app/infrastructure/` (Technical Implementation)**
   - **`repositories/`**: The primary abstraction over the database. Handles ORM queries and localized raw SQL.
   - **`tables/`**: SQLAlchemy Declarative Base entities. Suffixed with `Table`.
   - **Persistence**: Database engine, session management, and technical helpers.

4. **`app/common/` (Shared Base)**
   - **`models/`**: Pydantic v2 schemas used for API validation and internal data transfer.
   - **Cross-cutting**: Generic utilities, configuration (settings), constants, and custom exceptions. All other layers can depend on this.

---

## 🧑‍💻 Coding Conventions
- **Database Sessions**: Always use the `get_db()` generator from `app/infrastructure/db.py`. Do not manually open/close connections. Use `DbSession` annotation from `app/api/dependencies.py` for repository injections.
- **Dependency Injection**: Utilize FastAPI's `Depends()` at all levels (Routers -> Services -> Infrastructure/Common).
- **Validation**: Enforce strict typing via Pydantic. Use `ConfigDict(from_attributes=True)` in response models to allow entity mapping.

---

## 🚀 Testing Rules
This project uses **Testcontainers (PostgreSQL)** for all integration tests.
- **Global Table Management**: Handled in `tests/integration/conftest.py` via `postgres_engine`. Tables are created once per session.
- **Transactional Rollbacks**: `db_session` uses transactions and rollbacks after every test function. **Do not use `drop_all()` in individual tests**; rely on the rollback pattern to maintain speed and isolation.
- **Discovery**: Ensure `tests/__init__.py` exists and `tests/integration/conftest.py` contains the `sys.path` injection to allow VS Code discovery to resolve the `app` module.

---

## 🚀 Workflow for Adding Features
1. **Model**: Define the schema in `app/infrastructure/tables/`.
2. **Schema**: Define the request/response models in `app/common/models/`.
3. **Data Access**: Implement DB actions in `app/infrastructure/repositories/`.
4. **Logic**: Build the domain service in `app/services/`.
5. **Endpoints**: Expose routes in `app/api/routers/` using dependency injection.
6. **Registration**: Ensure the router is registered in `app/main.py`.
