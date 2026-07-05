import httpx

from common_utils.constants import GRAPHQL_URL, LEETCODE_BASE_URL
from cryptography.fernet import Fernet

from config import settings

cipher = Fernet(
    settings.COOKIE_ENCRYPTION_KEY.encode()
)


def encrypt_cookie(cookie: dict) -> str:
    return cipher.encrypt(
        str(cookie).encode()
    ).decode()


def decrypt_cookie(cookie: str) -> dict:
    return eval(cipher.decrypt(
        cookie.encode()
    ).decode())

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
