from fastapi import APIRouter, HTTPException
from services.profile import get_language_stats, get_profile, get_ranking_and_contributions, get_solved_stats, get_topic_stats
from store import cookie_store

router = APIRouter(
    prefix="/leetcode/profile",
    tags=["profile"],
)


@router.get("/{username}")
async def profile(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected."
        )

    return await get_profile(
        username
    )

@router.get("/{username}/solved-stats")
async def solved_stats(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected."
        )

    return await get_solved_stats(
        username
    )

@router.get("/{username}/ranking-and-contributions")
async def ranking_and_contributions(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected."
        )

    return await get_ranking_and_contributions(
        username
    )

@router.get("/{username}/topic-stats")
async def topic_stats(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected."
        )

    return await get_topic_stats(
        username
    )

@router.get("/{username}/language-stats")
async def language_stats(username: str):

    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected."
        )

    return await get_language_stats(
        username
    )