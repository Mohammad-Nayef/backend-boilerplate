import inspect
from contextlib import contextmanager
from functools import wraps

from fastapi import Request

from app.api.dependencies import resolve_current_user, resolve_optional_current_user
from app.common.constants import UserRole
from app.common.exceptions import ForbiddenException
from app.common.utils import limiter, running_in_pytest
from app.infrastructure.db import get_db
from app.infrastructure.repositories.user_repository import UserRepository


def _get_request(
    func_signature: inspect.Signature,
    args,
    kwargs,
) -> Request:
    request = func_signature.bind_partial(*args, **kwargs).arguments.get("request")
    if not isinstance(request, Request):
        raise RuntimeError(
            "Decorated route handlers must accept `request: Request`."
        )
    return request


@contextmanager
def _request_db_session(request: Request):
    db_dependency = request.app.dependency_overrides.get(get_db, get_db)
    db_resource = db_dependency()

    if inspect.isgenerator(db_resource):
        db = next(db_resource)
        try:
            yield db
        finally:
            db_resource.close()
        return

    yield db_resource


def authenticated(roles: set[UserRole] | None = None):
    def decorator(func):
        func_signature = inspect.signature(func)
        allowed_roles = {role.value for role in roles or set(UserRole)}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = _get_request(func_signature, args, kwargs)
            with _request_db_session(request) as db:
                current_user = resolve_current_user(
                    request=request,
                    user_repo=UserRepository(db),
                )
            if current_user.role not in allowed_roles:
                raise ForbiddenException()

            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        return wrapper
    return decorator


def optional_authentication():
    def decorator(func):
        func_signature = inspect.signature(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = _get_request(func_signature, args, kwargs)
            with _request_db_session(request) as db:
                resolve_optional_current_user(
                    request=request,
                    user_repo=UserRepository(db),
                )

            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        return wrapper
    return decorator


def rate_limit(value: str):
    def decorator(func):
        if running_in_pytest():
            return func
        return limiter.limit(value)(func)
    return decorator
