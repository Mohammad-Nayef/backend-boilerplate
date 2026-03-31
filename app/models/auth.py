from pydantic import BaseModel, EmailStr, Field

class TokenDto(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserRegisterDto(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

class UserLoginDto(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
