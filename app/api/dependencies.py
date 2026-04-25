import jwt
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.common.constants import Jwt
from app.common.exceptions import UnauthorizedException
from app.common.models.user import CurrentUser
from app.infrastructure.db import get_db
from app.infrastructure.email import EmailSender, build_email_sender
from app.infrastructure.repositories.auth_token_repository import AuthTokenRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security import decode_access_token
from app.services.auth_email_service import AuthEmailService
from app.services.auth_service import AuthService

DbSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_auth_token_repository(db: DbSession) -> AuthTokenRepository:
    return AuthTokenRepository(db)


def get_email_sender() -> EmailSender:
    return build_email_sender()


def get_auth_email_service(
    email_sender: EmailSender = Depends(get_email_sender),
) -> AuthEmailService:
    return AuthEmailService(email_sender=email_sender)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    auth_token_repo: AuthTokenRepository = Depends(get_auth_token_repository),
    auth_email_service: AuthEmailService = Depends(get_auth_email_service),
) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        auth_token_repo=auth_token_repo,
        auth_email_service=auth_email_service,
    )


def _build_current_user(user: dict) -> CurrentUser:
    return CurrentUser(
        id=int(user["id"]),
        full_name=user["full_name"],
        email=user["email"],
    )


def _get_current_user_from_token(token: str, user_repo: UserRepository) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        subject = payload.get(Jwt.Claim.SUB.value)
        user_id = int(subject)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError, ValueError):
        raise UnauthorizedException("Invalid authentication credentials")

    user = user_repo.get_by_id_raw(user_id)
    if not user or not user.get("is_active"):
        raise UnauthorizedException("Invalid authentication credentials")

    return _build_current_user(user)


def resolve_optional_current_user(
    request: Request,
    user_repo: UserRepository,
) -> CurrentUser | None:
    token = request.cookies.get(Jwt.COOKIE_NAME)
    if token is None:
        request.state.user = None
        return None

    try:
        current_user = _get_current_user_from_token(token, user_repo)
    except UnauthorizedException:
        request.state.user = None
        return None

    request.state.user = current_user
    return current_user


def resolve_current_user(
    request: Request,
    user_repo: UserRepository,
) -> CurrentUser:
    token = request.cookies.get(Jwt.COOKIE_NAME)
    if token is None:
        raise UnauthorizedException("Authentication required")

    current_user = _get_current_user_from_token(token, user_repo)
    request.state.user = current_user
    return current_user


def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
) -> CurrentUser:
    return resolve_current_user(request, user_repo)
