from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBaseDto(BaseModel):
    email: EmailStr
    role: str

class UserResponseDto(UserBaseDto):
    id: int
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class CurrentUserDto(UserBaseDto):
    id: int
