import logging
import sys
from datetime import time as dt_time

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.common.constants import RateLimits


def convert_to_time(value) -> dt_time:
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return dt_time(hour=hours, minute=minutes, second=seconds)


def running_in_pytest() -> bool:
    return "pytest" in sys.modules


def _request_identity_key(request: Request) -> str:
    return get_remote_address(request)


limiter = Limiter(
    key_func=_request_identity_key,
    default_limits=[] if running_in_pytest() else [RateLimits.TEN_PER_SECOND],
)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def get_logger(name: str):
    return logging.getLogger(name)
