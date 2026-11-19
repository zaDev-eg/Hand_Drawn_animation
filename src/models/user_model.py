
## imports 
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects import postgresql as pg


## user model 
class UserModel(SQLModel, table=True): 
    __tablename__ = "users"
    
    ## features of the user model 
    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )
    username: str
    email: str 
    hashed_password: str
    
    role: str = Field(
        sa_column=Column(
            pg.VARCHAR,
            nullable=False,
            server_default="user",
        )
    )
    
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            default=datetime.now(timezone.utc),
            nullable=False,
        )
    )
    
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            default=datetime.now(timezone.utc),
            nullable=False,
        )
    )