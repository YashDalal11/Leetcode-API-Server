from datetime import datetime
from http.client import HTTPException

from sqlalchemy.orm import Session

from common_utils.common_fuctions import encrypt_cookie
from leetcode.services.submission import verify_cookies
from model.leetcode_account import LeetcodeAccount


class LeetcodeService:

    @staticmethod
    async def connect_account(
        db: Session,
        user,
        leetcode_session: str,
        csrf_token: str,
    ):
        result = await verify_cookies(
            leetcode_session,
            csrf_token,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=401,
                detail=result["error"]
            )

        account = (
            db.query(LeetcodeAccount)
            .filter(
                LeetcodeAccount.user_id == user.id
            )
            .first()
        )

        encrypted = encrypt_cookie(
            {
                "LEETCODE_SESSION": leetcode_session,
                "csrftoken": csrf_token,
            }
        )

        if account:

            account.leetcode_username = result.get("username")
            account.encrypted_cookies = encrypted
            account.last_synced = datetime.utcnow()

        else:

            account = LeetcodeAccount(
                user_id=user.id,
                leetcode_username=result.get("username"),
                encrypted_cookies=encrypted,
                last_synced=datetime.utcnow(),
            )

            db.add(account)

        db.commit()
        db.refresh(account)

        return account