
from datetime import timedelta
from uuid import UUID
from typing import Annotated
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.db_connection import get_session
from ..database.redis_connection import add_tokens_to_blocklist

from ..services.user_crud_logic import UserService

from ..schemas.request_schema import (
    CreateUser,
    Login_User,
    UpdateUser,
    UpdateUserRole,
    GetUser,
)

from ..utils.authorization import (
    CurrentUser,
    AdminUser,
    get_access_token_data,
    get_refresh_token_data,
)

from ..utils.authontication import (
    create_access_token,
    create_url_safe_token,
    varify_url_safe_token,
)

from ..utils.config import mail_settings
from ..utils.celery import send_message

from ..models.user_model import UserModel


router = APIRouter()

user_router = router

service = UserService()


# -------------------------
# Token Generation
# -------------------------

def _token_pair(user: UserModel):

    payload = {
        "user_id": str(user.user_id)
    }

    access_token = create_access_token(
        payload,
        expire=timedelta(minutes=15),
    )

    refresh_token = create_access_token(
        payload,
        refresh=True,
        expire=timedelta(days=7),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# -------------------------
# Register
# -------------------------

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: CreateUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    user = await service.create_user(
        data,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    verification_token = create_url_safe_token(
        {
            "email": user.email
        }
    )

    link = (
        f"http://{mail_settings.DOMAIN_NAME}"
        f"/api/v1/users/verify/{verification_token}"
    )

    body = f"""
    <h2>Verify your email</h2>
    <p>
        <a href="{link}">Verify account</a>
    </p>
    """

    send_message.delay(
        recipients=[user.email],
        subject="Email verification",
        body=body,
    )

    # Return safe user information only
    safe_user = GetUser.model_validate(user)

    return {
        "message": "Registration successful. Check your email to verify.",
        "user": safe_user,
    }


# -------------------------
# Verify Email
# -------------------------

@router.get("/verify/{token}")
async def verify_email(
    token: str,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    token_data = varify_url_safe_token(token)

    if not token_data or not token_data.get("email"):

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link",
        )

    user = await service.get_user_by_email(
        token_data["email"],
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.is_verified:

        return {
            "message": "Email is already verified"
        }

    await service.verify_user_email(
        user,
        session,
    )

    return {
        "message": "Email verified successfully"
    }


# -------------------------
# Login
# -------------------------

@router.post("/login")
async def login(
    data: Login_User,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    user = await service.authenticate(
        str(data.email),
        data.password,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not user.is_verified:

        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in",
        )

    tokens = _token_pair(user)

    return {
        **tokens,
        "user": {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


# -------------------------
# Refresh Token
# -------------------------

@router.post("/refresh")
async def refresh(
    token_data: Annotated[
        dict,
        Depends(get_refresh_token_data),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    try:

        user_id = UUID(
            token_data["user"]["user_id"]
        )

    except (KeyError, TypeError, ValueError):

        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
        )

    return _token_pair(user)


# -------------------------
# Logout
# -------------------------

@router.post("/logout")
async def logout(
    token_data: Annotated[
        dict,
        Depends(get_access_token_data),
    ],
):

    remaining = max(
        1,
        int(token_data["exp"] - time.time()),
    )

    await add_tokens_to_blocklist(
        token_data,
        exp=remaining,
    )

    return {
        "message": "Logged out successfully"
    }


# -------------------------
# Current User
# -------------------------

@router.get(
    "/me",
    response_model=GetUser,
)
async def get_me(
    user: CurrentUser,
):

    return user


@router.patch(
    "/me",
    response_model=GetUser,
)
async def update_me(
    data: UpdateUser,
    user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    updated_user = await service.update_user(
        user,
        data,
        session,
    )

    return updated_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    await service.delete_user(
        user,
        session,
    )

    return None


# =========================
# Admin Endpoints
# =========================


# Get all users

@router.get(
    "/",
    response_model=list[GetUser],
)
async def admin_list_users(
    admin: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    return await service.get_all_users(
        session
    )


# Get user by ID

@router.get(
    "/{user_id}",
    response_model=GetUser,
)
async def admin_get_user(
    user_id: UUID,
    admin: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


# Update user

@router.patch(
    "/{user_id}",
    response_model=GetUser,
)
async def admin_update_user(
    user_id: UUID,
    data: UpdateUser,
    admin: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    updated_user = await service.update_user(
        user,
        data,
        session,
    )

    return updated_user


# Change user role

@router.patch(
    "/{user_id}/role",
    response_model=GetUser,
)
async def admin_change_role(
    user_id: UUID,
    data: UpdateUserRole,
    admin: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    if (
        admin.user_id == user_id
        and data.role.value != "admin"
    ):

        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role",
        )

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    updated_user = await service.update_role(
        user,
        data.role,
        session,
    )

    return updated_user


# Delete user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_delete_user(
    user_id: UUID,
    admin: AdminUser,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
):

    if admin.user_id == user_id:

        raise HTTPException(
            status_code=400,
            detail="Use /me to delete your own account",
        )

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    await service.delete_user(
        user,
        session,
    )

    return None