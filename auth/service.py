from http.client import HTTPException

from alembic.util import status
from click import UUID
from sqlalchemy.orm import Session

from auth.jwt import verify_token
from model.user import User

from exception.auth import AuthenticationError


class AuthService:

    @staticmethod
    def save_google_user(db: Session, google_user: dict) -> User:
        """
        Create a new user or update an existing user using Google profile.
        """

        user = (
            db.query(User)
            .filter(User.google_sub == google_user["sub"])
            .first()
        )

        if user:
            # Update latest profile info
            user.email = google_user["email"]
            user.name = google_user["name"]
            user.picture = google_user.get("picture")

        else:
            # Create new user
            user = User(
                google_sub=google_user["sub"],
                email=google_user["email"],
                name=google_user["name"],
                picture=google_user.get("picture"),
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        return user
    
    @staticmethod
    def authenticate(
        token: str,
        db: Session,
    ) -> User:

        try:

            payload = verify_token(token)

            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )

        except Exception as e:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            )

        try:

            user_id = UUID(payload["sub"])

        except Exception:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user id",
            )

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if user is None:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

