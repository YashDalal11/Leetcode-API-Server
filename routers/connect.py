
from models import CookiePayload
from services.submission import verify_cookies
from fastapi import APIRouter, HTTPException

from store import cookie_store

router = APIRouter(
    prefix="/connect",
    tags=["Connect"],
)

@router.post("/")
async def connect(payload: CookiePayload):

    try:
        result = await verify_cookies(
            payload.leetcode_session,
            payload.csrf_token,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=401,
                detail=result["error"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify LeetCode session: {str(e)}"
        )
    
    username = result["username"]
    
    if username in cookie_store:
        # Update cookies only
        cookie_store[username]["LEETCODE_SESSION"] = payload.leetcode_session
        cookie_store[username]["csrftoken"] = payload.csrf_token
        
        return {
            "success": True,
            "message": "Successfully connected.",
            "username": username
        }


    cookie_store[username] = {
        "username": username,
        "LEETCODE_SESSION": payload.leetcode_session,
        "csrftoken": payload.csrf_token,
    }

    return {
        "success": True,
        "username": username,
        "message": "Successfully connected."
    }