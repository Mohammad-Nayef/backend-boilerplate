from enum import Enum

class Environment:
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class UserRole(str, Enum):
    REGISTERED_STUDENT = "registered_student"
    MEMBER = "member"
    FINANCIAL_OFFICER = "financial_officer"
    LEADER = "leader"
    DEVELOPER = "developer"

class Jwt:
    COOKIE_NAME = "token"

    class Claim(str, Enum):
        SUB = "sub"
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        EMAIL = "email"
        ROLE = "role"
        EXP = "exp"
        GENDER = "gender"

class QueryResult(str, Enum):
    LIST_OF_DICT = "list[dict]"
    LIST = "list"
    DICT = "dict"
    SCALAR = "scalar"

GUEST_COOKIE_NAME = "guest-token"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "gif", "svg"}
