from pydantic import BaseModel


class CookiePayload(BaseModel):
    leetcode_session: str
    csrf_token: str