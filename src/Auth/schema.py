from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime


class RegisterUserDto(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginUserDto(BaseModel):
    email: EmailStr
    password: str



class UserResponse(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class RefreshTokenDto(BaseModel):
    refresh_token: str
    
class LogoutDto(BaseModel):
    refresh_token: str


    
   

