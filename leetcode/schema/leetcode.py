from pydantic import BaseModel, Field


class ConnectLeetcodeRequest(BaseModel):
    leetcode_session: str = Field(
        min_length=1,
    )

    csrf_token: str = Field(
        min_length=1,
    )