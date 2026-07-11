import sys
from pathlib import Path

# Add project root directory to sys.path to resolve root-level imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import jwt
from mcp.server.auth.provider import AccessToken, TokenVerifier
from config import settings

class JWTTokenVerifier(TokenVerifier):
    """
    Token verifier that validates JWT access tokens issued by the FastAPI server
    using the shared JWT_SECRET.
    """
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            # Decode the token using jwt
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            
            # Ensure it is an access token
            if payload.get("type") != "access":
                return None
                
            user_id = payload.get("sub")
            expires_at = payload.get("exp")
            
            # Construct the AccessToken expected by the MCP SDK
            return AccessToken(
                token=token,
                client_id="mcp-client",
                scopes=["mcp:tools"],
                expires_at=expires_at,
                subject=user_id,
                claims=payload
            )
        except Exception:
            # Any validation failure (expired, invalid signature, etc.) returns None
            return None
