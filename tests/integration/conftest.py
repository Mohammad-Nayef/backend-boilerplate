import os
import re
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

import app.infrastructure.tables  # noqa: F401
from app.api.dependencies import get_email_sender
from app.infrastructure.db import Base, get_db
from app.infrastructure.email import OutboundEmail
from app.main import app

DEFAULT_TEST_PASSWORD = "Password123!"
DEFAULT_TEST_FULL_NAME = "Test User"
CODE_PATTERN = re.compile(r"code:\s*(\d{4})", re.IGNORECASE)


class RecordingEmailSender:
    def __init__(self):
        self.sent: list[OutboundEmail] = []

    def send(self, email: OutboundEmail) -> None:
        self.sent.append(email)


def extract_code_from_email(email: OutboundEmail) -> str:
    match = CODE_PATTERN.search(email.text_body)
    if not match:
        raise AssertionError(f"Could not find code in email body: {email.text_body}")
    return match.group(1)


@pytest.fixture(scope="session")
def postgres_engine():
    with PostgresContainer("postgres:15", dbname="test_db") as postgres:
        database_url = postgres.get_connection_url(driver="pg8000")
        engine = create_engine(database_url)
        Base.metadata.create_all(bind=engine)
        yield engine
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(postgres_engine):
    connection = postgres_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def recording_email_sender():
    return RecordingEmailSender()


@pytest.fixture(scope="function")
def client(db_session, recording_email_sender):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_sender] = lambda: recording_email_sender
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()
