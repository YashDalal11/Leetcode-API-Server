import httpx

from common_utils.common_fuctions import graphql_request
from services.graphql.queries import GET_LANG_STATS_QUERY, GET_SOLVED_STATS, GET_TOPIC_STATS_QUERY, GET_USER_PUBLIC_PROFILE_QUERY

from store import cookie_store

async def get_profile(username: str):

    try:
        cookies = cookie_store[username]
        result = await graphql_request(
            query=GET_USER_PUBLIC_PROFILE_QUERY,
            variables={"username": username},
            cookies=cookies,
        )
    except httpx.TimeoutException:
        raise Exception("Request to LeetCode timed out.")
    except httpx.HTTPError as e:
        raise Exception(f"HTTP error occurred: {str(e)}")

    user = result["data"]
    return user


async def get_solved_stats(username: str):
    cookies = cookie_store[username]

    try:
        result = await graphql_request(
            query=GET_SOLVED_STATS,
            variables={"username": username},
            cookies=cookies,
        )
    except httpx.TimeoutException:
        raise Exception("Request to LeetCode timed out.")
    except httpx.HTTPError as e:
        raise Exception(f"HTTP error occurred: {str(e)}")

    stats = result["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]

    return {stat["difficulty"]: stat["count"] for stat in stats}

async def get_ranking_and_contributions(username: str):
    cookies = cookie_store[username]

    try:
        result = await graphql_request(
            query=GET_SOLVED_STATS,
            variables={"username": username},
            cookies=cookies,
        )
    except httpx.TimeoutException:
        raise Exception("Request to LeetCode timed out.")
    except httpx.HTTPError as e:
        raise Exception(f"HTTP error occurred: {str(e)}")

    user_data = result["data"]["matchedUser"]
    ranking = user_data["profile"]["ranking"]
    contributions = user_data["contributions"]["points"]

    return {
        "ranking": ranking,
        "contributions": contributions
    }

async def get_topic_stats(username: str):
    cookies = cookie_store[username]

    try:
        result = await graphql_request(
            query=GET_TOPIC_STATS_QUERY,
            variables={"username": username},
            cookies=cookies,
        )
    except httpx.TimeoutException:
        raise Exception("Request to LeetCode timed out.")
    except httpx.HTTPError as e:
        raise Exception(f"HTTP error occurred: {str(e)}")

    topic_stats = result["data"]["matchedUser"]["tagProblemCounts"]

    return {
        "advanced": {stat["tagName"]: stat["problemsSolved"] for stat in topic_stats["advanced"]},
        "intermediate": {stat["tagName"]: stat["problemsSolved"] for stat in topic_stats["intermediate"]},
        "fundamental": {stat["tagName"]: stat["problemsSolved"] for stat in topic_stats["fundamental"]},
    }

async def get_language_stats(username: str):
    cookies = cookie_store[username]

    try:
        result = await graphql_request(
            query=GET_LANG_STATS_QUERY,
            variables={"username": username},
            cookies=cookies,
        )
    except httpx.TimeoutException:
        raise Exception("Request to LeetCode timed out.")
    except httpx.HTTPError as e:
        raise Exception(f"HTTP error occurred: {str(e)}")

    lang_stats = result["data"]["matchedUser"]["languageProblemCount"]

    return {stat["languageName"]: stat["problemsSolved"] for stat in lang_stats}