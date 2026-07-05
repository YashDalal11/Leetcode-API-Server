import hashlib

from sqlalchemy.orm import Session

from model.refresh_token import RefreshToken


class TokenService:

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def save_refresh_token(
        db: Session,
        user_id,
        refresh_token: str,
        expires_at,
    ):
        token = RefreshToken(
            user_id=user_id,
            token_hash=TokenService.hash_token(refresh_token),
            expires_at=expires_at,
        )

        db.add(token)
        db.commit()
        db.refresh(token)

        return token
    
    @staticmethod
    def get_refresh_token(
        db: Session,
        refresh_token: str,
    ) -> RefreshToken | None:

        hashed_token = TokenService.hash_token(refresh_token)

        return (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == hashed_token,
                RefreshToken.revoked == False,
            )
            .first()
        )
    
    @staticmethod
    def revoke_refresh_token(
        db: Session,
        refresh_token: str,
    ):

        token = TokenService.get_refresh_token(
            db=db,
            refresh_token=refresh_token,
        )

        if not token:
            return False

        token.revoked = True
        db.commit()


        return True