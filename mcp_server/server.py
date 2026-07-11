import os
import sys
import secrets
import time
import logging
import jwt
import uvicorn
import httpx
from uuid import UUID
from pathlib import Path
from urllib.parse import urlencode
from pydantic import AnyHttpUrl
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

# Add project root directory to sys.path to resolve root-level imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from database.session import SessionLocal
from model.user import User
from model.leetcode_account import LeetcodeAccount
from config import settings
from common_utils.common_fuctions import decrypt_cookie
from store import cookie_store
from leetcode.services.connect import LeetcodeService
from leetcode.services.profile import (
    get_profile,
    get_solved_stats,
    get_ranking_and_contributions,
    get_topic_stats,
    get_language_stats,
)
from leetcode.services.problem import (
    get_problem_detail,
    get_similar_problems,
    get_daily_problem,
)
from leetcode.services.contest import (
    get_contest_rating,
    get_contest_history,
    get_contest_question,
    get_contest_result,
    get_upcoming_contests,
)
from leetcode.services.submission import (
    get_latest_submission,
    get_submission_detail,
    get_submissions,
    get_submission_history,
)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Base URLs and Google Credentials
# PUBLIC_URL = os.environ.get("MCP_BASE_URL", "http://localhost:8000").rstrip("/")
PUBLIC_URL = settings.MCP_BASE_URL.rstrip("/")
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET


class InMemoryOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """Simple in-memory OAuth 2.1 Provider with Google Authentication."""

    def __init__(self):
        self.clients = {}
        self.codes = {}
        self.refresh_tokens = {}
        self.refresh_to_user = {}
        self.auth_sessions = {}
        self.JWT_SECRET = secrets.token_urlsafe(32)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        if client_id in self.clients:
            return self.clients[client_id]

        # Fallback for mock clients
        auth_method = "client_secret_post" if client_id == "test-client" else "none"
        secret = "test-secret" if client_id == "test-client" else None

        return OAuthClientInformationFull(
            client_id=client_id,
            client_secret=secret,
            token_endpoint_auth_method=auth_method,
            redirect_uris=[
                "http://localhost:6274/oauth/callback",
                "http://localhost:6274/callback",
                f"{PUBLIC_URL}/callback",
            ],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            client_name="Test Client",
            scope="mcp:tools",
        )

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self.clients[client_info.client_id] = client_info

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        # Generate a unique state parameter for this Google authorization flow
        google_state = secrets.token_urlsafe(16)
        
        # Save ChatGPT/Inspector's authorization parameters in memory mapped by the google_state
        self.auth_sessions[google_state] = {
            "client_id": client.client_id,
            "redirect_uri": str(params.redirect_uri),
            "state": params.state,
            "code_challenge": params.code_challenge,
        }
        
        google_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": f"{PUBLIC_URL}/login/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": google_state,
        }
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(google_params)

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        if authorization_code in self.codes:
            challenge = self.codes[authorization_code]
            redirect_uri = (
                client.redirect_uris[0]
                if client.redirect_uris
                else f"{PUBLIC_URL}/callback"
            )
            return AuthorizationCode(
                code=authorization_code,
                scopes=["mcp:tools"],
                expires_at=time.time() + 300,
                client_id=client.client_id,
                code_challenge=challenge,
                redirect_uri=redirect_uri,
                redirect_uri_provided_explicitly=True,
            )
        return None

    def _generate_jwt(self, client_id: str, scope: str, user_info: dict | None = None) -> str:
        sub_value = "anonymous"
        if user_info:
            email = user_info.get("email")
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    sub_value = str(user.id)
                else:
                    sub_value = email
            except Exception:
                sub_value = email
            finally:
                db.close()

        payload = {
            "iss": f"{PUBLIC_URL}/",
            "sub": sub_value,
            "aud": f"{PUBLIC_URL}/mcp",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "client_id": client_id,
            "scope": scope,
        }
        if user_info:
            payload["user_info"] = user_info
        return jwt.encode(payload, self.JWT_SECRET, algorithm="HS256")

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        user_info = self.codes.get(authorization_code.code + "_userinfo", {})
        jwt_token = self._generate_jwt(
            client.client_id, " ".join(authorization_code.scopes), user_info=user_info
        )
        refresh_token_str = secrets.token_urlsafe(32)

        self.refresh_tokens[refresh_token_str] = RefreshToken(
            token=refresh_token_str,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
        )
        self.refresh_to_user[refresh_token_str] = user_info

        return OAuthToken(
            access_token=jwt_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token_str,
            scope=" ".join(authorization_code.scopes),
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        token_obj = self.refresh_tokens.get(refresh_token)
        if token_obj and token_obj.client_id == client.client_id:
            return token_obj
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Rotate refresh token
        self.refresh_tokens.pop(refresh_token.token, None)
        user_info = self.refresh_to_user.pop(refresh_token.token, {})

        jwt_token = self._generate_jwt(client.client_id, " ".join(scopes), user_info=user_info)
        new_refresh_token_str = secrets.token_urlsafe(32)

        self.refresh_tokens[new_refresh_token_str] = RefreshToken(
            token=new_refresh_token_str,
            client_id=client.client_id,
            scopes=scopes,
        )
        self.refresh_to_user[new_refresh_token_str] = user_info

        return OAuthToken(
            access_token=jwt_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=new_refresh_token_str,
            scope=" ".join(scopes),
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        try:
            payload = jwt.decode(
                token,
                self.JWT_SECRET,
                algorithms=["HS256"],
                audience=f"{PUBLIC_URL}/mcp",
            )
            client_id = payload.get("client_id")
            subject = payload.get("sub")
            scope = payload.get("scope", "mcp:tools")
            expires_at = payload.get("exp")

            if not client_id or not subject or subject == "anonymous":
                return None

            return AccessToken(
                token=token,
                client_id=client_id,
                scopes=scope.split(" "),
                subject=subject,
                expires_at=expires_at,
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        pass



# Create FastMCP instance with "Leetcode AI MCP Server" configuration
app = FastMCP(
    name="Leetcode AI MCP Server",
    instructions="MCP Server that connects to the Leetcode API Server to access authenticated user data.",
    json_response=True,
    # Register the self-contained OAuth Provider
    auth_server_provider=InMemoryOAuthProvider(),
    # Auth settings for RFC 9728 Protected Resource Metadata
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(PUBLIC_URL),  # Authorization Server URL
        resource_server_url=AnyHttpUrl(f"{PUBLIC_URL}/mcp"),  # This server's URL
        required_scopes=["mcp:tools"],
        client_registration_options=ClientRegistrationOptions(
            enabled=True, valid_scopes=["mcp:tools"], default_scopes=["mcp:tools"]
        ),
    ),
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@app.custom_route("/login/google/callback", methods=["GET"])
async def google_callback(request: Request):
    code = request.query_params.get("code")
    google_state = request.query_params.get("state")
    
    if not code or not google_state:
        return JSONResponse({"error": "invalid_request", "error_description": "Missing code or state from Google"}, status_code=400)
        
    provider = app._auth_server_provider
    session = provider.auth_sessions.get(google_state)
    if not session:
        return JSONResponse({"error": "invalid_request", "error_description": "Invalid or expired state session"}, status_code=400)
        
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": f"{PUBLIC_URL}/login/google/callback",
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            if "error" in token_data:
                return JSONResponse(token_data, status_code=400)
                
            google_access_token = token_data.get("access_token")
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )
            user_info = userinfo_response.json()
        except Exception as e:
            return JSONResponse({"error": "server_error", "error_description": str(e)}, status_code=500)
            
    # Google exchange succeeded! Generate local code for client
    local_code = secrets.token_urlsafe(16)
    provider.codes[local_code] = session["code_challenge"]
    provider.codes[local_code + "_userinfo"] = user_info
    
    redirect_uri = construct_redirect_uri(
        session["redirect_uri"],
        code=local_code,
        state=session["state"]
    )
    return RedirectResponse(redirect_uri)


def resolve_username_and_load_cookies(requested_username: str = None) -> str:
    """
    Resolves the target username and loads their Leetcode cookies into cookie_store.
    If requested_username is None, uses the authenticated user's Leetcode username.
    """
    token_info = get_access_token()
    user_id = token_info.subject if token_info else None
    
    db = SessionLocal()
    try:
        if requested_username:
            account = db.query(LeetcodeAccount).filter(LeetcodeAccount.leetcode_username == requested_username).first()
            if not account:
                raise Exception(f"Leetcode account for '{requested_username}' is not connected.")
        else:
            if not user_id or user_id == "anonymous":
                user = db.query(User).first()
            else:
                user = db.query(User).filter(User.id == UUID(user_id)).first()
                if not user:
                    user = db.query(User).first()
            
            if not user or not user.leetcode_account:
                raise Exception("Authentication required or no Leetcode account connected to your profile.")
                
            account = user.leetcode_account
            
        username = account.leetcode_username
        
        # Load/update cookies in cookie_store
        if account.encrypted_cookies:
            cookies = decrypt_cookie(account.encrypted_cookies)
            cookie_store[username] = cookies
            
        return username
    finally:
        db.close()


@app.tool()
async def connect_leetcode_account(leetcode_session: str, csrf_token: str) -> str:
    """
    Connect your Leetcode account to your profile using session cookies.
    """
    token_info = get_access_token()
    if not token_info or not token_info.subject:
        return "Authentication required. Please authenticate the MCP client first."
    
    user_id = token_info.subject
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            user = db.query(User).first()
        if not user:
            return "User not found in database."
            
        account = await LeetcodeService.connect_account(
            db=db,
            user=user,
            leetcode_session=leetcode_session,
            csrf_token=csrf_token,
        )
        return f"Successfully connected Leetcode account: {account.leetcode_username}"
    except Exception as e:
        return f"Failed to connect account: {str(e)}"
    finally:
        db.close()


@app.tool()
async def get_profile_details(username: str = None) -> dict:
    """
    Get the profile details for a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_profile(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_solved_statistics(username: str = None) -> dict:
    """
    Get the solved problem statistics (counts by difficulty) for a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_solved_stats(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_user_ranking_and_contributions(username: str = None) -> dict:
    """
    Get the ranking and contributions points for a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_ranking_and_contributions(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_user_topic_stats(username: str = None) -> dict:
    """
    Get the detailed topic stats (solved counts by advanced, intermediate, fundamental topics) for a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_topic_stats(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_user_language_stats(username: str = None) -> dict:
    """
    Get solved problem counts by programming language for a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_language_stats(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_problem_details(titleSlug: str, username: str = None) -> dict:
    """
    Get detail of a specific Leetcode question by its titleSlug.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_problem_detail(target_username, titleSlug)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_similar_problems_list(titleSlug: str, username: str = None) -> dict:
    """
    Get similar problems and next challenges for a specific Leetcode question by its titleSlug.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_similar_problems(target_username, titleSlug)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_daily_leetcode_challenge(username: str = None) -> dict:
    """
    Get the active Leetcode Daily Coding Challenge details.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_daily_problem(target_username)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_contest_rating_details(username: str = None) -> dict:
    """
    Get the contest ranking and rating details of a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        res = await get_contest_rating(target_username)
        return res if res else {"message": "No contest rating found."}
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_contest_participation_history(username: str = None) -> list:
    """
    Get the complete contest participation history of a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        res = await get_contest_history(target_username)
        return res if res else []
    except Exception as e:
        return [{"error": str(e)}]


@app.tool()
async def get_contest_questions_list(contest_slug: str, username: str = None) -> dict:
    """
    Get the list of questions of a specific Leetcode contest by its slug.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        res = await get_contest_question(target_username, contest_slug)
        return res if res else {"message": "Contest question list not found."}
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_user_contest_result(contest_slug: str, username: str = None) -> dict:
    """
    Get the detailed result (rank, problems solved, total time, rating) of a Leetcode user for a specific contest.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_contest_result(target_username, contest_slug)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_upcoming_contests_list(username: str = None) -> list:
    """
    Get the upcoming Leetcode contests.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        res = await get_upcoming_contests(target_username)
        return res if res else []
    except Exception as e:
        return [{"error": str(e)}]


@app.tool()
async def get_user_latest_submission(username: str = None) -> dict:
    """
    Get the details of the latest submission made by a Leetcode user.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        res = await get_latest_submission(target_username)
        return res if res else {"message": "No submissions found."}
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_leetcode_submission_detail(submission_id: str, username: str = None) -> dict:
    """
    Get full details of a specific Leetcode submission (including source code, runtime, memory, correctness) by its ID.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_submission_detail(target_username, submission_id)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_recent_submissions(limit: int = 20, offset: int = 0, username: str = None) -> dict:
    """
    Get recent submissions list of a Leetcode user (maximum limit 20).
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_submissions(target_username, limit, offset)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_question_submission_history(questionSlug: str, limit: int = 20, offset: int = 0, username: str = None) -> dict:
    """
    Get the list of all historical submissions of a Leetcode user for a specific question.
    """
    try:
        target_username = resolve_username_and_load_cookies(username)
        return await get_submission_history(target_username, questionSlug, limit, offset)
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_leetcode_profile() -> str:
    """
    Retrieve the connected Leetcode profile details for the authenticated user.
    """
    token_info = get_access_token()
    if not token_info or not token_info.subject:
        return "Authentication required. Please authenticate the MCP client first."
        
    user_id = token_info.subject
    db = SessionLocal()
    try:
        # Try to look up the user by ID
        try:
            user = db.query(User).filter(User.id == UUID(user_id)).first()
        except Exception:
            user = None
            
        # Fallback to the first available user in database for mock testing/test-token!
        if not user:
            user = db.query(User).first()
            
        if not user:
            return "No users found in database."
            
        account = user.leetcode_account
        if not account:
            return (
                f"Hello {user.name}!\n"
                f"No Leetcode account is currently connected to your profile. "
                f"Please link your Leetcode account using the browser extension."
            )
            
        last_synced_str = account.last_synced.strftime('%Y-%m-%d %H:%M:%S') if account.last_synced else 'Never'
        return (
            f"Hello {user.name}!\n"
            f"Connected Leetcode Account: {account.leetcode_username}\n"
            f"Last Synced: {last_synced_str}"
        )
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return f"Error retrieving profile: {str(e)}"
    finally:
        db.close()


# Get Starlette ASGI app and add CORSMiddleware to expose headers to web-based clients
asgi_app = app.streamable_http_app()
asgi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "Mcp-Session-Id", "Authorization"],
)


def main():
    logger.info("Starting Leetcode AI MCP Server on port 8000...")
    logger.info(f"OAuth Issuer: {PUBLIC_URL}")
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
