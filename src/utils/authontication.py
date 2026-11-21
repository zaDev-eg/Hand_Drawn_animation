
import logging
import uuid

from datetime import datetime, timedelta, timezone

import jwt

from fastapi import HTTPException

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired,
)

from .config import jwt_settings


serializer = URLSafeTimedSerializer(
    secret_key=jwt_settings.JWT_SECRET_KEY,
    salt="email_verification",
)


password_reset_serializer = URLSafeTimedSerializer(
    secret_key=jwt_settings.JWT_SECRET_KEY,
    salt="password_reset",
)


ACCESS_TOKEN_EXPIRY = 15 * 60
PASSWORD_RESET_EXPIRY = 30 * 60


def create_access_token(
    user_data: dict,
    expire: timedelta | None = None,
    refresh: bool = False,
):

    payload = {
        "user": user_data,
        "exp": datetime.now(timezone.utc) + (
            expire or timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        ),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }

    token = jwt.encode(
        payload,
        jwt_settings.JWT_SECRET_KEY,
        algorithm=jwt_settings.JWT_ALGORITHM,
    )

    return token


def varify_access_token(token: str):

    try:

        return jwt.decode(
            token,
            jwt_settings.JWT_SECRET_KEY,
            algorithms=[jwt_settings.JWT_ALGORITHM],
        )

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        )

    except jwt.PyJWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


def create_url_safe_token(data: dict) -> str:

    return serializer.dumps(data)


def varify_url_safe_token(
    token: str,
    max_age: int = 3600,
) -> dict | None:

    try:

        return serializer.loads(
            token,
            max_age=max_age,
        )

    except (SignatureExpired, BadSignature):

        return None

    except Exception:

        logging.exception(
            "Verification token could not be decoded"
        )

        return None


def create_password_reset_token(data: dict) -> str:

    return password_reset_serializer.dumps(data)


def varify_password_reset_token(
    token: str,
    max_age: int = PASSWORD_RESET_EXPIRY,
) -> dict | None:

    try:

        return password_reset_serializer.loads(
            token,
            max_age=max_age,
        )

    except (SignatureExpired, BadSignature):

        return None

    except Exception:

        logging.exception(
            "Password reset token could not be decoded"
        )

        return None