from typing import Any
from fastapi import HTTPException, status

class CustomHTTPException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, details: Any = None):
        super().__init__(status_code=self.status_code, detail=details)

class BadRequestException(CustomHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST

class UnauthorizedException(CustomHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED

class ForbiddenException(CustomHTTPException):
    status_code = status.HTTP_403_FORBIDDEN

class NotFoundException(CustomHTTPException):
    status_code = status.HTTP_404_NOT_FOUND

class ConflictException(CustomHTTPException):
    status_code = status.HTTP_409_CONFLICT
