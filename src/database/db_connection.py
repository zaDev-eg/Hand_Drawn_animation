## Imports
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from ..models.user_model import UserModel
from ..utils.config import db_url

## Create the Engine
engine = create_async_engine(
    url=db_url,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


## Create the database
async def init_db():
    async with engine.begin() as conniction:
        await conniction.run_sync(SQLModel.metadata.create_all)


## Open sessions with the database
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session