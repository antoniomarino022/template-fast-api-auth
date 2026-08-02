from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Auth(SQLModel, table=True):
    __tablename__: str = "auths"

    id: Optional[int] = Field(default=None, primary_key=True)
    refresh_token: Optional[str] = Field(default=None, max_length=128)
    expiration: Optional[datetime] = Field(default=None)
    user_id: int = Field(foreign_key="users.id")
    user: "User" = Relationship(back_populates="auth_tokens")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))