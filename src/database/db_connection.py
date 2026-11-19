
## Imports
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from ..utils.config import db_url
from ..models.user_model import UserModel

## Create the Engine
engine = create_async_engine(
        url=db_url,
    )


## Create the database
async def init_db():
    async with engine.begin() as conniction:
        ## Create all models in database
        await conniction.run_sync(SQLModel.metadata.create_all)


## Open sessions with the database
async def get_session():
    async_session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    ## create the session
    async with async_session() as session:
        yield session
