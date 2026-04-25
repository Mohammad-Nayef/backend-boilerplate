from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

from app.api.decorators import authenticated, rate_limit
from app.api.dependencies import get_auth_service
from app.common.constants import Jwt, RateLimitKey, RateLimits
from app.common.models.auth import (
    ForgotPasswordRequest,
    LoginResponse,
    MessageResponse,
    ResetPasswordRequest,
    ResetTokenResponse,
    ResendVerificationCodeRequest,
    UserLogin,
    UserRegister,
    VerifyEmailRequest,
    VerifyResetCodeRequest,
)
from app.common.models.user import CurrentUser, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
@rate_limit(RateLimits.FIVE_PER_MINUTE)
def register(
    request: Request,
    payload: UserRegister,
    response: Response,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    user, created = auth_service.register_user(
        payload, background_tasks=background_tasks
    )
    if not created:
        response.status_code = 200
    return user


@router.post("/login", response_model=LoginResponse)
@rate_limit(RateLimits.FIVE_PER_MINUTE, keys=[RateLimitKey.IP, RateLimitKey.EMAIL])
def login(
    request: Request,
    payload: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    token, _ = auth_service.login_user(payload)
    response.set_cookie(
        key=Jwt.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
    )
    return {"message": "Login successful"}


@router.get("/me", response_model=CurrentUser)
@authenticated()
def get_current_authenticated_user(request: Request):
    return request.state.user


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    response.delete_cookie(
        key=Jwt.COOKIE_NAME,
        httponly=True,
        samesite="none",
        secure=True,
    )
    return {"message": "Logged out successfully"}


@router.post("/verify-email", response_model=MessageResponse)
@rate_limit(RateLimits.FIVE_PER_MINUTE, keys=[RateLimitKey.IP, RateLimitKey.EMAIL])
def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.verify_email(payload)


@router.post("/resend-verification-code", response_model=MessageResponse)
@rate_limit(RateLimits.FIVE_PER_MINUTE, keys=[RateLimitKey.IP, RateLimitKey.EMAIL])
def resend_verification_code(
    request: Request,
    payload: ResendVerificationCodeRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.resend_verification_code(
        payload,
        background_tasks=background_tasks,
    )


@router.post("/forgot-password", response_model=MessageResponse)
@rate_limit(RateLimits.FIVE_PER_MINUTE, keys=[RateLimitKey.IP, RateLimitKey.EMAIL])
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.forgot_password(payload, background_tasks=background_tasks)


@router.post("/verify-reset-code", response_model=ResetTokenResponse)
@rate_limit(RateLimits.FIVE_PER_MINUTE, keys=[RateLimitKey.IP, RateLimitKey.EMAIL])
def verify_reset_code(
    request: Request,
    payload: VerifyResetCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.verify_reset_code(payload)


@router.post("/reset-password", response_model=MessageResponse)
@rate_limit(
    RateLimits.FIVE_PER_MINUTE,
    keys=[RateLimitKey.IP, RateLimitKey.RESET_TOKEN],
)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.reset_password(payload)
