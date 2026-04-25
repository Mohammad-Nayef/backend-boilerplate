from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks

from app.common.constants import AuthTokenPurpose
from app.common.exceptions import ConflictException, UnauthorizedException
from app.common.models.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserLogin,
    UserRegister,
    VerifyEmailRequest,
    VerifyResetCodeRequest,
)
from app.infrastructure.security import (
    generate_salt,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.infrastructure.tables.auth_token import AuthTokenTable
from app.infrastructure.tables.user import UserTable
from app.services.auth_service import AuthService


def build_service() -> tuple[AuthService, MagicMock, MagicMock, MagicMock]:
    user_repo = MagicMock()
    auth_token_repo = MagicMock()
    auth_email_service = MagicMock()
    service = AuthService(
        user_repo=user_repo,
        auth_token_repo=auth_token_repo,
        auth_email_service=auth_email_service,
    )
    return service, user_repo, auth_token_repo, auth_email_service


@pytest.mark.unit
def test_register_user_creates_inactive_user_and_sends_code():
    service, user_repo, auth_token_repo, auth_email_service = build_service()
    user_repo.get_by_email.return_value = None

    def create_user(user: UserTable) -> UserTable:
        user.id = 7
        return user

    user_repo.create.side_effect = create_user

    result, created = service.register_user(
        UserRegister(
            full_name="John Doe",
            email="John@example.com",
            password="Password123!",
        )
    )

    assert created is True
    assert result.id == 7
    assert result.email == "john@example.com"
    assert result.full_name == "John Doe"
    assert result.is_active is False
    assert verify_password("Password123!", result.password_salt, result.hashed_password)
    auth_token_repo.issue_token.assert_called_once()
    auth_email_service.send_verification_email.assert_called_once()


@pytest.mark.unit
def test_register_user_rejects_duplicate_verified_email():
    service, user_repo, _, _ = build_service()
    user_repo.get_by_email.return_value = UserTable(
        id=1,
        full_name="Existing User",
        email="john@example.com",
        password_salt="unused",
        hashed_password="hash",
        is_active=True,
    )

    with pytest.raises(ConflictException):
        service.register_user(
            UserRegister(
                full_name="John Doe",
                email="john@example.com",
                password="Password123!",
            )
        )


@pytest.mark.unit
def test_login_user_requires_verified_account():
    service, user_repo, _, _ = build_service()
    salt = generate_salt()
    user_repo.get_by_email.return_value = UserTable(
        id=3,
        full_name="John Doe",
        email="john@example.com",
        password_salt=salt,
        hashed_password=get_password_hash("Password123!", salt),
        is_active=False,
        email_verified_at=None,
    )

    with pytest.raises(UnauthorizedException):
        service.login_user(UserLogin(email="john@example.com", password="Password123!"))


@pytest.mark.unit
def test_verify_email_consumes_token_and_activates_user():
    service, user_repo, auth_token_repo, _ = build_service()
    user = UserTable(
        id=5,
        full_name="John Doe",
        email="john@example.com",
        password_salt="unused",
        hashed_password="hash",
        is_active=False,
    )
    user_repo.get_by_email.return_value = user
    auth_token_repo.get_latest_for_user.return_value = AuthTokenTable(
        id=11,
        user_id=5,
        purpose=AuthTokenPurpose.EMAIL_VERIFICATION.value,
        token_hash=hash_token("1234"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=None,
    )
    auth_token_repo.consume_by_id.return_value = True

    result = service.verify_email(
        VerifyEmailRequest(email="john@example.com", code="1234")
    )

    assert result["message"] == "Email verified successfully"
    assert user.is_active is True
    assert user.email_verified_at is not None
    user_repo.save.assert_called_once_with(user)


@pytest.mark.unit
def test_reset_flow_issues_and_consumes_reset_session_token():
    service, user_repo, auth_token_repo, _ = build_service()
    user = UserTable(
        id=9,
        full_name="John Doe",
        email="john@example.com",
        password_salt="old-salt",
        hashed_password="old-hash",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    user_repo.get_by_email.return_value = user
    auth_token_repo.get_latest_for_user.return_value = AuthTokenTable(
        id=15,
        user_id=9,
        purpose=AuthTokenPurpose.PASSWORD_RESET.value,
        token_hash=hash_token("5678"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=None,
    )
    auth_token_repo.consume_by_id.return_value = True

    reset_token = service.verify_reset_code(
        VerifyResetCodeRequest(email="john@example.com", code="5678")
    ).reset_token
    assert reset_token

    auth_token_repo.get_by_token_hash.return_value = AuthTokenTable(
        id=16,
        user_id=9,
        purpose=AuthTokenPurpose.PASSWORD_RESET_SESSION.value,
        token_hash=hash_token(reset_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        used_at=None,
    )
    user_repo.get_by_id.return_value = user
    auth_token_repo.consume_by_id.return_value = True

    result = service.reset_password(
        ResetPasswordRequest(reset_token=reset_token, new_password="NewPassword123!")
    )

    assert result["message"] == "Password reset successfully"
    assert verify_password("NewPassword123!", user.password_salt, user.hashed_password)
    user_repo.save.assert_called_once_with(user)


@pytest.mark.unit
def test_background_tasks_path_does_not_call_email_sender_synchronously():
    service, user_repo, auth_token_repo, auth_email_service = build_service()
    user_repo.get_by_email.return_value = None
    user_repo.create.side_effect = lambda user: UserTable(
        id=1,
        full_name=user.full_name,
        email=user.email,
        password_salt=user.password_salt,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
    )

    background_tasks = BackgroundTasks()
    service.register_user(
        UserRegister(
            full_name="John Doe",
            email="john@example.com",
            password="Password123!",
        ),
        background_tasks=background_tasks,
    )

    assert len(background_tasks.tasks) == 1
    auth_email_service.send_verification_email.assert_not_called()

    user_repo.get_by_email.return_value = UserTable(
        id=1,
        full_name="John Doe",
        email="john@example.com",
        password_salt="salt",
        hashed_password="hash",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    background_tasks = BackgroundTasks()
    service.forgot_password(
        ForgotPasswordRequest(email="john@example.com"),
        background_tasks=background_tasks,
    )

    assert len(background_tasks.tasks) == 1
