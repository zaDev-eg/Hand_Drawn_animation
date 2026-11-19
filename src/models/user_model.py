
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column
from sqlalchemy.dialects import postgresql as pg
from sqlmodel import SQLModel, Field


class UserModel(SQLModel, table=True):

    __tablename__ = "users"

    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )

    username: str

    email: str = Field(
        index=True,
        unique=True,
        nullable=False,
    )

    hashed_password: str

    is_verified: bool = Field(
        default=False,
        nullable=False,
    )

    role: str = Field(
        sa_column=Column(
            pg.VARCHAR,
            nullable=False,
            server_default="user",
        )
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
        ),
    )