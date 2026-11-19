
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, List
from .authontication import varify_access_token
from ..database.db_connection import get_session
from ..services.user_crud_logic import UserService
from ..models.user_model import UserModel

service = UserService()

##--------------->
## Authorization
##--------------->
class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        ## got back the redentials
        creds = await super().__call__(request)

        ## creds -> schema, credentials
        token = creds.credentials  ## got the token back from creds

        ## check if the token is available
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please enther the access token! ",
            )

        ## got the data back from the token
        token_data = varify_access_token(token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired or invalid",
            )

        # ## check if the token is in the blocklist or not
        # if await check_blocklist(token_data):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="This token is in the blocklist",
        #     )

        ## check if the tokens is still alife or not
        self.validate_access_token(token_data)

        return token_data

    def validate_access_token(self, token_data: dict):
        raise NotImplementedError("Please Emplement this method in all child classes")


## check if the token is valid or not
class AccessToken(TokenBearer):

    def validate_access_token(self, token_data: dict) -> None:
        if token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please enter an access token",
            )


## check if the refresh token is valid or not
class RefreshToken(TokenBearer):

    def validate_access_token(self, token_data: dict) -> None:
        if not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please enter a refresh token",
            )


async def get_currect_user(
    token_data: Annotated[dict, Depends(AccessToken())],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ## get the user email and password for get service
    user_email = token_data["user"]["user_email"]
    user_password = token_data["user"]["user_password"]

    ## use the get service
    user = await service.get_user_by_email(
        email=user_email,
        password=user_password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The user is not found ❌"
        )

    return user


## Roles class
class UsersRoles:
    def __init__(self, available_roles: List[str]):
        ## add the attribute
        self.available_roles = available_roles

    async def __call__(self, user: Annotated[UserModel, Depends(get_currect_user)]):
        ## check the user roles
        if user.role in self.available_roles:
            return True

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have no role to make this request"
        )
