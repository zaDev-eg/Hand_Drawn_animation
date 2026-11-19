
import logging
import jwt
import uuid
from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta, timezone
from .config import jwt_settings

## take instances 
serializer = URLSafeTimedSerializer(
    secret_key=jwt_settings.JWT_SECRET_KEY,
    salt="email_varification"
)


## variables
ACCESS_TOKEN_EXPIRY = 60


## method that will create the access token
def create_access_token(
    user_data: dict, expire: timedelta = None, refresh: bool = False
):
    ## create an empty payload
    payload = {}

    ## fill the payload
    payload["user"] = user_data
    payload["exp"] = datetime.now(timezone.utc) + (
        expire if expire is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY)
    )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh

    ## encode the data in the token
    token = jwt.encode(
        key=jwt_settings.JWT_SECRET_KEY,
        algorithm=jwt_settings.JWT_ALGORITHM,
        payload=payload,
    )

    ## return the token
    return token


## method that will varify the access token
def varify_access_token(token: str):
    try:
        return jwt.decode(
            jwt=token,
            key=jwt_settings.JWT_SECRET_KEY,
            algorithms=[jwt_settings.JWT_ALGORITHM],
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Access token has expired",
        )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )


## create a varification token
def create_url_safe_token(data: dict): 
    
    ## create the token 
    token = serializer.dumps(data)
    
    ## get back the tokne 
    return token

## varify the urltoken
def varify_url_safe_token(token: str): 
    
    try: 
        ## decode the token
        token_data = serializer.loads(token)
        
        ## return the token data 
        return token_data
    except Exception as e: 
        logging.exception(e)
        return None