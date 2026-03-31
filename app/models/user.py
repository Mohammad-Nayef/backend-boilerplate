from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBaseDto(BaseModel):
    email: EmailStr
    role: str

class UserResponseDto(UserBaseDto):
    id: int
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CurrentUserDto(UserBaseDto):
    id: int
