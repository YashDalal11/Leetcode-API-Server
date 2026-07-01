import httpx

from common_utils.constants import GRAPHQL_URL, LEETCODE_BASE_URL

async def graphql_request(
    query: str,
    variables: dict,
    cookies: dict,
):
    headers = {
        "Referer": LEETCODE_BASE_URL,
        "x-csrftoken": cookies["csrftoken"],
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "variables": variables,
            },
            headers=headers,
            cookies=cookies,
        )

    response.raise_for_status()


    return response.json()