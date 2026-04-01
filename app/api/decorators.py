from functools import wraps
from fastapi import Request
import jwt
from app.common.exceptions import ForbiddenException, UnauthorizedException
from app.common.constants import Jwt, UserRole
from app.common.config import settings
from app.common.utils import running_in_pytest, limiter
from app.common.models.user import CurrentUser

def authenticated(roles: set[UserRole] = set(UserRole)):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.cookies.get(Jwt.COOKIE_NAME)
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
                role: str = payload.get(Jwt.Claim.ROLE.value, "")
                if role not in roles:
                    raise ForbiddenException()

                # Add UserState equivalent to the request
                request.state.user = CurrentUser(
                    id=int(payload.get(Jwt.Claim.SUB.value, 0)),
                    email=payload.get(Jwt.Claim.EMAIL.value, ""),
                    role=role
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError):
                raise UnauthorizedException()

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def optional_authentication():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.cookies.get(Jwt.COOKIE_NAME)
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
                role: str = payload.get(Jwt.Claim.ROLE.value, "")
                
                request.state.user = CurrentUser(
                    id=int(payload.get(Jwt.Claim.SUB.value, 0)),
                    email=payload.get(Jwt.Claim.EMAIL.value, ""),
                    role=role
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError):
                request.state.user = None

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit(value: str):
    def decorator(func):
        if running_in_pytest():
            return func
        return limiter.limit(value)(func)
    return decorator
