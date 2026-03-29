# Agent Instructions

This repository is a **FastAPI Backend Boilerplate** with a clean, layered architecture. It serves as a strong foundation for developing scalable RESTful APIs backed by a generic relational database.

## 🎯 Primary Directives
- **Relational DB Agnostic**: The system is designed for **any** relational database supported by SQLAlchemy (e.g., PostgreSQL, MySQL, SQLite). **Do NOT write dialect-specific logic, raw database queries, or couple the code to a specific database engine (like MySQL)** unless explicitly instructed by the user. Rely entirely on standard, generic SQLAlchemy ORM constructs.
- **Maintain Boilerplate Principles**: Keep features generalized and highly reusable. Do not over-engineer or add hyper-specific domain complexities unless requested. The focus remains on cleanly separated, easily testable layers suitable for any domain.

## 🏗 Architecture & Separation of Concerns

The boilerplate enforces a strict layered architecture. Follow these rules when modifying or adding features:

1. **`app/api/` (Routers / Controllers)**
   - Responsible for HTTP routing, request parsing, and response formatting.
   - Depends **only** on components in `services` via FastAPI dependency injection (`Depends`).
   - Must contain **no** business logic or database queries.

2. **`app/services/` (Business Logic)**
   - Core application logic, calculations, and rules live here.
   - Depends entirely on `repositories` to perform data operations.
   - Must be completely decoupled from HTTP request objects, HTTP exceptions, and database session lifecycles.

3. **`app/repositories/` (Data Access Layer)**
   - The primary abstraction over the database. Handles data retrieval, insertion, and manipulation via SQLAlchemy.
   - Initializes with a database `Session` (provided by the generator in `app/core/db.py`).
   - Shields `services` from direct SQLAlchemy details.

4. **`app/tables/` (ORM Models)**
   - SQLAlchemy Declarative Base classes mapped to generic relational database tables.
   - Use standard SQLAlchemy data types (`Integer`, `String`, `DateTime`, `Boolean`, etc.) and generic relationships. Avoid DB-specific dialect types (e.g., `sqlalchemy.dialects.mysql`) to maintain db-agnosticism.

5. **`app/dtos/` (Data Transfer Objects)**
   - Pydantic v2 schemas used for API request validation, response serialization, and internal data transfer across layers.
   - Do not leak SQLAlchemy models (`app/tables/`) directly into API responses; map them to `dtos` first.

6. **`app/core/` (Configurations & Infra)**
   - Database connection management (e.g., the `get_db()` session generator).
   - Application configurations (`BaseSettings` populated from environment variables/`.env`).
   - Reusable infrastructure primitives (security, JWT config, hashing).

## 🧑‍💻 Coding Conventions
- **Database Sessions**: Use the `get_db()` dependency generator from `app/core/db.py`. Do not manually open/close connections deep inside services. Pass the session context explicitly to repositories.
- **Dependency Injection**: Utilize FastAPI's `Depends` as much as possible for loose coupling. Inject repositories into services, and services into routers.
- **Validation**: Enforce strict typing in Pydantic. Prefer Pydantic's built-in field validation decorators over manual python validation checks where appropriate.
- **Type Hinting**: All functions, classes, and return types must be completely and accurately type-hinted.

## 🚀 Workflow for Adding New Features
When instructed by a user to add a new entity or feature, systematically execute these steps:

1. **Model**: Define the relational schema in `app/tables/`.
2. **Schema**: Define the request/response Pydantic models in `app/dtos/`.
3. **Data Access**: Create database methods in a new class inside `app/repositories/`.
4. **Logic**: Implement the underlying business workflow in `app/services/`.
5. **Endpoints**: Expose the API routes in `app/api/` using dependency injection to consume the service.
6. **Registration**: Ensure the new sub-router is registered in `app/main.py`.
