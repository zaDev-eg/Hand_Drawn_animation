from contextlib import asynccontextmanager

from fastapi import FastAPI

from .utils.config import app_settings
from .database.db_connection import init_db
from .routers.user_router import user_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("The server is running ...")

    await init_db()

    yield

    print("Shutdown the server ...")


app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.APP_VERSION,
    lifespan=lifespan,
)


app.include_router(
    user_router,
    prefix="/api/v1/users",
    tags=["Users"],
)


@app.get("/")
async def healthy_check():

    return {
        "message": "The server is up and running"
    }