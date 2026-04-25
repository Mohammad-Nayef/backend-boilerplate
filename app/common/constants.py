from enum import Enum


class Jwt:
    COOKIE_NAME = "token"

    class Claim(str, Enum):
        SUB = "sub"
        IAT = "iat"
        EXP = "exp"


class AuthLimits:
    FULL_NAME_MAX_LENGTH = 120
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    TOKEN_MAX_LENGTH = 512
    CODE_LENGTH = 4


class RateLimits:
    TEN_PER_SECOND = "10/1 second"
    FIVE_PER_MINUTE = "5/minute"


class AuthTokenPurpose(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_SESSION = "password_reset_session"


class RateLimitKey(str, Enum):
    IP = "ip"
    EMAIL = "email"
    AUTHENTICATED_USER_ID = "authenticated_user_id"
    RESET_TOKEN = "reset_token"


class QueryResult(str, Enum):
    LIST_OF_DICT = "list[dict]"
    LIST = "list"
    DICT = "dict"
    SCALAR = "scalar"


MAX_RETRIES = 3
