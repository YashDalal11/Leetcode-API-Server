from common_utils.common_fuctions import graphql_request
from leetcode.services.graphql.queries import GET_CONTEST_HISTORY_QUERY, GET_CONTEST_QUESTION_QUERY, GET_CONTEST_RATING_QUERY, GET_UPCOMING_CONTESTS_QUERY
from store import cookie_store

async def get_contest_rating(username:str):
    """
    Get contest rating of a user.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_CONTEST_RATING_QUERY,
        variables ={
            "username": username,
        },
        cookies=cookies,
    )

    contest_rating = result.get("data", {}).get("userContestRanking",{})

    if not contest_rating:
        return None

    return contest_rating

async def get_contest_history(username:str):
    """
    Get contest history of a user.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_CONTEST_HISTORY_QUERY,
        variables ={
            "username": username,
        },
        cookies=cookies,
    )

    contest_history = result.get("data", {}).get("userContestRankingHistory",{})

    if not contest_history:
        return None

    return contest_history


async def get_contest_question(username:str, contest_slug:str):
    """
    Get contest question of a user.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_CONTEST_QUESTION_QUERY,
        variables ={
            "contestSlug": contest_slug,
        },
        cookies=cookies,
    )

    contest_question = result.get("data", {}).get("contestQuestionList",{})

    if not contest_question:
        return None

    return contest_question

async def get_contest_result(
    username: str,
    contest_slug: str,
):
    cookies = cookie_store.get(username)

    result = await graphql_request(
        query=GET_CONTEST_HISTORY_QUERY,
        variables={"username": username},
        cookies=cookies,
    )

    history = result.get("data", {}).get("userContestRankingHistory",{})

    for contest in history:
        if not contest["attended"]:
            continue

        if contest["contest"]["titleSlug"] == contest_slug:
            return {
                "participated": True,
                "contest": {
                    "title": contest["contest"]["title"],
                    "slug": contest["contest"]["titleSlug"],
                    "startTime": contest["contest"]["startTime"],
                },
                "result": {
                    "rating": contest["rating"],
                    "rank": contest["ranking"],
                    "problemsSolved": contest["problemsSolved"],
                    "totalProblems": contest["totalProblems"],
                    "finishTimeSeconds": contest["finishTimeInSeconds"],
                    "trend": contest["trendDirection"],
                },
            }

    return {
        "participated": False,
        "message": "Contest not found or user did not participate.",
    }

async def get_upcoming_contests(username: str):
    """
    Get upcoming contests of a user.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_UPCOMING_CONTESTS_QUERY,
        variables ={},
        cookies=cookies,
    )
    print(result)

    upcoming_contests = result.get("data", {}).get("topTwoContests",{})

    if not upcoming_contests:
        return None

    return upcoming_contests