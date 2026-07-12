# LeetCode AI API & MCP Server

A unified API and Model Context Protocol (MCP) server that interfaces with LeetCode. It allows you to fetch authenticated profile statistics, contest history, similar questions, and detailed submissions with source code. 

This project integrates a **FastAPI backend** (for Chrome extensions or web frontends) and a **FastMCP Server** (to expose LeetCode tools directly to AI assistants like ChatGPT, Claude Desktop, and Cursor) into a single, unified service.

---

## Features

- **LeetCode Integration**: Fetch profiles, solved counts, contest ratings, contest history, similar questions, daily challenges, and historical submission codes.
- **Unified Port Architecture**: Both the FastAPI Web API routes and the FastMCP endpoints run concurrently on the same port (`8000`), simplifying deployment and tunneling.
- **Persistent OAuth 2.1**: A database-backed OAuth provider using PostgreSQL to manage clients, auth sessions, codes, and refresh tokens securely across server restarts.
- **Dynamic CORS Middleware**: Custom middleware dynamically handles requests from both the Chrome extension (with credentials) and web-based MCP clients.
- **Docker Ready**: Pre-configured Dockerfiles and Docker Compose setup utilizing `uv` for ultra-fast, lightweight container builds.

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) & [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
- **Database**: PostgreSQL (using [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) migrations)
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (built in Rust for speed)
- **Containerization**: Docker & Docker Compose

---

## Configuration (`.env`)

Create a `.env` file in the root directory. Here is a template:

```env
# Google OAuth Credentials (for signing in)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# JWT Signing Secret (must remain persistent)
JWT_SECRET=your-secure-jwt-secret-key

# Secret key for encrypting user LeetCode session cookies in the database
COOKIE_ENCRYPTION_KEY=your-cookie-encryption-key

# Database Connection (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/leetcode_ai

# Public Access URL (pointing to port 8000, e.g. your public URL)
MCP_BASE_URL=your-public-mcp-server-url
```

> [!IMPORTANT]
> If you are running locally without a public tunnel, set `MCP_BASE_URL` to `http://localhost:8000`.

---

## Installation & Setup

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd Leetcode-API-Server
   ```

2. **Install dependencies** using `uv`:
   ```bash
   uv sync
   ```

3. **Run database migrations** to create all tables (including users, accounts, and MCP OAuth tables):
   ```bash
   uv run alembic upgrade head
   ```

4. **Run the unified server** locally on port `8000`:
   ```bash
   uv run python mcp_server/server.py
   ```

---

## Connecting to MCP Clients

### 1. Claude Desktop Setup
Add the server configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leetcode-ai": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client-sse",
        "https://your-tunnel-subdomain.ngrok-free.app/sse"
      ]
    }
  }
}
```

### 2. ChatGPT or Custom SSE Gateways
Configure the gateway with the following URLs:
*   **SSE URL**: `https://your-tunnel-subdomain.ngrok-free.app/sse`
*   **Authorization Endpoint**: `https://your-tunnel-subdomain.ngrok-free.app/auth/oauth/authorize`
*   **Token Endpoint**: `https://your-tunnel-subdomain.ngrok-free.app/auth/oauth/token`
*   **Required Scopes**: `mcp:tools`

---

## Docker & Deployment

We use multi-stage builds copying the `uv` binary to keep container sizes small.

### Build the Images

- **Web API Server (Standalone)**:
  ```bash
  docker build -t leetcode-api -f Dockerfile.api .
  ```

- **MCP + Unified Server (Recommended)**:
  ```bash
  docker build -t leetcode-mcp -f Dockerfile.mcp .
  ```

### Run using Docker Compose
Orchestrate the API, MCP, and a PostgreSQL database container together in one command:
```bash
docker compose up --build
```
