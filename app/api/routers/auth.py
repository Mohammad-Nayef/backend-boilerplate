from fastapi import APIRouter, Depends, Request, Response

from app.api.decorators import authenticated, rate_limit
from app.common.models.auth import UserRegister, UserLogin
from app.common.models.user import CurrentUser, UserResponse
from app.services.auth_service import AuthService
from app.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(
    payload: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    return auth_service.register_user(payload)

@router.post("/login")
@rate_limit("5/minute")
def login(
    request: Request,
    payload: UserLogin,
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


@router.get("/me", response_model=CurrentUser)
@authenticated()
def get_current_authenticated_user(request: Request):
    """Return the current authenticated user from the auth cookie."""
    return request.state.user


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
