from common_utils.common_fuctions import graphql_request
from leetcode.services.graphql.queries import GET_DAILY_PROBLEM_QUERY, GET_PROBLEM_DETAIL_QUERY, GET_SIMILAR_PROBLEMS_QUERY
from store import cookie_store

async def get_problem_detail(
    username: str,
    titleSlug: str,
):
    """
    Get problem detail of a user for a specific question.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_PROBLEM_DETAIL_QUERY,
        variables ={
            "username": username,
            "titleSlug": titleSlug
        },
        cookies=cookies,
    )

    problem_detail = result.get("data", {}).get("question",{})

    if not problem_detail:
        return None

    return problem_detail

async def get_similar_problems(
    username: str,
    titleSlug: str,
):
    """
    Get similar problems of a user for a specific question.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_SIMILAR_PROBLEMS_QUERY,
        variables ={
            "username": username,
            "titleSlug": titleSlug
        },
        cookies=cookies,
    )

    similar_problems = result.get("data", {}).get("question",{}).get("similarQuestionList", [])
    nextChallenges = result.get("data", {}).get("question",{}).get("nextChallenges", [])

    return {
        "similar_problems": similar_problems,
        "nextChallenges": nextChallenges
    }

async def get_daily_problem(
    username: str,
):
    """
    Get daily problem of a user.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_DAILY_PROBLEM_QUERY,
        variables ={
            "username": username,
            "titleSlug": "daily-challenge"
        },
        cookies=cookies,
    )

    daily_problem = result.get("data", {}).get("activeDailyCodingChallengeQuestion", {})

    if not daily_problem:
        return None

    return daily_problem