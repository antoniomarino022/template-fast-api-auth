import time
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta,timezone


from config.database import SessionDep


from src.User.model import User
from src.Auth.model import Auth

from src.Auth.schema import AuthTokenResponse, UserResponse
from fastapi import HTTPException, status
from sqlmodel import select

from config.settings import settings


SECRET_KEY_JWT = settings.SECRET_KEY_JWT
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_SECONDS = settings.ACCESS_TOKEN_EXPIRE_SECONDS
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def generate_access_token(user: User) -> str:
    """Generate a JWT token valid for 15 minutes."""
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY_JWT, algorithm=ALGORITHM)




async def create_auth_tokens(user: User, session: SessionDep) -> AuthTokenResponse:
    if user.id is None:
        raise ValueError("User ID cannot be None when creating auth tokens")

    access_token = generate_access_token(user)

    raw_refresh_token = secrets.token_urlsafe(64)
    hashed_refresh_token = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    auth_entry = Auth(
        refresh_token=hashed_refresh_token,
        user_id=user.id,
        expiration=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(auth_entry)
    await session.commit()

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=UserResponse(
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )
    )


async def refresh_token(raw_refresh_token: str, session: SessionDep) -> AuthTokenResponse:
    hashed_token = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    query = select(Auth).where(Auth.refresh_token == hashed_token)
    auth_entry = (await session.exec(query)).first()

    if not auth_entry:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    if auth_entry.expiration and auth_entry.expiration < datetime.now(timezone.utc):
        await session.delete(auth_entry)  
        await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = await session.get(User, auth_entry.user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    await session.delete(auth_entry)
    await session.commit()

    return await create_auth_tokens(user, session)