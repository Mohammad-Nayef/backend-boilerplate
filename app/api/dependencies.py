from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.common.exceptions import UnauthorizedException
from app.infrastructure.security import decode_access_token
import jwt
from app.common.models.user import CurrentUser
from typing import Annotated

# Database dependency
DbSession = Annotated[Session, Depends(get_db)]

def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)

def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

def get_current_user(request: Request) -> CurrentUser:
    """Dependency for extracting and validating JWT from cookies."""
    token = request.cookies.get("token")
    if not token:
        raise UnauthorizedException("Not authenticated")
        
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email", "") 
        role: str = payload.get("role")
        
        if user_id_str is None:
            raise UnauthorizedException("Invalid credentials")
            
        return CurrentUser(
            id=int(user_id_str),
            email=email,
            role=role
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Could not validate credentials")
