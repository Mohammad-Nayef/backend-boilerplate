import inspect
from contextlib import contextmanager
from functools import wraps

from fastapi import Request
from slowapi.util import get_remote_address

from app.api.dependencies import resolve_current_user, resolve_optional_current_user
from app.common.constants import RateLimitKey
from app.common.utils import limiter, running_in_pytest
from app.infrastructure.db import get_db
from app.infrastructure.repositories.user_repository import UserRepository

_PREPARED_RATE_LIMIT_KEY = "_prepared_rate_limit_key"


def _get_request(bound_arguments: inspect.BoundArguments) -> Request:
    request = bound_arguments.arguments.get("request")
    if not isinstance(request, Request):
        raise RuntimeError("Decorated route handlers must accept `request: Request`.")
    return request


def _bind_arguments(
    func_signature: inspect.Signature,
    args,
    kwargs,
) -> inspect.BoundArguments:
    return func_signature.bind_partial(*args, **kwargs)


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


def _find_argument_value(
    bound_arguments: inspect.BoundArguments,
    *,
    field_name: str,
):
    for value in bound_arguments.arguments.values():
        if isinstance(value, Request):
            continue
        if isinstance(value, dict) and field_name in value:
            return value[field_name]
        if hasattr(value, field_name):
            return getattr(value, field_name)
    raise RuntimeError(
        f"Could not resolve rate limit key field `{field_name}` from route arguments."
    )


def _resolve_authenticated_user_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        with _request_db_session(request) as db:
            user = resolve_optional_current_user(
                request=request,
                user_repo=UserRepository(db),
            )
    if user is None:
        raise RuntimeError(
            "Could not resolve `AUTHENTICATED_USER_ID` without a valid authentication token."
        )
    return str(user.id)


def _resolve_rate_limit_key_part(
    key: RateLimitKey,
    *,
    request: Request,
    bound_arguments: inspect.BoundArguments,
) -> str:
    if key == RateLimitKey.IP:
        return get_remote_address(request)
    if key == RateLimitKey.EMAIL:
        return (
            str(_find_argument_value(bound_arguments, field_name="email"))
            .strip()
            .lower()
        )
    if key == RateLimitKey.AUTHENTICATED_USER_ID:
        return _resolve_authenticated_user_id(request)
    if key == RateLimitKey.RESET_TOKEN:
        return str(
            _find_argument_value(bound_arguments, field_name="reset_token")
        ).strip()
    raise RuntimeError(f"Unsupported rate limit key `{key}`.")


def _prepare_rate_limit_key(
    *,
    request: Request,
    bound_arguments: inspect.BoundArguments,
    keys: list[RateLimitKey],
) -> str:
    resolved_parts: list[str] = []
    seen_keys: set[RateLimitKey] = set()

    for key in keys:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        value = _resolve_rate_limit_key_part(
            key,
            request=request,
            bound_arguments=bound_arguments,
        )
        if not value:
            raise RuntimeError(f"Resolved empty rate limit key for `{key}`.")
        resolved_parts.append(f"{key.value}:{value}")

    return "|".join(resolved_parts)


def _request_state_key_func(request: Request) -> str:
    key = getattr(request.state, _PREPARED_RATE_LIMIT_KEY, None)
    if not isinstance(key, str) or not key:
        raise RuntimeError("Rate limit key was not prepared before evaluation.")
    return key


def authenticated():
    def decorator(func):
        func_signature = inspect.signature(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = _get_request(_bind_arguments(func_signature, args, kwargs))
            with _request_db_session(request) as db:
                resolve_current_user(
                    request=request,
                    user_repo=UserRepository(db),
                )

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
            request = _get_request(_bind_arguments(func_signature, args, kwargs))
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


def rate_limit(
    value: str,
    *,
    keys: list[RateLimitKey] = [RateLimitKey.IP],
):
    def decorator(func):
        if running_in_pytest():
            return func
        func_signature = inspect.signature(func)

        def _prepare_request_state(*args, **kwargs) -> None:
            bound_arguments = _bind_arguments(func_signature, args, kwargs)
            request = _get_request(bound_arguments)
            setattr(
                request.state,
                _PREPARED_RATE_LIMIT_KEY,
                _prepare_rate_limit_key(
                    request=request,
                    bound_arguments=bound_arguments,
                    keys=keys,
                ),
            )

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def prepare_and_call(*args, **kwargs):
                _prepare_request_state(*args, **kwargs)
                return await limited_func(*args, **kwargs)

        else:

            @wraps(func)
            def prepare_and_call(*args, **kwargs):
                _prepare_request_state(*args, **kwargs)
                return limited_func(*args, **kwargs)

        limited_func = limiter.limit(value, key_func=_request_state_key_func)(func)
        return prepare_and_call

    return decorator
