from fastapi import APIRouter

from config.database import SessionDep
from src.Auth.schema import (
    AuthTokenResponse,
    LoginUserDto,
    LogoutDto,
    RegisterUserDto,
)
from src.Auth.service import login, logout, register


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register_route(data: RegisterUserDto, session: SessionDep):
    return await register(data, session)


@router.post("/login", response_model=AuthTokenResponse)
async def login_route(data: LoginUserDto, session: SessionDep):
    return await login(data, session)



@router.post("/logout")
async def logout_route(data: LogoutDto, session: SessionDep):
    return await logout(data.refresh_token, session)
