from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    role: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CurrentUser(UserBase):
    id: int
