import hashlib
import secrets
import time
import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlmodel import select

from src.User.model import User
from src.Auth.model import Auth
from src.Auth.schema import RegisterUserDto, LoginUserDto, AuthTokenResponse, UserResponse
from config.database import SessionDep
from config.settings import settings

# JWT Configuration
SECRET_KEY_JWT = settings.SECRET_KEY_JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 15  # 15 minutes


def generate_access_token(user: User) -> str:
    """Generate a JWT token valid for 15 minutes."""
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY_JWT, algorithm=ALGORITHM)


async def create_auth_tokens(user: User, session: SessionDep) -> AuthTokenResponse:
    """Generate access and refresh tokens, saving the hashed refresh token to the DB."""
    if user.id is None:
        raise ValueError("User ID cannot be None when creating auth tokens")

    access_token = generate_access_token(user)

    # Generate a secure random refresh token
    raw_refresh_token = secrets.token_urlsafe(64)
    hashed_refresh_token = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    # Save token hash to database
    auth_entry = Auth(
        access_token=access_token,
        refresh_token=hashed_refresh_token,
        user_id=user.id
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
    hashed_pw = bcrypt.hashpw(data.password.encode("utf-8"), salt).decode("utf-8")

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

    # 2. Verify password with bcrypt
    is_valid_pw = (
        user is not None 
        and user.password is not None 
        and bcrypt.checkpw(data.password.encode("utf-8"), user.password.encode("utf-8"))
    )

    if not is_valid_pw or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 3. Generate tokens
    return await create_auth_tokens(user, session)


async def refresh_token(raw_refresh_token: str, session: SessionDep) -> AuthTokenResponse:
    # 1. Hash the incoming raw refresh token
    hashed_token = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()

    # 2. Retrieve session from database
    query = select(Auth).where(Auth.refresh_token == hashed_token)
    auth_entry = (await session.exec(query)).first()

    if not auth_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # 3. Retrieve user associated with session
    user = await session.get(User, auth_entry.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 4. Delete the old refresh token (one-time use)
    await session.delete(auth_entry)
    await session.commit()

    # 5. Generate a new pair of tokens
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
