import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp.shared.auth import OAuthClientInformationFull
from mcp_server.server import DatabaseOAuthProvider

async def main():
    provider = DatabaseOAuthProvider()
    
    # Simulate a dynamic client registration request
    client_info = OAuthClientInformationFull(
        client_id="test-register-client-id-123",
        client_secret="some-secret",
        token_endpoint_auth_method="none",
        redirect_uris=[
            "http://localhost:6274/oauth/callback"
        ],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        client_name="Test Dynamic Client",
        scope="mcp:tools"
    )
    
    print("Testing register_client...")
    try:
        await provider.register_client(client_info)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
