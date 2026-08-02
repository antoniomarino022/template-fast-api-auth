from datetime import datetime, timezone
from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

class User(SQLModel, table=True):
    __tablename__:str = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    username: str = Field(max_length=50, index=True)
    email: EmailStr = Field(unique=True, index=True)
    password: Optional[str] = Field(default=None, max_length=100)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    
    auth_tokens: list["Auth"] = Relationship(back_populates="user")
