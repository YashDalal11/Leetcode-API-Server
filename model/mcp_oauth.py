import datetime
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base

class McpOAuthClient(Base):
    __tablename__ = "mcp_oauth_clients"

    client_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    client_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_name: Mapped[str] = mapped_column(String(255))
    redirect_uris: Mapped[list[str]] = mapped_column(JSON)
    grant_types: Mapped[list[str]] = mapped_column(JSON)
    response_types: Mapped[list[str]] = mapped_column(JSON)
    scope: Mapped[str] = mapped_column(String(255))
    token_endpoint_auth_method: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class McpOAuthSession(Base):
    __tablename__ = "mcp_oauth_sessions"

    google_state: Mapped[str] = mapped_column(String(255), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255))
    redirect_uri: Mapped[str] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_challenge: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class McpOAuthCode(Base):
    __tablename__ = "mcp_oauth_codes"

    code: Mapped[str] = mapped_column(String(255), primary_key=True)
    code_challenge: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_info: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class McpOAuthRefreshToken(Base):
    __tablename__ = "mcp_oauth_refresh_tokens"

    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255))
    scopes: Mapped[list[str]] = mapped_column(JSON)
    user_info: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
