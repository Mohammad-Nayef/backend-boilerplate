from app.core.security import get_password_hash, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.tables.user import UserTable
from app.models.auth import UserRegisterDto, UserLoginDto
from app.core.exceptions import ConflictException, UnauthorizedException

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, payload: UserRegisterDto) -> UserTable:
        existing_user = self.user_repo.get_by_email_orm(payload.email)
        if existing_user:
            raise ConflictException("Email already exists")
            
        hashed_password = get_password_hash(payload.password)
        
        new_user = UserTable(
            email=payload.email,
            hashed_password=hashed_password,
            role="user" 
        )
        return self.user_repo.create(new_user)

    def login_user(self, payload: UserLoginDto) -> str:
        # Example using ORM to validate login
        user = self.user_repo.get_by_email_orm(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
            
        if not user.is_active:
            raise UnauthorizedException("Inactive user account")
            
        access_token = create_access_token(
            subject=user.id,
            role=user.role
        )
        return access_token
