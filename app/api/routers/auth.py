from fastapi import APIRouter, Depends, Response
from app.models.auth import UserRegisterDto, UserLoginDto
from app.models.user import UserResponseDto
from app.services.auth_service import AuthService
from app.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponseDto)
def register(
    payload: UserRegisterDto,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    return auth_service.register_user(payload)

@router.post("/login")
def login(
    payload: UserLoginDto,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate a user and set an HTTP-only cookie."""
    token = auth_service.login_user(payload)
    
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax", 
        secure=True, 
    )
    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    """Clear the authentication cookie."""
    response.delete_cookie(
        key="token",
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return {"message": "Logged out successful"}
