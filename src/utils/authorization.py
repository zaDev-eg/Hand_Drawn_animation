
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.db_connection import get_session
from ..database.redis_connection import check_blocklist

from ..services.user_crud_logic import UserService
from ..models.user_model import UserModel

from .authontication import varify_access_token


service = UserService()

bearer = HTTPBearer()


async def _decode_bearer(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
    refresh_expected: bool,
):

    token_data = varify_access_token(
        credentials.credentials
    )

    if token_data.get("refresh") is not refresh_expected:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )

    if await check_blocklist(token_data):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return token_data


async def get_access_token_data(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
):

    return await _decode_bearer(
        credentials,
        refresh_expected=False,
    )


async def get_refresh_token_data(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
):

    return await _decode_bearer(
        credentials,
        refresh_expected=True,
    )


async def get_current_user(
    token_data: Annotated[
        dict,
        Depends(get_access_token_data),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> UserModel:

    try:

        user_id = UUID(
            token_data["user"]["user_id"]
        )

    except (KeyError, ValueError, TypeError):

        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
        )

    user = await service.get_user_by_id(
        user_id,
        session,
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User associated with token no longer exists",
        )

    return user


class UsersRoles:

    def __init__(self, available_roles: list[str]):

        self.available_roles = available_roles


    async def __call__(
        self,
        user: Annotated[
            UserModel,
            Depends(get_current_user),
        ],
    ) -> UserModel:

        if user.role in self.available_roles:

            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action",
        )


CurrentUser = Annotated[
    UserModel,
    Depends(get_current_user),
]


AdminUser = Annotated[
    UserModel,
    Depends(UsersRoles(["admin"])),
]