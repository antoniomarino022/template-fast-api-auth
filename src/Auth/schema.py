from pydantic import BaseModel, EmailStr,Field
from typing import Optional
from datetime import datetime


class RegisterUserDto(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginUserDto(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class RefreshTokenDto(BaseModel):
    refresh_token: str
    
class LogoutDto(BaseModel):
    refresh_token: str


    
   

