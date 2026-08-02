import hashlib
import bcrypt
import asyncio
from fastapi import HTTPException, status
from sqlmodel import select

from src.User.model import User
from src.Auth.model import Auth

from src.Auth.schema import RegisterUserDto, LoginUserDto, AuthTokenResponse, UserResponse


from src.Auth.utils import create_auth_tokens

from config.database import SessionDep

DUMMY_HASH = bcrypt.hashpw(b"dummy_password_for_timing", bcrypt.gensalt()).decode("utf-8")  

async def register(data: RegisterUserDto, session: SessionDep) -> AuthTokenResponse:
    # 1. Check if email or username already exists
    query_email = select(User).where(User.email == data.email)
    existing_user = (await session.exec(query_email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )

    # 2. Hash password with bcrypt
    salt = bcrypt.gensalt()
    hashed_pw_bytes = await asyncio.to_thread(bcrypt.hashpw, data.password.encode("utf-8"), salt)
    hashed_pw = hashed_pw_bytes.decode("utf-8")
    # 3. Create user
    new_user = User(
        username=data.username,
        email=data.email,
        password=hashed_pw
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # 4. Generate initial tokens
    return await create_auth_tokens(new_user, session)


async def login(data: LoginUserDto, session: SessionDep) -> AuthTokenResponse:
    # 1. Search for the user by email
    query = select(User).where(User.email == data.email)
    user = (await session.exec(query)).first()

   
    stored_hash = (user.password if user and user.password else DUMMY_HASH).encode("utf-8")
    is_valid_pw = await asyncio.to_thread(bcrypt.checkpw, data.password.encode("utf-8"), stored_hash)

    if not is_valid_pw or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 3. Generate tokens
    return await create_auth_tokens(user, session)


async def logout(raw_refresh_token: str, session: SessionDep) -> dict[str, str]:
    # Hash the incoming raw refresh token
    hashed_token = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    # Delete matching session from database
    query = select(Auth).where(Auth.refresh_token == hashed_token)
    auth_entry = (await session.exec(query)).first()

    if auth_entry:
        await session.delete(auth_entry)
        await session.commit()

    return {"message": "Successfully logged out"}
