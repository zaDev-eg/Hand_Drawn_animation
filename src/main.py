from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .utils.config import app_settings
from .database.db_connection import init_db
from .routers.user_router import user_router


FRONTEND_FILE = (
    Path(__file__).resolve().parent.parent / "frontend" / "login.html"
)


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

# Let the standalone HTML page (file:// or any local dev server) call the API.
allowed_origins = [
    origin.strip()
    for origin in app_settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/login", include_in_schema=False)
async def login_page():

    if not FRONTEND_FILE.is_file():

        raise HTTPException(
            status_code=404,
            detail="Frontend page is missing",
        )

    return FileResponse(FRONTEND_FILE)
