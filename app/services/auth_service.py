from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import secrets

from fastapi import BackgroundTasks

from app.common.config import settings
from app.common.constants import AuthLimits, AuthTokenPurpose
from app.common.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.common.models.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResetTokenResponse,
    ResendVerificationCodeRequest,
    UserLogin,
    UserRegister,
    VerifyEmailRequest,
    VerifyResetCodeRequest,
)
from app.infrastructure.repositories.auth_token_repository import AuthTokenRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security import (
    create_access_token,
    generate_salt,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.infrastructure.tables.auth_token import AuthTokenTable
from app.infrastructure.tables.user import UserTable
from app.services.auth_email_service import AuthEmailService


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        auth_token_repo: AuthTokenRepository,
        auth_email_service: AuthEmailService,
    ):
        self.user_repo = user_repo
        self.auth_token_repo = auth_token_repo
        self.auth_email_service = auth_email_service

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def _generate_one_time_code(self) -> str:
        return f"{secrets.randbelow(10**AuthLimits.CODE_LENGTH):0{AuthLimits.CODE_LENGTH}d}"

    def _issue_one_time_code(
        self,
        *,
        user_id: int,
        purpose: AuthTokenPurpose,
    ) -> str:
        code = self._generate_one_time_code()
        self.auth_token_repo.issue_token(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_token(code),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.AUTH_CODE_EXPIRE_MINUTES),
        )
        return code

    def _issue_reset_session_token(self, *, user_id: int) -> str:
        reset_token = secrets.token_urlsafe(32)
        self.auth_token_repo.issue_token(
            user_id=user_id,
            purpose=AuthTokenPurpose.PASSWORD_RESET_SESSION,
            token_hash=hash_token(reset_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.PASSWORD_RESET_SESSION_EXPIRE_MINUTES),
        )
        return reset_token

    def _send_email(
        self,
        *,
        background_tasks: BackgroundTasks | None,
        sender: Callable[..., None],
        **kwargs,
    ) -> None:
        if background_tasks is None:
            sender(**kwargs)
            return

        background_tasks.add_task(sender, **kwargs)

    def _issue_and_send_verification_code(
        self,
        *,
        user: UserTable,
        background_tasks: BackgroundTasks | None,
    ) -> None:
        verification_code = self._issue_one_time_code(
            user_id=user.id,
            purpose=AuthTokenPurpose.EMAIL_VERIFICATION,
        )
        self._send_email(
            background_tasks=background_tasks,
            sender=self.auth_email_service.send_verification_email,
            recipient_email=user.email,
            full_name=user.full_name,
            code=verification_code,
        )

    def _get_valid_code_record(
        self,
        *,
        email: str,
        code: str,
        purpose: AuthTokenPurpose,
        error_message: str,
    ) -> tuple[UserTable, AuthTokenTable]:
        user = self.user_repo.get_by_email(self._normalize_email(email))
        if user is None:
            raise BadRequestException(error_message)

        token_record = self.auth_token_repo.get_latest_for_user(
            user_id=user.id,
            purpose=purpose,
        )
        now = datetime.now(timezone.utc)
        if (
            token_record is None
            or token_record.token_hash != hash_token(code)
            or token_record.used_at is not None
            or token_record.expires_at <= now
        ):
            raise BadRequestException(error_message)
        return user, token_record

    def _get_valid_token_record(
        self,
        *,
        token: str,
        purpose: AuthTokenPurpose,
        error_message: str,
    ) -> tuple[UserTable, AuthTokenTable]:
        token_record = self.auth_token_repo.get_by_token_hash(
            purpose=purpose,
            token_hash=hash_token(token),
        )
        now = datetime.now(timezone.utc)
        if (
            token_record is None
            or token_record.used_at is not None
            or token_record.expires_at <= now
        ):
            raise BadRequestException(error_message)

        user = self.user_repo.get_by_id(token_record.user_id)
        if user is None:
            raise BadRequestException(error_message)

        return user, token_record

    def register_user(
        self,
        payload: UserRegister,
        background_tasks: BackgroundTasks | None = None,
    ) -> tuple[UserTable, bool]:
        normalized_email = self._normalize_email(str(payload.email))
        existing_user = self.user_repo.get_by_email(normalized_email)
        full_name = payload.full_name.strip()
        salt = generate_salt()
        hashed_password = get_password_hash(payload.password, salt)

        if existing_user:
            if existing_user.email_verified_at is not None or existing_user.is_active:
                raise ConflictException("Email already exists")

            existing_user.full_name = full_name
            existing_user.password_salt = salt
            existing_user.hashed_password = hashed_password
            existing_user.is_active = False
            existing_user.email_verified_at = None
            updated_user = self.user_repo.save(existing_user)
            self._issue_and_send_verification_code(
                user=updated_user,
                background_tasks=background_tasks,
            )
            return updated_user, False

        new_user = UserTable(
            full_name=full_name,
            email=normalized_email,
            password_salt=salt,
            hashed_password=hashed_password,
            is_active=False,
        )
        created_user = self.user_repo.create(new_user)
        self._issue_and_send_verification_code(
            user=created_user,
            background_tasks=background_tasks,
        )
        return created_user, True

    def login_user(self, payload: UserLogin) -> tuple[str, UserTable]:
        user = self.user_repo.get_by_email(self._normalize_email(str(payload.email)))
        if not user or not verify_password(
            payload.password,
            user.password_salt,
            user.hashed_password,
        ):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active or user.email_verified_at is None:
            raise UnauthorizedException("Email verification is required before login")

        return create_access_token(subject=user.id), user

    def verify_email(self, payload: VerifyEmailRequest) -> dict[str, str]:
        normalized_email = self._normalize_email(str(payload.email))
        user = self.user_repo.get_by_email(normalized_email)
        if user is not None and user.is_active and user.email_verified_at is not None:
            return {"message": "Email is already verified"}

        user, token_record = self._get_valid_code_record(
            email=normalized_email,
            code=payload.code,
            purpose=AuthTokenPurpose.EMAIL_VERIFICATION,
            error_message="Invalid or expired email verification code",
        )
        if not self.auth_token_repo.consume_by_id(token_record.id):
            raise BadRequestException("Invalid or expired email verification code")
        user.is_active = True
        user.email_verified_at = datetime.now(timezone.utc)
        self.user_repo.save(user)

        return {"message": "Email verified successfully"}

    def forgot_password(
        self,
        payload: ForgotPasswordRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, str]:
        user = self.user_repo.get_by_email(self._normalize_email(str(payload.email)))
        if user is not None:
            reset_code = self._issue_one_time_code(
                user_id=user.id,
                purpose=AuthTokenPurpose.PASSWORD_RESET,
            )
            self._send_email(
                background_tasks=background_tasks,
                sender=self.auth_email_service.send_password_reset_email,
                recipient_email=user.email,
                full_name=user.full_name,
                code=reset_code,
            )

        return {
            "message": "If the account exists, a password reset email has been sent"
        }

    def resend_verification_code(
        self,
        payload: ResendVerificationCodeRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, str]:
        user = self.user_repo.get_by_email(self._normalize_email(str(payload.email)))
        if user is not None and user.email_verified_at is None:
            self._issue_and_send_verification_code(
                user=user,
                background_tasks=background_tasks,
            )

        return {
            "message": "If the account exists and is not verified, a verification code has been sent"
        }

    def verify_reset_code(self, payload: VerifyResetCodeRequest) -> ResetTokenResponse:
        user, token_record = self._get_valid_code_record(
            email=str(payload.email),
            code=payload.code,
            purpose=AuthTokenPurpose.PASSWORD_RESET,
            error_message="Invalid or expired password reset code",
        )
        if not self.auth_token_repo.consume_by_id(token_record.id):
            raise BadRequestException("Invalid or expired password reset code")
        reset_token = self._issue_reset_session_token(user_id=user.id)
        return ResetTokenResponse(reset_token=reset_token)

    def reset_password(self, payload: ResetPasswordRequest) -> dict[str, str]:
        user, token_record = self._get_valid_token_record(
            token=payload.reset_token,
            purpose=AuthTokenPurpose.PASSWORD_RESET_SESSION,
            error_message="Invalid or expired password reset token",
        )
        if not self.auth_token_repo.consume_by_id(token_record.id):
            raise BadRequestException("Invalid or expired password reset token")
        salt = generate_salt()
        user.password_salt = salt
        user.hashed_password = get_password_hash(payload.new_password, salt)
        self.user_repo.save(user)

        return {"message": "Password reset successfully"}
