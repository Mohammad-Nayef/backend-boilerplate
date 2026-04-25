from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    full_name: str
    email: EmailStr


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime | None = None
    email_verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CurrentUser(UserBase):
    id: int
