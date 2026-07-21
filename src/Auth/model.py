from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.User.model import User


class Auth(SQLModel, table=True):
    __tablename__: str = "auths"

    id: Optional[int] = Field(default=None, primary_key=True)

    access_token: Optional[str] = Field(default=None, max_length=2048)
    refresh_token: Optional[str] = Field(default=None, max_length=128)

    user_id: int = Field(foreign_key="users.id")

    user: "User" = Relationship(back_populates="auth_tokens")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
