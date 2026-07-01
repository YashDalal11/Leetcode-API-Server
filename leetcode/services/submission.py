import httpx

from common_utils.common_fuctions import graphql_request
from common_utils.constants import GRAPHQL_URL, LEETCODE_BASE_URL
from leetcode.services.graphql.queries import GET_SUBMISSION_LIST_QUERY, GET_SUBMISSIONS_QUERY, GET_SUBMISSION_QUERY, LATEST_SUBMISSION_QUERY, VERIFY_COOKIES_QUERY
from store import cookie_store

async def verify_cookies(
    leetcode_session: str,
    csrf_token: str,
) -> dict:
    """
    Verify LeetCode cookies.

    Returns:
    {
        "success": True,
        "username": "yash"
    }

    or

    {
        "success": False,
        "error": "Invalid or expired session"
    }
    """

    headers = {
        "Referer": LEETCODE_BASE_URL,
        "x-csrftoken": csrf_token,
    }

    cookies = {
        "LEETCODE_SESSION": leetcode_session,
        "csrftoken": csrf_token,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                GRAPHQL_URL,
                json={"query": VERIFY_COOKIES_QUERY},
                headers=headers,
                cookies=cookies,
            )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"LeetCode returned HTTP {response.status_code}"
            }

        data = response.json()

        if "errors" in data:
            return {
                "success": False,
                "error": data["errors"][0]["message"]
            }

        user_status = data.get("data", {}).get("userStatus")

        if not user_status:
            return {
                "success": False,
                "error": "Unable to fetch user status."
            }

        if not user_status.get("isSignedIn"):
            return {
                "success": False,
                "error": "Invalid or expired LeetCode session."
            }

        return {
            "success": True,
            "username": user_status["username"]
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request to LeetCode timed out."
        }

    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": str(e)
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error while verifying cookies."
        }

async def get_latest_submission(
    username: str,
):
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=LATEST_SUBMISSION_QUERY,
        variables={
            "username": username
        },
        cookies=cookies,
    )

    submissions = result["data"]["recentSubmissionList"]

    if not submissions:
        return None

    latest = submissions[0]

    return {
        "submission_id": latest["id"],
        "title": latest["title"],
        "title_slug": latest["titleSlug"],
        "status": latest["statusDisplay"],
        "language": latest["lang"],
        "timestamp": latest["timestamp"],
    }

async def get_submission_detail(
    username: str,
    submission_id: str,
):

    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_SUBMISSION_QUERY,
        variables={
            "username": username,
            "submissionId": submission_id,
        },
        cookies=cookies,
    )

    submission = result["data"]["submissionDetails"]

    return {
        "question_id": submission["question"]['questionId'],
        "titleSlug": submission["question"]["titleSlug"],
        "status": submission["statusCode"],
        "language": submission["lang"],
        "timestamp": submission["timestamp"],
        "code": submission["code"],
        "memory": submission["memory"],
        "memoryDisplay": submission["memoryDisplay"],
        "memoryPercentile": submission["memoryPercentile"],
        "totalCorrect": submission["totalCorrect"],
        "totalTestcases": submission["totalTestcases"],
        "runtimeError":submission["runtimeError"],
        "compileError":submission["compileError"],
        "lastTestcase":submission["lastTestcase"],
        "codeOutput":submission["codeOutput"],
        "expectedOutput":submission["expectedOutput"],
        "fullCodeOutput":submission["fullCodeOutput"],
    }

async def get_submissions(
    username: str,limit: int = 20,offset:int = 0
):
    # max limit is 20, if user requests more than 20, we will return only 20
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_SUBMISSIONS_QUERY,
        variables ={
            "username": username,
            "limit": limit,
            "offset": offset,
            "lastKey": None,
            "questionSlug": None,
            "status": None,
            "lang": None,
        },
        cookies=cookies,
    )

    submissions = result.get("data", {}).get("submissionList",{}).get("submissions",[])
    lastKey = result.get("data", {}).get("submissionList",{}).get("lastKey",None)
    hasNext = result.get("data", {}).get("submissionList",{}).get("hasNext",False)

    return {
        "count": min(limit, len(submissions)),
        "lastKey": lastKey,
        "hasNext": hasNext,
        "submissions": submissions,
    }

async def get_submission_history(
    username: str,
    questionSlug: str = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get submission history of a user for a specific question.
    """
    cookies = cookie_store.get(username)
    result = await graphql_request(
        query=GET_SUBMISSION_LIST_QUERY,
        variables ={
            "username": username,
            "limit": limit,
            "offset": offset,
            "lastKey": None,
            "questionSlug": questionSlug,
            "status": None,
            "lang": None,
        },
        cookies=cookies,
    )

    submissions = result.get("data", {}).get("questionSubmissionList",{}).get("submissions",[])
    lastKey = result.get("data", {}).get("questionSubmissionList",{}).get("lastKey",None)
    hasNext = result.get("data", {}).get("questionSubmissionList",{}).get("hasNext",False)

    return {
        "count": min(limit, len(submissions)),
        "lastKey": lastKey,
        "hasNext": hasNext,
        "submissions": submissions,
    }



