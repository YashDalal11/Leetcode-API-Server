from fastapi import APIRouter, HTTPException
from leetcode.services.problem import get_daily_problem, get_problem_detail, get_similar_problems
from store import cookie_store

router = APIRouter(
    prefix="/leetcode/problems",
    tags=["LeetCode Problems"],
)

@router.get("/problem-detail/{username}/{titleSlug}")
async def problem_detail(username: str, titleSlug: str):    
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    problem_detail = await get_problem_detail(
        username=username,
        titleSlug=titleSlug
    )

    if not problem_detail:
        raise HTTPException(
            status_code=404,
            detail="Problem detail not found"
        )

    return problem_detail

@router.get("/similar-problems/{username}/{titleSlug}")
async def similar_problems(username: str, titleSlug: str):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    similar_problems = await get_similar_problems(
        username=username,
        titleSlug=titleSlug
    )

    if not similar_problems:
        raise HTTPException(
            status_code=404,
            detail="Similar problems not found"
        )

    return similar_problems

@router.get("/daily-problem/{username}")
async def daily_problem(username: str):
    if username not in cookie_store:
        raise HTTPException(
            status_code=404,
            detail="User not connected"
        )

    daily_problem = await get_daily_problem(
        username=username
    )

    if not daily_problem:
        raise HTTPException(
            status_code=404,
            detail="Daily problem not found"
        )

    return daily_problem

