

## Imports
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .utils.config import app_settings
from .database.db_connection import init_db


## lifespan funtion
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("The server is running ...")
    ## execute the method
    await init_db()
    yield
    print("Shutdown the server ...")


## initialize the main app
app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.APP_VERSION,
    lifespan=lifespan,
)


## EndPoints
@app.get("/")
async def healthy_check():
    return {"message": "The server is up and running ✅"}
