import os
import sys
import logging
from uuid import UUID
from pathlib import Path
from pydantic import AnyHttpUrl

# Add project root directory to sys.path to resolve root-level imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.middleware.auth_context import get_access_token

from config import settings
from database.session import SessionLocal
from model.user import User
from model.leetcode_account import LeetcodeAccount
from mcp_server.token_verifier import JWTTokenVerifier

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Load base URLs
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000").rstrip("/")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000").rstrip("/")

# Initialize FastMCP Server with AuthSettings and JWTTokenVerifier
app = FastMCP(
    name="Leetcode AI MCP Server",
    instructions="MCP Server that connects to the Leetcode API Server to access authenticated user data.",
    host="0.0.0.0",
    port=8000,
    token_verifier=JWTTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(API_BASE_URL),
        required_scopes=["mcp:tools"],
        resource_server_url=AnyHttpUrl(MCP_BASE_URL),
    )
)

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
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            return "User account not found."
            
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

import uvicorn
from starlette.middleware.cors import CORSMiddleware

# Get the Starlette ASGI app from FastMCP
asgi_app = app.streamable_http_app()

# Add CORS middleware to allow web clients to connect and expose crucial headers
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
    logger.info(f"Authorization Server (Issuer): {API_BASE_URL}")
    logger.info(f"Resource Server: {MCP_BASE_URL}")
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
