from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt

from app.common.config import settings
from app.common.constants import Jwt


def generate_salt() -> str:
    return secrets.token_hex(32)


def get_password_hash(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def verify_password(plain_password: str, salt: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password, salt) == hashed_password


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + (
        expires_delta or timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    )
    to_encode = {
        Jwt.Claim.SUB.value: str(subject),
        Jwt.Claim.IAT.value: issued_at,
        Jwt.Claim.EXP.value: expire,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
