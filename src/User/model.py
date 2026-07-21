from datetime import datetime
from typing import TYPE_CHECKING, Optional
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.Auth.model import Auth  
class User(SQLModel, table=True):
    __tablename__:str = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    username: str = Field(max_length=50, index=True)
    email: EmailStr = Field(unique=True, index=True)
    password: Optional[str] = Field(default=None, min_length=4, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    
    auth_tokens: list["Auth"] = Relationship(back_populates="user")
