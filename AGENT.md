# Agent Instructions

This repository is a **FastAPI Backend Boilerplate** with a clean, layered architecture. It serves as a strong foundation for developing scalable RESTful APIs backed by a generic relational database.

## 🎯 Primary Directives

- **Database Agnostic Core**: The system is designed for **any** relational database supported by SQLAlchemy. **Never write raw, dialect-specific SQL (like MySQL syntax)** unless absolutely necessary. Rely on standard, generic SQLAlchemy ORM constructs to ensure portability.
- **Maintain Boilerplate Principles**: Keep features generalized and highly reusable. Avoid over-engineering or introducing hyper-specific domain complexities unless requested. Focus on clean separation and testable layers.

## 🏗 Architecture & Separation of Concerns

Follow these layering rules strictly:

1. **`app/api/` (Presentation)**
   - Responsible for HTTP routing, request parsing, and response formatting.
   - Depends **only** on `services` via FastAPI dependency injection.
   - Must contain **no** business logic or raw database access.

2. **`app/services/` (Business Logic)**
   - Core application logic lives here. Orchestrates domain workflows.
   - Depends exclusively on `repositories`.
   - Must be decoupled from HTTP objects, HTTP exceptions, and database session lifecycles.

3. **`app/repositories/` (Data Access Layer)**
   - The primary abstraction over the database.
   - Handles ORM queries and localized raw SQL using provided helpers in `app/core/sql_helpers`.
   - Shields `services` from direct SQLAlchemy session management.

4. **`app/tables/` (Relational Models)**
   - SQLAlchemy Declarative Base entities. Mapping tables to Python objects.
   - Suffixed with `Table`.

5. **`app/models/` (Data Models)**
   - Pydantic v2 schemas used for API validation and internal data transfer.
   - Suffixed with `Dto`. Never leak `tables` directly into API responses; map them to `models` first.

6. **`app/core/` (Infrastructure)**
   - Contains cross-cutting systems: Database engine, security (JWT), app settings, and shared utilities.

---

## 🧑‍💻 Coding Conventions
- **Database Sessions**: Always use the `get_db()` generator from `app/core/db.py`. Do not manually open/close connections. Use `DbSession` annotation from `app/api/dependencies.py` for repository injections.
- **Dependency Injection**: Utilize FastAPI's `Depends()` at all levels (Routers -> Services -> Repositories).
- **Validation**: Enforce strict typing via Pydantic. Use `ConfigDict(from_attributes=True)` in response DTOs to allow entity mapping.

---

## 🚀 Testing Rules
This project uses **Testcontainers (PostgreSQL)** for all integration tests.
- **Global Table Management**: Handled in `tests/conftest.py` via `postgres_engine`. Tables are created once per session.
- **Transactional Rollbacks**: `db_session` uses transactions and rollbacks after every test function. **Do not use `drop_all()` in individual tests**; rely on the rollback pattern to maintain speed and isolation.
- **Discovery**: Ensure `tests/__init__.py` exists and `conftest.py` contains the `sys.path` injection to allow VS Code discovery to resolve the `app` module.

---

## 🚀 Workflow for Adding Features
1. **Model**: Define the schema in `app/tables/`.
2. **Schema**: Define the request/response models in `app/models/`.
3. **Data Access**: Implement DB actions in `app/repositories/`.
4. **Logic**: Build the domain service in `app/services/`.
5. **Endpoints**: Expose routes in `app/api/routers/` using dependency injection.
6. **Registration**: Ensure the router is registered in `app/main.py`.
