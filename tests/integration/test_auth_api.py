from fastapi.testclient import TestClient
import pytest

from tests.integration.conftest import (
    DEFAULT_TEST_FULL_NAME,
    DEFAULT_TEST_PASSWORD,
    extract_code_from_email,
)


def _register(client: TestClient, email: str):
    return client.post(
        "/api/auth/register",
        json={
            "full_name": DEFAULT_TEST_FULL_NAME,
            "email": email,
            "password": DEFAULT_TEST_PASSWORD,
        },
    )


@pytest.mark.integration
def test_register_starts_verification_flow(client: TestClient, recording_email_sender):
    response = _register(client, "integration@example.com")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "integration@example.com"
    assert body["is_active"] is False
    assert len(recording_email_sender.sent) == 1


@pytest.mark.integration
def test_login_sets_cookie_and_me_reads_current_user(
    client: TestClient,
    recording_email_sender,
):
    register = _register(client, "session@example.com")
    assert register.status_code == 201

    code = extract_code_from_email(recording_email_sender.sent[-1])
    verify = client.post(
        "/api/auth/verify-email",
        json={"email": "session@example.com", "code": code},
    )
    assert verify.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"email": "session@example.com", "password": DEFAULT_TEST_PASSWORD},
    )
    assert login.status_code == 200
    assert "token" in login.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "session@example.com"
    assert me.json()["full_name"] == DEFAULT_TEST_FULL_NAME


@pytest.mark.integration
def test_logout_clears_cookie(client: TestClient, recording_email_sender):
    register = _register(client, "logout@example.com")
    assert register.status_code == 201

    code = extract_code_from_email(recording_email_sender.sent[-1])
    verify = client.post(
        "/api/auth/verify-email",
        json={"email": "logout@example.com", "code": code},
    )
    assert verify.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"email": "logout@example.com", "password": DEFAULT_TEST_PASSWORD},
    )
    assert login.status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    after_logout = client.get("/api/auth/me")
    assert after_logout.status_code == 401


@pytest.mark.integration
def test_password_reset_two_step_flow(client: TestClient, recording_email_sender):
    register = _register(client, "reset@example.com")
    assert register.status_code == 201

    verification_code = extract_code_from_email(recording_email_sender.sent[-1])
    verify = client.post(
        "/api/auth/verify-email",
        json={"email": "reset@example.com", "code": verification_code},
    )
    assert verify.status_code == 200

    forgot = client.post(
        "/api/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert forgot.status_code == 200

    reset_code = extract_code_from_email(recording_email_sender.sent[-1])
    verify_code = client.post(
        "/api/auth/verify-reset-code",
        json={"email": "reset@example.com", "code": reset_code},
    )
    assert verify_code.status_code == 200
    reset_token = verify_code.json()["reset_token"]

    reset = client.post(
        "/api/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewPassword123!"},
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": DEFAULT_TEST_PASSWORD},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "NewPassword123!"},
    )
    assert new_login.status_code == 200
