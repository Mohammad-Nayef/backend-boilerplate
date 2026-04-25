import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import OperationalError

from app.common.config import settings
from app.common.constants import MAX_RETRIES
from app.common.exceptions import CustomHTTPException
from app.common.utils import limiter, get_logger

logger = get_logger(__name__)


class HTTPExceptionMiddleware(BaseHTTPMiddleware):
    "Handle exceptions and return a JSON response accordingly"

    async def dispatch(self, request: Request, call_next):
        for retries in range(MAX_RETRIES):
            try:
                response = await call_next(request)
                return response
            except OperationalError as ex:
                logger.error(
                    f"Database connection error: {ex}\n{traceback.format_exc()}"
                )
                if retries == MAX_RETRIES - 1:
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except CustomHTTPException as ex:
                return JSONResponse(status_code=ex.status_code, content=ex.detail)
            except Exception as ex:
                if settings.ENVIRONMENT == "development":
                    error = f"Unhandled exception: {ex}\n{traceback.format_exc()}"
                else:
                    error = "Internal server error"

                logger.error(f"Unhandled exception: {ex}\n{traceback.format_exc()}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": error},
                )


def setup_rate_limit_middleware(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def add_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(HTTPExceptionMiddleware)
    setup_rate_limit_middleware(app)
