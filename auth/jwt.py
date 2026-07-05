from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError,
)

from config import settings


def create_access_token(user_id: UUID) -> str:
    """
    Create an access token.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a refresh token.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token,expire


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT.
    Raises an exception if invalid.
    """

    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )

    return payload


def verify_token(token: str) -> dict | None:
    """
    Verify token safely.
    Returns payload if valid else None.
    """

    try:
        payload = decode_token(token)
        return payload

    except ExpiredSignatureError:
        print("Token has expired.")  # Debugging line
        return None

    except InvalidTokenError:
        print("Invalid token.")  # Debugging line
        return None
    
def get_user_id(token: str) -> UUID:
    payload = verify_token(token)

    return UUID(payload["sub"])