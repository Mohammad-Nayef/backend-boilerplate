from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend Boilerplate"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = (
        "Production-ready FastAPI boilerplate with layered architecture."
    )
    ENVIRONMENT: str = Field(...)
    DEBUG: bool = Field(...)

    DB_USER: str = Field(...)
    DB_PASSWORD: str = Field(...)
    DB_HOST: str = Field(...)
    DB_PORT: str = Field(...)
    DB_NAME: str = Field(...)
    DB_POOL_SIZE: int = Field(...)
    ISOLATION_LEVEL: str = Field(...)

    ALLOWED_ORIGINS: str = Field(...)
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(...)
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = Field(60)
    AUTH_CODE_EXPIRE_MINUTES: int = Field(15)
    PASSWORD_RESET_SESSION_EXPIRE_MINUTES: int = Field(10)
    EMAIL_FROM_ADDRESS: str = Field("no-reply@boilerplate.local")
    SMTP_HOST: str | None = Field(default=None)
    SMTP_PORT: int = Field(587)
    SMTP_USERNAME: str | None = Field(default=None)
    SMTP_PASSWORD: str | None = Field(default=None)
    SMTP_USE_TLS: bool = Field(True)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {
                "0",
                "false",
                "no",
                "off",
                "release",
                "prod",
                "production",
            }:
                return False
        return bool(value)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if len(value.strip()) < 16:
            raise ValueError("JWT_SECRET_KEY must be at least 16 characters long")
        return value

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")
        return normalized

    @property
    def DB_URL(self) -> str:
        return (
            "postgresql+pg8000://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
