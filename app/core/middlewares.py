import os
import traceback
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.exceptions import CustomHTTPException
from app.core.constants import GUEST_COOKIE_NAME, MAX_RETRIES
from app.core.utils import limiter
from app.core.config import settings

class HTTPExceptionMiddleware(BaseHTTPMiddleware):
    "Handle exceptions and return a JSON response accordingly"
    async def dispatch(self, request: Request, call_next):
        for retries in range(MAX_RETRIES):
            try:
                response = await call_next(request)
                return response
            except OperationalError as ex:
                logging.error(f"Database connection error: {ex}\n{traceback.format_exc()}")
                if retries == MAX_RETRIES - 1:
                    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except CustomHTTPException as ex:
                return JSONResponse(status_code=ex.status_code, content=ex.detail)
            except Exception as ex:
                if settings.ENVIRONMENT == "development":
                    error = f"Unhandled exception: {ex}\n{traceback.format_exc()}"
                else:
                    error = "Internal server error"

                logging.error(f"Unhandled exception: {ex}\n{traceback.format_exc()}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": error},
                )

class GuestCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.cookies.get(GUEST_COOKIE_NAME) is None:
            response = await call_next(request)
            response.set_cookie(
                GUEST_COOKIE_NAME,
                os.urandom(16).hex(),
                httponly=True,
                samesite="None",
                secure=True,
            )
            return response
        return await call_next(request)

def setup_rate_limit_middleware(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

def add_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(HTTPExceptionMiddleware)
    app.add_middleware(GuestCookieMiddleware)
    setup_rate_limit_middleware(app)
