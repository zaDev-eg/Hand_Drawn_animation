from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from typing import List
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime

from src.utils.authontication import create_access_token, create_url_safe_token, varify_url_safe_token
from ..schemas.request_schema import GetUser, CreateUser, UpdateUser, Login_User, MailSchema
from ..database.db_connection import get_session
from ..services.user_crud_logic import UserService
from ..utils.authorization import AccessToken, RefreshToken, UsersRoles
from ..utils.config import mail_settings
from ..database.redis_connection import add_tokens_to_blocklist
from ..utils.celery import send_message


## take instances
user_router = APIRouter()
service = UserService(Depends(get_session))
roles = Depends(UsersRoles(["admin", "user"]))

##------------>
## End Points
##------------>


## Get methods
@user_router.get("/", response_model=List[GetUser])
async def get_all_users():
    ## user the service
    users = await service.get_all_users()

    ## check
    if users is not None:
        return users
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no users yet ❌",
        )


@user_router.get("/user/{email}", response_model=GetUser, dependencies=[roles])
async def get_user(
    email: str,
    password: str,
):
    ## get the user
    user = await service.get_user_by_email(email, password)

    ## check
    if user is not None:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user is not found ❌ or wrong in password",
        )


## get the verification token and make sure the user is verified
@user_router.get("/verify/{token}")
async def verify_user_account(
    token: str,
):
    ## first we will decode the token to get the user data
    token_data = varify_url_safe_token(token=token)

    ## get back the user email and password from the token
    user_email = token_data["email"]
    user_password = token_data["password"]

    ## check
    if user_email is not None and user_password is not None:
        ## get the user back
        user = await service.get_user_by_email(
            email=user_email,
            password=user_password,
        )

        ## check
        if user is not None:
            await service.verify_user_email(
                user=user,
                updated_data={"is_varified": True},
            )
            return JSONResponse(
                content={"message": "The user is verified successfully✅"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="the user is not found ❌"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is some thing wrong with user email and password ❌",
        )


## get a new access token
@user_router.get("/refresh_token")
async def refresh_access_token(
    token_data: Annotated[dict, Depends(RefreshToken())],
):
    ## get the expiration time
    expiration_timestap = token_data["exp"]

    ## check if the access token is still alive
    if datetime.fromtimestamp(expiration_timestap) > datetime.now():
        ## create a new access token
        access_token = create_access_token(user_data=token_data["user"])

        return JSONResponse(content={"New Access Token": access_token})

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired token"
    )


@user_router.get("/logout")
async def user_logout(
    token_data: Annotated[dict, Depends(AccessToken())],
):
    ## add the token to the blocklist
    await add_tokens_to_blocklist(token_data)

    return JSONResponse(
        content={"message": "The token is added to the block list Successfully ✅"}
    )


## Post methods
@user_router.post(
    "/",
)
async def add_user(
    user_data: CreateUser,
):
    ## add the new user
    new_user = await service.create_user(user_data)

    if new_user is not None:

        ## create the url_safe_token
        token = create_url_safe_token(
            {
                "email": new_user.email,
                "password": new_user.hashed_password,
            }
        )

        ## prepare the link that the user will use to varify his/her email
        Link = f"http://{mail_settings.DOMAIN_NAME}/api/v1/users/verify/{token}"

        ## create the body of the message that will be sent by email
        html_message = f"""
        <h1>Verification Mail</h1>
        <p>Please press this link:
        <a href="{Link}">Link</a>
        </p>
        """

        ## use Celery for BackGroundTasks
        send_message.delay(
            recipients=[new_user.email],
            subject="Varification Message",
            body=html_message,
        )

        return {
            "message": "check your email to verify your email",
            "new_use": new_user,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user is already exist ❌",
        )


@user_router.post("/login")
async def user_login(
    user_data: Login_User,
):
    ## get the user by email and password
    user = await service.get_user_by_email(
        user_data.email,
        user_data.password,
    )

    ## check if the user is exist
    if user is not None:
        ## create an access token
        access_token = create_access_token(
            user_data={
                "user_uid": str(user.uid),
                "user_email": user.email,
                "user_password": user.hashed_password,
            }
        )

        ## create a refresh token
        refresh_token = create_access_token(
            user_data={
                "user_uid": str(user.uid),
                "user_email": user.email,
                "user_password": user.hashed_password,
            },
            refresh=True,
            expire=timedelta(days=2),
        )

        ## return results
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "user_uid": user.uid,
                "username": user.username,
                "user_email": user.email,
            },
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="the user is not found or the wrong in password or email ❌",
        )


## sending email service
@user_router.post("/mail")
async def send_mails(
    recipients: MailSchema,
):
    ## prepare the parameters for the message
    html = "<h>Welcom to our Bookly Store</h>"

    ## use Celery as a BackGroundTask for sending messages
    send_message.delay(
        recipients=recipients,
        subject="Welcom Message",
        body=html,
    )

    return JSONResponse(content={"message": "The mail is sent successfully ✅"})


## Update methods
@user_router.patch("/", response_model=GetUser)
async def update_user(
    email: str,
    password: str,
    updated_data: UpdateUser,
):
    ## update the already exist user
    updated_user = await service.update_user(
        email,
        password,
        updated_data,
    )

    ## check
    if updated_user is not None:
        return updated_user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user is not found ❌ or wrong in the password",
        )


## Delete methods
@user_router.delete("/")
async def delete_user(
    email: str,
    password: str,
) -> dict:
    ## delete the user
    check = await service.delete_user(email, password)

    ## check
    if check is not None:
        return {"message": "The user is deleted Successfully ✅"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user is not found ❌ or wrong in the password",
        )
