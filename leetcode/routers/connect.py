
from auth.dependency import get_current_user
from common_utils.common_fuctions import decrypt_cookie
from leetcode.schema.leetcode import ConnectLeetcodeRequest
from leetcode.services.connect import LeetcodeService
from model.leetcode_account import LeetcodeAccount
from model.user import User
from models import CookiePayload
from leetcode.services.submission import verify_cookies
from fastapi import APIRouter, Depends

from store import cookie_store
from sqlalchemy.orm import Session 

from database.session import get_db

router = APIRouter(
    prefix="/leetcode",
    tags=["leetcode"],
)

# @router.post("/connect")
# async def connect(payload: CookiePayload):

#     try:
#         result = await verify_cookies(
#             payload.leetcode_session,
#             payload.csrf_token,
#         )

#         if not result["success"]:
#             raise HTTPException(
#                 status_code=401,
#                 detail=result["error"]
#             )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to verify LeetCode session: {str(e)}"
#         )
    
#     username = result["username"]
    
#     if username in cookie_store:
#         # Update cookies only
#         cookie_store[username]["LEETCODE_SESSION"] = payload.leetcode_session
#         cookie_store[username]["csrftoken"] = payload.csrf_token
        
#         return {
#             "success": True,
#             "message": "Successfully connected.",
#             "username": username
#         }


#     cookie_store[username] = {
#         "username": username,
#         "LEETCODE_SESSION": payload.leetcode_session,
#         "csrftoken": payload.csrf_token,
#     }

#     return {
#         "success": True,
#         "username": username,
#         "message": "Successfully connected."
#     }

@router.get("/status")
async def leetcode_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    account = (
        db.query(LeetcodeAccount)
        .filter(
            LeetcodeAccount.user_id == current_user.id
        )
        .first()
    )

    if not account:
        return {
            "connected": False,
        }

    # Decrypt cookies
    cookies = decrypt_cookie(account.encrypted_cookies)

    valid = await verify_cookies(
        cookies["LEETCODE_SESSION"],
        cookies["csrftoken"],
    )

    if not valid:

        # Optional:
        # account.encrypted_cookies = None
        # db.commit()

        return {
            "connected": False,
            "reason": "cookies_expired",
        }

    return {
        "connected": True,
        "username": account.leetcode_username,
    }

@router.post("/connect")
async def connect_leetcode(
    body: ConnectLeetcodeRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    account = await LeetcodeService.connect_account(
        db=db,
        user=current_user,
        leetcode_session=body.leetcode_session,
        csrf_token=body.csrf_token,
    )

    return {
        "message": "Leetcode account connected.",
        "username": account.leetcode_username,
    }