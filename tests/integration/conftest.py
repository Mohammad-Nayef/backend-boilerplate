import os
import sys
# Force VS Code / Pytest to recognize the top-level repo path regardless of where it starts from
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from unittest.mock import patch

from app.main import app
from app.infrastructure.db import Base, get_db

@pytest.fixture(scope="session")
def postgres_engine():
    """Provides a global Postgres engine initialized via Testcontainers."""
    with PostgresContainer("postgres:15", dbname="test_db") as postgres:
        db_url = postgres.get_connection_url(driver="pg8000")
        engine = create_engine(db_url)
        # Create tables once per session
        Base.metadata.create_all(bind=engine)
        yield engine
        # Drop tables at the end of the test session
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(postgres_engine):
    """Provides a fresh database session for a test. Rolls back after each test."""
    # Connect and begin a transaction
    connection = postgres_engine.connect()
    transaction = connection.begin()
    
    # Bind the session to the transaction
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Roll back the transaction to ensure pristine state for the next test
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def mock_email_service():
    """Mocks the core email utility to prevent real network calls during tests."""
    with patch("app.common.utils.send_email") as mock_mail:
        yield mock_mail

@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient with the DB dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()
