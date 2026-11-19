
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class CreateUser(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Login_User(BaseModel):
    email: EmailStr
    password: str


class UpdateUser(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    email: EmailStr | None = None

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )


class UpdateUserRole(BaseModel):
    role: UserRole


class GetUser(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    username: str
    email: EmailStr
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: datetime