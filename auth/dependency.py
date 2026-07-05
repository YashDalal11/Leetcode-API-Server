from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from auth.service import AuthService
from database.session import get_db
from exception.auth import AuthenticationError
from model.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials
    try:
        return AuthService.authenticate(token, db)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=e.message,
        )