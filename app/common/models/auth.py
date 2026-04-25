from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.constants import AuthLimits


def _strip_and_require(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_full_name(value: str) -> str:
    normalized = _strip_and_require(value, field_name="full_name")
    if len(normalized) < 2:
        raise ValueError("full_name must be at least 2 characters long")
    if any(char.isdigit() for char in normalized):
        raise ValueError("full_name must not contain numbers")
    return normalized


def _normalize_digit_code(value: str) -> str:
    normalized = _strip_and_require(value, field_name="code")
    if not normalized.isdigit():
        raise ValueError("code must contain only digits")
    return normalized


class LoginResponse(BaseModel):
    message: str


class UserRegister(BaseModel):
    full_name: str = Field(max_length=AuthLimits.FULL_NAME_MAX_LENGTH)
    email: EmailStr
    password: str = Field(
        min_length=AuthLimits.PASSWORD_MIN_LENGTH,
        max_length=AuthLimits.PASSWORD_MAX_LENGTH,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return _normalize_full_name(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=AuthLimits.PASSWORD_MIN_LENGTH,
        max_length=AuthLimits.PASSWORD_MAX_LENGTH,
    )


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(
        min_length=AuthLimits.CODE_LENGTH,
        max_length=AuthLimits.CODE_LENGTH,
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _normalize_digit_code(value)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResendVerificationCodeRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(
        min_length=AuthLimits.CODE_LENGTH,
        max_length=AuthLimits.CODE_LENGTH,
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _normalize_digit_code(value)


class ResetTokenResponse(BaseModel):
    reset_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(max_length=AuthLimits.TOKEN_MAX_LENGTH)
    new_password: str = Field(
        min_length=AuthLimits.PASSWORD_MIN_LENGTH,
        max_length=AuthLimits.PASSWORD_MAX_LENGTH,
    )

    @field_validator("reset_token")
    @classmethod
    def validate_reset_token(cls, value: str) -> str:
        return _strip_and_require(value, field_name="reset_token")


class MessageResponse(BaseModel):
    message: str
