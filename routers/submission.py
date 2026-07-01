from fastapi import APIRouter, HTTPException
from services.submission import get_latest_submission, get_submission_detail, get_submission_history, get_submissions
from store import cookie_store

router = APIRouter(
    prefix="/leetcode/submission",
    tags=["LeetCode Submission"],
)

@router.get("/latest-submission/{username}")
async def latest_submission(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    return await get_latest_submission(
        username=username,
    )

@router.get("/review-latest-submission/{username}")
async def review_latest_submission(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    latest = await get_latest_submission(
        username=username,
    )

    detail = await get_submission_detail(
        username=username,
        submission_id=latest["submission_id"],
    )

    return detail


@router.get("/submission-detail/{username}/{submission_id}")
async def submission_detail(username: str, submission_id: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    detail = await get_submission_detail(
        username=username,
        submission_id=submission_id,
    )

    return detail

@router.get("/{username}")
async def submissions(username: str, limit: int = 20,offset: int = 0):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    submissions = await get_submissions(
        username=username,
        limit=limit,
        offset=offset
    )

    return submissions

@router.get("/submissions-history/{username}/{questionSlug}")
async def submissions_history(username: str, questionSlug: str, limit: int = 20, offset: int = 0):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    submissions = await get_submission_history(
        username=username,
        questionSlug=questionSlug,
        limit=limit,
        offset=offset
    )

    return submissions

