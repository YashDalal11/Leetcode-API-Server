from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    # JWT_SECRET: str
    COOKIE_ENCRYPTION_KEY: str
    DATABASE_URL: str

    JWT_SECRET: str

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MCP_BASE_URL: str

    @field_validator("MCP_BASE_URL", mode="before")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    class Config:
        env_file = ".env"
        extra="ignore"  # Ignore unknown variables


settings = Settings()
