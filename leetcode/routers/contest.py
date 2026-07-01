from http.client import HTTPException

from fastapi import APIRouter
from leetcode.services.contest import get_contest_history, get_contest_question, get_contest_rating, get_contest_result, get_upcoming_contests
from store import cookie_store

router = APIRouter(
    prefix="/leetcode/contest",
    tags=["LeetCode Contests"],
)


@router.get("/contest-rating/{username}")
async def contest_rating(username: str):
    if username not in cookie_store:
        return {"error": "User not connected"}

    contest_rating_data = await get_contest_rating(username=username)

    if not contest_rating_data:
        return {"error": "Contest rating not found"}

    return contest_rating_data

@router.get("/contest-history/{username}")
async def contest_history(username: str):
    if username not in cookie_store:
        return {"error": "User not connected"}

    contest_history_data = await get_contest_history(username=username)

    if not contest_history_data:
        return {"error": "Contest history not found"}

    return contest_history_data

@router.get("/contest-question/{username}/{contest_slug}")
async def contest_question(username: str, contest_slug: str):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    contest_question = await get_contest_question(
        username=username,
        contest_slug=contest_slug
    )

    if not contest_question:
        raise HTTPException(
            status_code=404,
            detail="Contest question not found"
        )

    return contest_question

@router.get("/contest-result/{username}/{contest_slug}")
async def contest_result(username: str, contest_slug: str):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    contest_result_data = await get_contest_result(
        username=username,
        contest_slug=contest_slug
    )

    if not contest_result_data:
        raise HTTPException(
            status_code=404,
            detail="Contest result not found"
        )

    return contest_result_data

@router.get("/upcoming-contests/{username}")
async def upcoming_contests(username: str):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    upcoming_contests_data = await get_upcoming_contests(username=username)

    if not upcoming_contests_data:
        raise HTTPException(
            status_code=404,
            detail="Upcoming contests not found"
        )

    return upcoming_contests_data
